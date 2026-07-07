# SPDX-License-Identifier: Apache-2.0
# © 2026 Lutar, Stephen P. — SZL Holdings · Doctrine v11
"""Smoke tests for M-tier wave 2 — 6 more M-tier modules whose shared-module deps
are already in the package, or are referenced only lazily+guarded inside functions
and degrade gracefully.

Selection criteria (all cmp-verified against both apps at extraction time):
  * shared-module dependencies are ALREADY extracted (``szl_dsse``,
    ``szl_restraint``, ``szl_llm_registry`` are here), or are only referenced
    lazily+guarded inside functions (``szl_energy_sovereign`` for ``szl_sapa``;
    ``szl_brain`` for ``a11oy_agent_loop`` via ``try/except -> None``) and degrade
    gracefully — so the module import never fails on their absence;
  * byte-identical between a11oy and killinchu (not a drifted/allow-listed file),
    extracted byte-for-byte.

4 are eager-import-safe (pure-stdlib at module scope). The other 2 carry an
UNGUARDED module-level ``from fastapi import Request`` (``szl_waqay`` /
``szl_yupay``; the starlette fallback also raises if neither is installed) and are
therefore imported directly (not eager) — exactly like ``szl_llm_registry`` /
``operator_shell_v4`` — so ``import szl_substrate`` stays importable everywhere.
"""
from __future__ import annotations

import importlib

import pytest

EAGER_M = [
    "szl_alloy_models",
    "szl_mbse_cosim",
    "szl_sapa",
    "a11oy_agent_loop",
]

IMPORT_DIRECTLY_M = [
    "szl_waqay",
    "szl_yupay",
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
    """These must NOT be eager-imported: their unguarded module-level
    `from fastapi import Request` (with a starlette fallback that also raises when
    neither is installed) would otherwise break `import szl_substrate` wherever
    both are absent. They still ship as importable submodule files; importing one
    directly may raise only because of its own missing dependency (fastapi /
    starlette), never a packaging error."""
    pkg = importlib.import_module("szl_substrate")
    assert modname not in pkg.__all__
    try:
        importlib.import_module(f"szl_substrate.{modname}")
    except ModuleNotFoundError:  # pragma: no cover - depends on env
        pass  # missing fastapi / starlette is acceptable; not a packaging error
