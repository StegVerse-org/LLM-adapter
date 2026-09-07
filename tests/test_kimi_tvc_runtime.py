from llm_adapter.kimi_intr_transport import build_kimi_intr_envelope
from llm_adapter.kimi_tvc_broker import (
    RUNTIME_PROFILE_ID,
    TVC_MEASUREMENT_EVIDENCE_SCHEMA,
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
    raw_usage = {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6}
    return {
        "decision": "ALLOW_OPERATION_RESULT",
        "result": {
            "id": "kimi-response-1",
            "model": "kimi-k3",
            "choices": [{"message": {"content": "Paris"}, "finish_reason": "stop"}],
            "usage": raw_usage,
        },
        "use_receipt": {
            "provider": "kimi",
            "secret_material_returned": False,
            "secret_material_logged": False,
            "secret_material_retained": False,
            "single_use_consumed": True,
        },
        "measurement_evidence": {
            "schema": TVC_MEASUREMENT_EVIDENCE_SCHEMA,
            "provider": "kimi",
            "provider_response_id": "kimi-response-1",
            "model": "kimi-k3",
            "candidate_output": "Paris",
            "provider_usage": raw_usage,
            "normalized_usage": {
                "prompt_tokens": 5,
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": 0,
                "completion_tokens": 1,
                "reasoning_tokens": 0,
                "total_tokens": 6,
            },
            "provider_api_key_transferred_to_consumer": False,
            "secret_material_returned": False,
            "cost_status": "RATE_CARD_BINDING_REQUIRED",
        },
    }


def test_builds_non_exportable_tvc_operation_without_secret_material_and_preserves_prompt():
    req = _request()
    operation = build_tvc_kimi_operation_request(_envelope(req), req, lease_receipt=_lease())
    assert operation["secret_ref"] == TVC_SECRET_REF
    assert operation["runtime_profile_id"] == RUNTIME_PROFILE_ID
    assert operation["intr_binding"]["transition_id"] == "tx-1"
    assert operation["operation"]["prompt"] == "What is the capital of France?"
    assert operation["credential_material_present"] is False
    assert operation["export_allowed"] is False
    assert operation["return_secret_material"] is False
    text = repr(operation).lower()
    assert "authorization" not in text
    assert "bearer " not in text
    assert "api_key" not in text


def test_tvc_v1_rejects_unrepresentable_multi_message_or_non_user_chat():
    invalid_requests = [
        build_provider_request(
            provider="kimi",
            model="kimi-k3",
            messages=[
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": "Hello"},
            ],
        ),
        build_provider_request(
            provider="kimi",
            model="kimi-k3",
            messages=[{"role": "system", "content": "Hello"}],
        ),
    ]
    for req in invalid_requests:
        try:
            build_tvc_kimi_operation_request(_envelope(req), req, lease_receipt=_lease())
            assert False, "TVC v1 must not execute a transformed chat request"
        except KimiTVCBrokerError:
            pass


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


def test_tvc_broker_consumes_canonical_measurement_evidence():
    req = _request()
    result = execute_kimi_via_tvc_broker(_envelope(req), req, lease_receipt=_lease(), broker_submitter=_broker)
    assert result.response.output == "Paris"
    assert result.response.metadata["provider_response_id"] == "kimi-response-1"
    assert result.response.metadata["usage"]["total_tokens"] == 6
    assert result.response.metadata["normalized_usage"]["total_tokens"] == 6
    assert result.measurement_evidence["schema"] == TVC_MEASUREMENT_EVIDENCE_SCHEMA
    assert result.response.metadata["credential_material_present"] is False
    assert result.response.metadata["egress_intr_required"] is True
    assert result.response.metadata["authority_effect"] == "NONE"


def test_raw_result_without_canonical_measurement_evidence_fails_closed():
    req = _request()
    raw_only = _broker({})
    raw_only.pop("measurement_evidence")
    try:
        execute_kimi_via_tvc_broker(
            _envelope(req),
            req,
            lease_receipt=_lease(),
            broker_submitter=lambda request: raw_only,
        )
        assert False, "raw provider result must not bypass canonical TVC normalization"
    except KimiTVCBrokerError:
        pass


def test_measurement_evidence_provider_or_model_drift_fails_closed():
    req = _request()
    for key, value in (("provider", "deepseek"), ("model", "other")):
        reply = _broker({})
        reply["measurement_evidence"] = dict(reply["measurement_evidence"], **{key: value})
        try:
            execute_kimi_via_tvc_broker(
                _envelope(req),
                req,
                lease_receipt=_lease(),
                broker_submitter=lambda request, reply=reply: reply,
            )
            assert False, f"measurement evidence {key} drift must fail closed"
        except KimiTVCBrokerError:
            pass


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
    assert execution.provider_usage_event["metrics"]["total_tokens"]["value"] == "6"
    assert execution.egress_handoff["requested_disposition"] == "ALLOW"
    assert execution.egress_handoff["egress_intr_required"] is True
    assert execution.egress_handoff["credential_material_present"] is False
    assert execution.egress_handoff["authority_effect"] == "NONE"
