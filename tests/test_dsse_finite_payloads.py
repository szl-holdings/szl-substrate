# SPDX-License-Identifier: Apache-2.0
"""Finite new JSON emission without rewriting historical signed bytes."""
import base64

import pytest

from szl_substrate import szl_dsse as dsse


@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("placement", ["root", "value", "nested", "key"])
def test_canonical_json_rejects_nonfinite_numbers(number, placement):
    payload = {
        "root": number,
        "value": {"score": number},
        "nested": {"evidence": [{"scores": [0.5, number]}]},
        "key": {number: "evidence"},
    }[placement]
    with pytest.raises(ValueError):
        dsse.canonical_json(payload)


@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf")])
def test_sign_payload_rejects_nonfinite_before_loading_any_key(monkeypatch, number):
    def forbidden_key_load():
        pytest.fail("invalid JSON must be rejected before accessing signing material")

    monkeypatch.setattr(dsse, "_load_private_key", forbidden_key_load)
    with pytest.raises(ValueError):
        dsse.sign_payload({"evidence": [number]})


def test_finite_unsigned_payload_and_pae_bytes_are_unchanged(monkeypatch):
    monkeypatch.setattr(dsse, "_load_private_key", lambda: None)
    payload = {"z": "λ", "values": [-0.0, 1.25, 1e-300, 1e300],
               "flags": [True, False, None], "count": 42}
    expected = ('{"count":42,"flags":[true,false,null],'
                '"values":[-0.0,1.25,1e-300,1e+300],"z":"λ"}').encode("utf-8")
    assert dsse.canonical_json(payload) == expected
    env = dsse.sign_payload(payload)
    assert env["signed"] is False
    assert env["signatures"] == []
    assert base64.b64decode(env["payload"]) == expected
    payload_type = dsse.KHIPU_PAYLOAD_TYPE.encode("utf-8")
    assert dsse.pae(dsse.KHIPU_PAYLOAD_TYPE, expected) == (
        b"DSSEv1 " + str(len(payload_type)).encode() + b" " + payload_type
        + b" " + str(len(expected)).encode() + b" " + expected
    )


@pytest.mark.parametrize("body", [
    b'{"score":NaN}', b'{"score":Infinity}', b'{"score":-Infinity}',
    b'{"score":1e999}', b'{ "score": 0.9 }', b"opaque historical payload",
])
def test_historical_signature_verification_preserves_raw_bytes(monkeypatch, body):
    # A real ephemeral TEST key exercises byte verification; it is never
    # installed as a runtime credential or represented as the published key.
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    monkeypatch.setattr(dsse, "_load_public_key", key.public_key)
    signature = key.sign(dsse.pae(dsse.KHIPU_PAYLOAD_TYPE, body),
                         ec.ECDSA(hashes.SHA256()))
    envelope = {"payloadType": dsse.KHIPU_PAYLOAD_TYPE,
                "payload": base64.b64encode(body).decode("ascii"),
                "signatures": [{"keyid": "ephemeral-test-key",
                                "sig": base64.b64encode(signature).decode("ascii")}]}
    assert dsse.verify_envelope(envelope)["verified"] is True
    envelope["payload"] = base64.b64encode(body + b" ").decode("ascii")
    assert dsse.verify_envelope(envelope)["verified"] is False
