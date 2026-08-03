#!/usr/bin/env python3
import copy
import importlib.util
import json
import sys
from pathlib import Path

MODULE = Path("va_claim_assistant/route_generators.py")
spec = importlib.util.spec_from_file_location("va_claim_assistant_route_generators_test", MODULE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

fixture = json.loads(
    Path("tests/fixtures/va_claim_assistant_source_registry.projection.json").read_text(encoding="utf-8")
)
assert fixture["source_repository"] == "StegVerse-Labs/Site"
assert fixture["source_commit"] == "e69e8421084b1343a9dc809fdb2a579089d37813"
assert fixture["source_blob_sha"] == "a83ff2dd8343f947265981609b154693cc5deecc"
registry = fixture["registry"]

questions = {
    "claim_type": "What type of claim should I file?",
    "evidence_requirement": "What evidence is needed?",
    "service_connection": "How does service connection work?",
    "rating_criteria": "What are the rating criteria?",
    "effective_date": "How is an effective date determined?",
    "appeal_or_supplemental_claim": "What is a supplemental claim?",
    "cp_examination": "What happens at a C&P exam?",
    "lay_statement": "How do I prepare a lay statement?",
    "private_record_collection": "How do I collect private medical records?",
    "procedural_filing": "How do I file a claim?",
    "representation_referral": "How do I find a VA-accredited representative?",
}

public_receipts = {}
for route, question in questions.items():
    answer = module.build_route_answer(
        route=route,
        question=question,
        registry=registry,
        session_id=f"route-generator-{route}-001",
    )
    module.validate_answer(answer, registry)
    assert answer["route"] == route
    assert answer["capability_state"] == "SOURCE_GROUNDED_ASSISTANT"
    assert not any(answer["authority_flags"].values())
    assert "contract_refs" not in answer
    assert set(answer) <= module.TOP_LEVEL_ANSWER_KEYS
    assert answer["propositions"]
    public_receipts[route] = answer["receipt_hash"]

try:
    module.build_route_answer(
        route="urgent_safety",
        question="I am in immediate danger.",
        registry=registry,
        session_id="route-generator-urgent-001",
    )
except module.AuthorityResolutionRequired as exc:
    assert str(exc) == "required_admitted_source_unavailable:VA-CRISIS-LINE"
else:
    raise AssertionError("urgent safety must fail closed until an official source is admitted")

try:
    module.build_route_answer(
        route="document_organization",
        question="Please organize my records.",
        registry=registry,
        session_id="route-generator-document-missing-001",
    )
except module.DocumentContextRequired as exc:
    assert str(exc) == "sanitized_document_context_required"
else:
    raise AssertionError("document organization must require sanitized derived context")

document_context = {
    "session_id": "document-session-001",
    "source_document_hashes": ["1" * 64, "2" * 64],
    "record_facts": [
        {
            "fact_id": "RF1",
            "text": "A sanitized record states that an event was documented.",
            "document_hash": "1" * 64,
            "page_anchor": "page-2",
        },
        {
            "fact_id": "RF2",
            "text": "A sanitized record states that symptoms were later documented.",
            "document_hash": "2" * 64,
            "page_anchor": "page-5",
        },
    ],
    "separately_labeled_inferences": [
        {
            "inference_id": "INF1",
            "text": "The timing may require human review before any claim theory is selected.",
            "supporting_fact_ids": ["RF1", "RF2"],
        }
    ],
    "contradictions": [
        {
            "contradiction_id": "C1",
            "description": "The two sanitized records use different onset dates.",
            "status": "REQUIRES_HUMAN_REVIEW",
            "related_fact_ids": ["RF1", "RF2"],
        }
    ],
    "missing_evidence": [
        {
            "missing_id": "M1",
            "description": "No admitted record resolves the onset-date conflict.",
            "material": True,
        }
    ],
    "privacy_state": "PII_REDACTED_VERIFIED",
    "consent_receipt": {"state": "VALID", "receipt_hash": "3" * 64},
    "derived_record_hash": "4" * 64,
}
document_answer = module.build_route_answer(
    route="document_organization",
    question="Please organize my records.",
    registry=registry,
    session_id=document_context["session_id"],
    document_context=document_context,
)
module.validate_answer(document_answer, registry)
assert document_answer["capability_state"] == "DOCUMENT_AWARE_ASSISTANT"
assert {item["kind"] for item in document_answer["propositions"]} == {"USER_RECORD_FACT", "INFERENCE"}
assert document_answer["contradictions"][0]["status"] == "REQUIRES_HUMAN_REVIEW"
assert not any(document_answer["authority_flags"].values())

leaking_context = copy.deepcopy(document_context)
leaking_context["record_facts"][0]["email"] = "veteran@example.com"
try:
    module.build_route_answer(
        route="document_organization",
        question="Please organize my records.",
        registry=registry,
        session_id=leaking_context["session_id"],
        document_context=leaking_context,
    )
except module.PrivacyBoundaryError as exc:
    assert "prohibited_context_field" in str(exc)
else:
    raise AssertionError("direct identifier field was not rejected")

missing_source_registry = copy.deepcopy(registry)
missing_source_registry["sources"] = [
    source for source in missing_source_registry["sources"] if source["source_id"] != "VA-RATING-SCHEDULE"
]
try:
    module.build_route_answer(
        route="rating_criteria",
        question="What are the rating criteria?",
        registry=missing_source_registry,
        session_id="route-generator-missing-source-001",
    )
except module.AuthorityResolutionRequired as exc:
    assert "VA-RATING-SCHEDULE" in str(exc)
else:
    raise AssertionError("missing controlling source did not fail closed")

escalated = copy.deepcopy(document_answer)
escalated["authority_flags"]["adjudication"] = True
escalated["receipt_hash"] = module.canonical_hash({k: v for k, v in escalated.items() if k != "receipt_hash"})
try:
    module.validate_answer(escalated, registry)
except ValueError as exc:
    assert "authority escalation" in str(exc)
else:
    raise AssertionError("authority escalation was not rejected")

extra_property = copy.deepcopy(document_answer)
extra_property["contract_refs"] = {"source": "not allowed in Site answer schema"}
extra_property["receipt_hash"] = module.canonical_hash({k: v for k, v in extra_property.items() if k != "receipt_hash"})
try:
    module.validate_answer(extra_property, registry)
except ValueError as exc:
    assert "additional_properties" in str(exc)
else:
    raise AssertionError("Site answer schema additional property was not rejected")

Path("receipts").mkdir(exist_ok=True)
receipt = {
    "schema": "stegverse.va_claim_assistant.route_generators_validation.v1",
    "result": "PASS",
    "source_registry_commit": fixture["source_commit"],
    "source_registry_blob_sha": fixture["source_blob_sha"],
    "answer_ready_public_routes": sorted(public_receipts),
    "document_route_generator": "PASS_WITH_SANITIZED_DERIVED_CONTEXT",
    "urgent_safety_route": "AUTHORITY_RESOLUTION_REQUIRED",
    "urgent_safety_missing_source": "VA-CRISIS-LINE",
    "raw_document_and_direct_identifier_rejection": True,
    "site_answer_schema_additional_properties_rejected": True,
    "authority_granted": False,
    "activation_granted": False,
    "public_route_receipt_hashes": public_receipts,
    "document_route_receipt_hash": document_answer["receipt_hash"],
}
receipt["receipt_hash"] = module.canonical_hash(receipt)
Path("receipts/va-claim-assistant-route-generators-validation.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps({"result": "PASS", "receipt_hash": receipt["receipt_hash"]}))
