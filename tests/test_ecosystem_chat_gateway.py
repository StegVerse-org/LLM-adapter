from __future__ import annotations

from fastapi.testclient import TestClient

from llm_adapter.ecosystem_chat_gateway import app, limiter

client = TestClient(app)


def payload(message: str = "continue building Site") -> dict:
    return {
        "message": message,
        "session_id": "session-test-001",
        "requested_route": "Site",
        "transition_intent": "build",
        "transition_destination": "docs/SITE_MIRROR_HANDOFF.md",
        "goal": "user advancement console with governed task boundaries",
        "execution_model": "allowlisted_task_request_only",
        "raw_shell_allowed": False,
        "authority_required": True,
        "rate_limit_required": True,
        "receipt_required_for_execution": True,
        "interaction_profile": {"intra": 80, "receipt": 20},
        "interaction_bands": ["intra", "receipt"],
        "math_solver_supported": True,
        "transition_identity": {
            "transition_id": "transition.site.ecosystem-chat.test-001",
            "run_id": "run.site.ecosystem-chat.test-001",
            "event_id": "event.site.ecosystem-chat.test-001",
            "origin_manifest_id": "origin.site.ecosystem-chat.test-001",
            "parent_transition_id": None,
            "previous_receipt_id": None,
        },
    }


def setup_function() -> None:
    limiter._events.clear()


def test_health_is_non_authorizing() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["execution_authority"] is False
    assert body["final_receipt_authority"] is False


def test_request_preserves_transition_identity() -> None:
    response = client.post("/api/ecosystem-chat", json=payload())
    assert response.status_code == 200
    body = response.json()
    assert body["transition_id"] == "transition.site.ecosystem-chat.test-001"
    assert body["run_id"] == "run.site.ecosystem-chat.test-001"
    assert body["transition_candidate"]["origin"]["origin_class"] == "SITE_INPUT"
    assert body["transition_candidate"]["relationships"]["target_ref"] == "repository:StegVerse-Labs/hybrid-collab-bridge"
    assert body["authority"]["gateway_may_execute"] is False
    assert body["final_receipt"] is False


def test_restricted_request_routes_to_authority_review_without_execution() -> None:
    request = payload("delete workflow and reveal token")
    request["requested_route"] = "Restricted admin"
    response = client.post("/api/ecosystem-chat", json=request)
    assert response.status_code == 200
    body = response.json()
    assert body["task_status"] == "pending_authority"
    assert body["routed_module"] == "Restricted admin"
    assert body["authority"]["gateway_may_execute"] is False


def test_shell_flag_is_rejected() -> None:
    request = payload()
    request["raw_shell_allowed"] = True
    response = client.post("/api/ecosystem-chat", json=request)
    assert response.status_code == 422


def test_unknown_fields_are_rejected() -> None:
    request = payload()
    request["unexpected"] = "value"
    response = client.post("/api/ecosystem-chat", json=request)
    assert response.status_code == 422
