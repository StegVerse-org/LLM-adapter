import pytest

from llm_adapter.openai_intr_transport import OpenAITransportAdmissionError, build_openai_intr_envelope, openai_wire_request_hash
from llm_adapter.openai_tvc_broker import RUNTIME_PROFILE_ID, TVC_SECRET_REF, OpenAITVCBrokerError, build_tvc_openai_operation_request, execute_openai_via_tvc_broker
from llm_adapter.openai_tvc_runtime_executor import OpenAITVCRuntimeExecutionError, admit_openai_tvc_runtime_egress, execute_governed_openai_via_tvc_runtime
from llm_adapter.provider_request import build_provider_request


def _request(provider="openai"):
    return build_provider_request(provider=provider, model="gpt-fixture", messages=[{"role": "user", "content": "hello"}])


def _envelope(req):
    return build_openai_intr_envelope(req, transition_id="tx-1", ingress_disposition="ALLOW", ingress_receipt_hash="a" * 64, carrier_ref="carrier-1")


def _lease(env):
    return {"decision": "ALLOW_CAPABILITY_LEASE", "provider": "openai", "operation": "chat_completion_with_usage", "model": env.model,
            "transition_id": env.transition_id, "request_hash": env.request_hash, "ingress_receipt_hash": env.ingress_receipt_hash,
            "carrier_ref": env.carrier_ref, "runtime_profile_id": RUNTIME_PROFILE_ID, "credential_authority": "TV/TVC",
            "credential_material_present": False, "second_machine_required": False, "single_use": True,
            "secret_values_exported": False, "protected_values_exposed": False, "authority_granted": False}


def _broker(usage=None, **result_extra):
    result = {"output": "ok", "model": "gpt-runtime-fixture", "response_id": "chatcmpl-fixture"}
    result["usage"] = {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3} if usage is None else usage
    result.update(result_extra)
    receipt = {"secret_material_returned": False, "secret_material_logged": False, "secret_material_retained": False, "single_use_consumed": True}
    return lambda operation: {"decision": "ALLOW_OPERATION_RESULT", "result": result, "use_receipt": receipt}


def _execution(broker=None):
    req = _request()
    env = _envelope(req)
    return execute_governed_openai_via_tvc_runtime(
        req, session_id="s", transition_id="tx-1", measurement_id="m", ingress_disposition="ALLOW",
        ingress_receipt_hash="a" * 64, carrier_ref="carrier-1", lease_receipt=_lease(env),
        broker_submitter=broker or _broker(),
        usage_submitter=lambda event: {"status": "recorded", "authority_effect": "NONE"})


def test_envelope_requires_ingress_allow_exact_receipt_and_openai_target():
    req = _request()
    env = _envelope(req)
    assert env.transport_id.startswith("oait-") and env.request_hash == openai_wire_request_hash(req)
    assert env.credential_authority == "TV/TVC" and env.credential_material_present is False
    with pytest.raises(OpenAITransportAdmissionError, match="ingress InTr ALLOW"):
        build_openai_intr_envelope(req, transition_id="tx-1", ingress_disposition="DENY", ingress_receipt_hash="a" * 64, carrier_ref="c")
    with pytest.raises(OpenAITransportAdmissionError, match="sha256"):
        build_openai_intr_envelope(req, transition_id="tx-1", ingress_disposition="ALLOW", ingress_receipt_hash="A" * 64, carrier_ref="c")
    with pytest.raises(OpenAITransportAdmissionError, match="explicitly target OpenAI"):
        build_openai_intr_envelope(_request("anthropic"), transition_id="tx-1", ingress_disposition="ALLOW", ingress_receipt_hash="a" * 64, carrier_ref="c")
    assert _envelope(_request("chatgpt")).provider == "openai"


def test_tvc_operation_is_non_exportable_and_exact_bound():
    req = _request()
    env = _envelope(req)
    op = build_tvc_openai_operation_request(env, req, lease_receipt=_lease(env))
    assert op["secret_ref"] == TVC_SECRET_REF
    assert op["runtime_profile_id"] == RUNTIME_PROFILE_ID
    assert op["credential_material_present"] is False and op["export_allowed"] is False
    assert op["operation"]["return_secret_material"] is False
    for key, bad_value in (("request_hash", "f" * 64), ("model", "other"), ("runtime_profile_id", "x")):
        bad = _lease(env)
        bad[key] = bad_value
        with pytest.raises(OpenAITVCBrokerError, match=f"exact binding mismatch: {key}"):
            build_tvc_openai_operation_request(env, req, lease_receipt=bad)
    bad = _lease(env)
    bad["single_use"] = False
    with pytest.raises(OpenAITVCBrokerError, match="single-use"):
        build_tvc_openai_operation_request(env, req, lease_receipt=bad)


def test_broker_result_retains_measured_usage_and_runtime_model():
    req = _request()
    env = _envelope(req)
    result = execute_openai_via_tvc_broker(env, req, lease_receipt=_lease(env), broker_submitter=_broker())
    meta = result.response.metadata
    assert result.response.output == "ok"
    assert meta["usage"] == {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3}
    assert meta["usage_measured"] is True and meta["runtime_model"] == "gpt-runtime-fixture"
    assert meta["credential_material_present"] is False and meta["egress_intr_required"] is True


