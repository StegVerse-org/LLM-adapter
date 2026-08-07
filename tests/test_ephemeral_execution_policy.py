import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "contracts" / "ephemeral-execution-policy.v1.json"
DOC = ROOT / "docs" / "STEGVERSE_EPHEMERAL_BY_DEFAULT_STANDARD.md"
MICRONODE_POLICY = ROOT / "contracts" / "least-stable-micronode-policy.v1.json"


def load_policy():
    return json.loads(POLICY.read_text())


def test_ephemeral_policy_requires_micronode_precursor():
    p = load_policy()
    assert p["prerequisite_required"] is True
    assert p["prerequisite_policy"] == "stegverse.least_stable_micronode_policy.v1"
    assert json.loads(MICRONODE_POLICY.read_text())["schema"] == p["prerequisite_policy"]


def test_ephemeral_is_default_and_persistence_fails_closed():
    p = load_policy()
    assert p["schema"] == "stegverse.ephemeral_execution_policy.v1"
    assert p["default_resource_lifecycle"] == "EPHEMERAL"
    assert p["default_connection_lifecycle"] == "BOUNDED_OPERATION"
    assert p["persistent_resource_policy"]["default"] == "DENY"
    assert p["persistent_resource_policy"]["allowed_only_when_target_or_protocol_requires"] is True


def test_persistent_exception_requires_finite_revalidation_controls():
    p = load_policy()
    required = set(p["persistent_resource_policy"]["required_fields"])
    assert {
        "persistence_reason",
        "target_identity",
        "lease_duration_seconds",
        "renewal_condition",
        "idle_timeout_seconds",
        "credential_scope",
        "reconnect_policy",
        "state_externalization",
        "teardown_receipt",
        "authority_effect",
    } <= required


def test_hosting_must_support_scale_to_zero_and_on_demand_execution():
    h = load_policy()["hosting_requirements"]
    assert h["support_on_demand_activation"] is True
    assert h["support_short_lived_workers"] is True
    assert h["support_scale_to_zero_when_semantics_permit"] is True
    assert h["support_independent_micronode_replacement"] is True
    assert h["vendor_always_on_default_is_authority"] is False


def test_ephemerality_cannot_hide_capability_aggregation():
    m = load_policy()["micro_node_lifecycle_constraints"]
    assert m["ephemerality_does_not_justify_capability_aggregation"] is True
    assert m["individual_jobs_remain_micro_nodes_when_service_is_addressable"] is True
    assert m["replacement_without_service_identity_loss"] is True
    assert m["provider_specific_process_identity_is_canonical"] is False


def test_provider_connection_is_post_admission_and_bounded():
    p = load_policy()["provider_model_requirements"]
    assert p["connectivity_downstream_of_admission"] is True
    assert p["credential_materialization_after_admission"] is True
    assert p["connection_closes_after_bounded_request_or_stream"] is True
    assert p["execution_node_terminates_after_bounded_operation_by_default"] is True


def test_document_states_normative_rule_and_authority_boundary():
    text = DOC.read_text()
    assert "Anything that can be performed ephemerally SHOULD be performed ephemerally." in text
    assert "Prerequisite standard" in text
    assert "connection persistence != authority" in text
    assert "service availability != execution authority" in text
    assert "ephemeral execution != authority" in text
