"""Deterministic external-framework compatibility intake for External Chat.

The evaluator maps a submitted framework description or trace onto the bounded
external-framework fields used by the Admissibility Wiki. It produces evidence
for cooperative compatibility testing only; it does not certify a framework,
grant execution authority, or establish commit-time admissibility.
"""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

REQUIRED_FIELDS = (
    "framework_id",
    "framework_name",
    "source_references",
    "input_artifact_type",
    "output_artifact_type",
    "actor_or_authority_model",
    "evidence_model",
    "policy_or_rule_model",
    "delegation_model",
    "decision_or_result_model",
    "receipt_or_trace_model",
    "reconstruction_model",
    "fail_closed_conditions",
)

KNOWN_REPORTS = {
    "decisionassure": "decisionassure",
    "glm": "glm",
    "morrison-runtime": "morrison-runtime",
    "care-runtime": "care-runtime",
    "nist-ai-rmf": "nist-ai-rmf",
    "eu-ai-act": "eu-ai-act",
    "mitre-atlas": "mitre-atlas",
    "owasp-top-10-llm": "owasp-top-10-llm",
    "iso-iec-42001": "iso-iec-42001",
    "policy-cards": "policy-cards",
    "mindforge": "mindforge",
    "decision-authority": "decision-authority",
}


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def evaluate_submission(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("submission must be a JSON object")

    framework_id = str(payload.get("framework_id", "")).strip().lower()
    mapping = {
        field: ("PRESENT" if _present(payload.get(field)) else "MISSING")
        for field in REQUIRED_FIELDS
    }
    missing = [field for field, state in mapping.items() if state == "MISSING"]

    execution_claim = bool(payload.get("execution_authority_claim", False))
    commit_claim = bool(payload.get("commit_time_authority_claim", False))
    certification_claim = bool(payload.get("certification_claim", False))
    equivalence_claim = bool(payload.get("equivalence_claim", False))

    failure_classes: list[str] = []
    if execution_claim:
        failure_classes.append("FC-002 Authority Drift")
    if commit_claim:
        failure_classes.append("FC-009 Non-Claim Boundary Collapse")
    if equivalence_claim:
        failure_classes.append("FC-001 Semantic Equivalence Divergence")
    if not _present(payload.get("source_references")):
        failure_classes.append("FC-008 Source-Claim Mismatch")
    if not _present(payload.get("actor_or_authority_model")):
        failure_classes.append("FC-011 Actor Ambiguity")
    if not _present(payload.get("evidence_model")):
        failure_classes.append("FC-012 Evidence Class Confusion")
    if not _present(payload.get("fail_closed_conditions")):
        failure_classes.append("FC-007 Fail-Open Runtime Error")

    boundary_violation = any((execution_claim, commit_claim, certification_claim, equivalence_claim))
    if boundary_violation:
        result = "FAIL_CLOSED_BOUNDARY_REVIEW"
    elif missing:
        result = "PARTIAL_COMPATIBILITY_INTAKE"
    else:
        result = "COMPATIBILITY_EVIDENCE_READY"

    report_slug = KNOWN_REPORTS.get(framework_id)
    wiki_page = (
        f"https://stegverse-labs.github.io/admissibility-wiki/external-frameworks/{report_slug}"
        if report_slug else None
    )
    report_url = (
        f"https://github.com/StegVerse-Labs/admissibility-wiki/blob/main/docs/external-frameworks/reports/{report_slug}.compatibility.json"
        if report_slug else None
    )

    submission_hash = sha256(_canonical(payload)).hexdigest()
    receipt_material = "\n".join([
        framework_id or "unidentified-framework",
        submission_hash,
        result,
        ",".join(missing),
        ",".join(failure_classes),
    ])
    receipt_id = "external-compatibility-receipt:sha256:" + sha256(receipt_material.encode("utf-8")).hexdigest()

    present_count = len(REQUIRED_FIELDS) - len(missing)
    return {
        "schema_version": "1.0.0",
        "artifact_type": "external_framework_compatibility_intake_result",
        "framework_id": framework_id or None,
        "framework_name": payload.get("framework_name"),
        "result": result,
        "compatibility_evidence_only": True,
        "submission_sha256": submission_hash,
        "receipt_id": receipt_id,
        "field_coverage": {
            "present": present_count,
            "required": len(REQUIRED_FIELDS),
            "ratio": round(present_count / len(REQUIRED_FIELDS), 4),
        },
        "transition_table_mapping_status": mapping,
        "missing_fields": missing,
        "failure_classes": list(dict.fromkeys(failure_classes)),
        "known_framework_report": report_slug is not None,
        "admissibility_wiki_page": wiki_page,
        "admissibility_wiki_report": report_url,
        "comparison_posture": (
            "Compare submitted field coverage and boundaries with the linked wiki report; matching fields are evidence of structural overlap, not equivalence."
            if report_slug else
            "No existing framework report matched this framework_id; retain as provisional intake pending sourced review."
        ),
        "next_required_action": (
            "Remove authority/equivalence claims and submit bounded evidence for review."
            if boundary_violation else
            "Supply the missing fields and source artifacts."
            if missing else
            "Attach reproducible artifacts, exact versions, commands, hashes, and observed outputs for cooperative validation."
        ),
        "boundary": {
            "certification_claim": False,
            "endorsement_claim": False,
            "execution_authority_claim": False,
            "commit_time_authority_claim": False,
            "equivalence_claim": False,
            "compatibility_result_is_authority": False,
            "publication_creates_standing": False,
            "missing_or_partial_fields_fail_closed": True,
        },
    }
