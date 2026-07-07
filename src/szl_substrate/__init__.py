# SPDX-License-Identifier: Apache-2.0
# © 2026 Lutar, Stephen P. — SZL Holdings · ORCID 0009-0001-0110-4173 · Doctrine v11
"""
szl_substrate — the installable shared substrate for a11oy + killinchu.

This package is the single source of truth for modules that were previously
duplicated byte-for-byte across the two flagship application repos. The goal is
to eliminate that duplication WITHOUT a big-bang cutover: each app imports a
module from here with a guarded fallback to its local copy, so nothing breaks if
the package is not yet installed in a given environment.

Honesty labels (Doctrine v11): every governance signal remains ADVISORY.
Λ = Conjecture 1 (advisory, never "green"/proven). Signed receipts use real DSSE
in-Space and an honest UNSIGNED marker when no cosign key is present — a
signature is NEVER fabricated.

Extracted modules (POC pass):
  - szl_calibration : ECE / Brier calibration tracking + advisory response gate
                      (pure-Python, no third-party deps).
  - szl_dsse        : DSSE (in-toto) ECDSA-P256-SHA256 signing/verification,
                      cosign-compatible, UNSIGNED-honest fallback (requires
                      `cryptography`).
  - szl_brain       : governed reasoning-brain scaffolding (pure-Python; makes a
                      lazy, guarded call into szl_rag when available).

Extracted modules (Wave-S batch — 10 S-tier leaves, byte-identical a11oy↔killinchu
at extraction time; 0 app-file importers + ≤1 shared-file importer; no local
imports; none drifted):
  - szl_allodial          : Denning(1976) lattice / Goguen-Meseguer(1982)
                            non-interference sovereignty formulas (stdlib-only;
                            EXPERIMENTAL/PROPOSED — adds nothing to the locked 8).
  - a11oy_hf_assets       : Hugging Face asset helpers (stdlib-only).
  - szl_chain_of_title    : chain-of-title provenance helpers (stdlib-only).
  - szl_conjecture_factory: conjecture registry (Λ uniqueness stays OPEN /
                            Conjecture 1; stdlib-only).
  - szl_connectors_serve  : Enterprise-Mesh FastAPI registration. NOTE: has an
                            UNGUARDED module-level `import szl_connectors`, so it
                            is intentionally NOT eager-imported at package init;
                            import it explicitly via
                            `from szl_substrate import szl_connectors_serve`
                            only where `szl_connectors` is present.
  - szl_ecosystem_routes  : ecosystem route registration (stdlib-only).
  - szl_entanglement      : 2-qubit entanglement measures + Λ-v5 coherence bridge
                            (stdlib-only).
  - szl_metrics_prom      : Prometheus metrics helpers (stdlib-only).
  - szl_neuroplasticity   : neuroplasticity formulas (stdlib-only).
  - szl_scaling           : scaling formulas (stdlib-only).

See MIGRATION.md for the full ranked plan covering all 69 shared files.
"""
from __future__ import annotations

__version__ = "0.1.0"

# Re-export the modules as attributes so callers can do either:
#   from szl_substrate import szl_dsse
#   from szl_substrate.szl_dsse import sign_payload
from . import szl_calibration  # noqa: E402,F401
from . import szl_dsse  # noqa: E402,F401
from . import szl_brain  # noqa: E402,F401

# Wave-S batch: eager-import the pure-stdlib leaves (safe to import anywhere).
# szl_connectors_serve is deliberately EXCLUDED from eager import because it has
# an unguarded module-level `import szl_connectors`; callers import it directly
# where that dependency exists (see docstring above).
from . import szl_allodial  # noqa: E402,F401
from . import a11oy_hf_assets  # noqa: E402,F401
from . import szl_chain_of_title  # noqa: E402,F401
from . import szl_conjecture_factory  # noqa: E402,F401
from . import szl_ecosystem_routes  # noqa: E402,F401
from . import szl_entanglement  # noqa: E402,F401
from . import szl_metrics_prom  # noqa: E402,F401
from . import szl_neuroplasticity  # noqa: E402,F401
from . import szl_scaling  # noqa: E402,F401

