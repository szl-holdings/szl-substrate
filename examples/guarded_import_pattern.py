#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
guarded_import_pattern.py — the canonical way an SZL app adopts szl-substrate
WITHOUT risking the running application.

Run:  python examples/guarded_import_pattern.py
"""
from __future__ import annotations


def load_dsse():
    """Prefer the shared package; fall back to a local vendored copy.

    This is exactly the shim the a11oy proof-of-concept PR installs. If
    `szl-substrate` is installed, imports resolve to the single source of truth.
    If it is NOT (e.g. an older image), the app keeps working against its local
    `szl_dsse.py`. Nothing breaks either way.
    """
    try:
        from szl_substrate import szl_dsse as dsse  # prefer the package
        return dsse, "szl-substrate"
    except Exception:  # pragma: no cover
        import szl_dsse as dsse  # fall back to the local vendored copy
        return dsse, "local-vendored"


def main() -> None:
    dsse, source = load_dsse()
    print(f"szl_dsse loaded from: {source}")

    env = dsse.sign_payload({"model": "a11oy-governed-engine", "policy": "advisory", "score": 0.97})
    print(f"signed={env['signed']}  honesty={env['honesty'][:60]}...")

    verdict = dsse.verify_envelope(env)
    print(f"verified={verdict['verified']}  reason={verdict.get('reason')}")

    from szl_substrate import szl_calibration as cal
    ece = cal.expected_calibration_error([0.9, 0.8, 0.95], [True, False, True])
    print(f"ECE={ece}  (advisory gate at {cal.DEFAULT_ECE_GATE})")


if __name__ == "__main__":
    main()
