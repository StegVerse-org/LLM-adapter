from llm_adapter.deepseek_intr_transport import build_deepseek_intr_envelope
from llm_adapter.deepseek_tvc_broker import (
    RUNTIME_PROFILE_ID,
    TVC_SECRET_REF,
    build_tvc_deepseek_operation_request,
    execute_deepseek_via_tvc_broker,
)
from llm_adapter.deepseek_tvc_runtime_executor import execute_governed_deepseek_via_tvc_runtime
from llm_adapter.provider_request import build_provider_request


def _request():
    return build_provider_request(
        provider="deepseek",
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "What is the capital of France?"}],
    )


def _lease():
    return {
        "decision": "ALLOW_CAPABILITY_LEASE",
        "provider": "deepseek",
        "operation": "chat_completion_with_usage",
        "single_use": True,
        "secret_values_exported": False,
        "protected_values_exposed": False,
        "authority_granted": False,
    }


def _envelope(req):
    return build_deepseek_intr_envelope(
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
            "provider": "deepseek",
            "secret_material_returned": False,
            "secret_material_logged": False,
            "secret_material_retained": False,
            "single_use_consumed": True,
        },
    }


def test_builds_non_exportable_tvc_operation_without_secret_material():
    req = _request()
    operation = build_tvc_deepseek_operation_request(_envelope(req), req, lease_receipt=_lease())
    assert operation["secret_ref"] == TVC_SECRET_REF
    assert operation["runtime_profile_id"] == RUNTIME_PROFILE_ID
    assert operation["credential_material_present"] is False
    assert operation["export_allowed"] is False
    assert operation["return_secret_material"] is False
    text = repr(operation).lower()
    assert "authorization" not in text
    assert "bearer " not in text
    assert "api_key" not in text


def test_tvc_broker_result_is_non_authoritative_and_requires_egress():
    req = _request()
    result = execute_deepseek_via_tvc_broker(_envelope(req), req, lease_receipt=_lease(), broker_submitter=_broker)
    assert result.response.output == "Paris"
    assert result.response.metadata["credential_material_present"] is False
    assert result.response.metadata["egress_intr_required"] is True
    assert result.response.metadata["authority_effect"] == "NONE"


def test_governed_runtime_continues_to_master_records_and_egress_handoff():
    req = _request()
    execution = execute_governed_deepseek_via_tvc_runtime(
        req,
        session_id="session-1",
        transition_id="tx-1",
        measurement_id="measurement-1",
        ingress_disposition="ALLOW",
        ingress_receipt_hash="a" * 64,
        carrier_ref="carrier-1",
        lease_receipt=_lease(),
        broker_submitter=_broker,
        usage_submitter=lambda event: {"status": "custodied", "authority_effect": "NONE", "event_sha256": event["event_sha256"]},
    )
    assert execution.runtime_profile_id == RUNTIME_PROFILE_ID
    assert execution.broker.response.output == "Paris"
    assert execution.egress_handoff["requested_disposition"] == "ALLOW"
    assert execution.egress_handoff["egress_intr_required"] is True
    assert execution.egress_handoff["credential_material_present"] is False
    assert execution.egress_handoff["authority_effect"] == "NONE"
