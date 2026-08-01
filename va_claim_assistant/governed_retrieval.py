#!/usr/bin/env python3
"""Deterministic first slice for the StegVerse VA Claim Assistant.

This module supports only the `evidence_requirement` route. It consumes a
commit-pinned admitted-source registry, rejects non-admitted sources, preserves
authority ordering, emits proposition-level citations, and never grants VA,
legal-representation, medical-opinion, rating, publication, or execution
authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

AUTHORITY_RANK = {
    "CONTROLLING": 1,
    "OFFICIAL_OPERATIONAL": 2,
    "PROFESSIONAL_SUPPORT": 3,
    "EXPERIENTIAL": 4,
}

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
        "authority_flags": {
            "adjudication": False,
            "representation": False,
            "medical_opinion": False,
            "rating": False,
            "execution": False,
            "publication": False,
        },
    }
    record["receipt_hash"] = canonical_hash(record)
    return record


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
