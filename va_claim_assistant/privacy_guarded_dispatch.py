#!/usr/bin/env python3
"""Privacy-first runtime wrapper for governed VA Claim Assistant dispatch."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

AUTHORITY_FLAGS = {
    "adjudication": False,
    "representation": False,
    "medical_opinion": False,
    "rating": False,
    "execution": False,
    "publication": False,
}


def _load_module(filename: str, module_name: str) -> Any:
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"{filename} could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _privacy() -> Any:
    return _load_module("privacy_runtime.py", "va_claim_assistant_privacy_runtime")


def _governed() -> Any:
    return _load_module("governed_retrieval.py", "va_claim_assistant_governed_retrieval")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def dispatch_privacy_guarded_question(
    *,
    question: str,
    registry: dict[str, Any],
    registry_commit: str,
    answer_schema_commit: str,
    session_id: str = "va-privacy-guarded-dispatch-001",
    document_context: dict[str, Any] | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    privacy = _privacy()
    try:
        privacy_event = privacy.enforce_runtime_privacy(
            question=question,
            session_id=session_id,
            document_context=document_context,
            observed_at=observed_at,
        )
    except privacy.PrivacyRuntimeRejected as exc:
        privacy_event = exc.decision
        governed_dispatch = None
        state = "REVIEW_REQUIRED"
        blocker = str(exc)
    else:
        governed_dispatch = _governed().dispatch_governed_question(
            question=question,
            registry=registry,
            registry_commit=registry_commit,
            answer_schema_commit=answer_schema_commit,
            session_id=session_id,
            document_context=document_context,
        )
        state = governed_dispatch["state"]
        blocker = governed_dispatch["blocker"]

    record: dict[str, Any] = {
        "schema": "stegverse.va_claim_assistant.privacy_guarded_dispatch.v1",
        "runtime": "va_claim_assistant.privacy_guarded_dispatch.v1",
        "state": state,
        "blocker": blocker,
        "privacy_event": privacy.safe_projection(privacy_event),
        "governed_dispatch": governed_dispatch,
        "question_retained_outside_governed_answer": False,
        "rejected_value_retained": False,
        "raw_document_retained": False,
        "prompt_or_model_content_retained": False,
        "authority_flags": dict(AUTHORITY_FLAGS),
        "authority_effect": False,
        "activation_effect": False,
    }
    record["receipt_hash"] = canonical_hash(record)
    return record


def validate_privacy_guarded_dispatch(record: dict[str, Any], registry: dict[str, Any]) -> None:
    if record.get("schema") != "stegverse.va_claim_assistant.privacy_guarded_dispatch.v1":
        raise ValueError("privacy_guarded_dispatch_schema_invalid")
    if record.get("runtime") != "va_claim_assistant.privacy_guarded_dispatch.v1":
        raise ValueError("privacy_guarded_dispatch_runtime_invalid")
    if any(record.get("authority_flags", {}).values()):
        raise ValueError("privacy_guarded_dispatch_authority_escalation")
    if record.get("authority_effect") is not False or record.get("activation_effect") is not False:
        raise ValueError("privacy_guarded_dispatch_effect_invalid")
    for field in (
        "question_retained_outside_governed_answer",
        "rejected_value_retained",
        "raw_document_retained",
        "prompt_or_model_content_retained",
    ):
        if record.get(field) is not False:
            raise ValueError(f"privacy_guarded_dispatch_retention_invalid:{field}")

    event = record.get("privacy_event")
    if not isinstance(event, dict):
        raise ValueError("privacy_guarded_dispatch_event_missing")
    if any(event.get(field) is not False for field in (
        "raw_question_present",
        "raw_document_present",
        "direct_identifier_present",
        "credential_present",
        "prompt_present",
        "model_input_present",
        "model_output_present",
        "trace_content_present",
        "log_content_present",
        "medical_narrative_present",
        "authority_effect",
        "activation_effect",
    )):
        raise ValueError("privacy_guarded_dispatch_event_retention_failed")

    governed_dispatch = record.get("governed_dispatch")
    if event.get("state") == "REJECTED":
        if record.get("state") != "REVIEW_REQUIRED":
            raise ValueError("privacy_rejection_must_require_review")
        if governed_dispatch is not None:
            raise ValueError("privacy_rejection_reached_governed_dispatch")
        if not str(record.get("blocker", "")).startswith("privacy_runtime_rejected:"):
            raise ValueError("privacy_rejection_blocker_invalid")
        if event.get("question_sha256") is not None or event.get("document_context_sha256") is not None:
            raise ValueError("privacy_rejection_retained_input_hash")
    elif event.get("state") == "PASS":
        if not isinstance(governed_dispatch, dict):
            raise ValueError("privacy_pass_missing_governed_dispatch")
        _governed().validate_dispatch(governed_dispatch, registry)
        if record.get("state") != governed_dispatch.get("state"):
            raise ValueError("privacy_guarded_dispatch_state_mismatch")
        if record.get("blocker") != governed_dispatch.get("blocker"):
            raise ValueError("privacy_guarded_dispatch_blocker_mismatch")
    else:
        raise ValueError("privacy_guarded_dispatch_event_state_invalid")

    expected = canonical_hash({key: value for key, value in record.items() if key != "receipt_hash"})
    if record.get("receipt_hash") != expected:
        raise ValueError("privacy_guarded_dispatch_receipt_hash_mismatch")
