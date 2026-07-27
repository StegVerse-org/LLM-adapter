from __future__ import annotations

from hashlib import sha256

from fastapi.testclient import TestClient

from llm_adapter.user_llm_activation import build_activation_proof
from llm_adapter.user_llm_http_transport import HTTPRouteConfig
from llm_adapter.user_llm_router import RouteTransports
from llm_adapter.user_llm_service import create_app


def test_activation_proof_defers_without_complete_endpoint_set():
    proof = build_activation_proof(
        HTTPRouteConfig(demo_test_suite_url="https://demo.example/submit")
    )
    public = proof.as_public_dict()

    assert proof.activated is False
    assert public["state"] == "DEFERRED"
    assert public["routes"][0]["configured"] is True
    assert public["routes"][1]["configured"] is False
    assert public["authority_attached"] is False


def test_activation_proof_is_deterministic_and_hides_endpoint_values():
    config = HTTPRouteConfig(
        demo_test_suite_url="https://demo.example/submit",
        entity_sandbox_runner_url="https://sandbox.example/submit",
        hil_response_packet_url="https://hil.example/submit",
        bearer_token="must-not-appear",
    )
    first = build_activation_proof(config).as_public_dict()
    second = build_activation_proof(config).as_public_dict()

    assert first == second
    assert first["state"] == "ACTIVATED"
    assert first["routes"][0]["endpoint_hash"] == sha256(
        b"https://demo.example/submit"
    ).hexdigest()
    serialized = str(first)
    assert "https://" not in serialized
    assert "must-not-appear" not in serialized
    assert first["execution_authority"] is False
    assert first["publication_authority"] is False
    assert first["continuity_authority"] is False
    assert first["master_record_custody"] is False


def test_activation_proof_endpoint_uses_environment_without_exposing_urls(monkeypatch):
    monkeypatch.setenv("STEGVERSE_DEMO_TEST_SUITE_URL", "https://demo.example/submit")
    monkeypatch.setenv("STEGVERSE_ENTITY_SANDBOX_RUNNER_URL", "https://sandbox.example/submit")
    monkeypatch.setenv("STEGVERSE_HIL_RESPONSE_PACKET_URL", "https://hil.example/submit")
    monkeypatch.setenv("STEGVERSE_USER_LLM_BEARER_TOKEN", "secret")

    client = TestClient(create_app(transports=RouteTransports(), load_environment=False))
    response = client.get("/v1/user-llm/activation-proof")
    payload = response.json()

    assert response.status_code == 200
    assert payload["state"] == "ACTIVATED"
    assert all(route["configured"] for route in payload["routes"])
    assert "https://" not in response.text
    assert "secret" not in response.text
