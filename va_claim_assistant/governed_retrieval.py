#!/usr/bin/env python3
"""Deterministic governed retrieval slice for the StegVerse VA Claim Assistant.

The dispatcher classifies every question before answer generation. Only the
implemented `evidence_requirement` route executes. Every other governed route,
ambiguous input, and unsupported input fails closed without inventing an
answer or granting authority.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUTHORITY_RANK = {
    "CONTROLLING": 1,
    "OFFICIAL_OPERATIONAL": 2,
    "PROFESSIONAL_SUPPORT": 3,
    "EXPERIENTIAL": 4,
}

AUTHORITY_FLAGS = {
    "adjudication": False,
    "representation": False,
    "medical_opinion": False,
    "rating": False,
    "execution": False,
    "publication": False,
}


def _load_route_classifier() -> Any:
    path = Path(__file__).with_name("route_classifier.py")
    spec = importlib.util.spec_from_file_location("va_claim_assistant_route_classifier", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("route classifier could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class Source:
    source_id: str
    authority_class: str
    name: str
    url: str
    admitted: bool


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_sources(registry: dict[str, Any]) -> dict[str, Source]:
    sources: dict[str, Source] = {}
    for item in registry.get("sources", []):
        source = Source(
            source_id=item["source_id"],
            authority_class=item["authority_class"],
            name=item["name"],
            url=item["url"],
            admitted=bool(item.get("admitted")),
        )
        if source.source_id in sources:
            raise ValueError(f"duplicate source_id: {source.source_id}")
        if source.authority_class not in AUTHORITY_RANK:
            raise ValueError(f"invalid authority class: {source.authority_class}")
        sources[source.source_id] = source
    return sources


def build_evidence_requirement_answer(
    *, question: str, registry: dict[str, Any], registry_commit: str,
    answer_schema_commit: str, session_id: str = "va-evidence-requirement-fixture-001"
) -> dict[str, Any]:
    if not question.strip():
        raise ValueError("question is required")
    sources = load_sources(registry)
    required = ["VA-EVIDENCE-NEEDED", "VA-COMPENSATION-EVIDENCE"]
    selected = []
    for source_id in required:
        source = sources.get(source_id)
        if source is None or not source.admitted:
            raise ValueError(f"required admitted source unavailable: {source_id}")
        selected.append(source)
    selected.sort(key=lambda source: AUTHORITY_RANK[source.authority_class])
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    propositions = [
        {
            "proposition_id": "P1",
            "text": "Evidence requirements depend on the type and procedural posture of the disability claim.",
            "kind": "PROCEDURAL_GUIDANCE",
            "support": [{
                "source_id": selected[0].source_id,
                "authority_class": selected[0].authority_class,
                "locator": selected[0].url,
                "retrieved_at": retrieved_at,
            }],
        },
        {
            "proposition_id": "P2",
            "text": "A claimant should identify current disability or symptoms, the relevant in-service event or exposure, and evidence connecting the two when that theory requires a nexus.",
            "kind": "PROCEDURAL_GUIDANCE",
            "support": [{
                "source_id": selected[1].source_id,
                "authority_class": selected[1].authority_class,
                "locator": selected[1].url,
                "retrieved_at": retrieved_at,
            }],
        },
    ]
    record: dict[str, Any] = {
        "schema_version": "1.0.0",
        "session_id": session_id,
        "question": question,
        "route": "evidence_requirement",
        "capability_state": "SOURCE_GROUNDED_ASSISTANT",
        "contract_refs": {
            "source_registry_commit": registry_commit,
            "answer_schema_commit": answer_schema_commit,
        },
        "propositions": propositions,
        "contradictions": [],
        "uncertainties": [{
            "uncertainty_id": "U1",
            "description": "No veteran-specific records were supplied, so the response cannot determine which evidence is present or missing in an individual claim.",
            "material": True,
        }],
        "referral_triggers": [],
        "authority_flags": dict(AUTHORITY_FLAGS),
    }
    record["receipt_hash"] = canonical_hash(record)
    return record


def dispatch_governed_question(
    *, question: str, registry: dict[str, Any], registry_commit: str,
    answer_schema_commit: str, session_id: str = "va-governed-dispatch-001"
) -> dict[str, Any]:
    """Classify first, execute only an implemented route, otherwise fail closed."""
    classifier = _load_route_classifier()
    classification = classifier.classify_question(question)
    classifier.validate_classification(classification)

    if classification["state"] != "CLASSIFIED":
        state = "REVIEW_REQUIRED"
        answer = None
        blocker = classification["reason"]
    elif classification["selected_route"] != "evidence_requirement":
        state = "NOT_IMPLEMENTED_FAIL_CLOSED"
        answer = None
        blocker = f"route_not_implemented:{classification['selected_route']}"
    else:
        answer = build_evidence_requirement_answer(
            question=question,
            registry=registry,
            registry_commit=registry_commit,
            answer_schema_commit=answer_schema_commit,
            session_id=session_id,
        )
        validate_answer(answer, registry)
        state = "ANSWER_READY_PENDING_TVC_AND_CUSTODY"
        blocker = "tvc_and_master_records_evidence_required"

    record: dict[str, Any] = {
        "schema_version": "1.0.0",
        "dispatcher": "va_claim_assistant.governed_dispatch.v1",
        "session_id": session_id,
        "question": question,
        "state": state,
        "classification": classification,
        "answer": answer,
        "blocker": blocker,
        "next_required_evidence": (
            ["tvc_capability_receipt", "master_records_custody_receipt", "reconstruction_receipt"]
            if answer is not None else []
        ),
        "authority_flags": dict(AUTHORITY_FLAGS),
    }
    record["receipt_hash"] = canonical_hash(record)
    return record


def validate_dispatch(record: dict[str, Any], registry: dict[str, Any]) -> None:
    if record.get("dispatcher") != "va_claim_assistant.governed_dispatch.v1":
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
    if state == "ANSWER_READY_PENDING_TVC_AND_CUSTODY":
        if route != "evidence_requirement" or not isinstance(answer, dict):
            raise ValueError("answer-ready dispatch route mismatch")
        validate_answer(answer, registry)
        required = record.get("next_required_evidence")
        if required != [
            "tvc_capability_receipt",
            "master_records_custody_receipt",
            "reconstruction_receipt",
        ]:
            raise ValueError("answer-ready dispatch lost required evidence gates")
    elif state == "NOT_IMPLEMENTED_FAIL_CLOSED":
        if classification.get("state") != "CLASSIFIED" or route == "evidence_requirement":
            raise ValueError("invalid unimplemented-route state")
        if answer is not None:
            raise ValueError("unimplemented route must not emit an answer")
    elif state == "REVIEW_REQUIRED":
        if classification.get("state") != "REVIEW_REQUIRED" or answer is not None:
            raise ValueError("invalid review-required dispatch")
    else:
        raise ValueError("invalid dispatch state")

    expected = canonical_hash({key: value for key, value in record.items() if key != "receipt_hash"})
    if record.get("receipt_hash") != expected:
        raise ValueError("receipt hash mismatch")


def validate_answer(record: dict[str, Any], registry: dict[str, Any]) -> None:
    if record.get("route") != "evidence_requirement":
        raise ValueError("only evidence_requirement is supported")
    if any(record.get("authority_flags", {}).values()):
        raise ValueError("authority escalation rejected")
    admitted = {item["source_id"]: item for item in registry.get("sources", []) if item.get("admitted")}
    for proposition in record.get("propositions", []):
        if not proposition.get("support"):
            raise ValueError(f"unsupported proposition: {proposition.get('proposition_id')}")
        for support in proposition["support"]:
            source = admitted.get(support.get("source_id"))
            if source is None:
                raise ValueError(f"non-admitted source: {support.get('source_id')}")
            if source["authority_class"] != support.get("authority_class"):
                raise ValueError("source authority mismatch")
    expected = canonical_hash({key: value for key, value in record.items() if key != "receipt_hash"})
    if record.get("receipt_hash") != expected:
        raise ValueError("receipt hash mismatch")
