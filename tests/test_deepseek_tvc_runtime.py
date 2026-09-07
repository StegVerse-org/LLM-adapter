import pytest

from llm_adapter.deepseek_intr_transport import build_deepseek_intr_envelope
from llm_adapter.deepseek_tvc_broker import (
    DeepSeekTVCBrokerError,
    RUNTIME_PROFILE_ID,
    TVC_SECRET_REF,
    build_tvc_deepseek_operation_request,
    execute_deepseek_via_tvc_broker,
)
from llm_adapter.deepseek_tvc_runtime_executor import (
    DeepSeekTVCRuntimeExecutionError,
    admit_deepseek_tvc_runtime_egress,
    execute_governed_deepseek_via_tvc_runtime,
)
from llm_adapter.provider_request import build_provider_request


def _request():
    return build_provider_request(
        provider="deepseek",
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "What is the capital of France?"}],
    )


def _envelope(req):
    return build_deepseek_intr_envelope(
        req,
        transition_id="tx-1",
        ingress_disposition="ALLOW",
        ingress_receipt_hash="a" * 64,
        carrier_ref="carrier-1",
    )


def _lease(envelope=None):
    env = envelope or _envelope(_request())
    return {
        "decision": "ALLOW_CAPABILITY_LEASE",
        "provider": "deepseek",
        "operation": "chat_completion_with_usage",
        "model": env.model,
        "transition_id": env.transition_id,
        "request_hash": env.request_hash,
        "ingress_receipt_hash": env.ingress_receipt_hash,
        "carrier_ref": env.carrier_ref,
        "runtime_profile_id": RUNTIME_PROFILE_ID,
        "credential_authority": "TV/TVC",
        "credential_material_present": False,
        "second_machine_required": False,
        "single_use": True,
        "secret_values_exported": False,
        "protected_values_exposed": False,
        "authority_granted": False,
    }


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


def _execution():
    req = _request()
    env = _envelope(req)
    return execute_governed_deepseek_via_tvc_runtime(
        req,
        session_id="session-1",
        transition_id="tx-1",
        measurement_id="measurement-1",
        ingress_disposition="ALLOW",
        ingress_receipt_hash="a" * 64,
        carrier_ref="carrier-1",
        lease_receipt=_lease(env),
        broker_submitter=_broker,
        usage_submitter=lambda event: {"status": "custodied", "authority_effect": "NONE", "event_sha256": event["event_sha256"]},
    )


def test_builds_non_exportable_tvc_operation_without_secret_material():
    req = _request()
    env = _envelope(req)
    operation = build_tvc_deepseek_operation_request(env, req, lease_receipt=_lease(env))
    assert operation["secret_ref"] == TVC_SECRET_REF
    assert operation["runtime_profile_id"] == RUNTIME_PROFILE_ID
    assert operation["credential_material_present"] is False
    assert operation["export_allowed"] is False
    assert operation["return_secret_material"] is False
    text = repr(operation).lower()
    assert "authorization" not in text
    assert "bearer " not in text
    assert "api_key" not in text


def test_tvc_lease_is_bound_to_exact_envelope_and_cannot_be_replayed_or_detached():
    req = _request()
    env = _envelope(req)
    for field, value in {
        "model": "deepseek-v4-pro",
        "transition_id": "tx-other",
        "request_hash": "f" * 64,
        "ingress_receipt_hash": "e" * 64,
        "carrier_ref": "carrier-other",
        "runtime_profile_id": "other-profile",
    }.items():
        lease = _lease(env)
        lease[field] = value
        with pytest.raises(DeepSeekTVCBrokerError, match=f"exact binding mismatch: {field}"):
            build_tvc_deepseek_operation_request(env, req, lease_receipt=lease)


def test_tvc_lease_rejects_credential_authority_or_second_machine_drift():
    req = _request(); env = _envelope(req)
    lease = _lease(env); lease["credential_authority"] = "OTHER"
    with pytest.raises(DeepSeekTVCBrokerError, match="credential authority mismatch"):
        build_tvc_deepseek_operation_request(env, req, lease_receipt=lease)
    lease = _lease(env); lease["second_machine_required"] = True
    with pytest.raises(DeepSeekTVCBrokerError, match="second-machine requirement"):
        build_tvc_deepseek_operation_request(env, req, lease_receipt=lease)


def test_tvc_broker_result_is_non_authoritative_and_requires_egress():
    req = _request(); env = _envelope(req)
    result = execute_deepseek_via_tvc_broker(env, req, lease_receipt=_lease(env), broker_submitter=_broker)
    assert result.response.output == "Paris"
    assert result.response.metadata["credential_material_present"] is False
    assert result.response.metadata["egress_intr_required"] is True
    assert result.response.metadata["authority_effect"] == "NONE"


def test_governed_runtime_continues_to_master_records_and_egress_handoff():
    execution = _execution()
    assert execution.runtime_profile_id == RUNTIME_PROFILE_ID
    assert execution.broker.response.output == "Paris"
    assert execution.egress_handoff["requested_disposition"] == "ALLOW"
    assert execution.egress_handoff["egress_intr_required"] is True
    assert execution.egress_handoff["credential_material_present"] is False
    assert execution.egress_handoff["authority_effect"] == "NONE"


def test_tvc_runtime_egress_requires_exact_external_allow_and_response_hash():
    execution = _execution()
    admission = admit_deepseek_tvc_runtime_egress(
        execution,
        egress_disposition="ALLOW",
        egress_receipt_hash="c" * 64,
        admitted_response_hash=execution.response_hash,
    )
    assert admission.state == "EGRESS_ADMITTED"
    assert admission.response_hash == execution.response_hash
    assert admission.egress_receipt_hash == "c" * 64
    assert admission.runtime_profile_id == RUNTIME_PROFILE_ID
    assert admission.authority_effect == "NONE_LOCAL"


def test_tvc_runtime_egress_fails_closed_on_deny_bad_receipt_or_response_drift():
    execution = _execution()
    with pytest.raises(DeepSeekTVCRuntimeExecutionError, match="requires egress InTr ALLOW"):
        admit_deepseek_tvc_runtime_egress(execution, egress_disposition="DENY", egress_receipt_hash="c" * 64, admitted_response_hash=execution.response_hash)
    with pytest.raises(DeepSeekTVCRuntimeExecutionError, match="exact lowercase sha256"):
        admit_deepseek_tvc_runtime_egress(execution, egress_disposition="ALLOW", egress_receipt_hash="bad", admitted_response_hash=execution.response_hash)
    with pytest.raises(DeepSeekTVCRuntimeExecutionError, match="does not match exact provider response"):
        admit_deepseek_tvc_runtime_egress(execution, egress_disposition="ALLOW", egress_receipt_hash="c" * 64, admitted_response_hash="d" * 64)
