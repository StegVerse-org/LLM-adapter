import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "contracts" / "least-stable-micronode-policy.v1.json"
DOC = ROOT / "docs" / "STEGVERSE_LEAST_STABLE_MICRONODE_STANDARD.md"
EPHEMERAL_DOC = ROOT / "docs" / "STEGVERSE_EPHEMERAL_BY_DEFAULT_STANDARD.md"
EPHEMERAL_POLICY = ROOT / "contracts" / "ephemeral-execution-policy.v1.json"


def load_policy():
    return json.loads(POLICY.read_text())


def test_least_stable_micro_node_is_normative_precursor():
    p = load_policy()
    assert p["schema"] == "stegverse.least_stable_micronode_policy.v1"
    assert p["status"] == "NORMATIVE_PRECURSOR"
    assert p["governing_rule"] == "ALL_CAPABILITIES_USE_LEAST_STABLE_VIABLE_MICRONODES"


def test_micro_nodes_minimize_capability_state_and_coupling():
    r = load_policy()["required_properties"]
    assert r["single_primary_capability"] is True
    assert r["minimum_capabilities"] is True
    assert r["implicit_authority"] is False
    assert r["externalize_reconstructable_mutable_state"] is True
    assert r["replaceable_without_process_identity"] is True
    assert r["unrelated_workload_coupling_by_convenience"] is False


def test_stability_order_prefers_one_shot_and_rejects_unjustified_stability():
    p = load_policy()
    order = p["stability_preference_order"]
    assert order[0] == "ONE_SHOT_OPERATION"
    assert order[-1] == "PERMANENT_PROCESS_OR_COUPLED_SERVICE"
    assert p["more_stable_construction_default"] == "DENY_UNLESS_EXCEPTION_JUSTIFIED"


def test_hosting_constructs_and_tears_down_independent_nodes():
    h = load_policy()["hosting"]
    assert h["independent_instance_construction"] is True
    assert h["independent_instance_replacement"] is True
    assert h["independent_instance_teardown"] is True
    assert h["scale_to_zero"] is True
    assert h["capability_scoped_secret_release"] is True
    assert h["hosting_substrate_expands_authority"] is False


def test_replacement_nodes_do_not_inherit_secret_or_process_identity():
    p = load_policy()
    assert p["credentials"]["replacement_instance_inherits_secret_material"] is False
    assert p["identity"]["process_identity_required_for_continuity"] is False
    assert p["identity"]["provider_specific_service_identity_canonical"] is False


def test_more_stable_exception_is_explicit_and_bounded():
    required = set(load_policy()["exception_required_fields"])
    assert {
        "exception_reason",
        "required_target_semantics",
        "capabilities_that_cannot_be_split",
        "state_that_cannot_be_externalized",
        "minimum_required_lifetime",
        "revalidation_condition",
        "teardown_or_split_condition",
        "authority_effect",
    } <= required


def test_document_preserves_user_rule_and_precedes_ephemeral_standard():
    text = DOC.read_text()
    assert "least-stable viable micro-node instances" in text
    assert "structurally prior to the StegVerse Ephemeral-by-Default Runtime Standard" in text
    assert "micro-node existence != authority" in text

    ephemeral_text = EPHEMERAL_DOC.read_text()
    ephemeral_policy = json.loads(EPHEMERAL_POLICY.read_text())
    assert "Prerequisite standard" in ephemeral_text
    assert ephemeral_policy["prerequisite_policy"] == "stegverse.least_stable_micronode_policy.v1"
