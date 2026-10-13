# SPDX-License-Identifier: Apache-2.0
# © 2026 Lutar, Stephen P. — SZL Holdings · Doctrine v11
"""The packaged org-RAG module exposes the explicit lexical-only switch.

The a11oy read facade imports ``szl_substrate.a11oy_org_rag`` before its
vendored copy and serves ``mode=lexical`` only when this contract constant and
``lexical_only`` parameter are present. A package without them fails closed.
"""
from __future__ import annotations

import inspect

from szl_substrate import a11oy_org_rag as rag


def test_lexical_reference_contract_and_switch_are_exported():
    assert rag.LEXICAL_REFERENCE_CONTRACT == "szl.a11oy.org_rag.lexical_reference/v1"
    param = inspect.signature(rag.query).parameters["lexical_only"]
    assert param.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert param.default is False


def test_lexical_switch_refuses_model_load_hyde_and_receipts_before_reading(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("refused lexical call reached the index or embedder")

    monkeypatch.setattr(rag, "_rehydrate_runtime_state", forbidden)
    monkeypatch.setattr(rag, "_maybe_embedder", forbidden)
    for kwargs in ({"load_embedder": True}, {"hyde_text": "hypothetical"},
                   {"emit_receipt": forbidden}):
        refused = rag.query("anchor", lexical_only=True, **kwargs)
        assert refused["ok"] is False
        assert refused["reason_code"] == "LEXICAL_ONLY_ARGUMENT_CONFLICT"
        assert refused["inference"] == "NOT_INVOKED"
        assert refused["router_dispatch_count"] == 0
