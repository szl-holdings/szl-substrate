"""Fail-open HTTP payloads name the exception class, never its message.

The apps fixed this in their vendored copies (a11oy #958, killinchu #242:
"never leak exception text into fail-open HTTP payloads"), but the package
copies of szl_anatomy_routes, szl_connectors_serve, szl_cuas_formulas and
szl_sapa_patch still interpolated str(exc) into client-facing JSON. Each test
makes the guarded call raise with a sentinel message and checks that only the
class name reaches the response.
"""
from __future__ import annotations

import importlib
import json
import sys
import types

import pytest

import szl_substrate

SENTINEL = "internal-detail-7f3a"


class Boom(RuntimeError):
    pass


def _boom(*_args, **_kwargs):
    raise Boom(SENTINEL)


@pytest.fixture
def load(monkeypatch):
    """Import an import-directly module with its bare-name host imports satisfied."""
    loaded = []

    def _load(module: str, bare: dict[str, object]):
        for name, value in bare.items():
            monkeypatch.setitem(sys.modules, name, value)
        full = f"szl_substrate.{module}"
        sys.modules.pop(full, None)
        mod = importlib.import_module(full)
        loaded.append((full, module, mod))
        return mod

    yield _load
    for full, module, mod in loaded:
        sys.modules.pop(full, None)
        if getattr(szl_substrate, module, None) is mod:
            delattr(szl_substrate, module)


def _web():
    pytest.importorskip("fastapi", reason="the route tests need the web extra")
    pytest.importorskip("httpx", reason="starlette.testclient needs httpx")
    from fastapi import FastAPI
    from starlette.testclient import TestClient
    return FastAPI, TestClient


def test_anatomy_run_one_reports_only_the_exception_class(load, monkeypatch):
    from szl_substrate import szl_formulas

    routes = load("szl_anatomy_routes", {"szl_formulas": szl_formulas})
    monkeypatch.setitem(routes.S.REGISTRY, "lambda_bounded", _boom)
    assert routes.run_one("lambda_bounded", [[0.5, 0.6]]) == {"ok": False, "error": "Boom"}


def test_cuas_compute_reports_only_the_exception_class(monkeypatch):
    FastAPI, TestClient = _web()
    from szl_substrate import szl_cuas_formulas as cuas

    monkeypatch.setattr(cuas, "szl_cuas_compute", _boom)
    app = FastAPI()
    cuas.register(app, "a11oy")
    response = TestClient(app).post("/api/a11oy/v1/cuas/compute", json={})
    assert response.status_code == 200
    assert response.json()["error"] == {"code": "compute_error", "detail": "Boom"}
    assert SENTINEL not in response.text


def test_sapa_handlers_report_only_the_exception_class(load, monkeypatch):
    FastAPI, TestClient = _web()
    from szl_substrate import szl_sapa

    patch = load("szl_sapa_patch", {"szl_sapa": szl_sapa})
    monkeypatch.setattr(szl_sapa, "compute_sapa", _boom)
    app = FastAPI()
    patch.register(app, ns="a11oy", serve_tab=False)
    client = TestClient(app)
    for path in ("/api/a11oy/v1/sapa", "/api/a11oy/v1/sapa/receipt"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.json()["error"] == "Boom", path
        assert SENTINEL not in response.text, path


def test_connector_routes_report_only_the_exception_class(load):
    FastAPI, TestClient = _web()

    class _Connector:
        writable = True
        read = staticmethod(_boom)
        write = staticmethod(_boom)

    oauth = types.SimpleNamespace(build_authorize_url=_boom, exchange_code=_boom)
    host = types.ModuleType("szl_connectors")
    host.oauth = oauth
    host.get = lambda cid: _Connector() if cid == "crm" else None
    host.all_ids = lambda: ["crm"]
    host.manifest = lambda probe=False, category=None: {"scoreboard": {}}
    host.REGISTRY = {"crm": _Connector}
    serve = load("szl_connectors_serve", {"szl_connectors": host, "szl_connectors.oauth": oauth})
    app = FastAPI()
    serve.register(app, ns="a11oy")
    client = TestClient(app)
    base = "/api/a11oy/v1/connectors/crm"
    checks = [
        (client.get(f"{base}/read"), 502, "note", "read failed: Boom: Boom"),
        (client.post(f"{base}/write", json={"op": "x"}), 502, "detail", "write failed: Boom: Boom"),
        (client.get(f"{base}/oauth/start"), 400, "error", "Boom"),
        (client.get(f"{base}/oauth/callback?code=c&state=s"), 400, "error", "Boom"),
    ]
    for response, status, field, expected in checks:
        assert response.status_code == status, response.text
        assert response.json()[field] == expected
        assert SENTINEL not in json.dumps(response.json())
