# SPDX-License-Identifier: Apache-2.0
"""Reported deployment parity must describe the exact two observed commits."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def readiness(monkeypatch):
    # Isolate this stdlib-only reader from unrelated eager package imports.
    path = Path(__file__).resolve().parents[1] / "src/szl_substrate/szl_readiness.py"
    spec = importlib.util.spec_from_file_location("readiness_parity_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "_deployed", Mock(return_value={
        "json": {"git_sha": "a" * 40}, "mode": "live",
    }))
    monkeypatch.setattr(module, "_gh_repo", Mock(return_value={
        "head_sha": "b" * 40, "mode": "live",
    }))
    monkeypatch.setattr(module, "_gh_release", Mock(return_value={"mode": "live"}))
    monkeypatch.setattr(module, "_hf_space", Mock(return_value={"mode": "live"}))
    monkeypatch.setattr(module, "_get", Mock(side_effect=AssertionError("unexpected network")))
    return module


CFG = {
    "deployment": {"version_url": "fixture://version", "healthz_url": "fixture://health"},
    "repo": "fixture/repo", "branch": "main", "hf_space": "fixture/space",
}


@pytest.mark.parametrize("ahead,behind,comparison,expected", [
    (0, 2, "behind", "ahead"),
    (2, 3, "diverged", "diverged"),
    (2, 0, "ahead", "behind"),
])
@pytest.mark.parametrize("mode", ["live", "cached"])
def test_distinct_commit_relationships(readiness, monkeypatch, ahead, behind, comparison, expected, mode):
    compare = Mock(return_value={"mode": mode, "ahead_by": ahead,
                                "behind_by": behind, "status": comparison})
    monkeypatch.setattr(readiness, "_gh_compare", compare)
    section = readiness._sec_parity(CFG, fresh=True)
    build = section["build"]
    assert build["status"] == expected
    assert build["behind_by"] == ahead
    assert build["deployment_ahead_by"] == behind
    assert build["compare_mode"] == mode
    assert "matches main" not in build["detail"]
    assert readiness._summary([section])["build_status"] == expected
    compare.assert_called_once_with("fixture/repo", "a" * 40, "b" * 40, fresh=True)


def test_exact_commit_match_does_not_need_comparison(readiness, monkeypatch):
    readiness._deployed.return_value["json"]["git_sha"] = "b" * 40
    compare = Mock(side_effect=AssertionError("comparison unnecessary"))
    monkeypatch.setattr(readiness, "_gh_compare", compare)
    build = readiness._sec_parity(CFG)["build"]
    assert build["status"] == "current"
    assert build["behind_by"] == 0
    compare.assert_not_called()


@pytest.mark.parametrize("comparison", [
    {"mode": "unreachable", "ahead_by": 0, "behind_by": 0},
    {"mode": "live", "ahead_by": None, "behind_by": 0},
    {"mode": "live", "ahead_by": 0},
    {"mode": "live", "ahead_by": False, "behind_by": 0},
    {"mode": "live", "ahead_by": 0, "behind_by": True},
    {"mode": "live", "ahead_by": -1, "behind_by": 0},
    {"mode": "live", "ahead_by": 0, "behind_by": -1},
    {"mode": "live", "ahead_by": 0.0, "behind_by": 0},
    {"mode": "live", "ahead_by": "0", "behind_by": 0},
    {"mode": "live", "ahead_by": 0, "behind_by": 0, "status": "identical"},
])
def test_unavailable_or_inconsistent_comparison_cannot_claim_parity(readiness, monkeypatch, comparison):
    monkeypatch.setattr(readiness, "_gh_compare", Mock(return_value=comparison))
    build = readiness._sec_parity(CFG)["build"]
    assert build["status"] == "unknown"
    assert "matches main" not in build["detail"]


@pytest.mark.parametrize("missing", ["deployment", "repository"])
def test_missing_commit_is_unknown(readiness, monkeypatch, missing):
    if missing == "deployment":
        readiness._deployed.return_value["json"].pop("git_sha")
    else:
        readiness._gh_repo.return_value.pop("head_sha")
    compare = Mock(side_effect=AssertionError("comparison without identities"))
    monkeypatch.setattr(readiness, "_gh_compare", compare)
    assert readiness._sec_parity(CFG)["build"]["status"] == "unknown"
    compare.assert_not_called()
