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


def test_health_reports_bounded_native_executor_and_storage_posture() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["schema_version"] == "1.2.0"
    assert body["native_executor"] == "STEGVERSE_AI_ENTITY"
    assert body["native_executor_status"] == "ACTIVE"
    assert body["bounded_response_pipeline"] is True
    assert body["sqlite_transition_store"] is True
    assert isinstance(body["storage_durable_across_restarts"], bool)
    assert body["local_persistence_is_master_records_custody"] is False
    assert body["custody_queue"] is True
    assert body["execution_authority"] is False
    assert body["repository_mutation_authority"] is False
    assert body["final_response_receipt_authority"] is True
    assert body["master_records_authority"] is False


def test_request_preserves_identity_and_returns_completed_lifecycle() -> None:
    response = client.post("/api/ecosystem-chat", json=payload())
    assert response.status_code == 200
    body = response.json()
    assert body["transition_id"] == "transition.site.ecosystem-chat.test-001"
    assert body["run_id"] == "run.site.ecosystem-chat.test-001"
    assert body["event_id"] == "event.site.ecosystem-chat.test-001"
    assert body["origin_manifest_id"] == "origin.site.ecosystem-chat.test-001"
    assert body["task_status"] == "completed_bounded_response"
    assert body["lifecycle_state"] == "COMPLETED"
    assert body["admissibility_result"] == "ALLOW"
    assert body["commit_time_validity"] == "VALID"
    assert body["final_receipt"] is True
    assert body["final_receipt_id"].startswith("final-response-receipt:sha256:")
    assert body["transition_candidate"]["origin"]["origin_class"] == "SITE_INPUT"
    assert body["transition_candidate"]["relationships"]["target_ref"] == "executor:STEGVERSE_AI_ENTITY"
    assert body["authority"]["native_executor_active"] is True
    assert body["authority"]["repository_mutation_allowed"] is False
    assert body["authority"]["local_persistence_is_master_records_custody"] is False
    assert body["sqlite_persisted"] is True
    assert body["master_record_status"] in {"PENDING", "RECORDED"}
    assert body["custody_submission"]["state"] in {"PENDING", "RETRY", "RECORDED"}


def test_transition_status_lookup_returns_same_receipt_and_queue_state() -> None:
    created = client.post("/api/ecosystem-chat", json=payload()).json()
    response = client.get(f"/api/transitions/{created['transition_id']}")
    assert response.status_code == 200
    status = response.json()
    assert status["transition_id"] == created["transition_id"]
    assert status["run_id"] == created["run_id"]
    assert status["lifecycle_state"] == "COMPLETED"
    assert status["final_receipt_id"] == created["final_receipt_id"]
    assert status["master_record_status"] in {"PENDING", "RECORDED"}
    assert status["sqlite_persisted"] is True
    assert status["local_persistence_is_custody"] is False
    assert status["custody_submission"] is not None


def test_restricted_request_routes_to_authority_review_without_final_receipt() -> None:
    request = payload("delete workflow and reveal token")
    request["requested_route"] = "Restricted admin"
    response = client.post("/api/ecosystem-chat", json=request)
    assert response.status_code == 200
    body = response.json()
    assert body["task_status"] == "pending_authority"
    assert body["routed_module"] == "Restricted admin"
    assert body["lifecycle_state"] == "VERIFICATION_REQUIRED"
    assert body["final_receipt"] is False
    assert body["final_receipt_id"] is None
    assert body["custody_submission"] is None
    assert body["authority"]["repository_mutation_allowed"] is False


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
