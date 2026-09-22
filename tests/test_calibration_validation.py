# SPDX-License-Identifier: Apache-2.0
"""Malformed observations and policy must never become calibration approval."""
import json
from unittest.mock import patch

import pytest

from szl_substrate import szl_calibration as cal


BAD_PROBABILITIES = [float('nan'), float('inf'), -float('inf'), -0.1, 1.1,
                     True, False, '0.5', None, 10 ** 400]
BAD_OUTCOMES = ['false', 'true', 0, 1, None, [], {}]


@pytest.mark.parametrize('confidence', BAD_PROBABILITIES)
def test_bad_confidence_does_not_create_a_window(confidence):
    tracker = cal.CalibrationTracker()
    with pytest.raises(ValueError):
        tracker.log('fixture', 'advisory', confidence, False)
    assert tracker.summary()['tracked'] == 0
    assert tracker.automated_response_gate('fixture', 'advisory')['allow'] is False


@pytest.mark.parametrize('outcome', BAD_OUTCOMES)
def test_truthy_outcome_does_not_create_a_window(outcome):
    tracker = cal.CalibrationTracker()
    with pytest.raises(ValueError):
        tracker.log('fixture', 'advisory', 1.0, outcome)
    assert tracker.summary()['tracked'] == 0


@pytest.mark.parametrize('metric', [cal.expected_calibration_error, cal.brier_binary,
                                   cal.reliability_bins])
@pytest.mark.parametrize('confidence', BAD_PROBABILITIES)
def test_public_metrics_reject_invalid_confidence(metric, confidence):
    with pytest.raises(ValueError):
        metric([confidence], [False])


@pytest.mark.parametrize('metric', [cal.expected_calibration_error, cal.brier_binary,
                                   cal.reliability_bins])
def test_public_metrics_reject_truthy_and_unpaired_outcomes(metric):
    with pytest.raises(ValueError):
        metric([1.0], ['false'])
    with pytest.raises(ValueError):
        metric([1.0, 0.0], [True])
    with pytest.raises(ValueError):
        metric([], [False])


@pytest.mark.parametrize('probs,index', [([], 0), ([0.0, 0.0], 0),
    ([float('nan'), 1.0], 0), ([float('inf'), 0.0], 0), ([1.1, 0.0], 0),
    ([0.5, 0.5], -1), ([0.5, 0.5], 2), ([0.5, 0.5], True),
    ([0.5, 0.5], 0.5), ([0.5, 0.5], '1')])
def test_multiclass_rejects_invalid_distribution_and_index(probs, index):
    with pytest.raises(ValueError):
        cal.brier_score([probs], [index])
    tracker = cal.CalibrationTracker()
    with pytest.raises(ValueError):
        tracker.log('fixture', 'advisory', 0.5, True, probs, index)
    assert tracker.summary()['tracked'] == 0


def test_partial_multiclass_observation_is_rejected_atomically():
    tracker = cal.CalibrationTracker(window=20)
    for _ in range(19):
        tracker.log('fixture', 'advisory', 1.0, True)
    before = tracker.metrics('fixture', 'advisory')
    for kwargs in [{'probs': [1.0, 0.0]}, {'true_index': 0},
                   {'probs': [1.0, 0.0], 'true_index': 9}]:
        with pytest.raises(ValueError):
            tracker.log('fixture', 'advisory', 1.0, True, **kwargs)
    assert tracker.metrics('fixture', 'advisory') == before
    assert tracker.automated_response_gate('fixture', 'advisory')['allow'] is False


def test_caller_mutation_cannot_poison_stored_distribution():
    tracker = cal.CalibrationTracker()
    probs = [1.0, 0.0]
    for _ in range(cal.MIN_SAMPLES):
        tracker.log('fixture', 'advisory', 1.0, True, probs, 0)
    probs[0] = float('nan')
    assert tracker.metrics('fixture', 'advisory')['brier'] == 0.0


