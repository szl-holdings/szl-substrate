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
