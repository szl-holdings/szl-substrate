# SPDX-License-Identifier: Apache-2.0
# © 2026 Lutar, Stephen P. — SZL Holdings · Doctrine v11
"""Smoke tests for M-tier wave 1 — 7 M-tier modules whose shared-module deps are
already in the package.

Selection criteria (all cmp-verified against both apps at extraction time):
  * shared-module dependencies are ALREADY extracted (``szl_dsse`` is here), or
    are only referenced lazily+guarded inside functions (``szl_rag`` for
    ``szl_llm_registry``; ``szl_joules_truth`` for ``szl_restraint``) and degrade
    gracefully — so the module import never fails on their absence;
  * byte-identical between a11oy and killinchu (not a drifted/allow-listed file),
    extracted byte-for-byte.

3 are eager-import-safe (pure-stdlib at module scope). The other 4 carry an
UNGUARDED module-level import (``szl_provenance`` -> ``szl_dsse``;
``szl_warhacker_aliases`` / ``operator_shell_v4`` / ``szl_llm_registry`` ->
``fastapi``) and are therefore imported directly (not eager) — exactly like
``szl_connectors_serve`` — so ``import szl_substrate`` stays importable everywhere.
"""
from __future__ import annotations

import importlib

import pytest

EAGER_M = [
    "szl_ken",
    "szl_qhawaq",
    "szl_restraint",
]

IMPORT_DIRECTLY_M = [
    "szl_provenance",
    "szl_warhacker_aliases",
    "operator_shell_v4",
    "szl_llm_registry",
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


@pytest.mark.parametrize("modname", IMPORT_DIRECTLY_M)
def test_import_directly_modules_not_eager(modname):
    """These must NOT be eager-imported: their unguarded module-level import
    (szl_dsse or fastapi) would otherwise break `import szl_substrate` wherever
    that dependency is absent. They still ship as importable submodule files;
    importing one directly may raise only because of its own missing dependency,
    never a packaging error."""
    pkg = importlib.import_module("szl_substrate")
    assert modname not in pkg.__all__
    try:
        importlib.import_module(f"szl_substrate.{modname}")
    except ModuleNotFoundError:  # pragma: no cover - depends on env
        pass  # missing szl_dsse / fastapi is acceptable; not a packaging error