# M-tier reconciled drift (Wave-E dev 5): the 3 shared files that had DRIFTED
# between a11oy and killinchu, reconciled to a single canonical copy here. All
# three are pure-stdlib at module scope (their szl_dsse / app-specific imports are
# lazy + guarded inside functions), so they are safe to eager-import. See
# MIGRATION.md for the per-file reconciliation decision. serve.py is intentionally
# NOT extracted — it is the per-app entrypoint (legitimately divergent, L-tier).
from . import _vendor_blobs  # noqa: E402,F401
from . import szl_be_hardening  # noqa: E402,F401
from . import szl_evidence_research  # noqa: E402,F401

# M-tier wave 1 (this pass): 7 M-tier modules whose shared-module deps are
# ALREADY in the package (szl_dsse is here; szl_rag / szl_joules_truth are only
# referenced lazily+guarded inside functions and degrade gracefully). All 7 were
# byte-identical between a11oy and killinchu at extraction time (cmp-verified),
# none was a drifted/allow-listed file, so each is extracted byte-for-byte.
#
# EAGER (3): pure-stdlib at module scope, so safe to import anywhere. Their
# szl_dsse / szl_joules_truth uses are all lazy+guarded inside functions.
from . import szl_ken  # noqa: E402,F401
from . import szl_qhawaq  # noqa: E402,F401
from . import szl_restraint  # noqa: E402,F401
#
# IMPORT-DIRECTLY (4): each has an UNGUARDED module-level import that would break
# `import szl_substrate` wherever that dependency is absent, which would violate
# the package's "importable everywhere" invariant (the same honest-fallback
# guarantee szl_dsse relies on). So — exactly like `szl_connectors_serve` — they
# are intentionally EXCLUDED from eager import and imported directly
# (`from szl_substrate import X`) only where their dependency is present:
#   - szl_provenance        : module-level `import szl_dsse` (app path only)
#   - szl_warhacker_aliases : module-level `from fastapi import ...`
#   - operator_shell_v4     : module-level `from fastapi import ...`
#   - szl_llm_registry      : module-level `from fastapi import ...`
# They still ship as importable submodule files and are byte-identical extracts.

# M-tier wave 2 (this pass): 6 more M-tier modules whose shared-module deps are
# ALREADY in the package, or are only referenced lazily+guarded inside functions
# and degrade gracefully. All 6 were byte-identical between a11oy and killinchu at
# extraction time (cmp-verified), none was a drifted/allow-listed file, so each is
# extracted byte-for-byte. Dependency status:
#   - szl_alloy_models : szl_llm_registry (in-function, lazy)      ✅ dep moved
#   - szl_mbse_cosim   : szl_dsse + szl_restraint (in-function)    ✅ deps moved
#   - szl_sapa         : szl_dsse (lazy) + szl_energy_sovereign
#                        (lazy+guarded soft-import, degrades)       ✅ szl_dsse moved
#   - a11oy_agent_loop : szl_brain (module-level but guarded
#                        try/except -> None) + szl_agent_loop_banach (lazy) ✅
#
# EAGER (4): pure-stdlib at module scope, so safe to import anywhere. Their
# szl_dsse / szl_restraint / szl_llm_registry / szl_energy_sovereign uses are all
# lazy+guarded inside functions; a11oy_agent_loop's szl_brain import is wrapped in
# try/except -> None, so its absence never breaks the module import.
from . import szl_alloy_models  # noqa: E402,F401
from . import szl_mbse_cosim  # noqa: E402,F401
from . import szl_sapa  # noqa: E402,F401
from . import a11oy_agent_loop  # noqa: E402,F401

