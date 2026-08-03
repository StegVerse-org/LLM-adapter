#!/usr/bin/env python3
"""Observe real TVC-backed service-connection execution evidence.

The observer is intentionally fail-closed. Deterministic route generation and
TVC capability admission are prerequisites, not provider/model execution.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADMISSION_PATH = ROOT / "tests/fixtures/tvc_va_service_connection_admission.projection.json"
EVIDENCE_PATH = ROOT / "receipts/va-claim-assistant-service-connection-execution.json"
READINESS_PATH = ROOT / "receipts/va-claim-assistant-service-connection-execution-readiness.json"

ALLOWED_DOMAINS = {
    "uscode.house.gov",
    "ecfr.gov",
    "va.gov",
    "benefits.va.gov",
    "knowva.ebenefits.va.gov",
    "uscourts.cavc.gov",
    "federalregister.gov",
}
EXPECTED_AUTHORITY_KEYS = {
    "adjudication",
    "representation",
    "medical_opinion",
    "rating",
    "publication",
    "public_activation",
    "filing",
    "submission",
}
EXPECTED_PRIVACY_KEYS = {
    "secret_values_present",
    "direct_identifiers_present",
    "raw_documents_present",
    "identity_proofing_artifacts_present",
    "prompts_present",
    "model_traces_present",
    "logs_contain_prohibited_data",
    "medical_narrative_present",
}


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def inspect_evidence(evidence: dict[str, Any], admission: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def check(condition: bool, code: str) -> None:
        if not condition:
            errors.append(code)

    check(evidence.get("schema_version") == "1.0.0", "schema_version_invalid")
    check(evidence.get("state") == "EXECUTED", "provider_execution_state_not_executed")
    check(evidence.get("route") == "service_connection", "route_mismatch")
    check(evidence.get("invocation_id") == admission.get("invocation_id"), "invocation_id_mismatch")
    check(evidence.get("tvc_admission_receipt_hash") == admission.get("tvc_receipt_hash"), "tvc_admission_hash_mismatch")
    check(evidence.get("answer_receipt_hash") == admission.get("answer_receipt_hash"), "answer_receipt_hash_mismatch")
    check(evidence.get("dispatch_receipt_hash") == admission.get("dispatch_receipt_hash"), "dispatch_receipt_hash_mismatch")

    provider = evidence.get("provider_execution", {})
    check(isinstance(provider, dict), "provider_execution_missing")
    if isinstance(provider, dict):
        check(provider.get("provider_used") is True, "provider_not_used")
        check(bool(provider.get("provider_class")), "provider_class_missing")
        check(provider.get("model_class") == "retrieval_grounded_text_generation", "model_class_invalid")
        check(provider.get("credential_source") == "TVC_CONTROLLED_RUNTIME", "credential_source_invalid")
        check(provider.get("credential_value_present") is False, "credential_value_exposed")

    domains = evidence.get("source_domains_used")
    check(isinstance(domains, list) and bool(domains), "source_domains_missing")
    if isinstance(domains, list):
        check(len(domains) == len(set(domains)), "source_domains_duplicated")
        check(set(domains).issubset(ALLOWED_DOMAINS), "source_domain_not_allowed")

    try:
        started = parse_time(str(evidence.get("execution_started_at")))
        completed = parse_time(str(evidence.get("execution_completed_at")))
        check(completed >= started, "execution_time_order_invalid")
    except Exception:
        errors.append("execution_time_invalid")

    cost = evidence.get("cost_usd")
    check(isinstance(cost, (int, float)) and not isinstance(cost, bool) and 0 <= float(cost) <= 1.0, "cost_limit_exceeded_or_invalid")

    privacy = evidence.get("privacy")
    check(isinstance(privacy, dict) and set(privacy) == EXPECTED_PRIVACY_KEYS, "privacy_fields_invalid")
    if isinstance(privacy, dict):
        check(not any(privacy.values()), "prohibited_data_present")

    authority = evidence.get("authority_flags")
    check(isinstance(authority, dict) and set(authority) == EXPECTED_AUTHORITY_KEYS, "authority_fields_invalid")
    if isinstance(authority, dict):
        check(not any(authority.values()), "authority_escalation_detected")
    check(evidence.get("activation_effect") is False, "activation_effect_detected")

    receipt_hash = evidence.get("receipt_hash")
    material = {key: value for key, value in evidence.items() if key != "receipt_hash"}
    check(isinstance(receipt_hash, str) and receipt_hash == canonical_hash(material), "execution_receipt_hash_invalid")
    return sorted(set(errors))


def main() -> None:
    admission = load(ADMISSION_PATH)
    base = {
        "schema_version": "1.0.0",
        "observer": "va_claim_assistant.service_connection_execution_observer.v1",
        "route": "service_connection",
        "tvc_admission": {
            "source_repository": admission["source_repository"],
            "source_handoff_commit": admission["source_handoff_commit"],
            "source_receipt_commit": admission["source_receipt_commit"],
            "source_receipt_path": admission["source_receipt_path"],
            "invocation_id": admission["invocation_id"],
            "receipt_hash": admission["tvc_receipt_hash"],
            "answer_receipt_hash": admission["answer_receipt_hash"],
            "dispatch_receipt_hash": admission["dispatch_receipt_hash"],
        },
        "execution_evidence_path": str(EVIDENCE_PATH.relative_to(ROOT)),
        "authority_effect": False,
        "activation_effect": False,
    }

    if not EVIDENCE_PATH.exists():
        receipt = {
            **base,
            "state": "BLOCKED",
            "evidence_present": False,
            "blockers": ["provider_execution_evidence_missing"],
            "provider_execution_observed": False,
            "custody_state": "PENDING_REAL_ADAPTER_EXECUTION",
            "reconstruction_state": "PENDING_REAL_ADAPTER_EXECUTION",
            "next_executable_action": "A repository-native adapter runtime must execute service_connection through the admitted TVC capability and write the schema-valid execution receipt.",
            "next_owner": "StegVerse-org/LLM-adapter#90",
        }
    else:
        evidence = load(EVIDENCE_PATH)
        errors = inspect_evidence(evidence, admission)
        if errors:
            receipt = {
                **base,
                "state": "REVIEW_REQUIRED",
                "evidence_present": True,
                "blockers": errors,
                "provider_execution_observed": evidence.get("state") == "EXECUTED",
                "custody_state": "BLOCKED_INVALID_EXECUTION_EVIDENCE",
                "reconstruction_state": "BLOCKED_INVALID_EXECUTION_EVIDENCE",
                "next_executable_action": "Repair or replace the execution receipt; do not submit invalid evidence to custody.",
                "next_owner": "StegVerse-org/LLM-adapter#90",
            }
        else:
            receipt = {
                **base,
                "state": "COMPLETE",
                "evidence_present": True,
                "blockers": [],
                "provider_execution_observed": True,
                "execution_receipt_hash": evidence["receipt_hash"],
                "source_domains_used": evidence["source_domains_used"],
                "cost_usd": evidence["cost_usd"],
                "custody_state": "READY_FOR_MASTER_RECORDS",
                "reconstruction_state": "READY_FOR_MASTER_RECORDS",
                "next_executable_action": "Submit the execution and TVC admission receipts to master-records/orchestration#15.",
                "next_owner": "master-records/orchestration#15",
            }

    receipt["receipt_hash"] = canonical_hash(receipt)
    READINESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    READINESS_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": receipt["state"], "blockers": receipt["blockers"], "receipt_hash": receipt["receipt_hash"]}))


if __name__ == "__main__":
    main()
