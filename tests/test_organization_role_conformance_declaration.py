"""The organization-role conformance declaration (LLM-adapter#368 F10) is well formed.

Source validation only: the declaration claims no runtime observation.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECLARATION = json.loads((ROOT / "data/organization-role-conformance.json").read_text(encoding="utf-8"))
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


def test_declaration_is_source_implemented_and_claims_no_runtime():
    assert DECLARATION["evidence_class"] == "SOURCE_IMPLEMENTED"
    assert DECLARATION["authority_effect"] == "NONE_DECLARATION_ONLY"
    assert DECLARATION["runtime_claim"] is False
    assert "CLAIM_RUNTIME_OBSERVATION" in DECLARATION["this_declaration_does_not"]
    assert DECLARATION["owning_existing_goal"] == "LLMA-DECLARED-PATH-CONFORMANCE-368"


def test_master_records_cannot_gate_or_be_awaited():
    role = DECLARATION["repository_role"]
    assert role["master_records_may_gate_a_transition"] is False
    assert role["master_records_may_be_awaited_by_a_transition"] is False
    assert role["authors_manifests"] is False and role["selects_processing"] is False
    standard = DECLARATION["conformance_standard"]
    assert standard["external_machine_awaiting_allowed"] is False
    assert tuple(standard["non_allow_required_fields"]) == SIX


def test_every_open_repair_carries_the_six_fields():
    for repair in DECLARATION["open_repairs"]:
        assert repair["disposition"] != "ALLOW"
        for key in SIX:
            assert isinstance(repair[key], str) and repair[key].strip(), (repair["surface"], key)
        assert repair["owning_existing_goal"] == "LLMA-DECLARED-PATH-CONFORMANCE-368"
    assert DECLARATION["exemptions_requested"] == []
