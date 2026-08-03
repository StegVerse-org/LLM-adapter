#!/usr/bin/env python3
import copy
import importlib.util
import json
import sys
from pathlib import Path

MODULE = Path("va_claim_assistant/governed_retrieval.py")
spec = importlib.util.spec_from_file_location("governed_retrieval_dispatch", MODULE)
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
}

questions = {
    "claim_type": "What type of claim should I file?",
    "evidence_requirement": "What evidence is needed for my disability claim?",
    "service_connection": "How does service connection work?",
    "rating_criteria": "What are the rating criteria?",
    "effective_date": "What is the effective date for back pay?",
    "appeal_or_supplemental_claim": "Should I file a supplemental claim?",
    "cp_examination": "What happens at a C&P exam?",
    "lay_statement": "How do I write a lay statement?",
    "private_record_collection": "How do I collect private medical records?",
    "procedural_filing": "How do I file a claim?",
    "representation_referral": "How do I find a VA-accredited representative?",
}

answer_ready_hashes = {}
for route, question in questions.items():
    record = module.dispatch_governed_question(
        question=question,
        session_id=f"va-dispatch-{route}-001",
        **common,
    )
    module.validate_dispatch(record, registry)
    assert record["state"] == "ANSWER_READY_PENDING_TVC_AND_CUSTODY"
    assert record["classification"]["selected_route"] == route
    assert record["answer"]["route"] == route
    assert record["next_required_evidence"] == [
        "tvc_capability_receipt",
        "master_records_custody_receipt",
        "reconstruction_receipt",
    ]
    assert record["document_context_refs"] is None
    assert not any(record["authority_flags"].values())
    answer_ready_hashes[route] = record["receipt_hash"]

document_required = module.dispatch_governed_question(
    question="Please organize my records.",
    session_id="va-dispatch-document-required-001",
    **common,
)
module.validate_dispatch(document_required, registry)
assert document_required["state"] == "DOCUMENT_CONTEXT_REQUIRED"
assert document_required["answer"] is None

document_context = {
    "session_id": "document-session-001",
    "source_document_hashes": ["1" * 64],
    "record_facts": [
        {
            "fact_id": "RF1",
            "text": "A sanitized record fact.",
            "document_hash": "1" * 64,
            "page_anchor": "page-2",
        }
    ],
    "separately_labeled_inferences": [
        {
            "inference_id": "INF1",
            "text": "A separately labeled inference requires human review.",
            "supporting_fact_ids": ["RF1"],
        }
    ],
    "contradictions": [
        {
            "contradiction_id": "C1",
            "description": "A sanitized conflict requires review.",
            "status": "REQUIRES_HUMAN_REVIEW",
            "related_fact_ids": ["RF1"],
        }
    ],
    "missing_evidence": [
        {
            "missing_id": "M1",
            "description": "A material record remains missing.",
            "material": True,
        }
    ],
    "privacy_state": "PII_REDACTED_VERIFIED",
    "consent_receipt": {"state": "VALID", "receipt_hash": "2" * 64},
    "derived_record_hash": "3" * 64,
}
document_ready = module.dispatch_governed_question(
    question="Please organize my records.",
    session_id=document_context["session_id"],
    document_context=document_context,
    **common,
)
module.validate_dispatch(document_ready, registry)
assert document_ready["state"] == "ANSWER_READY_PENDING_TVC_AND_CUSTODY"
assert document_ready["answer"]["route"] == "document_organization"
assert document_ready["answer"]["capability_state"] == "DOCUMENT_AWARE_ASSISTANT"
assert document_ready["document_context_refs"] == {
    "session_id": document_context["session_id"],
    "source_document_hashes": document_context["source_document_hashes"],
    "derived_record_hash": document_context["derived_record_hash"],
    "privacy_state": document_context["privacy_state"],
    "consent_receipt_hash": document_context["consent_receipt"]["receipt_hash"],
}
assert document_ready["next_required_evidence"] == [
    "pii_detector_receipt",
    "pii_redaction_manifest",
    "model_leakage_receipt",
    "tvc_capability_receipt",
    "master_records_custody_receipt",
    "reconstruction_receipt",
]
assert not any(document_ready["authority_flags"].values())

leaking_context = copy.deepcopy(document_context)
leaking_context["record_facts"][0]["email"] = "veteran@example.com"
privacy_rejected = module.dispatch_governed_question(
    question="Please organize my records.",
    session_id=leaking_context["session_id"],
    document_context=leaking_context,
    **common,
)
module.validate_dispatch(privacy_rejected, registry)
assert privacy_rejected["state"] == "REVIEW_REQUIRED"
assert privacy_rejected["blocker"].startswith("privacy_boundary_rejected:")
assert privacy_rejected["answer"] is None

urgent = module.dispatch_governed_question(
    question="I am in immediate danger and need help.",
    session_id="va-dispatch-urgent-001",
    **common,
)
module.validate_dispatch(urgent, registry)
assert urgent["state"] == "AUTHORITY_RESOLUTION_REQUIRED"
assert urgent["classification"]["selected_route"] == "urgent_safety"
assert urgent["blocker"] == "required_admitted_source_unavailable:VA-CRISIS-LINE"
assert urgent["answer"] is None

review_required = module.dispatch_governed_question(
    question="Please review this for me.",
    session_id="va-dispatch-review-001",
    **common,
)
module.validate_dispatch(review_required, registry)
assert review_required["state"] == "REVIEW_REQUIRED"
assert review_required["answer"] is None
assert review_required["classification"]["selected_route"] is None

escalated = copy.deepcopy(document_ready)
escalated["authority_flags"]["rating"] = True
escalated["receipt_hash"] = module.canonical_hash({k: v for k, v in escalated.items() if k != "receipt_hash"})
try:
    module.validate_dispatch(escalated, registry)
except ValueError as exc:
    assert "authority escalation" in str(exc)
else:
    raise AssertionError("dispatch authority escalation was not rejected")

Path("receipts").mkdir(exist_ok=True)
receipt = {
    "schema": "stegverse.va_claim_assistant.governed_dispatch_validation.v2",
    "result": "PASS",
    "states_verified": [
        "ANSWER_READY_PENDING_TVC_AND_CUSTODY",
        "DOCUMENT_CONTEXT_REQUIRED",
        "AUTHORITY_RESOLUTION_REQUIRED",
        "REVIEW_REQUIRED",
    ],
    "implemented_route_generators": [
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
    ],
    "answer_ready_public_routes": sorted(answer_ready_hashes),
    "document_route_answer_ready_with_sanitized_context": True,
    "document_route_missing_context_fails_closed": True,
    "privacy_boundary_rejection_verified": True,
    "urgent_safety_authority_resolution_required": True,
    "urgent_safety_missing_source": "VA-CRISIS-LINE",
    "authority_granted": False,
    "activation_granted": False,
    "answer_ready_dispatch_receipt_hashes": answer_ready_hashes,
    "document_dispatch_receipt_hash": document_ready["receipt_hash"],
    "urgent_dispatch_receipt_hash": urgent["receipt_hash"],
    "review_dispatch_receipt_hash": review_required["receipt_hash"],
}
receipt["receipt_hash"] = module.canonical_hash(receipt)
Path("receipts/va-claim-assistant-governed-dispatch-validation.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps({"result": "PASS", "receipt_hash": receipt["receipt_hash"]}))
