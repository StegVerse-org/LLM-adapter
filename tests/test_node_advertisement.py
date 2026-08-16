import hashlib
import json

from fastapi.testclient import TestClient

from llm_adapter.combined_gateway import app


def _digest(payload: dict) -> str:
    material = dict(payload)
    material.pop("advertisement_sha256", None)
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_node_advertisement_is_health_bound_and_non_authorizing(monkeypatch) -> None:
    monkeypatch.setenv("STEGVERSE_NODE_ID", "test-portable-node")
    monkeypatch.setenv("STEGVERSE_PROVIDER_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")

    response = TestClient(app).get("/api/stegverse-node")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "stegverse.node.endpoint-advertisement.v1"
    assert payload["node_id"] == "test-portable-node"
    assert payload["capability_id"] == "ecosystem-chat-gateway"
    assert payload["endpoint"].endswith("/api/ecosystem-chat")
    assert payload["health_endpoint"].endswith("/health")
    assert payload["math_solver_readiness_endpoint"].endswith("/api/math-solver/v1/readiness")
    assert payload["math_solver_solve_endpoint"].endswith("/api/math-solver/v1/solve")
    assert payload["health_bound"] is True
    assert payload["provider_enabled"] is True
    assert payload["durable_storage"] is True
    assert payload["credential_authority"] == "TV/TVC"
    assert payload["github_token_runtime_authority"] == "NONE"
    assert payload["authority_granted"] is False
    assert payload["publication_authority"] is False
    assert payload["execution_authority"] is False
    assert payload["advertisement_sha256"] == _digest(payload)


def test_default_cors_allows_stegverse_site() -> None:
    response = TestClient(app).options(
        "/api/stegverse-node",
        headers={
            "Origin": "https://stegverse.org",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://stegverse.org"
