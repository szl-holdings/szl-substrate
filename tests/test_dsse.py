# SPDX-License-Identifier: Apache-2.0
"""Tests for szl_substrate.szl_dsse — DSSE PAE + UNSIGNED-honest fallback.

These tests deliberately run WITHOUT a cosign private key present, exercising
the honest-unsigned path. The module must NEVER fabricate a signature.
"""
import base64
import json
import os

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