# M-tier wave 3 (this pass): 2 more M-tier modules whose deps are satisfied.
# Both are byte-identical between a11oy and killinchu at extraction time
# (cmp-verified, neither is a drifted/allow-listed file), so each is extracted
# byte-for-byte. Dependency status:
#   - szl_live_wires : only app-specific deps (szl_wire, szl_jack) and fastapi,
#                      ALL wrapped in module-level try/except -> None. Its module
#                      scope is pure-stdlib, so it is EAGER-safe (importing it
#                      never fails even when fastapi/szl_wire/szl_jack are absent).
#   - szl_sapa_patch : szl_sapa ✅ moved. BUT it carries an UNGUARDED module-level
#                      `import szl_sapa` (bare name) + `from fastapi import
#                      Request`, so it is import-directly (NOT eager) — exactly
#                      like szl_waqay / szl_yupay / operator_shell_v4.
#
# EAGER (1): szl_live_wires — pure-stdlib at module scope; every heavier import
# is guarded, so `import szl_substrate` still succeeds with fastapi absent.
from . import szl_live_wires  # noqa: E402,F401

# M-tier wave 4 (this pass): a dependency-ordered batch that first lands the 5
# remaining S-tier leaves that block the next M modules, then the 3 M modules
# they unblock. All 8 were byte-identical between a11oy and killinchu at
# extraction time (cmp-verified against BOTH fresh clones; none is a
# drifted/allow-listed file), so each is extracted byte-for-byte. Dependency
# status (strictly dependency-ordered):
#   S leaves (deps: none in shared set):
#     - szl_formulas       : pure-stdlib leaf (blast radius: 5 app + 1 shared)
#     - szl_conformal      : pure-stdlib leaf
#     - szl_khipu_replicate: pure-stdlib leaf
#     - szl_unay           : pure-stdlib leaf
#     - szl_khipu_lmdb     : leaf, but UNGUARDED module-level `import lmdb`
#   M modules (every shared dep now ALREADY in the package via this same batch):
#     - a11oy_autoreview   : szl_calibration / szl_conformal / szl_restraint, ALL
#                            guarded (try/except -> None); module scope pure-stdlib
#     - szl_anatomy_routes : UNGUARDED module-level `import szl_formulas` (✅ in this
#                            batch); fastapi guarded
#     - szl_unay_routes    : UNGUARDED module-level `import szl_unay` /
#                            `import szl_khipu_lmdb` / `import szl_khipu_replicate`
#                            (all ✅ in this batch); fastapi guarded
#
# EAGER (5): pure-stdlib at module scope (a11oy_autoreview's shared-dep imports
# are all wrapped in try/except -> None), so `import szl_substrate` never fails
# on their behalf (verified with fastapi + lmdb absent).
from . import szl_formulas  # noqa: E402,F401
from . import szl_conformal  # noqa: E402,F401
from . import szl_khipu_replicate  # noqa: E402,F401
from . import szl_unay  # noqa: E402,F401
from . import a11oy_autoreview  # noqa: E402,F401
#
# IMPORT-DIRECTLY (3): each has an UNGUARDED module-level import that would break
# `import szl_substrate` wherever that dependency is absent, so — exactly like
# szl_connectors_serve / szl_sapa_patch — they are EXCLUDED from eager import and
# imported directly (`from szl_substrate import X`) only where their dependency is
# present. They still ship as importable byte-identical submodule files:
#   - szl_khipu_lmdb    : module-level `import lmdb`
#   - szl_anatomy_routes: module-level `import szl_formulas` (bare name)
#   - szl_unay_routes   : module-level `import szl_unay` / `szl_khipu_lmdb` /
#                         `szl_khipu_replicate` (bare names) + transitive `lmdb`
#
# IMPORT-DIRECTLY (1): szl_sapa_patch — module-level fastapi + bare `import
# szl_sapa`, so it is EXCLUDED from eager import and imported directly
# (`from szl_substrate import szl_sapa_patch`) only where fastapi and szl_sapa
# are present. It still ships as an importable submodule file (byte-identical).
#
# IMPORT-DIRECTLY (2): each has an UNGUARDED module-level `from fastapi import
# Request` (with a starlette fallback that also raises if neither is installed),
# so eager-importing them would break `import szl_substrate` wherever fastapi and
# starlette are both absent. Exactly like szl_llm_registry / operator_shell_v4,
# they are EXCLUDED from eager import and imported directly
# (`from szl_substrate import X`) only where fastapi/starlette is present:
#   - szl_waqay : module-level `from fastapi import Request` (szl_dsse/szl_restraint lazy)
#   - szl_yupay : module-level `from fastapi import Request` (szl_dsse/szl_restraint lazy)
# They still ship as importable submodule files and are byte-identical extracts.

