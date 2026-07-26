# SPDX-License-Identifier: Apache-2.0
"""Cross-platform import and fail-closed sandbox tests."""

from szl_substrate import a11oy_code_engine as code_engine


def test_code_engine_imports_cross_platform():
    assert callable(code_engine._sandbox_exec)


def test_sandbox_denies_execution_without_posix_limits(monkeypatch):
    monkeypatch.setattr(code_engine, "_resource", None)

    result = code_engine._sandbox_exec("print('must not run')")

    assert result["ok"] is False
    assert result["execution_attempted"] is False
    assert result["exit"] == -1
    assert "POSIX resource limits" in result["error"]
    assert "fail closed" in result["isolation"]


def test_governed_turn_propagates_sandbox_refusal_into_signed_deny(monkeypatch):
    monkeypatch.setattr(code_engine, "_resource", None)
    signed_payload = {}

    def sign(payload):
        signed_payload.update(payload)
        return {"signed": True, "signatures": ["test-signature"]}

    run = code_engine.governed_turn(
        "code",
        "calculate fibonacci numbers",
        sign,
        "test-issuer",
        sandbox=True,
    )

    assert run["decision"] == "DENY"
    assert run["emitted"] is False
    assert run["execution_admission"] == {
        "allowed": False,
        "attempted": False,
        "refused": True,
        "reason": "sandbox unavailable: POSIX resource limits are required",
    }
    assert run["sandbox"]["execution_attempted"] is False
    assert "No code ran" in run["summary"]
    assert "then ran in the governed sandbox" not in run["summary"]

    assert signed_payload["decision"] == "DENY"
    assert signed_payload["emitted"] is False
    assert signed_payload["sandbox_execution_attempted"] is False
    assert signed_payload["sandbox_refused"] is True
    assert signed_payload["sandbox_error"] == (
        "sandbox unavailable: POSIX resource limits are required"
    )

    emit_receipt = run["receipt_chain"][-1]
    assert emit_receipt["kind"] == "emit"
    assert emit_receipt["body"]["decision"] == "DENY"
    assert emit_receipt["body"]["emitted"] is False
    assert emit_receipt["body"]["sandbox_execution_attempted"] is False
    assert emit_receipt["body"]["sandbox_refused"] is True
    assert code_engine.verify_run(run)["chain_intact"] is True