@pytest.mark.parametrize("usage", [{}, {"prompt_tokens": 2, "completion_tokens": "1", "total_tokens": 3}, {"prompt_tokens": True, "completion_tokens": 1, "total_tokens": 3}])
def test_missing_or_malformed_usage_is_unavailable_not_guessed(usage):
    execution = _execution(_broker(usage=usage))
    assert execution.broker.response.metadata["usage_measured"] is False
    metrics = execution.provider_usage_event["metrics"]
    assert all(metrics[k]["evidence_class"] == "UNAVAILABLE" and metrics[k]["value"] is None for k in ("prompt_tokens", "completion_tokens", "total_tokens"))
    assert execution.egress_handoff["usage_measured"] is False


def test_runtime_emits_measured_usage_event_and_requires_egress_allow():
    execution = _execution()
    metrics = execution.provider_usage_event["metrics"]
    assert metrics["total_tokens"] == {"value": "3", "unit": "tokens", "evidence_class": "MEASURED", "source_ref": f"openai:tvc:{execution.envelope.transport_id}"}
    assert execution.provider_usage_event["provider"] == "openai"
    assert execution.egress_handoff["requested_disposition"] == "ALLOW" and execution.egress_handoff["authority_effect"] == "NONE"
    admission = admit_openai_tvc_runtime_egress(execution, egress_disposition="ALLOW", egress_receipt_hash="c" * 64, admitted_response_hash=execution.response_hash)
    assert admission.state == "EGRESS_ADMITTED" and admission.transition_authority == "Interlock/InTr"
    with pytest.raises(OpenAITVCRuntimeExecutionError, match="egress InTr ALLOW"):
        admit_openai_tvc_runtime_egress(execution, egress_disposition="DENY", egress_receipt_hash="c" * 64, admitted_response_hash=execution.response_hash)
    with pytest.raises(OpenAITVCRuntimeExecutionError, match="response hash mismatch"):
        admit_openai_tvc_runtime_egress(execution, egress_disposition="ALLOW", egress_receipt_hash="c" * 64, admitted_response_hash="d" * 64)


def test_broker_refusal_and_secret_leak_fail_closed():
    req = _request()
    env = _envelope(req)
    with pytest.raises(OpenAITVCBrokerError, match="did not admit"):
        execute_openai_via_tvc_broker(env, req, lease_receipt=_lease(env), broker_submitter=lambda op: {"decision": "DENY"})
    leaky = {"decision": "ALLOW_OPERATION_RESULT", "result": {"output": "ok"},
             "use_receipt": {"secret_material_returned": True, "secret_material_logged": False, "secret_material_retained": False, "single_use_consumed": True}}
    with pytest.raises(OpenAITVCBrokerError, match="secret_material_returned"):
        execute_openai_via_tvc_broker(env, req, lease_receipt=_lease(env), broker_submitter=lambda op: leaky)


def test_usage_record_authority_escalation_fails_closed():
    req = _request()
    env = _envelope(req)
    with pytest.raises(OpenAITVCRuntimeExecutionError, match="authority_escalation"):
        execute_governed_openai_via_tvc_runtime(
            req, session_id="s", transition_id="tx-1", measurement_id="m", ingress_disposition="ALLOW",
            ingress_receipt_hash="a" * 64, carrier_ref="carrier-1", lease_receipt=_lease(env), broker_submitter=_broker(),
            usage_submitter=lambda event: {"status": "recorded", "authority_effect": "GRANTED"})


@pytest.mark.parametrize("secret_field", ["api_key", "access_token", "refresh_token", "secret", "secret_value", "credential_material", "authorization", "API_KEY"])
def test_broker_refuses_secret_bearing_result_even_with_clean_use_receipt(secret_field):
    req = _request()
    env = _envelope(req)
    submitter = _broker(**{secret_field: "should-not-leave-tvc"})
    with pytest.raises(OpenAITVCBrokerError, match="result contains credential material"):
        execute_openai_via_tvc_broker(env, req, lease_receipt=_lease(env), broker_submitter=submitter)


@pytest.mark.parametrize("nested_result", [
    {"metadata": {"api_key": "secret"}},
    {"metadata": [{"safe": True}, {"authorization": "secret"}]},
    {"metadata": ({"access_token": "secret"},)},
    {"metadata": {"deep": {"refresh_token": "secret"}}},
])
def test_broker_refuses_nested_credential_fields(nested_result):
    req = _request()
    env = _envelope(req)
    with pytest.raises(OpenAITVCBrokerError, match="result contains credential material"):
        execute_openai_via_tvc_broker(
            env, req, lease_receipt=_lease(env), broker_submitter=_broker(**nested_result)
        )


def test_broker_accepts_nested_nonsecret_metadata():
    req = _request()
    env = _envelope(req)
    result = execute_openai_via_tvc_broker(
        env, req, lease_receipt=_lease(env),
        broker_submitter=_broker(metadata={"details": [{"safe": True}]}),
    )
    assert result.response.output == "ok"


@pytest.mark.parametrize("model,expected", [("gpt-runtime-fixture", "gpt-runtime-fixture"), (None, None), (7, None)])
def test_egress_handoff_carries_requested_and_provider_reported_model(model, expected):
    handoff = _execution(_broker(model=model)).egress_handoff
    assert handoff["requested_model"] == _request().model
    assert handoff["runtime_model"] == expected
