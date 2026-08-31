# SPDX-License-Identifier: Apache-2.0
"""Tests for szl_substrate.szl_brain — Λ aggregator (advisory) + tier policy.

Λ is Conjecture 1 (advisory) — these tests check the geometric-mean aggregator
and the trust→tier routing, NOT any claim of proven trust.
"""

from szl_substrate import szl_brain as brain


def test_lambda_geometric_mean():
    # geometric mean of [0.25, 0.64] = sqrt(0.16) = 0.4
    L = brain.lambda_aggregate([0.25, 0.64])
    assert abs(L - 0.4) < 1e-9


def test_lambda_empty_defaults_half():
    assert brain.lambda_aggregate(None) == 0.5
    assert brain.lambda_aggregate([]) == 0.5


def test_pick_tier_high_trust_is_fast():
    out = brain.pick_tier([0.99, 0.98, 0.97])
    assert out["lambda"] >= 0.90
    assert "high-trust" in out["reason"]


def test_pick_tier_low_trust_is_premium():
    out = brain.pick_tier([0.2, 0.2, 0.2])
    assert out["lambda"] < 0.75
    assert "premium" in out["reason"]


def test_make_receipt_has_lambda():
    r = brain.make_receipt([0.9, 0.9, 0.9])
    assert "lambda" in r or "tier" in r


def test_reexport_module_from_package_root():
    from szl_substrate import szl_brain as b2
    assert b2 is brain
