# SPDX-License-Identifier: Apache-2.0
"""Cross-platform import and fail-closed sandbox tests."""

from szl_substrate import a11oy_code_engine as code_engine


def test_code_engine_imports_cross_platform():
    assert callable(code_engine._sandbox_exec)


def test_sandbox_denies_execution_without_posix_limits(monkeypatch):
    monkeypatch.setattr(code_engine, "_resource", None)

    result = code_engine._sandbox_exec("print('must not run')")

    assert result["ok"] is False
    assert result["exit"] == -1
    assert "POSIX resource limits" in result["error"]
    assert "fail closed" in result["isolation"]
