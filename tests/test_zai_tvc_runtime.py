import pytest
from llm_adapter.provider_request import build_provider_request
from llm_adapter.zai_intr_transport import build_zai_intr_envelope
from llm_adapter.zai_tvc_broker import RUNTIME_PROFILE_ID, TVC_SECRET_REF, ZAITVCBrokerError, build_tvc_zai_operation_request, execute_zai_via_tvc_broker
from llm_adapter.zai_tvc_runtime_executor import ZAITVCRuntimeExecutionError, execute_governed_zai_via_tvc_runtime, admit_zai_tvc_runtime_egress


def _request():
    return build_provider_request(provider="z.ai", model="glm-5.3-flash", messages=[{"role":"user","content":"hello"}])

def _envelope(req):
    return build_zai_intr_envelope(req, transition_id="tx-1", ingress_disposition="ALLOW", ingress_receipt_hash="a"*64, carrier_ref="carrier-1")

def _lease(env):
    return {"decision":"ALLOW_CAPABILITY_LEASE","provider":"zai","operation":"chat_completion_with_usage","model":env.model,"transition_id":env.transition_id,"request_hash":env.request_hash,"ingress_receipt_hash":env.ingress_receipt_hash,"carrier_ref":env.carrier_ref,"runtime_profile_id":RUNTIME_PROFILE_ID,"credential_authority":"TV/TVC","credential_material_present":False,"second_machine_required":False,"single_use":True,"secret_values_exported":False,"protected_values_exposed":False,"authority_granted":False}

def _broker(_):
    return {"decision":"ALLOW_OPERATION_RESULT","result":{"output":"ok","usage":{"prompt_tokens":2,"completion_tokens":1,"total_tokens":3}},"use_receipt":{"secret_material_returned":False,"secret_material_logged":False,"secret_material_retained":False,"single_use_consumed":True}}

def _execution():
    req=_request(); env=_envelope(req)
    return execute_governed_zai_via_tvc_runtime(req,session_id="s",transition_id="tx-1",measurement_id="m",ingress_disposition="ALLOW",ingress_receipt_hash="a"*64,carrier_ref="carrier-1",lease_receipt=_lease(env),broker_submitter=_broker,usage_submitter=lambda event:{"status":"custodied","authority_effect":"NONE","custody_recorded":True})

def test_tvc_operation_is_non_exportable_and_exact_bound():
    req=_request(); env=_envelope(req); op=build_tvc_zai_operation_request(env,req,lease_receipt=_lease(env))
    assert op["secret_ref"]==TVC_SECRET_REF
    assert op["runtime_profile_id"]==RUNTIME_PROFILE_ID
    assert op["credential_material_present"] is False
    assert op["export_allowed"] is False
    bad=_lease(env); bad["request_hash"]="f"*64
    with pytest.raises(ZAITVCBrokerError,match="exact binding mismatch: request_hash"): build_tvc_zai_operation_request(env,req,lease_receipt=bad)

def test_broker_result_and_runtime_require_egress():
    req=_request(); env=_envelope(req); result=execute_zai_via_tvc_broker(env,req,lease_receipt=_lease(env),broker_submitter=_broker)
    assert result.response.output=="ok"
    assert result.response.metadata["credential_material_present"] is False
    assert result.response.metadata["egress_intr_required"] is True
    execution=_execution()
    admission=admit_zai_tvc_runtime_egress(execution,egress_disposition="ALLOW",egress_receipt_hash="c"*64,admitted_response_hash=execution.response_hash)
    assert admission.state=="EGRESS_ADMITTED"
    with pytest.raises(ZAITVCRuntimeExecutionError): admit_zai_tvc_runtime_egress(execution,egress_disposition="DENY",egress_receipt_hash="c"*64,admitted_response_hash=execution.response_hash)
