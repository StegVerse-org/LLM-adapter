#!/usr/bin/env python3
"""Classifier-first governed dispatch for the StegVerse VA Claim Assistant.

Every supported route has a generator. Public-source routes use only admitted
Site sources. Document organization requires sanitized derived context.
Missing source authority, missing document context, ambiguous classification,
privacy-boundary failures, TVC, custody, reconstruction, deployment, and Site
activation all remain fail-closed.
"""
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


def _load_route_classifier() -> Any:
    return _load_module("route_classifier.py", "va_claim_assistant_route_classifier")


def _load_route_generators() -> Any:
    return _load_module("route_generators.py", "va_claim_assistant_route_generators")


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_sources(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Compatibility helper that validates source IDs and authority classes."""
    generators = _load_route_generators()
    return generators._source_map(registry)


def build_route_answer(
    *,
    route: str,
    question: str,
    registry: dict[str, Any],
    registry_commit: str,
    answer_schema_commit: str,
    session_id: str = "va-governed-route-fixture-001",
    document_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one schema-conforming answer without embedding contract metadata."""
    if not isinstance(registry_commit, str) or len(registry_commit) != 40:
        raise ValueError("registry_commit must be a 40-character commit")
    if not isinstance(answer_schema_commit, str) or len(answer_schema_commit) != 40:
        raise ValueError("answer_schema_commit must be a 40-character commit")
    generators = _load_route_generators()
    answer = generators.build_route_answer(
        route=route,
        question=question,
        registry=registry,
        session_id=session_id,
        document_context=document_context,
    )
    generators.validate_answer(answer, registry)
    return answer


def build_evidence_requirement_answer(
    *,
    question: str,
    registry: dict[str, Any],
    registry_commit: str,
    answer_schema_commit: str,
    session_id: str = "va-evidence-requirement-fixture-001",
) -> dict[str, Any]:
    """Compatibility wrapper for the original bounded route."""
    return build_route_answer(
        route="evidence_requirement",
        question=question,
        registry=registry,
        registry_commit=registry_commit,
        answer_schema_commit=answer_schema_commit,
        session_id=session_id,
    )


def _required_evidence(route: str) -> list[str]:
    common = [
        "tvc_capability_receipt",
        "master_records_custody_receipt",
        "reconstruction_receipt",
    ]
    if route == "document_organization":
        return [
            "pii_detector_receipt",
            "pii_redaction_manifest",
            "model_leakage_receipt",
            *common,
        ]
    return common


def dispatch_governed_question(
    *,
    question: str,
    registry: dict[str, Any],
    registry_commit: str,
    answer_schema_commit: str,
    session_id: str = "va-governed-dispatch-001",
    document_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify first, execute a governed generator, otherwise fail closed."""
    classifier = _load_route_classifier()
    generators = _load_route_generators()
    classification = classifier.classify_question(question)
    classifier.validate_classification(classification)

    answer = None
    route = classification.get("selected_route")
    next_required_evidence: list[str] = []
    document_context_refs: dict[str, Any] | None = None

    if classification["state"] != "CLASSIFIED":
        state = "REVIEW_REQUIRED"
        blocker = classification["reason"]
    else:
        try:
            answer = build_route_answer(
                route=route,
                question=question,
                registry=registry,
                registry_commit=registry_commit,
                answer_schema_commit=answer_schema_commit,
                session_id=session_id,
                document_context=document_context,
            )
        except generators.DocumentContextRequired as exc:
            state = "DOCUMENT_CONTEXT_REQUIRED"
            blocker = str(exc)
        except generators.AuthorityResolutionRequired as exc:
            state = "AUTHORITY_RESOLUTION_REQUIRED"
            blocker = str(exc)
        except generators.PrivacyBoundaryError as exc:
            state = "REVIEW_REQUIRED"
            blocker = f"privacy_boundary_rejected:{exc}"
        except generators.RouteGenerationError as exc:
            state = "NOT_IMPLEMENTED_FAIL_CLOSED"
            blocker = str(exc)
        else:
            state = "ANSWER_READY_PENDING_TVC_AND_CUSTODY"
            blocker = "tvc_and_master_records_evidence_required"
            next_required_evidence = _required_evidence(route)
            if route == "document_organization" and document_context is not None:
                document_context_refs = {
                    "session_id": document_context["session_id"],
                    "source_document_hashes": list(document_context["source_document_hashes"]),
                    "derived_record_hash": document_context["derived_record_hash"],
                    "privacy_state": document_context["privacy_state"],
                    "consent_receipt_hash": document_context["consent_receipt"]["receipt_hash"],
                }

    record: dict[str, Any] = {
        "schema_version": "2.0.0",
        "dispatcher": "va_claim_assistant.governed_dispatch.v2",
        "session_id": session_id,
        "question": question,
        "state": state,
        "classification": classification,
        "answer": answer,
        "blocker": blocker,
        "next_required_evidence": next_required_evidence,
        "document_context_refs": document_context_refs,
        "contract_refs": {
            "source_registry_commit": registry_commit,
            "answer_schema_commit": answer_schema_commit,
        },
        "authority_flags": dict(AUTHORITY_FLAGS),
    }
    record["receipt_hash"] = canonical_hash(record)
    return record


def validate_dispatch(record: dict[str, Any], registry: dict[str, Any]) -> None:
    if record.get("dispatcher") != "va_claim_assistant.governed_dispatch.v2":
        raise ValueError("unsupported dispatcher")
    if any(record.get("authority_flags", {}).values()):
        raise ValueError("authority escalation rejected")

    classifier = _load_route_classifier()
    classification = record.get("classification")
    if not isinstance(classification, dict):
        raise ValueError("classification is required")
    classifier.validate_classification(classification)

    state = record.get("state")
    answer = record.get("answer")
    route = classification.get("selected_route")
    next_required = record.get("next_required_evidence")
    document_refs = record.get("document_context_refs")
    if not isinstance(next_required, list):
        raise ValueError("next_required_evidence_invalid")

    if state == "ANSWER_READY_PENDING_TVC_AND_CUSTODY":
        if classification.get("state") != "CLASSIFIED" or route not in classifier.ROUTES:
            raise ValueError("answer-ready dispatch route mismatch")
        if not isinstance(answer, dict) or answer.get("route") != route:
            raise ValueError("answer-ready dispatch answer mismatch")
        validate_answer(answer, registry)
        if next_required != _required_evidence(route):
            raise ValueError("answer-ready dispatch lost required evidence gates")
        if route == "document_organization":
            if (
                not isinstance(document_refs, dict)
                or document_refs.get("session_id") != record.get("session_id")
                or not isinstance(document_refs.get("source_document_hashes"), list)
                or not document_refs["source_document_hashes"]
                or not isinstance(document_refs.get("derived_record_hash"), str)
                or len(document_refs["derived_record_hash"]) != 64
                or document_refs.get("privacy_state") not in {
                    "PII_REDACTED_VERIFIED",
                    "SANITIZED_DERIVED_CONTEXT",
                }
                or not isinstance(document_refs.get("consent_receipt_hash"), str)
                or len(document_refs["consent_receipt_hash"]) != 64
            ):
                raise ValueError("document_context_refs_invalid")
        elif document_refs is not None:
            raise ValueError("public_route_must_not_carry_document_context_refs")
    elif state == "DOCUMENT_CONTEXT_REQUIRED":
        if route != "document_organization" or answer is not None or next_required or document_refs is not None:
            raise ValueError("invalid document-context-required state")
    elif state == "AUTHORITY_RESOLUTION_REQUIRED":
        if classification.get("state") != "CLASSIFIED" or answer is not None or next_required or document_refs is not None:
            raise ValueError("invalid authority-resolution-required state")
    elif state == "REVIEW_REQUIRED":
        if answer is not None or next_required or document_refs is not None:
            raise ValueError("invalid review-required dispatch")
        if classification.get("state") == "CLASSIFIED" and not str(record.get("blocker", "")).startswith(
            "privacy_boundary_rejected:"
        ):
            raise ValueError("classified review state requires privacy-boundary evidence")
    elif state == "NOT_IMPLEMENTED_FAIL_CLOSED":
        if classification.get("state") != "CLASSIFIED" or answer is not None or next_required or document_refs is not None:
            raise ValueError("invalid fail-closed route state")
    else:
        raise ValueError("invalid dispatch state")

    refs = record.get("contract_refs")
    if (
        not isinstance(refs, dict)
        or not isinstance(refs.get("source_registry_commit"), str)
        or len(refs["source_registry_commit"]) != 40
        or not isinstance(refs.get("answer_schema_commit"), str)
        or len(refs["answer_schema_commit"]) != 40
    ):
        raise ValueError("dispatch contract references invalid")

    expected = canonical_hash({key: value for key, value in record.items() if key != "receipt_hash"})
    if record.get("receipt_hash") != expected:
        raise ValueError("receipt hash mismatch")


def validate_answer(record: dict[str, Any], registry: dict[str, Any]) -> None:
    generators = _load_route_generators()
    generators.validate_answer(record, registry)
