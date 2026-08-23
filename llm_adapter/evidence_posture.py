"""Evidence posture and reconstructable receipt primitives for Ecosystem Chat.

This module does not grant execution, provider, ERL, custody, or factual authority.
It constrains conversational certainty to the retained evidence posture and preserves
what evidence was actually used so the displayed response can be reconstructed.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping

POSTURES = (
    "UNKNOWN",
    "UNSUPPORTED",
    "INCOMPLETE",
    "MIXED",
    "SUPPORTED",
    "STRONGLY_SUPPORTED",
)
POSTURE_RANK = {value: index for index, value in enumerate(POSTURES)}

CERTAINTY_PATTERNS: tuple[tuple[str, int], ...] = (
    (r"\b(definitely|certainly|conclusively|proven|established fact)\b", POSTURE_RANK["STRONGLY_SUPPORTED"]),
    (r"\b(strongly supports?|well[- ]supported|high confidence|can confirm)\b", POSTURE_RANK["SUPPORTED"]),
    (r"\b(supports?|evidence indicates?|evidence suggests?)\b", POSTURE_RANK["MIXED"]),
    (r"\b(appears?|may|might|possibly|unclear|incomplete|mixed)\b", POSTURE_RANK["INCOMPLETE"]),
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return "sha256:" + sha256(canonical_json(value).encode("utf-8")).hexdigest()


def validate_posture(posture: str) -> str:
    normalized = str(posture).upper()
    if normalized not in POSTURE_RANK:
        raise ValueError(f"unsupported evidence posture: {posture}")
    return normalized


def strongest_certainty_claimed(text: str) -> int:
    """Return the strongest evidence rank implied by conversational wording.

    Neutral wording has rank 0. Detection is intentionally conservative and can be
    extended without changing receipt semantics.
    """

    claimed = 0
    for pattern, rank in CERTAINTY_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            claimed = max(claimed, rank)
    return claimed


def certainty_language_allowed(text: str, posture: str) -> bool:
    return strongest_certainty_claimed(text) <= POSTURE_RANK[validate_posture(posture)]


def assert_certainty_language_allowed(text: str, posture: str) -> None:
    normalized = validate_posture(posture)
    if not certainty_language_allowed(text, normalized):
        raise ValueError(
            "conversational certainty exceeds evidence posture: "
            f"claimed_rank={strongest_certainty_claimed(text)} posture={normalized}"
        )


def suggested_conversational_lead(posture: str) -> str:
    normalized = validate_posture(posture)
    return {
        "UNKNOWN": "I don't have enough evidence to determine this yet.",
        "UNSUPPORTED": "I don't have evidence that supports that claim.",
        "INCOMPLETE": "The available evidence is incomplete.",
        "MIXED": "The evidence is mixed.",
        "SUPPORTED": "The available evidence supports this.",
        "STRONGLY_SUPPORTED": "The available evidence strongly supports this.",
    }[normalized]


def _copy_records(records: Iterable[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    return [deepcopy(dict(record)) for record in (records or [])]


def _validate_evidence_sources(records: list[dict[str, Any]]) -> None:
    for index, record in enumerate(records):
        if not record.get("source_ref"):
            raise ValueError(f"evidence_sources[{index}] missing source_ref")
        if "data" not in record:
            raise ValueError(f"evidence_sources[{index}] missing actual data")


def build_evidence_receipt(
    *,
    query: str,
    final_response: str,
    evidence_posture: str,
    evidence_sources: Iterable[Mapping[str, Any]] | None = None,
    erl_relationships: Iterable[Mapping[str, Any]] | None = None,
    model_observations: Iterable[Mapping[str, Any]] | None = None,
    contradictions: Iterable[Mapping[str, Any]] | None = None,
    uncertainty: Iterable[Mapping[str, Any]] | None = None,
    governance_refs: Iterable[str] | None = None,
    transition_id: str | None = None,
    run_id: str | None = None,
    certainty_constraint_applied: bool = True,
) -> dict[str, Any]:
    """Build a deterministic, non-authorizing evidence receipt.

    When a governed evidence posture exists, certainty_constraint_applied MUST be
    true and the response wording is checked against that posture. Before a governed
    evidence aggregator has supplied a posture, callers may retain an exact response
    with UNKNOWN posture and certainty_constraint_applied=false. That state is
    explicit and cannot be used with a stronger posture to bypass the ceiling.
    """

    posture = validate_posture(evidence_posture)
    if certainty_constraint_applied:
        assert_certainty_language_allowed(final_response, posture)
    elif posture != "UNKNOWN":
        raise ValueError("certainty constraint may be skipped only while evidence posture is UNKNOWN")

    sources = _copy_records(evidence_sources)
    erl = _copy_records(erl_relationships)
    models = _copy_records(model_observations)
    conflicts = _copy_records(contradictions)
    uncertainty_records = _copy_records(uncertainty)
    _validate_evidence_sources(sources)

    body: dict[str, Any] = {
        "schema": "stegverse.ecosystem-chat-evidence-receipt/v1",
        "transition_id": transition_id,
        "run_id": run_id,
        "query": query,
        "final_response": final_response,
        "evidence_posture": posture,
        "certainty_claim_rank": strongest_certainty_claimed(final_response),
        "certainty_constraint_applied": certainty_constraint_applied,
        "evidence_sources": sources,
        "erl_relationships": erl,
        "model_observations": models,
        "contradictions": conflicts,
        "uncertainty": uncertainty_records,
        "governance_refs": list(governance_refs or []),
        "authority": {
            "provider_output_is_authority": False,
            "erl_relationship_is_authority": False,
            "majority_agreement_creates_truth": False,
            "evidence_posture_grants_execution": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": False,
            "render_authority": False,
        },
        "reconstructable": True,
    }
    return {**body, "receipt_id": "evidence-receipt:" + digest(body)}


def user_evidence_projection(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Return the minimum conversational UI projection of a full receipt."""

    posture = validate_posture(str(receipt["evidence_posture"]))
    return {
        "evidence_posture": posture,
        "certainty_constraint_applied": bool(receipt.get("certainty_constraint_applied", False)),
        "receipt_id": receipt.get("receipt_id"),
        "source_count": len(receipt.get("evidence_sources", [])),
        "erl_relationship_count": len(receipt.get("erl_relationships", [])),
        "model_observation_count": len(receipt.get("model_observations", [])),
        "contradiction_count": len(receipt.get("contradictions", [])),
        "uncertainty_count": len(receipt.get("uncertainty", [])),
        "full_evidence_embedded": False,
    }
