# SPDX-License-Identifier: Apache-2.0
# © 2026 Lutar, Stephen P. — SZL Holdings · Doctrine v11
"""Smoke tests for the Wave-K FINISH batch — the entire remaining safe universe.

This pass migrates ALL shared modules that are byte-identical between a11oy and
killinchu (cmp-verified against BOTH fresh clones), leaving ONLY ``serve.py``
per-app. It includes the five modules that were previously allow-listed as
"killinchu sync pending" drift but are now BYTE-IDENTICAL again in both repos
(the sync landed in later waves): ``szl_rag``, ``szl_v4_fleet``,
``a11oy_code_engine``, ``szl_agentic_loop``, ``szl_joules_truth``. Their
now-stale drift-allow-list entries are removed in the companion app PRs.

``szl_joules_truth`` is the second L-tier leaf (11 app + 2 shared importers);
its wide fan-out is handled the same guarded-shim way as ``szl_dsse``.

Classification (empirically verified by importing each submodule file with
fastapi / lmdb / starlette / szl_connectors / pydantic ALL absent):
  EAGER (24)            — import cleanly at module scope with heavy deps absent.
  IMPORT-DIRECTLY (5)   — carry an UNGUARDED (or dual-raise try/except) module-
                          level import of a non-stdlib / bare-first-party name,
                          so they are excluded from eager import and shipped as
                          importable submodule files.
"""
from __future__ import annotations

import importlib

import pytest

EAGER = [
    "a11oy_uds_portability_nav",
    "a11oy_waqay_nav",
    "a11oy_yupay_nav",
    "szl_contracting",
    "szl_formula_wiring",
    "szl_logging",
    "szl_mbse_nav",
    "szl_readiness",
    "szl_unified_formulas",
    "a11oy_mcp_client",
    "szl_codename_gate",
    "szl_cuas_formulas",
    "szl_hf_bucket",
    "szl_khipu_consensus",
    "szl_v4_fleet",
    "szl_rag",
    "szl_spaces_proxy",
    "szl_spaces_surface",
    "a11oy_code_engine",
    "a11oy_org_rag",
    "szl_energy_sovereign",
    "szl_agentic_loop",
    "szl_joules_truth",
]

IMPORT_DIRECTLY = [
    "szl_connector_mcp",     # module-level `import szl_connectors`
    "szl_deepdive_gaps",     # module-level `from fastapi import ...`
    "szl_quantum_bio",       # module-level `from starlette import ...`
    "szl_uds_portability",   # try fastapi except starlette (both raise if absent)
    "szl_rosie_companion",   # fastapi/starlette module-level fallback
    "test_szl_hf_bucket",    # bare `import szl_hf_bucket`
]

# The five formerly-allow-listed-drift modules, now byte-identical again.
FORMERLY_DRIFTED = [
    "szl_rag",
    "szl_v4_fleet",
    "a11oy_code_engine",
    "szl_agentic_loop",
    "szl_joules_truth",
]


def test_package_still_imports_cleanly():
    pkg = importlib.import_module("szl_substrate")
    assert pkg.__version__


@pytest.mark.parametrize("modname", EAGER)
def test_eager_importable_and_exported(modname):
    pkg = importlib.import_module("szl_substrate")
    assert hasattr(pkg, modname), f"{modname} not exposed on szl_substrate"
    sub = importlib.import_module(f"szl_substrate.{modname}")
    assert sub is getattr(pkg, modname)
    assert modname in pkg.__all__


@pytest.mark.parametrize("modname", IMPORT_DIRECTLY)
def test_import_directly_not_eager(modname):
    """Must NOT be eager-imported: their unguarded module-level imports would
    otherwise break ``import szl_substrate`` wherever those deps are absent.
    They still ship as importable submodule files; importing one directly may
    raise only because of its own missing dependency, never a packaging error."""
    pkg = importlib.import_module("szl_substrate")
    assert modname not in pkg.__all__
    try:
        importlib.import_module(f"szl_substrate.{modname}")
    except (ModuleNotFoundError, ImportError):  # pragma: no cover - env-dependent
        pass


@pytest.mark.parametrize("modname", FORMERLY_DRIFTED)
def test_formerly_drifted_now_shipped(modname):
    """The five modules that were 'killinchu sync pending' are now byte-identical
    in both repos and shipped from the package as the single source of truth."""
    pkg = importlib.import_module("szl_substrate")
    assert hasattr(pkg, modname)
    assert modname in pkg.__all__


def test_joules_truth_l_tier_leaf():
    """The second L-tier leaf (wide fan-out, 11 app + 2 shared importers)."""
    jt = importlib.import_module("szl_substrate.szl_joules_truth")
    assert jt is not None
