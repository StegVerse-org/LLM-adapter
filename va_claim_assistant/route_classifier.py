#!/usr/bin/env python3
"""Deterministic, non-authorizing route classifier for VA Claim Assistant.

The classifier selects only a governed route. It does not answer the question,
retrieve sources, assess entitlement, predict a rating, or grant authority.
Ambiguous or unsupported input fails closed as REVIEW_REQUIRED.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

ROUTES = (
    "claim_type",
    "evidence_requirement",
    "service_connection",
    "rating_criteria",
    "effective_date",
    "appeal_or_supplemental_claim",
    "cp_examination",
    "document_organization",
    "lay_statement",
    "private_record_collection",
    "procedural_filing",
    "representation_referral",
    "urgent_safety",
)

ROUTE_PATTERNS: dict[str, tuple[str, ...]] = {
    "claim_type": (
        r"\bwhat (kind|type) of claim\b",
        r"\bnew claim\b",
        r"\bsecondary claim\b",
        r"\bincreased? claim\b",
    ),
    "evidence_requirement": (
        r"\bwhat evidence\b",
        r"\bevidence (is|are) needed\b",
        r"\bwhat (records|documents) do i need\b",
        r"\bproof (is|are) needed\b",
    ),
    "service_connection": (
        r"\bservice connection\b",
        r"\bconnected to (my )?service\b",
        r"\bnexus\b",
        r"\bin[- ]service (event|injury|illness|exposure)\b",
    ),
    "rating_criteria": (
        r"\brating criteria\b",
        r"\bdiagnostic code\b",
        r"\bwhat percentage\b",
        r"\bdisability rating\b",
    ),
    "effective_date": (
        r"\beffective date\b",
        r"\bback ?pay\b",
        r"\bretroactive\b",
        r"\bdate benefits start\b",
    ),
    "appeal_or_supplemental_claim": (
        r"\bappeal\b",
        r"\bsupplemental claim\b",
        r"\bhigher[- ]level review\b",
        r"\bboard (appeal|review)\b",
        r"\bdecision review\b",
    ),
    "cp_examination": (
        r"\bc[& ]?p exam\b",
        r"\bcompensation and pension exam\b",
        r"\bva exam\b",
        r"\bexaminer\b",
    ),
    "document_organization": (
        r"\borganize (my )?(records|documents|evidence)\b",
        r"\bindex (my )?(records|documents)\b",
        r"\bclaim file\b",
        r"\bevidence packet\b",
    ),
    "lay_statement": (
        r"\blay statement\b",
        r"\bbuddy statement\b",
        r"\bpersonal statement\b",
        r"\bstatement in support of claim\b",
    ),
    "private_record_collection": (
        r"\bprivate medical records\b",
        r"\bdoctor records\b",
        r"\bprovider records\b",
        r"\brelease medical records\b",
    ),
    "procedural_filing": (
        r"\bhow (do|can) i file\b",
        r"\bfile (a|my) claim\b",
        r"\bsubmit (a|my) claim\b",
        r"\bva form\b",
    ),
    "representation_referral": (
        r"\bva[- ]accredited\b",
        r"\bclaims agent\b",
        r"\bveterans service organization\b",
        r"\bvso\b",
        r"\battorney\b",
        r"\brepresentative\b",
    ),
    "urgent_safety": (
        r"\bsuicid(e|al)\b",
        r"\bkill myself\b",
        r"\bhurt myself\b",
        r"\bimmediate danger\b",
        r"\bmedical emergency\b",
    ),
}

PRIORITY = (
    "urgent_safety",
    "representation_referral",
    "appeal_or_supplemental_claim",
    "cp_examination",
    "effective_date",
    "rating_criteria",
    "service_connection",
    "evidence_requirement",
    "private_record_collection",
    "document_organization",
    "lay_statement",
    "procedural_filing",
    "claim_type",
)

@dataclass(frozen=True)
class Match:
    route: str
    pattern: str
    span: tuple[int, int]


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def classify_question(question: str) -> dict[str, Any]:
    normalized = " ".join(question.strip().lower().split())
    if not normalized:
        raise ValueError("question is required")

    matches: list[Match] = []
    for route, patterns in ROUTE_PATTERNS.items():
        for pattern in patterns:
            result = re.search(pattern, normalized)
            if result:
                matches.append(Match(route=route, pattern=pattern, span=result.span()))
                break

    matched_routes = {match.route for match in matches}
    if "urgent_safety" in matched_routes:
        selected_route = "urgent_safety"
        state = "CLASSIFIED"
        reason = "urgent_safety_priority"
    elif len(matched_routes) == 1:
        selected_route = next(iter(matched_routes))
        state = "CLASSIFIED"
        reason = "single_governed_route_match"
    elif len(matched_routes) == 0:
        selected_route = None
        state = "REVIEW_REQUIRED"
        reason = "no_supported_route_match"
    else:
        selected_route = None
        state = "REVIEW_REQUIRED"
        reason = "multiple_governed_routes_match"

    ordered_matches = sorted(
        matches,
        key=lambda item: (PRIORITY.index(item.route), item.span[0], item.route),
    )
    record: dict[str, Any] = {
        "schema_version": "1.0.0",
        "classifier": "va_claim_assistant.route_classifier.v1",
        "question": question,
        "normalized_question": normalized,
        "state": state,
        "selected_route": selected_route,
        "reason": reason,
        "matches": [
            {"route": item.route, "pattern": item.pattern, "span": list(item.span)}
            for item in ordered_matches
        ],
        "supported_routes": list(ROUTES),
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


def validate_classification(record: dict[str, Any]) -> None:
    if record.get("classifier") != "va_claim_assistant.route_classifier.v1":
        raise ValueError("unsupported classifier")
    if any(record.get("authority_flags", {}).values()):
        raise ValueError("authority escalation rejected")
    state = record.get("state")
    route = record.get("selected_route")
    if state == "CLASSIFIED":
        if route not in ROUTES:
            raise ValueError("classified route is invalid")
        if not record.get("matches"):
            raise ValueError("classified route has no match evidence")
    elif state == "REVIEW_REQUIRED":
        if route is not None:
            raise ValueError("review-required classification must not select a route")
    else:
        raise ValueError("invalid classification state")
    expected = canonical_hash({key: value for key, value in record.items() if key != "receipt_hash"})
    if record.get("receipt_hash") != expected:
        raise ValueError("receipt hash mismatch")
