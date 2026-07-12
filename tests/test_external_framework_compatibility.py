from __future__ import annotations

from llm_adapter.external_framework_compatibility import evaluate_submission


def complete_payload() -> dict:
    return {
        "framework_id": "decisionassure",
        "framework_name": "DecisionAssure",
        "source_references": ["https://example.org/framework"],
        "input_artifact_type": "decision trace",
        "output_artifact_type": "allow deny result",
        "actor_or_authority_model": "declared actor and bounded authority",
        "evidence_model": "hash-linked evidence",
        "policy_or_rule_model": "versioned policy",
        "delegation_model": "explicit delegation reference",
        "decision_or_result_model": "ALLOW DENY FAIL_CLOSED",
        "receipt_or_trace_model": "causal trace",
        "reconstruction_model": "replay from canonical artifacts",
        "fail_closed_conditions": ["missing policy", "identity drift"],
        "execution_authority_claim": False,
    }


def test_complete_known_framework_links_wiki_report() -> None:
    result = evaluate_submission(complete_payload())
    assert result["result"] == "COMPATIBILITY_EVIDENCE_READY"
    assert result["known_framework_report"] is True
    assert result["admissibility_wiki_report"].endswith("decisionassure.compatibility.json")
    assert result["field_coverage"]["ratio"] == 1.0
    assert result["receipt_id"].startswith("external-compatibility-receipt:sha256:")
    assert result["boundary"]["compatibility_result_is_authority"] is False


def test_missing_fields_remain_partial() -> None:
    result = evaluate_submission({"framework_id": "new-framework", "framework_name": "New"})
    assert result["result"] == "PARTIAL_COMPATIBILITY_INTAKE"
    assert "source_references" in result["missing_fields"]
    assert result["known_framework_report"] is False


def test_authority_or_equivalence_claim_fails_closed() -> None:
    payload = complete_payload()
    payload["execution_authority_claim"] = True
    payload["equivalence_claim"] = True
    result = evaluate_submission(payload)
    assert result["result"] == "FAIL_CLOSED_BOUNDARY_REVIEW"
    assert "FC-002 Authority Drift" in result["failure_classes"]
    assert "FC-001 Semantic Equivalence Divergence" in result["failure_classes"]
