from llm_adapter.kimi_intr_transport import build_kimi_intr_envelope
from llm_adapter.kimi_tvc_broker import (
    RUNTIME_PROFILE_ID,
    TVC_SECRET_REF,
    KimiTVCBrokerError,
    build_tvc_kimi_operation_request,
    execute_kimi_via_tvc_broker,
)
from llm_adapter.kimi_tvc_runtime_executor import execute_governed_kimi_via_tvc_runtime
from llm_adapter.provider_request import build_provider_request


def _request():
    return build_provider_request(
        provider="kimi",
        model="kimi-k3",
        messages=[{"role": "user", "content": "What is the capital of France?"}],
    )


def _lease():
    return {
        "decision": "ALLOW_CAPABILITY_LEASE",
        "provider": "kimi",
        "operation": "chat_completion_with_usage",
        "model": "kimi-k3",
        "single_use": True,
        "secret_values_exported": False,
        "protected_values_exposed": False,
        "authority_granted": False,
    }


def _envelope(req):
    return build_kimi_intr_envelope(
        req,
        transition_id="tx-1",
        ingress_disposition="ALLOW",
        ingress_receipt_hash="a" * 64,
        carrier_ref="carrier-1",
    )


def _broker(_request):
    return {
        "decision": "ALLOW_OPERATION_RESULT",
        "result": {
            "output": "Paris",
            "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
        },
        "use_receipt": {
            "provider": "kimi",
            "secret_material_returned": False,
            "secret_material_logged": False,
            "secret_material_retained": False,
            "single_use_consumed": True,
        },
    }


def test_builds_non_exportable_tvc_operation_without_secret_material():
    req = _request()
    operation = build_tvc_kimi_operation_request(_envelope(req), req, lease_receipt=_lease())
    assert operation["secret_ref"] == TVC_SECRET_REF
    assert operation["runtime_profile_id"] == RUNTIME_PROFILE_ID
    assert operation["intr_binding"]["transition_id"] == "tx-1"
    assert operation["credential_material_present"] is False
    assert operation["export_allowed"] is False
    assert operation["return_secret_material"] is False
    text = repr(operation).lower()
    assert "authorization" not in text
    assert "bearer " not in text
    assert "api_key" not in text


def test_rejects_lease_for_wrong_provider_or_model():
    req = _request()
    wrong_provider = dict(_lease(), provider="deepseek")
    try:
        build_tvc_kimi_operation_request(_envelope(req), req, lease_receipt=wrong_provider)
        assert False, "wrong provider lease must fail closed"
    except KimiTVCBrokerError:
        pass
    wrong_model = dict(_lease(), model="other")
    try:
        build_tvc_kimi_operation_request(_envelope(req), req, lease_receipt=wrong_model)
        assert False, "wrong model lease must fail closed"
    except KimiTVCBrokerError:
        pass


def test_tvc_broker_result_is_non_authoritative_and_requires_egress():
    req = _request()
    result = execute_kimi_via_tvc_broker(_envelope(req), req, lease_receipt=_lease(), broker_submitter=_broker)
    assert result.response.output == "Paris"
    assert result.response.metadata["credential_material_present"] is False
    assert result.response.metadata["egress_intr_required"] is True
    assert result.response.metadata["authority_effect"] == "NONE"


def test_governed_runtime_continues_to_master_records_and_egress_handoff():
    req = _request()
    execution = execute_governed_kimi_via_tvc_runtime(
        req,
        session_id="session-1",
        transition_id="tx-1",
        measurement_id="measurement-1",
        ingress_disposition="ALLOW",
        ingress_receipt_hash="a" * 64,
        carrier_ref="carrier-1",
        lease_receipt=_lease(),
        broker_submitter=_broker,
        usage_submitter=lambda event: {"status": "CUSTODY_RECORDED", "custody_recorded": True, "authority_granted": False, "authority_effect": "NONE", "event_sha256": event["event_sha256"]},
    )
    assert execution.runtime_profile_id == RUNTIME_PROFILE_ID
    assert execution.broker.response.output == "Paris"
    assert execution.provider_usage_event["provider"] == "kimi"
    assert execution.egress_handoff["requested_disposition"] == "ALLOW"
    assert execution.egress_handoff["egress_intr_required"] is True
    assert execution.egress_handoff["credential_material_present"] is False
    assert execution.egress_handoff["authority_effect"] == "NONE"