# =========================================================================
# Wave-K finish batch (this pass): the ENTIRE remaining safe universe.
# =========================================================================
# With every prior wave landed, this pass migrates ALL remaining shared
# modules that are byte-identical between a11oy and killinchu (cmp-verified
# against BOTH fresh clones), leaving ONLY serve.py per-app. It includes the
# five modules that were previously allow-listed as "killinchu sync pending"
# drift but are now BYTE-IDENTICAL again in both repos (the sync landed in
# later waves): szl_rag, szl_v4_fleet, a11oy_code_engine, szl_agentic_loop,
# szl_joules_truth. Their now-STALE drift-allow-list entries are removed in
# BOTH app repos in the companion PRs (tightening the ratchet, exactly as the
# drift guard's stale-allow WARNING invites) — a signature is never fabricated
# and no real divergence is masked.
#
# szl_joules_truth is the second L-tier leaf (11 app + 2 shared importers);
# its wide fan-out is handled the same guarded-shim way as szl_dsse.
#
# EAGER (25): pure-stdlib at module scope, or every heavier/first-party import
# is guarded (try/except or in-function), so `import szl_substrate` never fails
# on their behalf (verified with fastapi + lmdb + starlette + szl_connectors
# all absent). Their intra-shared deps are all already in the package or only
# referenced lazily+guarded and degrade gracefully.
from . import a11oy_uds_portability_nav  # noqa: E402,F401
from . import a11oy_waqay_nav  # noqa: E402,F401
from . import a11oy_yupay_nav  # noqa: E402,F401
from . import szl_contracting  # noqa: E402,F401
from . import szl_formula_wiring  # noqa: E402,F401
from . import szl_logging  # noqa: E402,F401
from . import szl_mbse_nav  # noqa: E402,F401
from . import szl_readiness  # noqa: E402,F401
from . import szl_unified_formulas  # noqa: E402,F401
from . import a11oy_mcp_client  # noqa: E402,F401
from . import szl_codename_gate  # noqa: E402,F401
from . import szl_cuas_formulas  # noqa: E402,F401
from . import szl_hf_bucket  # noqa: E402,F401
from . import szl_khipu_consensus  # noqa: E402,F401
from . import szl_v4_fleet  # noqa: E402,F401
from . import szl_rag  # noqa: E402,F401
from . import szl_spaces_proxy  # noqa: E402,F401
from . import szl_spaces_surface  # noqa: E402,F401
from . import a11oy_code_engine  # noqa: E402,F401
from . import a11oy_org_rag  # noqa: E402,F401
from . import szl_energy_sovereign  # noqa: E402,F401
from . import szl_agentic_loop  # noqa: E402,F401
from . import szl_joules_truth  # noqa: E402,F401
#
# IMPORT-DIRECTLY (4): each has an UNGUARDED module-level import that would
# break `import szl_substrate` wherever that dependency is absent, so — exactly
# like szl_connectors_serve / szl_sapa_patch / szl_waqay — they are EXCLUDED
# from eager import and imported directly (`from szl_substrate import X`) only
# where their dependency is present. They still ship as importable
# byte-identical submodule files:
#   - szl_connector_mcp : module-level `import szl_connectors` (app path only)
#   - szl_deepdive_gaps : module-level `from fastapi import ...`
#   - szl_quantum_bio   : module-level `from starlette import ...`
#   - szl_uds_portability: module-level `try fastapi except starlette` (both
#                         raise if neither installed — same shape as szl_waqay)
#   - szl_rosie_companion: module-level `from fastapi import ...` fallback that
#                         also raises when fastapi/starlette are both absent
#   - test_szl_hf_bucket: module-level `import szl_hf_bucket` (bare name; it is
#                         the module's own byte-identical unit test, shipped so
#                         the 69-file shared set is fully accounted for)

