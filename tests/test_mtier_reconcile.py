# SPDX-License-Identifier: Apache-2.0
# © 2026 Lutar, Stephen P. — SZL Holdings · Doctrine v11
"""Tests for the M-tier reconciled drift batch (Wave-E dev 5).

Three shared files had DRIFTED between a11oy and killinchu and were reconciled to
a single canonical copy in the substrate:

  - ``_vendor_blobs``          : canonical = a11oy (strict SUPERSET of killinchu's
                                 asset set; all shared values byte-identical).
  - ``szl_be_hardening``       : canonical = UNION of both apps' rate-limit exempt
                                 routes + metered prefixes, with a11oy's SEC-08
                                 ``Server`` header redaction restored (killinchu had
                                 dropped it — the classic fixed-in-one-app-only bug).
  - ``szl_evidence_research``  : canonical = killinchu (SUPERSET claim map spanning
                                 both organ namespaces) with the OpenAlex polite-pool
                                 contact defaulting to the canonical org domain and
                                 still env-overridable via ``SZL_EVIDENCE_MAILTO``.

serve.py is intentionally NOT extracted — it is the per-app entrypoint and its
divergence is legitimate (two different applications), so there is nothing to
reconcile into a shared module.
"""
from __future__ import annotations

import importlib

import pytest

RECONCILED = ["_vendor_blobs", "szl_be_hardening", "szl_evidence_research"]


@pytest.mark.parametrize("modname", RECONCILED)
def test_reconciled_module_importable(modname):
    pkg = importlib.import_module("szl_substrate")
    sub = importlib.import_module(f"szl_substrate.{modname}")
    assert getattr(pkg, modname) is sub


def test_vendor_blobs_is_canonical_superset():
    from szl_substrate import _vendor_blobs as vb

    names = set(vb.names())
    # a11oy's superset: KaTeX woff2 + ttf + woff variants, plus the two UI fonts.
    assert len(names) >= 63
    # keys killinchu shipped must all be present (subset relationship preserved)…
    killinchu_subset = {
        "earth-night.jpg",
        "fonts/KaTeX_Main-Regular.woff2",
        "fonts/KaTeX_AMS-Regular.woff2",
    }
    assert killinchu_subset <= names
    # …plus the a11oy-only extras that were missing from killinchu.
    assert {"fonts/SpaceGrotesk.woff2", "fonts/JetBrainsMono.woff2"} <= names
    assert "fonts/KaTeX_Main-Regular.ttf" in names
    # get() actually decodes real bytes (no fabricated/empty blobs).
    blob = vb.get("earth-night.jpg")
    assert isinstance(blob, bytes) and len(blob) > 100_000
    assert vb.get("does-not-exist") is None


def test_be_hardening_route_union_and_metering():
    from szl_substrate import szl_be_hardening as h

    # both apps' human-facing pages are exempt from the meter (union)…
    for page in ("/", "/frontier", "/warhacker", "/drones", "/counter-uas", "/navy"):
        assert h._is_rate_limited_path(page) is False, page
    # health probes (incl. killinchu's under /api/*) are exempt…
    for probe in ("/healthz", "/readyz", "/api/killinchu/healthz"):
        assert h._is_rate_limited_path(probe) is False, probe
    # …while the JSON data surface stays metered, including killinchu's /mesh.
    for data in ("/api/a11oy/v1/reason", "/feeds/x", "/osint/y", "/mesh/telemetry"):
        assert h._is_rate_limited_path(data) is True, data


def test_be_hardening_keeps_sec08_server_redaction():
    """The SEC-08 ``Server`` header redaction lived only in a11oy; reconciliation
    must keep it so killinchu gains the fix too (single source of truth)."""
    import inspect

    src = inspect.getsource(importlib.import_module("szl_substrate.szl_be_hardening"))
    assert 'resp.headers["Server"] = "szl"' in src


def test_evidence_research_canonical_mailto_and_superset_claims(monkeypatch):
    from szl_substrate import szl_evidence_research as e

    # canonical org-domain default, still env-overridable.
    assert e._MAILTO == "research@a-11-oy.com"

    # superset claim map: both organ namespaces + killinchu's added tabs.
    all_ids = {c["id"] for claims in e.CLAIMS.values() for c in claims}
    assert {"a11oy", "killinchu"} <= set(e.CLAIMS)
    assert {"signed-receipts", "counter-uas"} <= all_ids  # shared originals
    assert {"finance-live-feeds", "real-estate-grounding", "fraud-controls"} <= all_ids
    assert hasattr(e, "register")