@pytest.mark.parametrize('raw', ['nan', 'inf', '-inf', '1.01', '-0.01', '', 'invalid', '1e1000'])
@pytest.mark.parametrize('measured', [False, True])
def test_invalid_threshold_denies_and_serializes_as_null(monkeypatch, raw, measured):
    monkeypatch.setenv('A11OY_ECE_GATE_THRESHOLD', raw)
    tracker = cal.CalibrationTracker()
    if measured:
        for _ in range(cal.MIN_SAMPLES):
            tracker.log('fixture', 'advisory', 1.0, True)
    gate = tracker.automated_response_gate('fixture', 'advisory')
    assert gate['allow'] is False
    assert gate['reason'] == 'invalid_threshold'
    assert gate['threshold'] is None
    json.dumps(gate, allow_nan=False)
    json.dumps(tracker.metrics('fixture', 'advisory'), allow_nan=False)
    json.dumps(tracker.summary(), allow_nan=False)


def test_gate_uses_one_captured_threshold():
    tracker = cal.CalibrationTracker()
    for _ in range(cal.MIN_SAMPLES):
        tracker.log('fixture', 'advisory', 0.5, False)
    with patch.object(cal, '_gate_threshold', side_effect=[0.05, 1.0]) as reader:
        gate = tracker.automated_response_gate('fixture', 'advisory')
    assert reader.call_count == 1
    assert gate['threshold'] == 0.05
    assert gate['allow'] is False


@pytest.mark.parametrize('raw,expected', [('0', False), ('0.05', True), ('1', True)])
def test_valid_configured_thresholds_preserve_strict_comparison(monkeypatch, raw, expected):
    monkeypatch.setenv('A11OY_ECE_GATE_THRESHOLD', raw)
    tracker = cal.CalibrationTracker()
    for _ in range(cal.MIN_SAMPLES):
        tracker.log('fixture', 'advisory', 1.0, True)
    assert tracker.automated_response_gate('fixture', 'advisory')['allow'] is expected


def test_default_valid_samples_and_window_are_preserved(monkeypatch):
    monkeypatch.delenv('A11OY_ECE_GATE_THRESHOLD', raising=False)
    tracker = cal.CalibrationTracker(window=20)
    for _ in range(19):
        tracker.log('fixture', 'advisory', 1.0, True)
    assert tracker.automated_response_gate('fixture', 'advisory')['reason'] == 'not_measured'
    tracker.log('fixture', 'advisory', 1.0, True)
    assert tracker.automated_response_gate('fixture', 'advisory')['allow'] is True
    for _ in range(20):
        tracker.log('fixture', 'advisory', 1.0, False)
    metrics = tracker.metrics('fixture', 'advisory')
    assert metrics['n'] == 20
    assert metrics['ece'] == 1.0
    assert metrics['brier'] == 1.0
    assert metrics['ece_gate_threshold'] == cal.DEFAULT_ECE_GATE == 0.05
    assert tracker.automated_response_gate('fixture', 'advisory')['allow'] is False


def test_valid_multiclass_and_empty_metrics_are_preserved():
    assert cal.expected_calibration_error([], []) is None
    assert cal.brier_binary([], []) is None
    assert cal.brier_score([], []) is None
    assert cal.brier_score([[1.0, 0.0], [0.0, 1.0]], [0, 1]) == 0.0
    # Retain the existing positive-mass normalization for valid components.
    assert cal.brier_score([[0.2, 0.2]], [0]) == 0.5
    assert abs(cal.brier_binary([0.9, 0.1], [True, False]) - 0.01) < 1e-9
    with pytest.raises(ValueError):
        cal.brier_score([[1.0, 0.0]], [])


@pytest.mark.parametrize('value', [0, -1, True, '10', 1.5, float('nan'), float('inf')])
def test_invalid_window_or_bin_configuration_is_rejected(value):
    with pytest.raises(ValueError):
        cal.CalibrationTracker(window=value)
    with pytest.raises(ValueError):
        cal.CalibrationTracker(n_bins=value)
    with pytest.raises(ValueError):
        cal.expected_calibration_error([0.5], [True], n_bins=value)
    with pytest.raises(ValueError):
        cal.reliability_bins([0.5], [True], n_bins=value)
