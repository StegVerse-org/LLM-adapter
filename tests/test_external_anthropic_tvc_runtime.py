import pytest
from llm_adapter.provider_request import build_provider_request
from llm_adapter.anthropic_convergence_bridge import build_anthropic_convergence_envelope
from llm_adapter.anthropic_tvc_broker import RUNTIME_PROFILE_ID, TVC_SECRET_REF, AnthropicTVCBrokerError, build_tvc_anthropic_operation_request, execute_anthropic_via_tvc_broker
from llm_adapter.anthropic_tvc_runtime_executor import AnthropicTVCRuntimeExecutionError, execute_governed_anthropic_via_tvc_runtime, admit_anthropic_tvc_runtime_egress


def _request():
    return build_provider_request(provider="anthropic", model="claude-opus-5", messages=[{"role":"user","content":"hello"}])

def _envelope(req):
    return build_anthropic_convergence_envelope(req, session_id="s", transition_id="tx-1", ingress_disposition="ALLOW", ingress_receipt_hash="a"*64, carrier_ref="carrier-1", max_tokens=2048)

def _lease(env):
    return {"decision":"ALLOW_CAPABILITY_LEASE","provider":"anthropic","operation":"message_with_usage","model":env.model,"transition_id":env.transition_id,"request_hash":env.request_hash,"ingress_receipt_hash":env.ingress_receipt_hash,"carrier_ref":env.carrier_ref,"runtime_profile_id":RUNTIME_PROFILE_ID,"credential_authority":"TV/TVC","credential_material_present":False,"second_machine_required":False,"single_use":True,"secret_values_exported":False,"protected_values_exposed":False,"authority_granted":False}

def _broker(_):
    return {"decision":"ALLOW_OPERATION_RESULT","result":{"output":"ok","usage":{"input_tokens":2,"output_tokens":1}},"use_receipt":{"secret_material_returned":False,"secret_material_logged":False,"secret_material_retained":False,"single_use_consumed":True}}

def _execution():
    req=_request(); env=_envelope(req)
    return execute_governed_anthropic_via_tvc_runtime(req,session_id="s",transition_id="tx-1",measurement_id="m",ingress_disposition="ALLOW",ingress_receipt_hash="a"*64,carrier_ref="carrier-1",lease_receipt=_lease(env),broker_submitter=_broker,usage_submitter=lambda event:{"status":"custodied","authority_effect":"NONE","custody_recorded":True})

def test_tvc_operation_is_non_exportable_and_exact_bound():
    req=_request(); env=_envelope(req); op=build_tvc_anthropic_operation_request(env,req,lease_receipt=_lease(env))
    assert op["secret_ref"]==TVC_SECRET_REF
    assert op["runtime_profile_id"]==RUNTIME_PROFILE_ID
    assert op["credential_material_present"] is False
    bad=_lease(env); bad["carrier_ref"]="other"
    with pytest.raises(AnthropicTVCBrokerError,match="exact binding mismatch: carrier_ref"): build_tvc_anthropic_operation_request(env,req,lease_receipt=bad)

def test_broker_result_and_runtime_require_egress():
    req=_request(); env=_envelope(req); result=execute_anthropic_via_tvc_broker(env,req,lease_receipt=_lease(env),broker_submitter=_broker)
    assert result.response.output=="ok"
    assert result.response.metadata["credential_material_present"] is False
    execution=_execution()
    admission=admit_anthropic_tvc_runtime_egress(execution,egress_disposition="ALLOW",egress_receipt_hash="c"*64,admitted_response_hash=execution.response_hash)
    assert admission.state=="EGRESS_ADMITTED"
    with pytest.raises(AnthropicTVCRuntimeExecutionError): admit_anthropic_tvc_runtime_egress(execution,egress_disposition="ALLOW",egress_receipt_hash="bad",admitted_response_hash=execution.response_hash)



def _broker_with(result_extra=None, usage=None):
    result = {"output": "ok", "model": "claude-runtime-fixture", "usage": {"input_tokens": 2, "output_tokens": 1} if usage is None else usage}
    result.update(result_extra or {})
    receipt = {"secret_material_returned": False, "secret_material_logged": False, "secret_material_retained": False, "single_use_consumed": True}
    return lambda operation: {"decision": "ALLOW_OPERATION_RESULT", "result": result, "use_receipt": receipt}


