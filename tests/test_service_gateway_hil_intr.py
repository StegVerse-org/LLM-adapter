from __future__ import annotations

import hashlib
import importlib

from fastapi import FastAPI
from fastapi.testclient import TestClient

mod = importlib.import_module("llm_adapter.service_gateway_hil_intr")


def app_client(monkeypatch, *, enabled: bool = True, upstream: str = "http://127.0.0.1:8765/intr/materialization") -> TestClient:
    monkeypatch.setenv("STEGVERSE_HIL_INTR_ENABLED", "true" if enabled else "false")
    monkeypatch.setenv("STEGVERSE_HIL_INTR_UPSTREAM", upstream)
    app = FastAPI()
    app.include_router(mod.router)
    return TestClient(app)


def headers(body: bytes, origin: str = "STEGOS_NODE_OUTBOX") -> dict[str, str]:
    value = {
        "Origin": "https://stegverse.org",
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": origin,
        "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
    }
    if origin == "TVC_RELAY_EGRESS":
        value["X-StegVerse-Authorization-Id"] = "TVC-AUTH-TEST"
    return value


def test_readiness_preserves_non_authority(monkeypatch):
    client = app_client(monkeypatch)
    payload = client.get("/intr/materialization/readiness").json()
    assert payload["state"] == "READY"
    assert payload["credential_authority"] == "TV/TVC"
    assert payload["github_token_runtime_authority"] == "NONE"
    assert payload["gateway_receipt_authority"] is False
    assert payload["gateway_execution_authority"] is False
    assert payload["gateway_custody_authority"] is False
    assert payload["g18_completion_required"] is False
    assert payload["second_user_device_required"] is False


def test_node_trigger_forwards_exact_bytes_and_headers(monkeypatch):
    body = b'{"schema":"stegos.node_intr_materialization_trigger.v1"}'
    observed = {}
    def fake_forward(raw, forwarded):
        observed["body"] = raw
        observed["headers"] = forwarded
        return 202, b'{"state":"INGRESS_ADMITTED"}', "application/json"
    monkeypatch.setattr(mod, "_forward", fake_forward)
    client = app_client(monkeypatch)
    response = client.post("/intr/materialization", content=body, headers=headers(body))
    assert response.status_code == 202
    assert observed["body"] == body
    assert observed["headers"]["x-stegverse-transport"] == "InTr"
    assert observed["headers"]["x-stegverse-transport-origin"] == "STEGOS_NODE_OUTBOX"
    assert "x-stegverse-authorization-id" not in observed["headers"]


def test_node_cannot_smuggle_authorization(monkeypatch):
    body = b"{}"
    h = headers(body)
    h["X-StegVerse-Authorization-Id"] = "FORBIDDEN"
    client = app_client(monkeypatch)
    assert client.post("/intr/materialization", content=body, headers=h).status_code == 400


def test_relay_requires_authorization(monkeypatch):
    body = b"{}"
    h = headers(body, "TVC_RELAY_EGRESS")
    h.pop("X-StegVerse-Authorization-Id")
    client = app_client(monkeypatch)
    assert client.post("/intr/materialization", content=body, headers=h).status_code == 400


def test_remote_upstream_is_rejected(monkeypatch):
    client = app_client(monkeypatch, upstream="https://example.com/intr/materialization")
    payload = client.get("/intr/materialization/readiness").json()
    assert payload["state"] == "NOT_READY"
    assert payload["loopback_upstream_configured"] is False


def test_disabled_proxy_fails_closed(monkeypatch):
    body = b"{}"
    client = app_client(monkeypatch, enabled=False)
    assert client.post("/intr/materialization", content=body, headers=headers(body)).status_code == 503
