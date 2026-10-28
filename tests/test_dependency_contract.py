"""Dependency contract for szl-substrate (stdlib only; executes no package code).

Every non-stdlib import under src/szl_substrate/ must be classified here, and the
classification must agree with pyproject.toml:

* DECLARED       the distribution is listed in core ([project].dependencies) or in the
                 named extras.
* GUARDED_ONLY   deliberately undeclared; allowed only while every import site sits in
                 ``try: ... except ImportError`` within the same scope.
* HOST_PROVIDED  modules supplied by the host application (a11oy / killinchu), not by
                 any distribution.

``import szl_substrate`` must need nothing beyond core: no module it executes may import
a non-core, non-stdlib name unguarded at module scope. Unclassified imports fail closed.
pyproject.toml is read with a minimal reader so the test also runs on Python 3.10 (no
tomllib); wherever tomllib exists the reader is cross-checked against it. The negative
controls at the end show that each check can fail.
"""
from __future__ import annotations

import ast
import functools
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    tomllib = None

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "src" / "szl_substrate"

# import name -> (distribution, groups that must list it); "core" is [project].dependencies.
DECLARED = {
    "cryptography": ("cryptography", ("core",)),
    "fastapi": ("fastapi", ("web",)),
    "starlette": ("starlette", ("web",)),
    "httpx": ("httpx", ("web", "rag")),
    "numpy": ("numpy", ("rag",)),
    "lmdb": ("lmdb", ("khipu",)),
    "sigstore": ("sigstore", ("sigstore",)),
}
RUNTIME_EXTRAS = ("web", "rag", "khipu", "sigstore")  # the "all" extra lists exactly their union
# import name -> distribution that would provide it; every import site must be guarded.
GUARDED_ONLY = {
    "faiss": "faiss-cpu",
    "huggingface_hub": "huggingface-hub",
    "llama_cpp": "llama-cpp-python",
    "opentelemetry": "opentelemetry-api",
    "pydantic": "pydantic",
    "sentence_transformers": "sentence-transformers",
    "slowapi": "slowapi",
    "sqlite_vss": "sqlite-vss",
    "z3": "z3-solver",
}
HOST_PROVIDED = frozenset({
    "a11oy_active_flux_router", "a11oy_code_orchestrator", "serve", "szl_agent_loop_banach",
    "szl_cheapest_watt", "szl_connectors", "szl_corpus_publish", "szl_energy_operator",
    "szl_jack", "szl_ltc_dynamics", "szl_model_harness", "szl_router", "szl_sgh_scheduler",
    "szl_wire",
})
_GUARDS = {"ImportError", "ModuleNotFoundError", "Exception", "BaseException"}


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _dist_name(requirement: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    if not match:
        raise ValueError(f"unparseable requirement: {requirement!r}")
    return _norm(match.group(1))


def _catches_import_error(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    types = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    return any(getattr(t, "id", getattr(t, "attr", None)) in _GUARDS for t in types)


def _is_main_block(node: ast.AST) -> bool:
    test = getattr(node, "test", None)
    return (isinstance(node, ast.If) and isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name) and test.left.id == "__name__"
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__")


def _imported_names(node: ast.AST) -> list[str]:
    """Names an import (or a literal __import__/import_module call) loads.

    Imports of this package's own modules come back as ".<module>".
    """
    if isinstance(node, ast.Import):
        dotted = [alias.name for alias in node.names]
    elif isinstance(node, ast.ImportFrom):
        if node.level:
            return ["." + (node.module or alias.name).split(".")[0] for alias in node.names]
        if node.module == "szl_substrate":
            return ["." + alias.name for alias in node.names]
        dotted = [node.module]
    elif (isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant)
          and isinstance(node.args[0].value, str)
          and getattr(node.func, "id", getattr(node.func, "attr", None)) in ("__import__", "import_module")):
        dotted = [node.args[0].value]
    else:
        return []
    parts = [name.split(".") for name in dotted]
    return ["." + p[1] if p[0] == "szl_substrate" and len(p) > 1 else p[0] for p in parts]


def import_sites(sources: dict[str, str]) -> list[tuple[str, str, int, str, bool]]:
    """(name, module, line, scope, guarded) for every import in ``sources`` ({module: text}).

    scope is "module" (runs on import), "function" (runs when called) or "main" (an
    ``if __name__ == "__main__":`` self-test); guarded means a ``try`` in the same scope
    catches ImportError around the import.
    """
    sites: list[tuple[str, str, int, str, bool]] = []

    def visit(node: ast.AST, module: str, scope: str, guarded: bool) -> None:
        for field, value in ast.iter_fields(node):
            for child in value if isinstance(value, list) else [value]:
                if not isinstance(child, ast.AST):
                    continue
                inner_scope, inner_guarded = scope, guarded
                if field == "body" and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                    inner_scope, inner_guarded = ("main" if scope == "main" else "function"), False
                elif field == "body" and isinstance(node, ast.Try):
                    inner_guarded = guarded or any(_catches_import_error(h) for h in node.handlers)
                elif field == "body" and _is_main_block(node):
                    inner_scope = "main"
                for name in _imported_names(child):
                    sites.append((name, module, child.lineno, inner_scope, inner_guarded))
                visit(child, module, inner_scope, inner_guarded)

    for module, text in sorted(sources.items()):
        visit(ast.parse(text, filename=module), module, "module", False)
    return sites


def _external(sites):
    """Sites that load something from neither the stdlib nor this package's namespace."""
    return [s for s in sites if not s[0].startswith(".") and s[0] != "szl_substrate"
            and s[0] not in sys.stdlib_module_names]


def classification_problems(sites, package_modules) -> list[str]:
    problems = []
    for name, module, line, _scope, guarded in _external(sites):
        if name in package_modules or name in DECLARED or name in HOST_PROVIDED:
            continue
        if name not in GUARDED_ONLY:
            problems.append(f"{module}:{line} imports unclassified {name!r}; "
                            "add it to DECLARED, GUARDED_ONLY or HOST_PROVIDED")
        elif not guarded:
            problems.append(f"{module}:{line} imports {name!r} without an ImportError guard; "
                            f"declare {GUARDED_ONLY[name]!r} and move it to DECLARED")
    return problems


def import_time_closure(sites) -> set[str]:
    """Modules that ``import szl_substrate`` executes: __init__ plus module-scope
    imports of the package's own modules, transitively."""
    edges: dict[str, set[str]] = {}
    for name, module, _line, scope, _guarded in sites:
        if scope == "module" and name.startswith("."):
            edges.setdefault(module, set()).add(name[1:])
    closure, todo = set(), ["__init__"]
    while todo:
        module = todo.pop()
        if module not in closure:
            closure.add(module)
            todo.extend(edges.get(module, ()))
    return closure


def import_time_problems(sites) -> list[str]:
    core = {name for name, (_dist, groups) in DECLARED.items() if "core" in groups}
    closure = import_time_closure(sites)
    return [(f"`import szl_substrate` runs {module}:{line}, an unguarded import of {name!r}; "
             "only core dependencies may load at import time")
            for name, module, line, scope, guarded in _external(sites)
            if module in closure and scope == "module" and not guarded and name not in core]


def declaration_problems(declared: dict[str, list[str]]) -> list[str]:
    """``declared`` maps "core" and each extra to its requirement strings."""
    listed = {group: {_dist_name(r) for r in reqs} for group, reqs in declared.items()}
    problems = [f"{dist} missing from [{group}] (imported as {name!r})"
                for name, (dist, groups) in sorted(DECLARED.items()) for group in groups
                if _norm(dist) not in listed.get(group, set())]
    union = {re.sub(r"\s+", "", r) for g in RUNTIME_EXTRAS for r in declared.get(g, [])}
    if {re.sub(r"\s+", "", r) for r in declared.get("all", [])} != union:
        problems.append("the all extra differs from the union of " + ", ".join(RUNTIME_EXTRAS))
    return problems


_TABLE = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")
_ARRAY = re.compile(r'^\s*"?([A-Za-z0-9_.-]+)"?\s*=\s*(\[.*)$')


def _minimal_reader(text: str) -> dict[str, list[str]]:
    """String arrays of [project].dependencies and [project.optional-dependencies]."""
    groups: dict[str, list[str]] = {}
    table, key, buffer = "", None, ""
    for line in text.splitlines():
        if key is None:
            header, array = _TABLE.match(line), _ARRAY.match(line)
            if header:
                table = header.group(1).strip()
            if not array or not (table == "project.optional-dependencies"
                                 or (table == "project" and array.group(1) == "dependencies")):
                continue
            key, buffer = ("core" if table == "project" else array.group(1)), array.group(2)
        else:
            buffer += "\n" + line
        try:
            value = ast.literal_eval(buffer)
        except SyntaxError:
            continue  # the array continues on the next line
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ValueError(f"pyproject.toml: {key!r} is not an array of strings")
        groups[key], key = value, None
    if key is not None:
        raise ValueError(f"pyproject.toml: array {key!r} is never closed")
    return groups


def read_declared(text: str) -> dict[str, list[str]]:
    groups = _minimal_reader(text)
    if tomllib is not None:
        project = tomllib.loads(text).get("project", {})
        expected = dict(project.get("optional-dependencies", {}))
        if "dependencies" in project:
            expected["core"] = project["dependencies"]
        if groups != expected:
            raise AssertionError(f"minimal reader {groups} != tomllib {expected}")
    return groups


@functools.cache
def _scan() -> tuple[frozenset[str], tuple]:
    sources = {p.stem: p.read_text(encoding="utf-8") for p in sorted(PACKAGE_DIR.glob("*.py"))}
    return frozenset(sources), tuple(import_sites(sources))


def _declared() -> dict[str, list[str]]:
    return read_declared((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_every_third_party_import_is_classified():
    modules, sites = _scan()
    assert classification_problems(sites, modules) == []


def test_classification_matches_what_the_package_imports():
    # The scan must see every classified name: stale entries and an empty scan both fail.
    modules, sites = _scan()
    seen = {site[0] for site in _external(sites)} - modules
    assert set(DECLARED) | set(GUARDED_ONLY) | HOST_PROVIDED == seen


def test_pyproject_declares_every_declared_import():
    assert declaration_problems(_declared()) == []


def test_import_szl_substrate_needs_only_core():
    _, sites = _scan()
    closure = import_time_closure(sites)
    assert {"__init__", "szl_dsse", "szl_rag"} <= closure and "operator_shell_v4" not in closure
    assert import_time_problems(sites) == []


PRE_FIX_PYPROJECT = """\
[project]
dependencies = ["cryptography>=42"]

[project.optional-dependencies]
dev = [
    "pytest>=8",
]
"""


def test_negative_control_pre_fix_pyproject_is_rejected():
    problems = declaration_problems(read_declared(PRE_FIX_PYPROJECT))
    assert sorted(p.split()[0] for p in problems) == [
        "fastapi", "httpx", "httpx", "lmdb", "numpy", "sigstore", "starlette"]


def test_negative_control_all_extra_drift_is_rejected():
    extras = {"web": ["fastapi>=1", "starlette>=1", "httpx>=1"], "rag": ["httpx>=1", "numpy>=2"],
              "khipu": ["lmdb>=2"], "sigstore": ["sigstore>=4"]}
    declared = {"core": ["cryptography>=42"], **extras,
                "all": ["fastapi>=1", "starlette>=1", "httpx>=1", "numpy>=2", "lmdb>=2", "sigstore>=4"]}
    assert declaration_problems(declared) == []
    declared["all"] = declared["all"][:-1]
    assert declaration_problems(declared) == [
        "the all extra differs from the union of web, rag, khipu, sigstore"]


def test_negative_control_unclassified_import_fails_closed():
    sites = import_sites({"m": "import requests\n"})
    assert classification_problems(sites, {"m"}) == [
        "m:1 imports unclassified 'requests'; add it to DECLARED, GUARDED_ONLY or HOST_PROVIDED"]


def test_negative_control_unguarded_optional_import_is_rejected():
    guarded = "try:\n    import faiss\nexcept ImportError:\n    faiss = None\n"
    in_function = "def f():\n    import faiss\n"
    guard_outside_def = "try:\n    def f():\n        import faiss\nexcept ImportError:\n    pass\n"
    assert classification_problems(import_sites({"m": guarded}), {"m"}) == []
    for source in (in_function, guard_outside_def):
        assert len(classification_problems(import_sites({"m": source}), {"m"})) == 1


def test_negative_control_import_time_dependency_is_rejected():
    sources = {"__init__": "from . import web\n", "web": "from fastapi import FastAPI\n"}
    assert import_time_problems(import_sites(sources)) == [
        ("`import szl_substrate` runs web:1, an unguarded import of 'fastapi'; "
         "only core dependencies may load at import time")]
    sources["web"] = 'if __name__ == "__main__":\n    from fastapi import FastAPI\n'
    assert import_time_problems(import_sites(sources)) == []
