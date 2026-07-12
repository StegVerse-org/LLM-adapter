from __future__ import annotations

from pathlib import Path

from llm_adapter.master_records_client import build_submission, validate_response
from llm_adapter.transition_store import TransitionStore


def completed_record() -> dict:
    return {
        "schema_version": "1.0.0",
        "record_type": "governed_transition_relationship",
        "transition_id": "transition.test.durable-001",
        "run_id": "run.test.durable-001",
        "lifecycle_state": "COMPLETED",
        "origin": {
            "origin_class": "SITE_INPUT",
            "event_id": "event.test.durable-001",
            "origin_manifest_id": "origin.test.durable-001",
        },
        "relationships": {},
        "governance": {
            "evidence_refs": [],
            "admissibility_result": "ALLOW",
            "commit_time_validity": "VALID",
        },
        "execution": {},
        "continuity": {
            "final_receipt_id": "final-response-receipt:test-001",
            "master_record_ref": None,
            "master_record_status": "PENDING",
            "reconstruction_status": "PARTIAL",
        },
        "projection": {},
    }


def test_store_survives_reopen_and_queues_custody(tmp_path: Path) -> None:
    path = tmp_path / "transitions.db"
    first = TransitionStore(path)
    record = completed_record()
    first.put(record)
    first.enqueue_custody(record)

    second = TransitionStore(path)
    restored = second.get(record["transition_id"])
    assert restored is not None
    assert restored["run_id"] == record["run_id"]
    queue = second.custody_status(record["transition_id"])
    assert queue is not None
    assert queue["state"] == "PENDING"


def test_mark_recorded_requires_external_receipt_values(tmp_path: Path) -> None:
    store = TransitionStore(tmp_path / "transitions.db")
    record = completed_record()
    store.put(record)
    store.enqueue_custody(record)
    updated = store.mark_recorded(
        record["transition_id"],
        custody_receipt_id="custody-receipt:test-001",
        master_record_ref="master-record:test-001",
    )
    assert updated["continuity"]["master_record_status"] == "RECORDED"
    assert updated["continuity"]["master_record_ref"] == "master-record:test-001"
    assert updated["continuity"]["reconstruction_status"] == "PASS"


def test_submission_and_response_preserve_identity() -> None:
    record = completed_record()
    submission = build_submission(record)
    assert submission["authority_boundary"]["submission_is_custody"] is False
    response = {
        "transition_id": record["transition_id"],
        "run_id": record["run_id"],
        "final_receipt_id": record["continuity"]["final_receipt_id"],
        "custody_status": "RECORDED",
        "custody_receipt_id": "custody-receipt:test-001",
        "master_record_ref": "master-record:test-001",
        "reconstruction_status": "PASS",
    }
    custody_receipt, master_ref = validate_response(record, response)
    assert custody_receipt == "custody-receipt:test-001"
    assert master_ref == "master-record:test-001"


def test_identity_mismatch_is_rejected() -> None:
    record = completed_record()
    response = {
        "transition_id": "transition.other",
        "run_id": record["run_id"],
        "final_receipt_id": record["continuity"]["final_receipt_id"],
        "custody_status": "RECORDED",
        "custody_receipt_id": "custody-receipt:test-001",
        "master_record_ref": "master-record:test-001",
        "reconstruction_status": "PASS",
    }
    try:
        validate_response(record, response)
    except ValueError as exc:
        assert "identity mismatch" in str(exc)
    else:
        raise AssertionError("identity mismatch should fail")
