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
