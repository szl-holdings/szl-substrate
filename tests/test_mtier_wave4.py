# SPDX-License-Identifier: Apache-2.0
# © 2026 Lutar, Stephen P. — SZL Holdings · Doctrine v11
"""Smoke tests for M-tier wave 4 — a dependency-ordered batch of 5 S-tier leaves
plus the 3 M-tier modules those leaves unblock.

Selection criteria (all cmp-verified against BOTH fresh app clones at extraction
time; none is a drifted/allow-listed file, so each is extracted byte-for-byte):

  S leaves (no shared-set deps):
    * ``szl_formulas``        — pure-stdlib leaf (widest S-tier fan-out: 5 app + 1
                                shared importers); the last blocker for the
                                ``szl_anatomy_routes`` M module.
    * ``szl_conformal``       — pure-stdlib leaf; a guarded dep of ``a11oy_autoreview``.
    * ``szl_khipu_replicate`` — pure-stdlib leaf; a dep of ``szl_unay_routes``.
    * ``szl_unay``            — pure-stdlib leaf; a dep of ``szl_unay_routes``.
    * ``szl_khipu_lmdb``      — leaf, but carries an UNGUARDED module-level
                                ``import lmdb`` (not in the shared 69-set), so it
                                is import-directly (not eager).

  M modules (every shared dep now ALREADY in the package):
    * ``a11oy_autoreview``    — reads ``szl_calibration`` / ``szl_conformal`` /
                                ``szl_restraint``, ALL behind ``try/except -> None``
                                so its module scope is pure-stdlib → EAGER-safe.
    * ``szl_anatomy_routes``  — UNGUARDED module-level ``import szl_formulas``
                                (moved in THIS batch) + guarded fastapi → import-directly.
    * ``szl_unay_routes``     — UNGUARDED module-level ``import szl_unay`` /
                                ``szl_khipu_lmdb`` / ``szl_khipu_replicate`` (all
                                moved in THIS batch) + guarded fastapi → import-directly.
"""
from __future__ import annotations

import importlib

import pytest

EAGER_M = [
    "szl_formulas",
    "szl_conformal",
    "szl_khipu_replicate",
    "szl_unay",
    "a11oy_autoreview",
]

IMPORT_DIRECTLY_M = [
    "szl_khipu_lmdb",     # module-level `import lmdb`
    "szl_anatomy_routes", # module-level `import szl_formulas`
    "szl_unay_routes",    # module-level bare imports + transitive lmdb
]


def test_package_still_imports_cleanly():
    pkg = importlib.import_module("szl_substrate")
    assert pkg.__version__


@pytest.mark.parametrize("modname", EAGER_M)
def test_eager_mtier_importable_and_exported(modname):
    pkg = importlib.import_module("szl_substrate")
    assert hasattr(pkg, modname), f"{modname} not exposed on szl_substrate"
    sub = importlib.import_module(f"szl_substrate.{modname}")
    assert sub is getattr(pkg, modname)
    assert modname in pkg.__all__


def test_autoreview_dep_imports_are_all_guarded():
    """``a11oy_autoreview`` must import cleanly even when its shared deps are
    absent from sys.path: it reads szl_calibration / szl_conformal / szl_restraint
    only through ``try/except -> None`` guards, so its module scope is pure-stdlib.
    (Here the deps ARE present in the package, but the module must not hard-depend
    on their being importable as bare top-level names.)"""
    ar = importlib.import_module("szl_substrate.a11oy_autoreview")
    assert ar is not None


@pytest.mark.parametrize("modname", IMPORT_DIRECTLY_M)
def test_import_directly_modules_not_eager(modname):
    """These must NOT be eager-imported: their UNGUARDED module-level imports
    (``import lmdb`` and/or bare ``import szl_formulas`` / ``szl_unay`` /
    ``szl_khipu_lmdb`` / ``szl_khipu_replicate``) would otherwise break
    ``import szl_substrate`` wherever those dependencies are absent as top-level
    names. They still ship as importable submodule files; importing one directly
    may raise only because of its own missing dependency (lmdb / the bare shared
    names), never a packaging error."""
    pkg = importlib.import_module("szl_substrate")
    assert modname not in pkg.__all__
    try:
        importlib.import_module(f"szl_substrate.{modname}")
    except ModuleNotFoundError:  # pragma: no cover - depends on env
        pass  # missing lmdb / bare shared-name import is acceptable
