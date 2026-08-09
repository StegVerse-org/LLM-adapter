from llm_adapter.steggate_portable_consumer import (
    GovernanceFacts,
    UserLLMIntent,
    canonical_runtime_identity,
    create_user_llm_governed_package,
    execute_user_llm_governed_package,
)

EXPECTED_IDENTITY = "stegverse:steggate:canonical:three-layer:v1"
EXPECTED_CONTRACT = "stegverse.steggate.runtime-identity.v1"


def facts(**overrides):
    base = dict(
        refusal_available=True,
        operator_recoverability="available",
        workload_state="supported",
        time_pressure="normal",
        isolation_state="supported",
        judgment_evidence_refs=("judgment:ecosystem-chat",),
        admitted_signal_refs=("prompt:sha256:abc",),
        missing_inputs=(),
        uncertainty_state="bounded",
        reference_state_hash="chat-state:1",
        expected_reference_state_hash="chat-state:1",
        reconstruction_available=True,
        transformation_provenance_complete=True,
        actor_authority_current=True,
        policy_current=True,
        delegation_current=True,
        evidence_current=True,
        affected_entity_conditions_represented=True,
        recoverability_profile="recoverable",
        validity_window_open=True,
        policy_ref="policy:ecosystem-chat:v1",
        delegation_ref="delegation:user-llm:v1",
        execution_evidence_refs=("execution:ecosystem-chat",),
        capability_allowed=True,
        continuity_required=True,
        previous_receipt_verified=True,
        previous_receipt_hash="receipt:prior-chat-turn",
        approval_required=False,
        permission_present=False,
    )
    base.update(overrides)
    return GovernanceFacts(**base)


def intent():
    return UserLLMIntent(
        user_id="portable-user",
        llm_id="ecosystem-chat",
        provider="fixture-provider",
        model="deterministic-model",
        prompt_hash="prompt:sha256:abc",
    )


def test_runtime_identity_is_canonical_and_transport_independent():
    identity = canonical_runtime_identity()
    assert identity["contract_version"] == EXPECTED_CONTRACT
    assert identity["runtime_identity"] == EXPECTED_IDENTITY
    assert identity["canonical_owner"] == "StegVerse-Labs/StegCore"
    assert identity["canonical_admissibility_runtime"] == "stegcore.three_layer.evaluate_three_layer"
    assert identity["transport_identity_authoritative"] is False


def test_ecosystem_chat_package_executes_provider_call_only_after_portable_steggate_allow():
    package = create_user_llm_governed_package(
        package_id="ecosystem-chat-portable-001",
        intent=intent(),
        governance=facts(),
    )
    calls = []

    receipt = execute_user_llm_governed_package(
        package,
        lambda: calls.append("provider_called") or {"response": "fixture-response"},
    )

    assert receipt.state == "EXECUTED"
    assert calls == ["provider_called"]
    assert receipt.execution_observation["evaluation"]["disposition"] == "ALLOW"
    assert receipt.execution_observation["coherence_receipt"]["decision"] == "ALLOW"
    assert receipt.execution_observation["result"] == {"response": "fixture-response"}
    assert package.admissibility_request.candidate.scope == "ecosystem_chat"
    params = package.admissibility_request.candidate.parameters
    assert params["prompt_hash"] == "prompt:sha256:abc"
    assert params["steggate_runtime_identity"] == EXPECTED_IDENTITY
    assert params["steggate_contract_version"] == EXPECTED_CONTRACT
    assert package.admissibility_request.declared_context["steggate_runtime_identity"] == EXPECTED_IDENTITY
    assert package.declared_execution_context["steggate_runtime_identity"] == EXPECTED_IDENTITY


def test_policy_drift_prevents_provider_call():
    package = create_user_llm_governed_package(
        package_id="ecosystem-chat-portable-deny",
        intent=intent(),
        governance=facts(policy_current=False),
    )
    calls = []

    receipt = execute_user_llm_governed_package(package, lambda: calls.append("should-not-run"))

    assert receipt.state == "REFUSED"
    assert calls == []
    assert receipt.execution_observation["evaluation"]["disposition"] == "DENY"
    assert receipt.execution_observation["executor_invoked"] is False


def test_package_can_be_serialized_for_transport_without_exposing_provider_credentials():
    package = create_user_llm_governed_package(
        package_id="ecosystem-chat-portable-transport",
        intent=intent(),
        governance=facts(),
    )
    payload = package.model_dump(mode="json")

    assert payload["artifact_type"] == "stegcore.governed_transition_package"
    assert payload["micronode"]["profile"] == "steggate.portable-micronode.v1"
    assert payload["package_hash"]
    assert payload["declared_execution_context"]["steggate_runtime_identity"] == EXPECTED_IDENTITY
    assert payload["declared_execution_context"]["steggate_contract_version"] == EXPECTED_CONTRACT
    assert "api_key" not in str(payload).lower()
    assert "credential" not in str(payload).lower()
