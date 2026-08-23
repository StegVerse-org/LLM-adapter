from __future__ import annotations

import pytest

from llm_adapter.evidence_posture import (
    assert_certainty_language_allowed,
    build_evidence_receipt,
    certainty_language_allowed,
    suggested_conversational_lead,
    user_evidence_projection,
)


def test_receipt_preserves_exact_response_and_actual_source_data() -> None:
    response = "The available evidence supports this."
    source = {
        "source_ref": "artifact:alpha",
        "data": {"claim": "x", "observed": True},
        "evidence_posture": "SUPPORTED",
    }
    receipt = build_evidence_receipt(
        query="Did x happen?",
        final_response=response,
        evidence_posture="SUPPORTED",
        evidence_sources=[source],
        erl_relationships=[{"relationship_id": "erl:1", "relation": "SUPPORTS", "artifact_refs": ["artifact:alpha"]}],
        model_observations=[{"model": "model-a", "candidate": "yes", "authority_effect": "NONE"}],
        governance_refs=["steggate:decision:1"],
        transition_id="transition:1",
        run_id="run:1",
    )
    assert receipt["final_response"] == response
    assert receipt["evidence_sources"][0]["data"] == {"claim": "x", "observed": True}
    assert receipt["erl_relationships"][0]["relationship_id"] == "erl:1"
    assert receipt["authority"]["provider_output_is_authority"] is False
    assert receipt["authority"]["erl_relationship_is_authority"] is False
    assert receipt["reconstructable"] is True
    assert receipt["receipt_id"].startswith("evidence-receipt:sha256:")


def test_receipt_rejects_source_reference_without_actual_data() -> None:
    with pytest.raises(ValueError, match="missing actual data"):
        build_evidence_receipt(
            query="q",
            final_response="The available evidence is incomplete.",
            evidence_posture="INCOMPLETE",
            evidence_sources=[{"source_ref": "artifact:missing-data"}],
        )


def test_unsupported_posture_cannot_use_strong_certainty_language() -> None:
    assert certainty_language_allowed("I don't have evidence that supports that claim.", "UNSUPPORTED")
    assert not certainty_language_allowed("This is definitely proven.", "UNSUPPORTED")
    with pytest.raises(ValueError, match="certainty exceeds evidence posture"):
        assert_certainty_language_allowed("The evidence strongly supports this.", "INCOMPLETE")


def test_strong_posture_may_use_weaker_conversational_language() -> None:
    assert certainty_language_allowed("This appears consistent with the available record.", "STRONGLY_SUPPORTED")


def test_contradictions_and_uncertainty_are_not_collapsed() -> None:
    receipt = build_evidence_receipt(
        query="q",
        final_response="The evidence is mixed.",
        evidence_posture="MIXED",
        evidence_sources=[{"source_ref": "a", "data": {"value": 1}}],
        contradictions=[{"claim_ref": "c1", "source_ref": "b", "conflict": "value differs"}],
        uncertainty=[{"field": "causation", "state": "UNRESOLVED"}],
    )
    assert receipt["contradictions"] == [{"claim_ref": "c1", "source_ref": "b", "conflict": "value differs"}]
    assert receipt["uncertainty"] == [{"field": "causation", "state": "UNRESOLVED"}]


def test_user_projection_is_minimum_information_not_raw_evidence() -> None:
    receipt = build_evidence_receipt(
        query="q",
        final_response="The available evidence supports this.",
        evidence_posture="SUPPORTED",
        evidence_sources=[{"source_ref": "a", "data": {"sensitive": "retained only in full receipt"}}],
        erl_relationships=[{"relationship_id": "erl:1"}],
        model_observations=[{"model": "a"}, {"model": "b"}],
        contradictions=[{"id": "conflict:1"}],
    )
    projection = user_evidence_projection(receipt)
    assert projection == {
        "evidence_posture": "SUPPORTED",
        "receipt_id": receipt["receipt_id"],
        "source_count": 1,
        "erl_relationship_count": 1,
        "model_observation_count": 2,
        "contradiction_count": 1,
        "uncertainty_count": 0,
        "full_evidence_embedded": False,
    }
    assert "evidence_sources" not in projection


def test_suggested_lead_matches_posture_without_exceeding_it() -> None:
    for posture in ("UNKNOWN", "UNSUPPORTED", "INCOMPLETE", "MIXED", "SUPPORTED", "STRONGLY_SUPPORTED"):
        lead = suggested_conversational_lead(posture)
        assert certainty_language_allowed(lead, posture)
