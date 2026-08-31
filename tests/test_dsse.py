# SPDX-License-Identifier: Apache-2.0
"""Tests for szl_substrate.szl_dsse — DSSE PAE + UNSIGNED-honest fallback.

These tests deliberately run WITHOUT a cosign private key present, exercising
the honest-unsigned path. The module must NEVER fabricate a signature.
"""
import base64
import json

import pytest

from szl_substrate import szl_dsse as dsse


@pytest.fixture(autouse=True)
def _no_signing_key(monkeypatch):
    # Ensure no private-key env var leaks in from the runtime.
    for var in dsse.PRIVATE_KEY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_pae_matches_dsse_spec():
    # PAE(type, body) = "DSSEv1" SP LEN(type) SP type SP LEN(body) SP body
    pae = dsse.pae("t", b"body")
    assert pae == b"DSSEv1 1 t 4 body"


def test_canonical_json_is_deterministic():
    a = dsse.canonical_json({"b": 1, "a": 2})
    b = dsse.canonical_json({"a": 2, "b": 1})
    assert a == b  # key order must not matter


def test_unsigned_envelope_is_honest_not_fabricated():
    env = dsse.sign_payload({"model": "test", "score": 0.9})
    assert env["signed"] is False
    assert env["signatures"] == []
    assert "UNSIGNED" in env["honesty"]
    # payload round-trips
    body = base64.b64decode(env["payload"])
    assert json.loads(body)["model"] == "test"


def test_verify_unsigned_is_false_never_fake_pass():
    env = dsse.sign_payload({"x": 1})
    verdict = dsse.verify_envelope(env)
    assert verdict["verified"] is False
    assert "unsigned" in verdict["reason"].lower()


def test_signing_available_reports_false_without_key():
    assert dsse.signing_available() is False


def test_reexport_from_package_root():
    from szl_substrate import sign_payload, KHIPU_PAYLOAD_TYPE
    env = sign_payload({"a": 1})
    assert env["payloadType"] == KHIPU_PAYLOAD_TYPE


# ---------------------------------------------------------------------------
# Adversarial / fail-closed coverage for verify_envelope.
#
# The verifier is bound to the PUBLISHED SZLHOLDINGS cosign.pub embedded in the
# module. It must (1) reject a real ECDSA signature produced by any OTHER key,
# (2) reject a tampered payload, and (3) never raise and always fail closed on
# malformed envelope shapes. None of these paths fabricate a signature — the
# forged-key test signs with a freshly generated, in-memory foreign key and
# asserts the verifier REFUSES it.
# ---------------------------------------------------------------------------


def _foreign_p256_pem() -> str:
    """A fresh, in-memory ECDSA P-256 key that is NOT the cosign key.

    Generated at runtime (never committed), so gitleaks sees no key material.
    Used only to forge a real-but-untrusted signature the verifier must reject.
    """
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization

    key = ec.generate_private_key(ec.SECP256R1())
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")


def test_forged_foreign_key_signature_is_rejected(monkeypatch):
    # Sign with a foreign key => a REAL ECDSA sig, but from the wrong keypair.
    monkeypatch.setenv("SZL_COSIGN_PRIVATE_KEY_PEM", _foreign_p256_pem())
    env = dsse.sign_payload({"model": "a11oy-governed-engine", "score": 0.98})
    assert env["signed"] is True
    assert len(env["signatures"]) == 1  # a genuine signature was produced
    verdict = dsse.verify_envelope(env)
    # ...and the verifier bound to cosign.pub must refuse the foreign key.
    assert verdict["verified"] is False
    assert verdict["signatures"][0]["verified"] is False
    assert verdict["signatures"][0]["reason"] == "signature mismatch"


def test_tampered_payload_after_signing_is_rejected(monkeypatch):
    monkeypatch.setenv("SZL_COSIGN_PRIVATE_KEY_PEM", _foreign_p256_pem())
    env = dsse.sign_payload({"score": 0.90})
    # Swap the payload for a different one; the signature no longer matches PAE.
    env["payload"] = base64.b64encode(
        dsse.canonical_json({"score": 0.99})
    ).decode("ascii")
    assert dsse.verify_envelope(env)["verified"] is False


def test_verify_non_dict_envelope_fails_closed():
    for bad in (None, [], "not-an-envelope", 42):
        verdict = dsse.verify_envelope(bad)  # type: ignore[arg-type]
        assert verdict["verified"] is False
        assert "reason" in verdict


def test_verify_signatures_not_a_list_fails_closed():
    env = dsse.sign_payload({"x": 1})
    env["signatures"] = "AAAA"  # malformed: a string, not a list
    verdict = dsse.verify_envelope(env)
    assert verdict["verified"] is False
    assert verdict["reason"] == "signatures is not a list"


def test_verify_non_object_signature_entry_fails_closed():
    env = dsse.sign_payload({"x": 1})
    env["signatures"] = ["not-an-object", 123]  # entries are not dicts
    verdict = dsse.verify_envelope(env)
    assert verdict["verified"] is False
    assert all(s["verified"] is False for s in verdict["signatures"])


def test_verify_garbage_base64_payload_fails_closed():
    env = dsse.sign_payload({"x": 1})
    env["payload"] = "!!!not base64!!!"
    env["signatures"] = [{"sig": "AAAA", "keyid": "szlholdings-cosign"}]
    verdict = dsse.verify_envelope(env)
    assert verdict["verified"] is False
    assert verdict["reason"] == "payload is not valid base64"


def test_verify_missing_payload_fails_closed():
    verdict = dsse.verify_envelope({"payloadType": dsse.KHIPU_PAYLOAD_TYPE,
                                    "signatures": [{"sig": "AAAA"}]})
    assert verdict["verified"] is False
    assert "missing payload" in verdict["reason"]


def test_verify_wrong_type_payload_fails_closed():
    verdict = dsse.verify_envelope({"payload": 123, "payloadType": 456,
                                    "signatures": [{"sig": "AAAA"}]})
    assert verdict["verified"] is False
    assert verdict["reason"] == "payload/payloadType wrong type"


def test_verify_corrupt_signature_bytes_fail_closed():
    # A well-shaped entry whose sig bytes are not a valid ECDSA signature must
    # be reported as failed (never raise, never a spurious pass).
    env = dsse.sign_payload({"x": 1})
    env["signatures"] = [{"sig": base64.b64encode(b"\x00\x01\x02\x03").decode(),
                          "keyid": "szlholdings-cosign"}]
    verdict = dsse.verify_envelope(env)
    assert verdict["verified"] is False
    assert verdict["signatures"][0]["verified"] is False
