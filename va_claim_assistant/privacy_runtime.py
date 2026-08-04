#!/usr/bin/env python3
"""Fail-closed privacy gate for the governed VA Claim Assistant runtime."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

SCHEMA = "stegverse.va_claim_assistant.privacy_runtime_event.v1"
HEX64 = re.compile(r"^[a-f0-9]{64}$")

PROHIBITED_KEYS = {
    "raw_document", "raw_documents", "raw_bytes", "document_bytes", "file_bytes",
    "full_text", "ocr_text", "prompt", "prompts", "model_input", "model_inputs",
    "model_output", "model_outputs", "trace", "traces", "log", "logs",
    "ssn", "social_security_number", "va_file_number", "claim_number",
    "veteran_name", "claimant_name", "patient_name", "full_name", "first_name",
    "last_name", "date_of_birth", "dob", "email", "phone", "telephone",
    "address", "street_address", "mailing_address", "credential", "credentials",
    "access_token", "refresh_token", "password", "api_key", "secret",
    "identity_proofing_artifact", "identity_artifact", "raw_credential",
}

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("EMAIL", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("PHONE", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b")),
    ("IP_ADDRESS", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
)

SAFE_REJECTION_PLACEHOLDER = "[REDACTED_BY_PRIVACY_GATE]"


class PrivacyRuntimeError(ValueError):
    """Base privacy-runtime error."""


@dataclass(frozen=True)
class PrivacyRuntimeRejected(PrivacyRuntimeError):
    decision: dict[str, Any]

    def __str__(self) -> str:
        categories = ",".join(self.decision.get("detected_categories") or ["UNKNOWN"])
        return f"privacy_runtime_rejected:{categories}"


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _scan(value: Any, *, categories: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in PROHIBITED_KEYS:
                categories.add(f"PROHIBITED_FIELD:{normalized}")
                continue
            _scan(child, categories=categories)
    elif isinstance(value, list):
        for child in value:
            _scan(child, categories=categories)
    elif isinstance(value, str):
        for category, pattern in PATTERNS:
            if pattern.search(value):
                categories.add(category)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def inspect_runtime_request(
    *,
    question: str,
    session_id: str,
    document_context: dict[str, Any] | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    if not isinstance(question, str) or not question.strip():
        raise PrivacyRuntimeError("question_is_required")
    if not isinstance(session_id, str) or not session_id:
        raise PrivacyRuntimeError("session_id_is_required")
    if document_context is not None and not isinstance(document_context, dict):
        raise PrivacyRuntimeError("document_context_must_be_object")

    categories: set[str] = set()
    _scan(question, categories=categories)
    if document_context is not None:
        _scan(document_context, categories=categories)
        if document_context.get("privacy_state") not in {"PII_REDACTED_VERIFIED", "SANITIZED_DERIVED_CONTEXT"}:
            categories.add("SANITIZED_CONTEXT_STATE_REQUIRED")

    rejected = bool(categories)
    event: dict[str, Any] = {
        "schema": SCHEMA,
        "state": "REJECTED" if rejected else "PASS",
        "observed_at": observed_at or _utc_now(),
        "session_id_sha256": _sha256_text(session_id),
        "input_profile": {
            "question_present": True,
            "question_length": len(question),
            "question_sha256": None if rejected else _sha256_text(question),
            "document_context_present": document_context is not None,
            "document_context_sha256": None if rejected or document_context is None else canonical_hash(document_context),
        },
        "detected_categories": sorted(categories),
        "allowed_to_classify": not rejected,
        "allowed_to_generate": not rejected,
        "retention": {
            "raw_question_present": False,
            "raw_document_present": False,
            "direct_identifier_present": False,
            "credential_present": False,
            "prompt_present": False,
            "model_input_present": False,
            "model_output_present": False,
            "trace_content_present": False,
            "log_content_present": False,
            "medical_narrative_present": False,
            "rejected_input_hash_present": False,
        },
        "purpose": "VA_CLAIM_ASSISTANT_PRIVACY_GATE",
        "scope": "RAW_PII_REJECTION_AND_SANITIZED_CONTEXT_ENFORCEMENT",
        "authority_effect": False,
        "activation_effect": False,
        "custody_claimed": False,
        "reconstruction_claimed": False,
    }
    event["receipt_hash"] = canonical_hash(event)
    return event


def enforce_runtime_privacy(
    *,
    question: str,
    session_id: str,
    document_context: dict[str, Any] | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    decision = inspect_runtime_request(
        question=question,
        session_id=session_id,
        document_context=document_context,
        observed_at=observed_at,
    )
    if decision["state"] != "PASS":
        raise PrivacyRuntimeRejected(decision)
    return decision


def validate_privacy_event(event: dict[str, Any]) -> None:
    if event.get("schema") != SCHEMA:
        raise PrivacyRuntimeError("privacy_event_schema_invalid")
    if event.get("state") not in {"PASS", "REJECTED"}:
        raise PrivacyRuntimeError("privacy_event_state_invalid")
    if event.get("authority_effect") is not False or event.get("activation_effect") is not False:
        raise PrivacyRuntimeError("privacy_event_authority_escalation")
    if event.get("custody_claimed") is not False or event.get("reconstruction_claimed") is not False:
        raise PrivacyRuntimeError("privacy_event_false_claim")
    retention = event.get("retention")
    if not isinstance(retention, dict) or any(retention.values()):
        raise PrivacyRuntimeError("privacy_event_retention_boundary_failed")
    categories = event.get("detected_categories")
    if not isinstance(categories, list):
        raise PrivacyRuntimeError("privacy_event_categories_invalid")
    profile = event.get("input_profile")
    if not isinstance(profile, dict):
        raise PrivacyRuntimeError("privacy_event_input_profile_invalid")
    if event["state"] == "REJECTED":
        if profile.get("question_sha256") is not None or profile.get("document_context_sha256") is not None:
            raise PrivacyRuntimeError("rejected_input_hash_must_not_be_retained")
        if event.get("allowed_to_classify") is not False or event.get("allowed_to_generate") is not False:
            raise PrivacyRuntimeError("rejected_input_must_fail_closed")
        if not categories:
            raise PrivacyRuntimeError("rejected_input_categories_missing")
    else:
        question_hash = profile.get("question_sha256")
        if not isinstance(question_hash, str) or not HEX64.fullmatch(question_hash):
            raise PrivacyRuntimeError("accepted_question_hash_invalid")
        if event.get("allowed_to_classify") is not True or event.get("allowed_to_generate") is not True:
            raise PrivacyRuntimeError("accepted_input_not_admitted")
        if categories:
            raise PrivacyRuntimeError("accepted_input_has_detected_categories")
    expected = canonical_hash({key: value for key, value in event.items() if key != "receipt_hash"})
    if event.get("receipt_hash") != expected:
        raise PrivacyRuntimeError("privacy_event_receipt_hash_mismatch")


def safe_projection(event: dict[str, Any]) -> dict[str, Any]:
    validate_privacy_event(event)
    profile = event["input_profile"]
    return {
        "schema": event["schema"],
        "state": event["state"],
        "receipt_hash": event["receipt_hash"],
        "session_id_sha256": event["session_id_sha256"],
        "question_length": profile["question_length"],
        "question_sha256": profile["question_sha256"],
        "document_context_present": profile["document_context_present"],
        "document_context_sha256": profile["document_context_sha256"],
        "detected_categories": list(event["detected_categories"]),
        "raw_question_present": False,
        "raw_document_present": False,
        "direct_identifier_present": False,
        "credential_present": False,
        "prompt_present": False,
        "model_input_present": False,
        "model_output_present": False,
        "trace_content_present": False,
        "log_content_present": False,
        "medical_narrative_present": False,
        "authority_effect": False,
        "activation_effect": False,
    }
