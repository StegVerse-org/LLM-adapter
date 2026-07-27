from __future__ import annotations

from fastapi.testclient import TestClient


def test_explicit_test_mode_returns_non_authoritative_fixture(monkeypatch):
    monkeypatch.setenv("STEGVERSE_USER_LLM_TEST_MODE", "true")
    monkeypatch.setenv("STEGVERSE_DEMO_TEST_SUITE_URL", "http://127.0.0.1/user-llm-test/demo")
    monkeypatch.setenv("STEGVERSE_ENTITY_SANDBOX_RUNNER_URL", "http://127.0.0.1/user-llm-test/sandbox")
    monkeypatch.setenv("STEGVERSE_HIL_RESPONSE_PACKET_URL", "http://127.0.0.1/user-llm-test/hil")

    from llm_adapter.user_llm_service import create_app

    client = TestClient(create_app())
    assert client.get("/readyz").json()["state"] == "READY"
    activation = client.get("/v1/user-llm/activation-proof").json()
    assert activation["state"] == "ACTIVATED"
    assert activation["test_mode"] is True
    assert activation["downstream_execution_verified"] is False

    response = client.post(
        "/v1/user-llm/requests",
        json={
            "identity": {
                "user_id": "test-user",
                "llm_id": "test-llm",
                "provider": "test-provider",
                "model": "test-model",
                "scopes": ["demo:read"],
            },
            "route": "demo_test_suite",
            "action": "list",
            "payload": {},
        },
    ).json()
    assert response["status"] == "RETURNED"
    assert response["result"]["status"] == "TEST_RETURNED"
    assert response["test_mode"] is True
    assert response["downstream_execution_verified"] is False
    assert response["authority_attached"] is False
