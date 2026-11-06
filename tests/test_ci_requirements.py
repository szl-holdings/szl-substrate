"""The hash-locked CI requirement files stay in step with pyproject.toml.

ci.yml and base-python-ci.yml install every distribution from
requirements/ci/<lock>.txt with --require-hashes and then install the package
with --no-deps, so pip never checks the locks against what pyproject.toml
declares. These tests do: each .in file repeats the pyproject specifiers of the
groups its workflow needs, every pin in the compiled .txt carries hashes and
satisfies those specifiers, and the workflows install nothing unhashed.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

from tests.test_dependency_contract import _dist_name, _norm, read_declared

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_DIR = REPO_ROOT / "requirements" / "ci"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

# lock -> (pyproject groups it carries verbatim, extra build/lint tools, workflow)
LOCKS = {
    "test": (("core", "dev", "web"), {"hatchling", "editables"}, "ci.yml"),
    "base": (("core", "dev"), {"hatchling", "editables", "ruff"}, "base-python-ci.yml"),
}
_PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==(\S+)")
_PIP_INSTALL = re.compile(r"pip\s+install\b[^\n]*")


def _in_requirements(lock: str) -> list[str]:
    text = (CI_DIR / f"{lock}.in").read_text(encoding="utf-8")
    lines = (line.split("#", 1)[0].strip() for line in text.splitlines())
    return [line for line in lines if line]


def _pins(lock: str) -> dict[str, list[tuple[str, int]]]:
    """Normalized distribution -> [(pinned version, number of sha256 hashes)]."""
    text = (CI_DIR / f"{lock}.txt").read_text(encoding="utf-8")
    pins: dict[str, list[tuple[str, int]]] = {}
    for block in re.split(r"\n(?=\S)", text):
        match = _PIN.match(block)
        if match:
            pins.setdefault(_norm(match.group(1)), []).append(
                (match.group(2), block.count("--hash=sha256:")))
    return pins


@pytest.mark.parametrize("lock", sorted(LOCKS))
def test_in_file_repeats_the_pyproject_specifiers(lock):
    groups, tools, _workflow = LOCKS[lock]
    declared = read_declared((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    expected = {re.sub(r"\s+", "", r) for g in groups for r in declared[g]} | tools
    assert {re.sub(r"\s+", "", r) for r in _in_requirements(lock)} == expected


@pytest.mark.parametrize("lock", sorted(LOCKS))
def test_every_pin_is_hashed_and_satisfies_its_specifier(lock):
    pins = _pins(lock)
    assert pins, f"{lock}.txt pins nothing"
    for dist, entries in pins.items():
        for version, hashes in entries:
            assert hashes > 0, f"{lock}.txt pins {dist}=={version} without a hash"
    for line in _in_requirements(lock):
        requirement = Requirement(line)
        entries = pins.get(_dist_name(line))
        assert entries, f"{lock}.txt does not pin {requirement.name}; recompile it"
        for version, _hashes in entries:
            assert requirement.specifier.contains(Version(version), prereleases=True), (
                f"{lock}.txt pins {requirement.name}=={version}, outside {line!r}; recompile it")


@pytest.mark.parametrize("lock", sorted(LOCKS))
def test_workflow_installs_only_from_the_hashed_lock(lock):
    _groups, _tools, workflow = LOCKS[lock]
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    assert f"--require-hashes -r requirements/ci/{lock}.txt" in text
    installs = _PIP_INSTALL.findall(text)
    assert installs
    for command in installs:
        assert "--require-hashes" in command or "--no-deps" in command, command


def test_test_extra_is_the_dev_extra_plus_the_web_extra():
    declared = read_declared((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert sorted(declared["test"]) == sorted(set(declared["dev"]) | set(declared["web"]))
