from llm_adapter.kimi_canonical_runtime import execute_canonical_kimi_via_tvc_runtime
from llm_adapter.kimi_governed_admission import build_governed_kimi_admission
from llm_adapter.kimi_intr_transport import KimiTransportAdmissionError
from llm_adapter.kimi_tvc_broker import TVC_MEASUREMENT_EVIDENCE_SCHEMA
from llm_adapter.provider_request import build_provider_request


def request():
    return build_provider_request(provider="kimi", model="kimi-k3", messages=[{"role":"user","content":"canonical prompt"}])


def lease():
    return {"decision":"ALLOW_CAPABILITY_LEASE","provider":"kimi","operation":"chat_completion_with_usage","model":"kimi-k3","single_use":True,"secret_values_exported":False,"protected_values_exposed":False,"authority_granted":False}


def broker(_):
    usage={"prompt_tokens":2,"completion_tokens":1,"total_tokens":3}
    return {
        "decision":"ALLOW_OPERATION_RESULT",
        "result":{"id":"r1","model":"kimi-k3","choices":[{"message":{"content":"ok"}}],"usage":usage},
        "use_receipt":{"provider":"kimi","secret_material_returned":False,"secret_material_logged":False,"secret_material_retained":False,"single_use_consumed":True},
        "measurement_evidence":{"schema":TVC_MEASUREMENT_EVIDENCE_SCHEMA,"provider":"kimi","provider_response_id":"r1","model":"kimi-k3","candidate_output":"ok","provider_usage":usage,"normalized_usage":{"prompt_tokens":2,"prompt_cache_hit_tokens":0,"prompt_cache_miss_tokens":0,"completion_tokens":1,"reasoning_tokens":0,"total_tokens":3},"provider_api_key_transferred_to_consumer":False,"secret_material_returned":False,"cost_status":"RATE_CARD_BINDING_REQUIRED"},
    }


def custody(event):
    return {"status":"CUSTODY_RECORDED","custody_recorded":True,"authority_granted":False,"authority_effect":"NONE","event_sha256":event["event_sha256"]}


def test_transport_complete_and_governance_allow_are_separate_required_evidence():
    admitted=build_governed_kimi_admission(request(),transition_id="tx",ingress_transport_state="TRANSPORT_COMPLETE",ingress_receipt_hash="a"*64,governance_disposition="ALLOW",governance_receipt_hash="b"*64,carrier_ref="hb:1")
    e=admitted.evidence()
    assert e["ingress_transport_state"]=="TRANSPORT_COMPLETE"
    assert e["governance_disposition"]=="ALLOW"
    assert e["transport_grants_execution_authority"] is False
    assert e["governance_grants_execution_authority"] is False
    assert e["provider_operation_authority"]=="TV/TVC"


def test_transport_complete_cannot_substitute_for_governance_allow():
    try:
        build_governed_kimi_admission(request(),transition_id="tx",ingress_transport_state="TRANSPORT_COMPLETE",ingress_receipt_hash="a"*64,governance_disposition="DENY",governance_receipt_hash="b"*64,carrier_ref="hb:1")
        assert False
    except KimiTransportAdmissionError:
        pass


def test_governance_allow_cannot_substitute_for_transport_completion():
    try:
        build_governed_kimi_admission(request(),transition_id="tx",ingress_transport_state="ALLOW",ingress_receipt_hash="a"*64,governance_disposition="ALLOW",governance_receipt_hash="b"*64,carrier_ref="hb:1")
        assert False
    except KimiTransportAdmissionError:
        pass


def test_canonical_runtime_binds_both_evidence_classes_before_tvc():
    result=execute_canonical_kimi_via_tvc_runtime(request(),session_id="s",transition_id="tx",measurement_id="m",ingress_transport_state="TRANSPORT_COMPLETE",ingress_receipt_hash="a"*64,governance_disposition="ALLOW",governance_receipt_hash="b"*64,carrier_ref="hb:1",lease_receipt=lease(),broker_submitter=broker,usage_submitter=custody)
    assert result.execution.broker.response.output=="ok"
    assert result.egress_handoff["ingress_transport_state"]=="TRANSPORT_COMPLETE"
    assert result.egress_handoff["governance_disposition"]=="ALLOW"
    assert result.egress_handoff["governance_receipt_hash"]=="b"*64
    assert result.egress_handoff["provider_operation_authority"]=="TV/TVC"
    assert result.egress_handoff["transport_grants_execution_authority"] is False
    assert result.egress_handoff["governance_grants_credential_authority"] is False
