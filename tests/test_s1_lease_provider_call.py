import pytest

from llm_adapter import provider_usage_submission
from llm_adapter.anthropic_convergence_bridge import build_anthropic_convergence_envelope
from llm_adapter.anthropic_tvc_broker import RUNTIME_PROFILE_ID as ANTHROPIC_PROFILE
from llm_adapter.openai_intr_transport import build_openai_intr_envelope
from llm_adapter.openai_tvc_broker import RUNTIME_PROFILE_ID as OPENAI_PROFILE
from llm_adapter.provider_request import build_provider_request
from llm_adapter.s1_lease_provider_call import S1LeaseProviderCallError, build_s1_provider_call

INGRESS = dict(ingress_disposition="ALLOW", ingress_receipt_hash="a" * 64, carrier_ref="carrier-1")
EGRESS_RECEIPT = "e" * 64


@pytest.fixture(autouse=True)
def local_usage_ledger_untouched(monkeypatch):
    monkeypatch.setattr(provider_usage_submission, "_persist_event",
                        lambda event, **_: ({**event, "event_sha256": event.get("event_sha256", "f" * 64)}, True))


def _request(provider):
    model = "gpt-fixture" if provider == "openai" else "claude-opus-5"
    return build_provider_request(provider=provider, model=model, messages=[{"role": "user", "content": "hello"}])


def _envelope(provider, req, transition_id="tx-s1"):
    if provider == "openai":
        return build_openai_intr_envelope(req, transition_id=transition_id, **INGRESS)
    return build_anthropic_convergence_envelope(req, session_id="s", transition_id=transition_id, max_tokens=2048, **INGRESS)


def _lease(provider, env):
    return {"decision": "ALLOW_CAPABILITY_LEASE", "provider": provider,
            "operation": "chat_completion_with_usage" if provider == "openai" else "message_with_usage",
            "model": env.model, "transition_id": env.transition_id, "request_hash": env.request_hash,
            "ingress_receipt_hash": env.ingress_receipt_hash, "carrier_ref": env.carrier_ref,
            "runtime_profile_id": OPENAI_PROFILE if provider == "openai" else ANTHROPIC_PROFILE,
            "credential_authority": "TV/TVC", "credential_material_present": False, "second_machine_required": False,
            "single_use": True, "secret_values_exported": False, "protected_values_exposed": False, "authority_granted": False}


def _broker(calls):
    def submit(operation):
        calls.append(operation)
        return {"decision": "ALLOW_OPERATION_RESULT",
                "result": {"output": "ok", "model": "runtime-fixture", "usage": {"input_tokens": 2, "output_tokens": 1,
                           "prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3}},
                "use_receipt": {"secret_material_returned": False, "secret_material_logged": False,
                                "secret_material_retained": False, "single_use_consumed": True}}
    return submit


def _call(provider, *, decision=None, calls=None):
    req = _request(provider)
    env = _envelope(provider, req)
    calls = [] if calls is None else calls
    call = build_s1_provider_call(req, session_id="s", measurement_id="m", lease_receipt=_lease(provider, env),
                                  broker_submitter=_broker(calls),
                                  egress_decider=lambda handoff: decision or {"disposition": "ALLOW", "egress_receipt_hash": EGRESS_RECEIPT},
                                  **INGRESS)
    governed = {"transition_id": "tx-s1", "request_hash": env.request_hash,
                "runtime_profile_id": OPENAI_PROFILE if provider == "openai" else ANTHROPIC_PROFILE}
    return call, governed, calls


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_allow_returns_admitted_egress_records_for_the_named_transition(provider):
    call, governed, calls = _call(provider)
    out = call(governed)
    assert len(calls) == 1
    assert out["egress_handoff"]["transition_id"] == "tx-s1"
    assert out["egress_handoff"]["request_hash"] == governed["request_hash"]
    assert out["egress_handoff"]["runtime_model"] == "runtime-fixture"
    assert out["egress_admission"]["state"] == "EGRESS_ADMITTED"
    assert out["egress_admission"]["transition_authority"] == "Interlock/InTr"
    assert out["egress_admission"]["response_hash"] == out["egress_handoff"]["response_hash"]
    assert out["egress_admission"]["egress_receipt_hash"] == EGRESS_RECEIPT


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
@pytest.mark.parametrize("override,message", [
    ({"request_hash": "f" * 64}, "request_hash does not name this request"),
    ({"runtime_profile_id": "stegverse:runtime-profile:llm-adapter-zai:v1"}, "runtime_profile_id does not name"),
])
def test_lease_naming_another_request_or_route_is_refused_before_any_provider_call(provider, override, message):
    call, governed, calls = _call(provider)
    with pytest.raises(PermissionError, match=message):
        call({**governed, **override})
    assert calls == []


def test_profiles_are_not_interchangeable_between_s1_routes():
    call, governed, calls = _call("openai")
    with pytest.raises(PermissionError):
        call({**governed, "runtime_profile_id": ANTHROPIC_PROFILE})
    assert calls == []


@pytest.mark.parametrize("disposition", ["DENY", "FAIL_CLOSED", None])
def test_non_allow_egress_is_a_refusal(disposition):
    call, governed, calls = _call("openai", decision={"disposition": disposition, "egress_receipt_hash": EGRESS_RECEIPT})
    with pytest.raises(PermissionError, match="egress InTr"):
        call(governed)
    assert len(calls) == 1


def test_malformed_inputs_fail_closed():
    call, governed, _ = _call("openai")
    with pytest.raises(S1LeaseProviderCallError):
        call({**governed, "transition_id": ""})
    with pytest.raises(S1LeaseProviderCallError):
        call(None)
    with pytest.raises(S1LeaseProviderCallError, match="not an S1 governed provider route"):
        build_s1_provider_call(build_provider_request(provider="kimi", model="k", messages=[{"role": "user", "content": "x"}]),
                               session_id="s", measurement_id="m", lease_receipt={}, broker_submitter=lambda _: {},
                               egress_decider=lambda _: {}, **INGRESS)


@pytest.mark.parametrize("field,value", [
    ("transition_id", "tx-other"),
    ("request_hash", "f" * 64),
    ("response_hash", "f" * 64),
])
def test_egress_decision_cannot_name_another_transition_or_response(field, value):
    decision = {"disposition": "ALLOW", "egress_receipt_hash": EGRESS_RECEIPT, field: value}
    call, governed, calls = _call("openai", decision=decision)
    with pytest.raises(PermissionError, match="egress InTr " + field + " binding mismatch"):
        call(governed)
    assert len(calls) == 1
