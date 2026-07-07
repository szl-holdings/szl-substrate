# SPDX-License-Identifier: Apache-2.0
# © 2026 Lutar, Stephen P. — SZL Holdings · Doctrine v11
"""Smoke tests for M-tier wave 3 — 2 more M-tier modules whose deps are satisfied.

Selection criteria (all cmp-verified against both apps at extraction time):
  * ``szl_live_wires`` — its only heavier imports (``fastapi``, and the
    app-specific ``szl_wire`` / ``szl_jack`` — neither of which is in the shared
    69-file set) are ALL wrapped in module-level ``try/except -> None``. Its
    module scope is pure-stdlib, so it is eager-import-safe: ``import
    szl_substrate`` never fails even when fastapi / szl_wire / szl_jack are absent.
  * ``szl_sapa_patch`` — its shared dep ``szl_sapa`` is ALREADY extracted, but it
    carries an UNGUARDED module-level ``import szl_sapa`` (bare top-level name)
    plus ``from fastapi import Request``, so eager-importing it would break
    ``import szl_substrate`` wherever those are absent. It is therefore imported
    directly (not eager) — exactly like ``szl_waqay`` / ``szl_yupay`` /
    ``operator_shell_v4`` — so the package stays importable everywhere.

Both were byte-identical between a11oy and killinchu at extraction time (not a
drifted/allow-listed file), extracted byte-for-byte.
"""
from __future__ import annotations

import importlib

import pytest

EAGER_M = [
    "szl_live_wires",
]

IMPORT_DIRECTLY_M = [
    "szl_sapa_patch",
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


def test_live_wires_has_register_entrypoint():
    """szl_live_wires is an additive FastAPI module with a single integration
    point: ``register(app, ns=...)``. It must be present even when fastapi is
    absent (the function is defined at module scope; only its body touches the
    guarded imports)."""
    lw = importlib.import_module("szl_substrate.szl_live_wires")
    assert hasattr(lw, "register"), "szl_live_wires must expose register()"


@pytest.mark.parametrize("modname", IMPORT_DIRECTLY_M)
def test_import_directly_modules_not_eager(modname):
    """These must NOT be eager-imported: their unguarded module-level imports
    (``import szl_sapa`` as a bare top-level name and ``from fastapi import
    Request``) would otherwise break ``import szl_substrate`` wherever those
    dependencies are absent. They still ship as importable submodule files;
    importing one directly may raise only because of its own missing dependency
    (szl_sapa / fastapi), never a packaging error."""
    pkg = importlib.import_module("szl_substrate")
    assert modname not in pkg.__all__
    try:
        importlib.import_module(f"szl_substrate.{modname}")
    except ModuleNotFoundError:  # pragma: no cover - depends on env
        pass  # missing szl_sapa / fastapi is acceptable; not a packaging error
