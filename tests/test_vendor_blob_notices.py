"""Every asset embedded in _vendor_blobs is covered by NOTICE-THIRD-PARTY.md.

The blobs are third-party fonts and an image (MIT and SIL OFL 1.1), not
Apache-2.0 SZL works, so a new blob must not ship without a provenance and
license entry.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path

from szl_substrate import _vendor_blobs

NOTICE = Path(__file__).resolve().parent.parent / "NOTICE-THIRD-PARTY.md"
# key pattern documented in NOTICE-THIRD-PARTY.md -> number of blobs it covers
DOCUMENTED = {
    "fonts/KaTeX_*": 60,
    "earth-night.jpg": 1,
    "fonts/SpaceGrotesk.woff2": 1,
    "fonts/JetBrainsMono.woff2": 1,
}


def test_every_blob_matches_a_documented_entry():
    names = _vendor_blobs.names()
    counts = {p: sum(fnmatch.fnmatchcase(n, p) for n in names) for p in DOCUMENTED}
    assert counts == DOCUMENTED
    assert sum(counts.values()) == len(names)


def test_notice_lists_every_entry_and_the_blob_count():
    text = NOTICE.read_text(encoding="utf-8")
    for pattern, count in DOCUMENTED.items():
        assert f"| `{pattern}`" in text and f"| {count} |" in text, pattern
    assert f"embeds {len(_vendor_blobs.names())} binary assets" in text
