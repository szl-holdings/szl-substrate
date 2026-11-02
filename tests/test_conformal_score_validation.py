# SPDX-License-Identifier: Apache-2.0
"""Invalid calibration evidence must not narrow a conformal prediction set."""
import json

import pytest

from szl_substrate.szl_conformal import conformal_quantile, conformal_set


BAD_SCORES = [
    pytest.param("invalid", id="not-numeric"),
    pytest.param(None, id="null"),
    pytest.param(True, id="boolean"),
    pytest.param(float("nan"), id="nan"),
    pytest.param(float("inf"), id="positive-infinity"),
    pytest.param(float("-inf"), id="negative-infinity"),
    pytest.param(-0.1, id="below-score-range"),
    pytest.param(1.1, id="above-score-range"),
    pytest.param(10 ** 1000, id="float-overflow"),
]


@pytest.mark.parametrize("bad_score", BAD_SCORES)
@pytest.mark.parametrize("mixed", [False, True], ids=["all-invalid", "one-invalid"])
def test_invalid_score_returns_full_label_space(bad_score, mixed):
    # Dropping a single invalid sample is also unsafe: the remaining low scores
    # would still imply a tight threshold from a corrupt calibration pool.
    scores = [0.1] * 19 + [bad_score] if mixed else [bad_score] * 20
    result = conformal_set([0.6, 0.3, 0.1], scores, alpha=0.1,
                           labels=["A", "B", "C"])

    assert result["q_hat"] == 1.0
    assert result["set"] == ["A", "B", "C"]
    assert result["full_label_space"] is True
    assert result["singleton"] is False
    json.dumps(result, allow_nan=False)


def test_valid_scores_keep_finite_sample_order_statistic():
    scores = [0.9, 0.0, 0.3, 1.0, 0.1]
    original = list(scores)
    # ceil((5 + 1) * (1 - 0.5)) = 3: choose the third sorted score.
    assert conformal_quantile(scores, alpha=0.5) == 0.3
    assert scores == original
    assert conformal_quantile(["0.9", "0.0", "0.3", "1.0", "0.1"], 0.5) == 0.3


@pytest.mark.parametrize("scores", [[], [0.0]])
def test_insufficient_calibration_keeps_full_label_fallback(scores):
    assert conformal_quantile(scores, alpha=0.05) == 1.0
