from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from llm_adapter import service_gateway as gateway


def runtime(tmp_path: Path):
    for name in ("packets", "receipts", "attempts", "notifications", "notification-outbox"):
        (tmp_path / name).mkdir(parents=True, exist_ok=True)
    return {
        "root": tmp_path,
        "key": b"k" * 32,
        "tvc": {"decision_id": "TVC-TEST", "policy_hash": "sha256:test"},
    }


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_notification_without_participant_copy_contains_no_address(tmp_path: Path):
    rt = runtime(tmp_path)
    public = gateway._record_notification(
        runtime=rt,
        attempt_id="HIL-ATTEMPT-ONE",
        terminal_state="SUBMISSION_ACCEPTED",
        last_completed_transition="RECEIPT_EMITTED",
        submission_id="HIL-SUBMISSION-ONE",
        receipt_id="HIL-RECEIPT-ONE",
        chain_validation_state="PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED",
        custody_state="COMMITTED",
    )

    assert public["participant_copy_requested"] is False
    assert public["participant_address_retained_in_public_record"] is False
    assert "@" not in json.dumps(public)

    envelope = load(tmp_path / "notification-outbox" / "HIL-ATTEMPT-ONE.json")
    assert envelope["scope"] == "ATTEMPT_NOTIFICATION_ONLY"
    assert envelope["delivery_failure_does_not_change_submission_outcome"] is True
    assert envelope["recipients"] == [
        {"role": "STEGVERSE_STUDY_AUTHORITY", "address": "Rigel@stegverse.org"}
    ]


def test_participant_address_exists_only_in_restricted_delivery_envelope(tmp_path: Path):
    rt = runtime(tmp_path)
    email = "participant@example.com"
    public = gateway._record_notification(
        runtime=rt,
        attempt_id="HIL-ATTEMPT-TWO",
        terminal_state="CHAIN_REFUSED",
        last_completed_transition="CHAIN_REFUSED",
        reason_code="provenance_chain_mismatch",
        retry_or_reconciliation_state="PARTICIPANT_CORRECTION_REQUIRED",
        participant_email=email,
    )

    notification_path = tmp_path / "notifications" / "HIL-ATTEMPT-TWO.json"
    envelope_path = tmp_path / "notification-outbox" / "HIL-ATTEMPT-TWO.json"
    notification_text = notification_path.read_text(encoding="utf-8")
    envelope = load(envelope_path)

    assert public["participant_copy_requested"] is True
    assert email not in notification_text
    assert envelope["recipients"] == [
        {"role": "STEGVERSE_STUDY_AUTHORITY", "address": "Rigel@stegverse.org"},
        {"role": "PARTICIPANT_ATTEMPT_COPY", "address": email},
    ]


def test_participant_notification_requires_explicit_bounded_scope():
    assert gateway._normalize_participant_email("false", "participant@example.com", "NONE") is None
    assert gateway._normalize_participant_email(
        "true", "participant@example.com", "ATTEMPT_NOTIFICATION_ONLY"
    ) == "participant@example.com"

    with pytest.raises(HTTPException) as wrong_scope:
        gateway._normalize_participant_email("true", "participant@example.com", "MARKETING")
    assert wrong_scope.value.status_code == 422
    assert wrong_scope.value.detail == "participant_notification_scope_invalid"

    with pytest.raises(HTTPException) as invalid_email:
        gateway._normalize_participant_email("true", "not-an-email", "ATTEMPT_NOTIFICATION_ONLY")
    assert invalid_email.value.status_code == 422
    assert invalid_email.value.detail == "participant_notification_email_invalid"


def test_receipt_signing_never_requires_or_adds_recipient_address():
    receipt = {
        "schema_version": gateway.SCHEMA,
        "submission_id": "HIL-SUBMISSION-THREE",
        "receipt_id": "HIL-RECEIPT-THREE",
        "terminal_state": "SUBMISSION_ACCEPTED",
    }
    signed = gateway._sign_receipt(receipt, b"k" * 32)

    assert "receiver_signature" in signed
    assert "receipt_sha256" in signed
    assert "participant_notification_email" not in signed
    assert "recipients" not in signed