@pytest.mark.parametrize("secret_field", ["api_key", "access_token", "refresh_token", "secret", "secret_value", "credential_material", "authorization", "x-api-key", "API_KEY"])
def test_broker_refuses_secret_bearing_result_even_with_clean_use_receipt(secret_field):
    req = _request(); env = _envelope(req)
    with pytest.raises(AnthropicTVCBrokerError, match="result contains credential material"):
        execute_anthropic_via_tvc_broker(env, req, lease_receipt=_lease(env), broker_submitter=_broker_with({secret_field: "should-not-leave-tvc"}))


def test_broker_retains_measured_usage_and_runtime_model():
    req = _request(); env = _envelope(req)
    meta = execute_anthropic_via_tvc_broker(env, req, lease_receipt=_lease(env), broker_submitter=_broker_with()).response.metadata
    assert meta["usage"] == {"input_tokens": 2, "output_tokens": 1}
    assert meta["usage_measured"] is True and meta["runtime_model"] == "claude-runtime-fixture"


@pytest.mark.parametrize("usage", [{}, {"input_tokens": -5, "output_tokens": 1}, {"input_tokens": 2.5, "output_tokens": 1}, {"input_tokens": True, "output_tokens": 1}, {"input_tokens": "2", "output_tokens": 1}])
def test_negative_fractional_or_malformed_usage_is_unavailable_not_measured(usage):
    req = _request(); env = _envelope(req)
    execution = execute_governed_anthropic_via_tvc_runtime(
        req, session_id="s", transition_id="tx-1", measurement_id="m", ingress_disposition="ALLOW",
        ingress_receipt_hash="a" * 64, carrier_ref="carrier-1", lease_receipt=_lease(env),
        broker_submitter=_broker_with(usage=usage), usage_submitter=lambda event: {"status": "recorded", "authority_effect": "NONE"})
    assert execution.broker.response.metadata["usage_measured"] is False
    metrics = execution.provider_usage_event["metrics"]
    assert all(metrics[k]["evidence_class"] == "UNAVAILABLE" for k in ("prompt_tokens", "completion_tokens", "total_tokens"))



@pytest.mark.parametrize("result_extra", [
    {"apiKey": "s"}, {"openai_api_key": "s"}, {"X-Api-Key": "s"}, {"bearer_token": "s"}, {"password": "s"},
    {"metadata": {"api_key": "s"}},
    {"metadata": [{"safe": True}, {"Authorization": "s"}]},
    {"metadata": ({"access_token": "s"},)},
    {"metadata": {"deep": {"refresh-token": "s"}}},
])
def test_broker_refuses_nested_and_variant_credential_keys(result_extra):
    req = _request(); env = _envelope(req)
    with pytest.raises(AnthropicTVCBrokerError, match="result contains credential material"):
        execute_anthropic_via_tvc_broker(env, req, lease_receipt=_lease(env), broker_submitter=_broker_with(result_extra))


def test_broker_accepts_nested_nonsecret_metadata_and_usage_token_keys():
    req = _request(); env = _envelope(req)
    result = execute_anthropic_via_tvc_broker(env, req, lease_receipt=_lease(env),
        broker_submitter=_broker_with({"metadata": {"details": [{"safe": True}], "prompt_tokens": 3, "cache_read_input_tokens": 0}}))
    assert result.response.output == "ok"


def test_pathologically_deep_result_fails_closed_with_broker_error():
    req = _request(); env = _envelope(req)
    deep = {}; cur = deep
    for _ in range(2000):
        cur["n"] = {}; cur = cur["n"]
    with pytest.raises(AnthropicTVCBrokerError, match="result exceeds nesting limit"):
        execute_anthropic_via_tvc_broker(env, req, lease_receipt=_lease(env), broker_submitter=_broker_with({"metadata": deep}))


@pytest.mark.parametrize("model,expected", [("claude-runtime-fixture", "claude-runtime-fixture"), (None, None), ("", None)])
def test_egress_handoff_carries_requested_and_provider_reported_model(model, expected):
    req = _request(); env = _envelope(req)
    execution = execute_governed_anthropic_via_tvc_runtime(
        req, session_id="s", transition_id="tx-1", measurement_id="m", ingress_disposition="ALLOW",
        ingress_receipt_hash="a" * 64, carrier_ref="carrier-1", lease_receipt=_lease(env),
        broker_submitter=_broker_with({"model": model}), usage_submitter=lambda event: {"status": "recorded", "authority_effect": "NONE"})
    handoff = execution.egress_handoff
    assert handoff["requested_model"] == req.model
    assert handoff["runtime_model"] == expected
    assert handoff["usage_measured"] is True
