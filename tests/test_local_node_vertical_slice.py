import hashlib
import json

from fastapi.testclient import TestClient

from llm_adapter.combined_gateway import app


def _advertisement_digest(payload: dict) -> str:
    material = dict(payload)
    material.pop("advertisement_sha256", None)
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_local_node_identity_health_and_governed_request_slice(monkeypatch) -> None:
    monkeypatch.setenv("STEGVERSE_NODE_ID", "vertical-slice-node")
    monkeypatch.setenv("STEGVERSE_PROVIDER_ENABLED", "false")
    monkeypatch.setenv("STEGVERSE_EXTERNAL_MUTATION_ENABLED", "false")
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")

    client = TestClient(app, base_url="http://127.0.0.1:8000")

    advertisement_response = client.get("/api/stegverse-node")
    assert advertisement_response.status_code == 200
    advertisement = advertisement_response.json()
    assert advertisement["schema"] == "stegverse.node.endpoint-advertisement.v1"
    assert advertisement["node_id"] == "vertical-slice-node"
    assert advertisement["endpoint"] == "http://127.0.0.1:8000/api/ecosystem-chat"
    assert advertisement["health_endpoint"] == "http://127.0.0.1:8000/health"
    assert advertisement["advertisement_sha256"] == _advertisement_digest(advertisement)
    assert advertisement["health_bound"] is True
    assert advertisement["authority_granted"] is False
    assert advertisement["publication_authority"] is False
    assert advertisement["execution_authority"] is False

    health_response = client.get("/health")
    assert health_response.status_code == 200
    health = health_response.json()
    assert health["status"] == "ok"
    assert health["governed_provider_enabled"] is False
    assert health["storage_durable_across_restarts"] is True

    transition = {
        "transition_id": "site-transition-local-slice",
        "run_id": "site-run-local-slice",
        "event_id": "site-event-local-slice",
        "origin_manifest_id": "site-origin-local-slice",
        "parent_transition_id": None,
        "previous_receipt_id": None,
    }
    request_response = client.post(
        "/api/ecosystem-chat",
        headers={"X-SteGVerse-Session": "site-local-slice-session"},
        json={
            "message": "Verify the local portable-node request path.",
            "session_id": "site-local-slice-session",
            "requested_route": "chat_answer",
            "transition_intent": "bounded_information_request",
            "transition_destination": "ecosystem_chat",
            "goal": "governed Ecosystem Chat request response provider usage custody and reconstruction",
            "execution_model": "allowlisted_task_request_only",
            "raw_shell_allowed": False,
            "authority_required": True,
            "rate_limit_required": True,
            "receipt_required_for_execution": True,
            "interaction_profile": "default",
            "interaction_bands": [],
            "math_solver_supported": True,
            "transition_identity": transition,
        },
    )

    assert request_response.status_code == 200
    result = request_response.json()
    assert result["transition_id"] == transition["transition_id"]
    assert result["run_id"] == transition["run_id"]
    assert result["provider"]["used"] is False
    assert result["authority"]["provider_usage_grants_authority"] is False
    assert result["master_records_usage_submission"] is None
