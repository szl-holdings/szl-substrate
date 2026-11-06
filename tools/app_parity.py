#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Report which szl_substrate modules are byte-identical to the app copies.

    python tools/app_parity.py a11oy=../a11oy killinchu=../killinchu [--json]

For every module in src/szl_substrate/ (``__init__.py`` excluded) the report
compares the package file with each app's top-level copy (``<checkout>/<module>``)
and the apps' copies with each other. It only reads files: it fetches nothing
and never imports or runs app code. When a checkout is a git work tree its
``git rev-parse HEAD`` is recorded, so a report names the commits it describes
(uncommitted edits in the work tree are compared as they are).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent.parent / "src" / "szl_substrate"


def package_modules(package_dir: Path | None = None) -> list[str]:
    package_dir = package_dir or PACKAGE_DIR
    return sorted(p.name for p in package_dir.glob("*.py") if p.name != "__init__.py")


def git_head(path: Path) -> str | None:
    try:
        proc = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def compare(apps: dict[str, Path], package_dir: Path | None = None) -> dict[str, Any]:
    package_dir = package_dir or PACKAGE_DIR
    modules = package_modules(package_dir)
    report: dict[str, Any] = {"modules": len(modules), "apps": {}, "between_apps": {}}
    copies: dict[str, dict[str, bytes]] = {}
    for name, root in apps.items():
        identical, different, missing = [], [], []
        copies[name] = {}
        for module in modules:
            app_file = root / module
            if not app_file.is_file():
                missing.append(module)
                continue
            data = app_file.read_bytes()
            copies[name][module] = data
            same = data == (package_dir / module).read_bytes()
            (identical if same else different).append(module)
        report["apps"][name] = {"path": str(root), "head": git_head(root),
                                "identical": identical, "different": different,
                                "missing": missing}
    names = sorted(apps)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            shared = sorted(set(copies[first]) & set(copies[second]))
            report["between_apps"][f"{first}~{second}"] = {
                "identical": [m for m in shared if copies[first][m] == copies[second][m]],
                "different": [m for m in shared if copies[first][m] != copies[second][m]],
            }
    return report


def _names(modules: list[str]) -> str:
    return ", ".join(m[:-3] for m in modules)


def render(report: dict[str, Any]) -> str:
    total = report["modules"]
    lines = []
    for name, app in report["apps"].items():
        lines.append(f"{name} ({app['head'] or 'no git HEAD'}): "
                     f"{len(app['identical'])}/{total} byte-identical to the package, "
                     f"{len(app['different'])} differ, {len(app['missing'])} missing")
        if app["different"]:
            lines.append(f"  differ: {_names(app['different'])}")
        if app["missing"]:
            lines.append(f"  missing: {_names(app['missing'])}")
    for pair, result in report["between_apps"].items():
        shared = len(result["identical"]) + len(result["different"])
        lines.append(f"{pair}: {len(result['identical'])}/{shared} copies byte-identical "
                     "between the apps")
        if result["different"]:
            lines.append(f"  differ: {_names(result['different'])}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("apps", nargs="+", metavar="NAME=PATH",
                        help="an app checkout, e.g. a11oy=../a11oy")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)
    apps: dict[str, Path] = {}
    for spec in args.apps:
        name, sep, path = spec.partition("=")
        if not sep or not name or not path:
            parser.error(f"expected NAME=PATH, got {spec!r}")
        if name in apps:
            parser.error(f"app {name!r} given twice")
        root = Path(path)
        if not root.is_dir():
            parser.error(f"{path} is not a directory")
        apps[name] = root
    report = compare(apps)
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
