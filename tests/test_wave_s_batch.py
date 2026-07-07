# SPDX-License-Identifier: Apache-2.0
# © 2026 Lutar, Stephen P. — SZL Holdings · Doctrine v11
"""Smoke tests for the Wave-S batch of extracted S-tier leaf modules.

These modules were extracted byte-identical from a11oy/killinchu (0 app-file
importers + ≤1 shared-file importer, no local shared-set imports, none drifted).
The 9 pure-stdlib leaves must be importable via the package; szl_connectors_serve
carries an unguarded module-level ``import szl_connectors`` and is therefore
imported lazily (guarded) so the package stays importable everywhere.
"""
from __future__ import annotations

import importlib

import pytest

EAGER_LEAVES = [
    "szl_allodial",
    "a11oy_hf_assets",
    "szl_chain_of_title",
    "szl_conjecture_factory",
    "szl_ecosystem_routes",
    "szl_entanglement",
    "szl_metrics_prom",
    "szl_neuroplasticity",
    "szl_scaling",
]


def test_package_imports_cleanly():
    pkg = importlib.import_module("szl_substrate")
    assert pkg.__version__


@pytest.mark.parametrize("modname", EAGER_LEAVES)
def test_eager_leaf_importable_and_exported(modname):
    pkg = importlib.import_module("szl_substrate")
    # accessible both as attribute and as submodule
    assert hasattr(pkg, modname), f"{modname} not exposed on szl_substrate"
    sub = importlib.import_module(f"szl_substrate.{modname}")
    assert sub is getattr(pkg, modname)
    assert modname in pkg.__all__


def test_connectors_serve_is_lazy_not_eager():
    """szl_connectors_serve must NOT be eager-imported (its unguarded
    ``import szl_connectors`` would otherwise break package import wherever that
    dependency is absent)."""
    pkg = importlib.import_module("szl_substrate")
    assert "szl_connectors_serve" not in pkg.__all__
    # It should still ship as a submodule file; importing it may raise only
    # because of its own missing optional dependency, never a packaging error.
    try:
        importlib.import_module("szl_substrate.szl_connectors_serve")
    except ModuleNotFoundError as e:  # pragma: no cover - depends on env
        assert "szl_connectors" in str(e)
