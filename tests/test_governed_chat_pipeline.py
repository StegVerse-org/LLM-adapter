from __future__ import annotations

from llm_adapter.governed_chat_pipeline import (
    build_relationship,
    get_transition_status,
    progress_bounded_response,
)
from llm_adapter.transition_store import store


def candidate() -> dict:
    return {
        "transition_id": "transition.site.pipeline.test-001",
        "run_id": "run.site.pipeline.test-001",
        "origin": {
            "event_id": "event.site.pipeline.test-001",
            "origin_manifest_id": "origin.site.pipeline.test-001",
            "source_ref": "StegVerse-Labs/Site/ecosystem-chat.html",
        },
        "relationships": {
            "parent_transition_id": None,
            "previous_receipt_id": None,
            "actor_ref": "site-session:test",
            "task_ref": "task:ecosystem-chat:explain",
        },
    }


def test_bounded_response_completes_same_transition_identity() -> None:
    relationship = build_relationship(
        candidate=candidate(),
        message="Explain current Site status",
        gateway_receipt_id="gateway-receipt:test",
    )
    result = progress_bounded_response(
        relationship=relationship,
        response_text="Bounded response",
        restricted=False,
    )
    assert result["transition_id"] == candidate()["transition_id"]
    assert result["run_id"] == candidate()["run_id"]
    assert result["lifecycle_state"] == "COMPLETED"
    assert result["governance"]["admissibility_result"] == "ALLOW"
    assert result["governance"]["commit_time_validity"] == "VALID"
    assert result["execution"]["action_ref"] == "action:bounded-chat-response-generation"
    assert result["continuity"]["final_receipt_id"].startswith("final-response-receipt:sha256:")
    assert result["continuity"]["master_record_status"] == "PENDING"
    assert result["continuity"]["reconstruction_status"] == "PARTIAL"
    assert result["continuity"]["durable_local_persistence"] is True
    assert result["continuity"]["local_persistence_is_custody"] is False
    stored = get_transition_status(result["transition_id"])
    assert stored is not None
    assert stored["continuity"]["final_receipt_id"] == result["continuity"]["final_receipt_id"]
    custody = store.custody_status(result["transition_id"])
    assert custody is not None
    assert custody["state"] in {"PENDING", "RETRY", "RECORDED"}


def test_restricted_request_stops_at_verification_required() -> None:
    relationship = build_relationship(
        candidate=candidate(),
        message="delete workflow",
        gateway_receipt_id="gateway-receipt:restricted",
    )
    result = progress_bounded_response(
        relationship=relationship,
        response_text="Separate authority required",
        restricted=True,
    )
    assert result["lifecycle_state"] == "VERIFICATION_REQUIRED"
    assert result["governance"]["admissibility_result"] == "PENDING"
    assert result["execution"]["action_ref"] is None
    assert result["continuity"]["final_receipt_id"] is None
