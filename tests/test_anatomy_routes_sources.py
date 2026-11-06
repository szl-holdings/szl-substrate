"""szl_anatomy_routes links to formula source that exists and counts what it serves.

Every formula result, chakra payload and HTML page this router renders carries a
source link. Those links used to point at recipe paths in szl-cookbook that never
existed there (the repository is now archived), and the page footer hard-coded a
formula count that no longer matched the registry it renders.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

import szl_substrate
from szl_substrate import szl_formulas

MODULE = "szl_substrate.szl_anatomy_routes"
REPO_ROOT = Path(__file__).resolve().parent.parent
BLOB_MAIN = "https://github.com/szl-holdings/szl-substrate/blob/main/"


@pytest.fixture
def routes(monkeypatch):
    # The module keeps the host-app layout (`import szl_formulas` as a bare name).
    # Satisfy that with the packaged copy instead of adding the package directory
    # to sys.path, and leave no imported module behind for other tests.
    monkeypatch.setitem(sys.modules, "szl_formulas", szl_formulas)
    sys.modules.pop(MODULE, None)
    module = importlib.import_module(MODULE)
    yield module
    sys.modules.pop(MODULE, None)
    if getattr(szl_substrate, "szl_anatomy_routes", None) is module:
        delattr(szl_substrate, "szl_anatomy_routes")


def test_source_links_resolve_to_files_in_this_repository(routes):
    for url in (routes.FORMULA_SRC, routes.COMPOSER_SRC):
        assert "szl-cookbook" not in url
        assert url.startswith(BLOB_MAIN), url
        assert (REPO_ROOT / url[len(BLOB_MAIN):]).is_file(), url


def test_rendered_payloads_carry_the_source_link(routes):
    result = routes.run_one("lambda_bounded", [[0.82, 0.91, 0.77]])
    assert result["ok"] is True
    assert result["source"] == routes.FORMULA_SRC
    chakra = routes.chakra_payload("a11oy", 1)
    assert chakra["formula_python_source_link"] == routes.FORMULA_SRC


def test_page_footer_counts_the_registry_it_renders(routes):
    html = routes._page("Formulas", "")
    assert f"· {len(szl_formulas.REGISTRY)} canonical formulas ·" in html
    assert f'href="{routes.FORMULA_SRC}"' in html
    assert "szl-cookbook" not in html
