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

Extracted modules (this pass):
  - szl_calibration : ECE / Brier calibration tracking + advisory response gate
                      (pure-Python, no third-party deps).
  - szl_dsse        : DSSE (in-toto) ECDSA-P256-SHA256 signing/verification,
                      cosign-compatible, UNSIGNED-honest fallback (requires
                      `cryptography`).
  - szl_brain       : governed reasoning-brain scaffolding (pure-Python; makes a
                      lazy, guarded call into szl_rag when available).

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
