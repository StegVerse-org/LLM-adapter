#!/usr/bin/env python3
"""Validate the VA Claim Assistant PII-RDY-06 runtime receipt and source binding."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "receipts" / "va-claim-assistant-privacy-runtime-validation.json"
SCHEMA = ROOT / "contracts" / "va-claim-assistant-privacy-runtime.schema.json"
PRIVACY_RUNTIME = ROOT / "va_claim_assistant" / "privacy_runtime.py"
PRIVACY_DISPATCH = ROOT / "va_claim_assistant" / "privacy_guarded_dispatch.py"

EXPECTED_KEYS = {
    "schema",
    "state",
    "observation_source",
    "privacy_runtime_commit",
    "privacy_guarded_dispatch_commit",
    "accepted_public_route_state",
    "accepted_document_route_state",
    "negative_fixture_count",
    "negative_fixture_categories",
    "raw_pii_rejected_before_classifier",
    "sanitized_context_enforced",
    "rejected_values_retained",
    "rejected_input_hashes_retained",
    "raw_documents_retained",
    "prompts_or_model_content_retained",
    "privacy_event_safe_for_custody",
    "authority_effect",
    "activation_effect",
    "custody_claimed",
    "reconstruction_claimed",
    "receipt_hash",
}


def fail(message: str) -> None:
    raise SystemExit(f"VA_PRIVACY_RUNTIME_FAIL:{message}")


def canonical_hash(value: dict[str, Any]) -> str:
    material = {key: item for key, item in value.items() if key != "receipt_hash"}
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if schema.get("additionalProperties") is not False:
        fail("schema_must_reject_additional_properties")
    value = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if set(value) != EXPECTED_KEYS:
        fail("receipt_keys_mismatch")
    if value.get("schema") != "stegverse.va_claim_assistant.privacy_runtime_validation.v1":
        fail("receipt_schema_invalid")
    if value.get("state") != "PASS":
        fail("receipt_state_not_pass")
    if value.get("observation_source") not in {"LOCAL_DETERMINISTIC_VALIDATION", "GITHUB_ACTIONS_WORKFLOW"}:
        fail("observation_source_invalid")
    for field in ("privacy_runtime_commit", "privacy_guarded_dispatch_commit"):
        item = value.get(field)
        if not isinstance(item, str) or len(item) != 40 or any(char not in "0123456789abcdef" for char in item):
            fail(f"{field}_invalid")
    if value.get("accepted_public_route_state") != "ANSWER_READY_PENDING_TVC_AND_CUSTODY":
        fail("public_route_state_invalid")
    if value.get("accepted_document_route_state") != "ANSWER_READY_PENDING_TVC_AND_CUSTODY":
        fail("document_route_state_invalid")
    if int(value.get("negative_fixture_count", 0)) < 9:
        fail("negative_fixture_coverage_insufficient")
    categories = value.get("negative_fixture_categories")
    required_categories = {
        "SSN",
        "EMAIL",
        "PHONE",
        "IP_ADDRESS",
        "PROHIBITED_FIELD:raw_document",
        "PROHIBITED_FIELD:prompt",
        "PROHIBITED_FIELD:credentials",
        "PROHIBITED_FIELD:identity_proofing_artifact",
        "PROHIBITED_FIELD:veteran_name",
    }
    if not isinstance(categories, list) or not required_categories.issubset(set(categories)):
        fail("negative_fixture_categories_incomplete")
    required_true = (
        "raw_pii_rejected_before_classifier",
        "sanitized_context_enforced",
        "privacy_event_safe_for_custody",
    )
    for field in required_true:
        if value.get(field) is not True:
            fail(f"{field}_must_be_true")
    required_false = (
        "rejected_values_retained",
        "rejected_input_hashes_retained",
        "raw_documents_retained",
        "prompts_or_model_content_retained",
        "authority_effect",
        "activation_effect",
        "custody_claimed",
        "reconstruction_claimed",
    )
    for field in required_false:
        if value.get(field) is not False:
            fail(f"{field}_must_be_false")
    if value.get("receipt_hash") != canonical_hash(value):
        fail("receipt_hash_mismatch")

    privacy_source = PRIVACY_RUNTIME.read_text(encoding="utf-8")
    dispatch_source = PRIVACY_DISPATCH.read_text(encoding="utf-8")
    for marker in (
        "rejected_input_hash_present",
        "raw_question_present",
        "raw_document_present",
        "model_input_present",
        "model_output_present",
        "medical_narrative_present",
    ):
        if marker not in privacy_source:
            fail(f"privacy_source_marker_missing:{marker}")
    privacy_position = dispatch_source.find("privacy.enforce_runtime_privacy")
    governed_position = dispatch_source.find("_governed().dispatch_governed_question")
    if privacy_position < 0 or governed_position < 0 or privacy_position >= governed_position:
        fail("privacy_gate_not_before_governed_dispatch")
    if "models: read" in privacy_source or "models: read" in dispatch_source:
        fail("privacy_runtime_must_not_request_provider_permission")

    print(f"VA_PRIVACY_RUNTIME_PASS:{value['receipt_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
