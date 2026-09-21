from __future__ import annotations

import importlib

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

mod = importlib.import_module("llm_adapter.service_gateway_hil_receiver_proxy")


def client(monkeypatch, *, enabled=True, upstream="http://127.0.0.1:8877"):
    monkeypatch.setenv(mod.ENABLED_ENV, "true" if enabled else "false")
    monkeypatch.setenv(mod.UPSTREAM_ENV, upstream)
    app = FastAPI()
    app.add_middleware(mod.HILMachineReceiverProxyMiddleware)

    @app.get("/api/hil/readiness")
    def local_readiness():
        return {"source": "local-copy"}

    return TestClient(app, base_url="https://stegverse.org")


def test_receiver_projection_uses_distinct_loopback_origin(monkeypatch):
    monkeypatch.setenv(mod.UPSTREAM_ENV, "http://127.0.0.1:8877")
    assert mod.upstream_base() == "http://127.0.0.1:8877"
    assert mod.target_url("/api/hil/submissions") == "http://127.0.0.1:8877/api/hil/submissions"


def test_receiver_projection_rejects_intr_path_or_remote_origin(monkeypatch):
    monkeypatch.setenv(mod.UPSTREAM_ENV, "http://127.0.0.1:8877/intr/materialization")
    try:
        mod.upstream_base()
    except ValueError as exc:
        assert "origin without path" in str(exc)
    else:
        raise AssertionError("path-bearing HIL receiver upstream accepted")
    monkeypatch.setenv(mod.UPSTREAM_ENV, "https://example.com")
    try:
        mod.upstream_base()
    except ValueError as exc:
        assert "loopback http" in str(exc)
    else:
        raise AssertionError("remote HIL receiver upstream accepted")


def test_proxy_precedes_local_hil_copy_and_preserves_exact_multipart_bytes(monkeypatch):
    observed = {}
    def fake_forward(method, target, body, headers):
        observed.update(method=method,target=target,body=body,headers=headers)
        return 201, b'{"schema_version":"HIL-RECEIVER-RECEIPT-v2","custody_state":"EXACT_BYTES_PERSISTED"}', "application/json", {}
    monkeypatch.setattr(mod, "_forward", fake_forward)
    c = client(monkeypatch)
    body = b"--X\r\nContent-Disposition: form-data; name=\"response_pdf\"\r\n\r\n%PDF-exact\r\n--X--\r\n"
    response = c.post("/api/hil/submissions", content=body, headers={"Content-Type":"multipart/form-data; boundary=X","Origin":"https://stegverse.org"})
    assert response.status_code == 201
    assert response.json()["schema_version"] == "HIL-RECEIVER-RECEIPT-v2"
    assert observed["target"] == "http://127.0.0.1:8877/api/hil/submissions"
    assert observed["body"] == body
    assert observed["headers"]["content-type"] == "multipart/form-data; boundary=X"


def test_proxy_preserves_reconstruction_header(monkeypatch):
    def fake_forward(method, target, body, headers):
        return 200, b"%PDF-exact", "application/pdf", {"x-stegverse-hil-reconstruction-state":"EXACT_BYTES_HASH_VERIFIED"}
    monkeypatch.setattr(mod, "_forward", fake_forward)
    c = client(monkeypatch)
    response = c.get("/api/hil/submissions/S1/exact-bytes", headers={"X-SteGVerse-HIL-Review-Token":"opaque"})
    assert response.status_code == 200
    assert response.content == b"%PDF-exact"
    assert response.headers["x-stegverse-hil-reconstruction-state"] == "EXACT_BYTES_HASH_VERIFIED"


def test_disabled_projection_falls_through_to_local_route(monkeypatch):
    c = client(monkeypatch, enabled=False)
    response = c.get("/api/hil/readiness")
    assert response.status_code == 200
    assert response.json() == {"source":"local-copy"}


def test_browser_authorization_and_cookie_headers_fail_closed(monkeypatch):
    c = client(monkeypatch)
    assert c.get("/api/hil/readiness", headers={"Authorization":"Bearer forbidden"}).status_code == 400
    assert c.get("/api/hil/readiness", headers={"Cookie":"x=y"}).status_code == 400
