#!/usr/bin/env python3
import copy
import importlib.util
import json
import sys
from pathlib import Path

MODULE = Path("va_claim_assistant/privacy_guarded_dispatch.py")
spec = importlib.util.spec_from_file_location("va_privacy_guarded_dispatch_test", MODULE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

fixture = json.loads(
    Path("tests/fixtures/va_claim_assistant_source_registry.projection.json").read_text(encoding="utf-8")
)
registry = fixture["registry"]
common = {
    "registry": registry,
    "registry_commit": fixture["source_commit"],
    "answer_schema_commit": "ae64a81df7ac91a9b2df00e9b8ff1a8358fcb9ab",
    "observed_at": "2026-08-04T03:10:00Z",
}

public_record = module.dispatch_privacy_guarded_question(
    question="How does service connection work?",
    session_id="privacy-public-001",
    **common,
)
module.validate_privacy_guarded_dispatch(public_record, registry)
assert public_record["state"] == "ANSWER_READY_PENDING_TVC_AND_CUSTODY"
assert public_record["privacy_event"]["state"] == "PASS"
assert public_record["governed_dispatch"]["classification"]["selected_route"] == "service_connection"

document_context = {
    "session_id": "privacy-document-001",
    "source_document_hashes": ["1" * 64],
    "record_facts": [{
        "fact_id": "RF1",
        "text": "A sanitized record fact without direct identifiers.",
        "document_hash": "1" * 64,
        "page_anchor": "page-2",
    }],
    "separately_labeled_inferences": [{
        "inference_id": "INF1",
        "text": "A separately labeled inference requires human review.",
        "supporting_fact_ids": ["RF1"],
    }],
    "contradictions": [{
        "contradiction_id": "C1",
        "description": "A sanitized conflict requires review.",
        "status": "REQUIRES_HUMAN_REVIEW",
        "related_fact_ids": ["RF1"],
    }],
    "missing_evidence": [{
        "missing_id": "M1",
        "description": "A material record remains missing.",
        "material": True,
    }],
    "privacy_state": "PII_REDACTED_VERIFIED",
    "consent_receipt": {"state": "VALID", "receipt_hash": "2" * 64},
    "derived_record_hash": "3" * 64,
}
document_record = module.dispatch_privacy_guarded_question(
    question="Please organize my records.",
    session_id=document_context["session_id"],
    document_context=document_context,
    **common,
)
module.validate_privacy_guarded_dispatch(document_record, registry)
assert document_record["state"] == "ANSWER_READY_PENDING_TVC_AND_CUSTODY"
assert document_record["privacy_event"]["state"] == "PASS"
assert document_record["governed_dispatch"]["answer"]["route"] == "document_organization"

negative_fixtures = [
    ("SSN", "My SSN is 123-45-6789. How does service connection work?", None, "123-45-6789"),
    ("EMAIL", "Email me at veteran@example.test about service connection.", None, "veteran@example.test"),
    ("PHONE", "Call 254-555-0199 about my service connection.", None, "254-555-0199"),
    ("IP_ADDRESS", "My IP is 192.168.4.25; explain service connection.", None, "192.168.4.25"),
]

for key, value in (
    ("raw_document", "raw document payload must not persist"),
    ("prompt", "hidden prompt must not persist"),
    ("credentials", "credential material must not persist"),
    ("identity_proofing_artifact", "identity proof must not persist"),
    ("veteran_name", "Named Veteran Must Not Persist"),
    ("email", "another@example.test"),
):
    context = copy.deepcopy(document_context)
    context[key] = value
    negative_fixtures.append((f"PROHIBITED_FIELD:{key}", "Please organize my records.", context, value))

observed_categories = set()
for index, (expected_category, question, context, prohibited_value) in enumerate(negative_fixtures, start=1):
    record = module.dispatch_privacy_guarded_question(
        question=question,
        session_id=f"privacy-negative-{index:02d}",
        document_context=context,
        **common,
    )
    module.validate_privacy_guarded_dispatch(record, registry)
    serialized = json.dumps(record, sort_keys=True)
    assert prohibited_value not in serialized
    assert record["state"] == "REVIEW_REQUIRED"
    assert record["governed_dispatch"] is None
    assert record["privacy_event"]["state"] == "REJECTED"
    assert record["privacy_event"]["question_sha256"] is None
    assert record["privacy_event"]["document_context_sha256"] is None
    assert expected_category in record["privacy_event"]["detected_categories"]
    assert record["question_retained_outside_governed_answer"] is False
    assert record["rejected_value_retained"] is False
    observed_categories.update(record["privacy_event"]["detected_categories"])

for record in (public_record, document_record):
    event = record["privacy_event"]
    for field in (
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
    ):
        assert event[field] is False

receipt = {
    "schema": "stegverse.va_claim_assistant.privacy_runtime_validation.v1",
    "state": "PASS",
    "observation_source": "LOCAL_DETERMINISTIC_VALIDATION",
    "privacy_runtime_commit": "e14e70be89f24d418d28a2a44c091d3349414ebc",
    "privacy_guarded_dispatch_commit": "e007689277cc2f3961bbcd9361b7b2373e1340ce",
    "accepted_public_route_state": public_record["state"],
    "accepted_document_route_state": document_record["state"],
    "negative_fixture_count": len(negative_fixtures),
    "negative_fixture_categories": sorted(observed_categories),
    "raw_pii_rejected_before_classifier": True,
    "sanitized_context_enforced": True,
    "rejected_values_retained": False,
    "rejected_input_hashes_retained": False,
    "raw_documents_retained": False,
    "prompts_or_model_content_retained": False,
    "privacy_event_safe_for_custody": True,
    "authority_effect": False,
    "activation_effect": False,
    "custody_claimed": False,
    "reconstruction_claimed": False,
}
receipt["receipt_hash"] = module.canonical_hash(receipt)
Path("receipts").mkdir(exist_ok=True)
Path("receipts/va-claim-assistant-privacy-runtime-validation.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps({"state": "PASS", "receipt_hash": receipt["receipt_hash"]}))
