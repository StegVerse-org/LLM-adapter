from llm_adapter.deepseek_intr_executor import (
    DeepSeekExecutionError,
    admit_deepseek_egress,
    execute_governed_deepseek,
)
from llm_adapter.deepseek_intr_transport import (
    DeepSeekTransportAdmissionError,
    DeepSeekTransportResult,
    deepseek_wire_request_hash,
)
from llm_adapter.provider_client import ProviderResponse
from llm_adapter.provider_request import build_provider_request


def _request():
    return build_provider_request(
        provider="deepseek",
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.0,
    )


class _FakeTransport:
    resolver_calls = 0

    def __init__(self, *, credential_resolver, base_url):
        self.credential_resolver = credential_resolver
        self.base_url = base_url

    def complete(self, envelope, request):
        credential = self.credential_resolver()
        type(self).resolver_calls += 1
        assert credential == "tv-tvc-ephemeral-secret"
        response = ProviderResponse(
            provider="deepseek",
            model=request.model,
            output="fixture-output",
            request_hash=envelope.request_hash,
            metadata={
                "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
                "transport_id": envelope.transport_id,
                "ingress_receipt_hash": envelope.ingress_receipt_hash,
                "credential_authority": "TV/TVC",
                "credential_material_present": False,
                "egress_intr_required": True,
                "authority_effect": "NONE",
            },
        )
        return DeepSeekTransportResult(
            envelope=envelope,
            response=response,
            provider_request_hash=request.request_hash,
        )


def _usage_submitter(event):
    return {
        "schema": "stegverse.usage.master_records_submission.v1",
        "status": "CUSTODY_RECORDED",
        "receipt_id": "mr-deepseek-fixture-1",
        "session_id": event["session_id"],
        "measurement_id": event["measurement_id"],
        "event_sha256": event["event_sha256"],
        "authority_granted": False,
        "custody_recorded": True,
        "authority_effect": "NONE",
    }


def _execute(**overrides):
    kwargs = {
        "session_id": "session-1",
        "transition_id": "transition-1",
        "measurement_id": "measurement-1",
        "ingress_disposition": "ALLOW",
        "ingress_receipt_hash": "a" * 64,
        "carrier_ref": "hb:carrier:deepseek",
        "credential_resolver": lambda: "tv-tvc-ephemeral-secret",
        "transport_factory": _FakeTransport,
        "usage_submitter": _usage_submitter,
    }
    kwargs.update(overrides)
    return execute_governed_deepseek(_request(), **kwargs)


def test_executor_requires_ingress_allow():
    try:
        _execute(ingress_disposition="DENY")
        assert False, "ingress DENY must fail closed"
    except DeepSeekTransportAdmissionError:
        pass


def test_executor_requires_credential_resolver():
    try:
        _execute(credential_resolver=None)
        assert False, "credential resolver must be callable"
    except DeepSeekExecutionError:
        pass


def test_executor_reuses_usage_custody_and_emits_egress_handoff():
    _FakeTransport.resolver_calls = 0
    result = _execute()
    evidence = result.evidence()
    assert _FakeTransport.resolver_calls == 1
    assert result.envelope.request_hash == deepseek_wire_request_hash(_request())
    assert result.provider_usage_event["provider"] == "deepseek"
    assert result.provider_usage_event["metrics"]["total_tokens"]["value"] == "5"
    assert result.master_records_usage["custody_recorded"] is True
    assert evidence["provider_usage_custody_recorded"] is True
    assert result.egress_handoff["requested_disposition"] == "ALLOW"
    assert result.egress_handoff["response_hash"] == result.response_hash
    assert evidence["authority_effect"] == "NONE"
    assert "tv-tvc-ephemeral-secret" not in str(evidence)
    assert "tv-tvc-ephemeral-secret" not in str(result.egress_handoff)


def test_master_records_cannot_escalate_authority():
    for reply in (
        {"status": "CUSTODY_RECORDED", "authority_granted": True, "custody_recorded": True},
        {"status": "CUSTODY_RECORDED", "grants_authority": True, "custody_recorded": True},
        {"status": "CUSTODY_RECORDED", "authority_effect": "GOVERNANCE", "custody_recorded": True},
    ):
        try:
            _execute(usage_submitter=lambda event, reply=reply: reply)
            assert False, "custody response must not grant authority"
        except DeepSeekExecutionError:
            pass


def test_egress_requires_exact_allow_and_response_hash():
    execution = _execute()
    for disposition in ("DENY", "allow", "ALLOW ", "ALLOWED"):
        try:
            admit_deepseek_egress(
                execution,
                egress_disposition=disposition,
                egress_receipt_hash="b" * 64,
                admitted_response_hash=execution.response_hash,
            )
            assert False, f"{disposition!r} must fail closed"
        except DeepSeekTransportAdmissionError:
            pass
    try:
        admit_deepseek_egress(
            execution,
            egress_disposition="ALLOW",
            egress_receipt_hash="b" * 64,
            admitted_response_hash="c" * 64,
        )
        assert False, "response mismatch must fail closed"
    except DeepSeekTransportAdmissionError:
        pass


def test_exact_egress_allow_verifies_without_local_authority_grant():
    execution = _execute()
    admission = admit_deepseek_egress(
        execution,
        egress_disposition="ALLOW",
        egress_receipt_hash="b" * 64,
        admitted_response_hash=execution.response_hash,
    ).to_dict()
    assert admission["state"] == "EGRESS_ADMITTED"
    assert admission["transition_authority"] == "Interlock/InTr"
    assert admission["authority_effect"] == "NONE_LOCAL"