# Convenience re-exports of the most commonly used entry points. These are the
# stable public surface the apps import through the guarded shim.
from .szl_dsse import (  # noqa: E402,F401
    sign_payload,
    verify_envelope,
    sign_khipu_receipt,
    signing_available,
    canonical_json,
    KHIPU_PAYLOAD_TYPE,
    KEYID,
)
from .szl_calibration import (  # noqa: E402,F401
    expected_calibration_error,
    brier_score,
    brier_binary,
    reliability_bins,
    CalibrationTracker,
    DEFAULT_ECE_GATE,
)

__all__ = [
    "__version__",
    "szl_calibration",
    "szl_dsse",
    "szl_brain",
    # Wave-S batch (eager)
    "szl_allodial",
    "a11oy_hf_assets",
    "szl_chain_of_title",
    "szl_conjecture_factory",
    "szl_ecosystem_routes",
    "szl_entanglement",
    "szl_metrics_prom",
    "szl_neuroplasticity",
    "szl_scaling",
    # Wave-S batch (lazy — import directly): szl_connectors_serve
    # M-tier reconciled drift (Wave-E dev 5)
    "szl_be_hardening",
    "szl_evidence_research",
    # M-tier wave 1 (eager — pure-stdlib at module scope)
    "szl_ken",
    "szl_qhawaq",
    "szl_restraint",
    # M-tier wave 1 (import-directly, NOT eager — unguarded module-level dep):
    #   szl_provenance (szl_dsse), szl_warhacker_aliases / operator_shell_v4 /
    #   szl_llm_registry (fastapi). They ship as submodule files.
    # M-tier wave 2 (eager — pure-stdlib at module scope; deps lazy/guarded)
    "szl_alloy_models",
    "szl_mbse_cosim",
    "szl_sapa",
    "a11oy_agent_loop",
    # M-tier wave 3 (eager — pure-stdlib at module scope; heavier deps guarded)
    "szl_live_wires",
    # M-tier wave 4 (eager — pure-stdlib at module scope; shared deps guarded)
    "szl_formulas",
    "szl_conformal",
    "szl_khipu_replicate",
    "szl_unay",
    "a11oy_autoreview",
    # M-tier wave 4 (import-directly, NOT eager — unguarded module-level dep):
    #   szl_khipu_lmdb (lmdb), szl_anatomy_routes (szl_formulas),
    #   szl_unay_routes (szl_unay/szl_khipu_lmdb/szl_khipu_replicate). They ship
    #   as importable byte-identical submodule files.
    # M-tier wave 3 (import-directly, NOT eager — module-level fastapi + bare
    #   `import szl_sapa`): szl_sapa_patch. It ships as a submodule file.
    # Wave-K finish batch (eager)
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
    # Wave-K finish batch (import-directly, NOT eager — unguarded module-level
    #   dep): szl_connector_mcp (szl_connectors), szl_deepdive_gaps (fastapi),
    #   szl_quantum_bio (starlette), szl_uds_portability (fastapi/starlette),
    #   szl_rosie_companion (fastapi/starlette), test_szl_hf_bucket
    #   (szl_hf_bucket). They ship as importable byte-identical submodule files.
    # M-tier wave 2 (import-directly, NOT eager — module-level fastapi):
    #   szl_waqay, szl_yupay. They ship as submodule files.
    # _vendor_blobs is underscore-private but ships as an importable submodule
    # dsse
    "sign_payload",
    "verify_envelope",
    "sign_khipu_receipt",
    "signing_available",
    "canonical_json",
    "KHIPU_PAYLOAD_TYPE",
    "KEYID",
    # calibration
    "expected_calibration_error",
    "brier_score",
    "brier_binary",
    "reliability_bins",
    "CalibrationTracker",
    "DEFAULT_ECE_GATE",
]
