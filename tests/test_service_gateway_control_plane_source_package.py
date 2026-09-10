from __future__ import annotations

import hashlib
import importlib

from fastapi import FastAPI
from fastapi.testclient import TestClient

mod = importlib.import_module("llm_adapter.service_gateway_hil_intr")


def client(monkeypatch) -> TestClient:
    monkeypatch.setenv("STEGVERSE_UNIVERSAL_INTR_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_UNIVERSAL_INTR_UPSTREAM", "http://127.0.0.1:8765/intr/materialization")
    app = FastAPI(); app.include_router(mod.router)
    return TestClient(app, base_url="https://stegverse.org")


def profile() -> dict:
    return {
        "schema": "stegverse.hil-intr-materialization-ingress-profile/v1",
        "state": "ACTIVE_SOVEREIGN_INTR_INGRESS",
        "protocol": "InTr",
        "profile_path": "/intr/profile",
        "materialization_path": "/intr/materialization",
        "control_plane_source_package_path": "/intr/source-package",
        "additional_materialization_profiles": ["HIL:Ingress", "stegverse.control-plane"],
        "event_triggered": True,
        "always_on_receiver_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "authority_effect": "NONE_DISCOVERY_EVIDENCE_ONLY",
    }


def headers(body: bytes, *, relay: bool = True) -> dict[str, str]:
    out = {
        "Origin": "https://stegverse.org",
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": "TVC_RELAY_EGRESS" if relay else "STEGOS_NODE_OUTBOX",
        "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
    }
    if relay:
        out["X-StegVerse-Authorization-Id"] = "AUTH-SOURCE-PACKAGE-1"
    return out


def test_source_package_projects_to_same_loopback_receiver(monkeypatch):
    monkeypatch.setattr(mod, "_read_profile", lambda: profile())
    observed = {}
    def forward(target, body, forwarded, **kwargs):
        observed["target"] = target; observed["body"] = body; observed["headers"] = forwarded; observed["kwargs"] = kwargs
        return 202, b'{"state":"SOURCE_MATERIALIZED_VERIFIED"}', "application/json"
    monkeypatch.setattr(mod, "_forward_to", forward)
    body = b'{"schema":"stegverse.source-package/v1"}'
    response = client(monkeypatch).post("/intr/source-package", content=body, headers=headers(body))
    assert response.status_code == 202
    assert observed["target"] == "http://127.0.0.1:8765/intr/source-package"
    assert observed["body"] == body
    assert observed["headers"]["x-stegverse-transport-origin"] == "TVC_RELAY_EGRESS"
    assert observed["headers"]["x-stegverse-authorization-id"] == "AUTH-SOURCE-PACKAGE-1"


def test_source_package_rejects_node_origin(monkeypatch):
    monkeypatch.setattr(mod, "_read_profile", lambda: profile())
    body = b"{}"
    response = client(monkeypatch).post("/intr/source-package", content=body, headers=headers(body, relay=False))
    assert response.status_code == 400
    assert response.json()["detail"] == "tvc_relay_egress_required"


def test_source_package_requires_advertised_capability(monkeypatch):
    value = profile(); value["additional_materialization_profiles"] = ["HIL:Ingress"]
    monkeypatch.setattr(mod, "_read_profile", lambda: value)
    body = b"{}"
    response = client(monkeypatch).post("/intr/source-package", content=body, headers=headers(body))
    assert response.status_code == 503
    assert "stegverse.control-plane" in response.json()["detail"]


def test_source_package_requires_public_https(monkeypatch):
    monkeypatch.setattr(mod, "_read_profile", lambda: profile())
    monkeypatch.setenv("STEGVERSE_UNIVERSAL_INTR_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_UNIVERSAL_INTR_UPSTREAM", "http://127.0.0.1:8765/intr/materialization")
    app = FastAPI(); app.include_router(mod.router)
    body = b"{}"
    response = TestClient(app).post("/intr/source-package", content=body, headers=headers(body))
    assert response.status_code == 400
    assert response.json()["detail"] == "public_https_required"


def test_readiness_advertises_source_package_path(monkeypatch):
    payload = client(monkeypatch).get("/intr/materialization/readiness").json()
    assert payload["control_plane_source_package_path"] == "/intr/source-package"
    assert payload["gateway_execution_authority"] is False
    assert payload["credential_authority"] == "TV/TVC"
