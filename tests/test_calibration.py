# SPDX-License-Identifier: Apache-2.0
"""Tests for szl_substrate.szl_calibration — ECE / Brier / reliability bins."""
from szl_substrate import szl_calibration as cal


def test_ece_perfect_calibration_is_zero():
    # Confidences that exactly match accuracy => ECE ~ 0.
    conf = [1.0, 1.0, 1.0, 1.0]
    correct = [True, True, True, True]
    ece = cal.expected_calibration_error(conf, correct, n_bins=10)
    assert ece == 0.0


def test_ece_overconfident_is_positive():
    # Fully confident but always wrong => ECE = 1.0.
    conf = [1.0, 1.0, 1.0, 1.0]
    correct = [False, False, False, False]
    ece = cal.expected_calibration_error(conf, correct, n_bins=10)
    assert ece == 1.0


def test_ece_empty_returns_none():
    assert cal.expected_calibration_error([], []) is None


def test_brier_binary_bounds():
    bs = cal.brier_binary([0.9, 0.1], [True, False])
    # (0.9-1)^2 + (0.1-0)^2 = 0.01 + 0.01, mean = 0.01
    assert abs(bs - 0.01) < 1e-9


def test_brier_multiclass_perfect():
    bs = cal.brier_score([[1.0, 0.0], [0.0, 1.0]], [0, 1])
    assert bs == 0.0


def test_reliability_bins_shape():
    bins = cal.reliability_bins([0.05, 0.95], [False, True], n_bins=10)
    assert len(bins) == 10
    assert all("bin" in b and "count" in b for b in bins)


def test_default_gate_constant():
    assert cal.DEFAULT_ECE_GATE == 0.05


def test_reexport_from_package_root():
    from szl_substrate import expected_calibration_error, DEFAULT_ECE_GATE
    assert DEFAULT_ECE_GATE == 0.05
    assert expected_calibration_error([1.0], [True]) == 0.0
