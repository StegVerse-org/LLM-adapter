from types import SimpleNamespace

import pytest

import llm_adapter.universal_ai_ingress as mod
from llm_adapter.provider_request import build_provider_request


def request(provider="z.ai", *, purpose="answer", allowed_sources=("model_knowledge",), temperature=0.0):
    return build_provider_request(
        provider=provider,
        model="test-model",
        messages=[{"role": "user", "content": "hello"}],
        purpose=purpose,
        allowed_sources=allowed_sources,
        temperature=temperature,
    )


def envelope(provider="z.ai", **kwargs):
    return mod.AIIngressEnvelope(
        request=request(provider, **kwargs),
        session_id="session-1",
        transition_id="transition-1",
        measurement_id="measurement-1",
        ingress_disposition="ALLOW",
        ingress_receipt_hash="a" * 64,
        carrier_ref="hb:test",
    )


@pytest.mark.parametrize(
    "provider,adapter_id",
    [
        ("z.ai", "ai-adapter:zai"),
        ("deepseek", "ai-adapter:deepseek"),
        ("moonshot", "ai-adapter:kimi"),
        ("claude", "ai-adapter:anthropic"),
        ("openai", "ai-adapter:openai"),
        ("openai-compatible", "ai-adapter:openai-compatible"),
        ("resident", "ai-adapter:sovereign-local"),
        ("browser", "ai-adapter:browser-session"),
    ],
)
def test_registry_resolves_one_canonical_owner(provider, adapter_id):
    assert mod.resolve_ai_adapter(provider).adapter_id == adapter_id


def test_unknown_provider_fails_closed():
    with pytest.raises(mod.UnsupportedAIIngressRoute):
        mod.resolve_ai_adapter("future-provider-without-contract")


def test_registry_duplicate_owner_audit_passes():
    result = mod.audit_ai_adapter_registry()
    assert result["pass"] is True
    assert result["duplicates"] == {}
    assert result["forbidden_authority_effect"] == []


def test_registry_audit_detects_duplicate_alias():
    first = mod.AIAdapterContract(
        "one",
        "one",
        ("shared",),
        "provider_http",
        "owner-one",
        mod.HOSTED_API,
        False,
    )
    second = mod.AIAdapterContract(
        "two",
        "two",
        ("shared",),
        "provider_http",
        "owner-two",
        mod.HOSTED_API,
        False,
    )
    result = mod.audit_ai_adapter_registry((first, second))
    assert result["pass"] is False
    assert result["duplicates"]["shared"] == ["one", "two"]


def test_ingress_requires_intr_allow():
    env = mod.AIIngressEnvelope(
        request=request("z.ai"),
        session_id="s",
        transition_id="t",
        measurement_id="m",
        ingress_disposition="DENY",
        ingress_receipt_hash="a" * 64,
        carrier_ref="hb:test",
    )
    with pytest.raises(mod.AIIngressError, match="admitted Interlock/InTr ingress"):
        env.validate()


def test_ingress_confinement_fails_closed_on_purpose_source_and_temperature():
    with pytest.raises(mod.AIIngressError, match="purpose"):
        envelope("z.ai", purpose="trade").validate()
    with pytest.raises(mod.AIIngressError, match="source"):
        envelope("z.ai", allowed_sources=("private_unadmitted_source",)).validate()
    with pytest.raises(mod.AIIngressError, match="temperature"):
        envelope("z.ai", temperature=1.1).validate()


def test_route_directive_is_not_runtime_proof():
    directive = mod.route_ai_ingress(envelope("resident"))
    payload = directive.to_dict()
    assert directive.adapter.execution_owner == "StegVerse-002/micro-node-runtime"
    assert directive.execution_supported_here is False
    assert payload["connected"] is False
    assert payload["runtime_proof"] is False
    assert payload["authority_effect"] == "NONE"


def test_registered_non_external_owner_cannot_execute_here():
    with pytest.raises(mod.UnsupportedAIIngressRoute, match="not executable"):
        mod.execute_ai_ingress(envelope("browser"))


def test_existing_external_dispatch_is_reused(monkeypatch):
    seen = {}
    sentinel = SimpleNamespace(response_hash="b" * 64)

    def fake(request_obj, **kwargs):
        seen["request"] = request_obj
        seen.update(kwargs)
        return sentinel

    monkeypatch.setattr(mod, "execute_governed_external_llm", fake)
    env = envelope("z.ai")
    result = mod.execute_ai_ingress(
        env,
        credential_resolver=lambda: "secret",
        endpoint_profile="general",
    )
    assert result is sentinel
    assert seen["request"] is env.request
    assert seen["transition_id"] == env.transition_id
    assert seen["ingress_receipt_hash"] == env.ingress_receipt_hash
    assert seen["endpoint_profile"] == "general"


def test_existing_external_egress_is_reused(monkeypatch):
    sentinel = object()
    seen = {}

    def fake(result, **kwargs):
        seen["result"] = result
        seen.update(kwargs)
        return sentinel

    monkeypatch.setattr(mod, "admit_external_llm_egress", fake)
    execution = SimpleNamespace()
    assert (
        mod.admit_ai_egress(
            execution,
            egress_disposition="ALLOW",
            egress_receipt_hash="c" * 64,
            admitted_response_hash="d" * 64,
        )
        is sentinel
    )
    assert seen["result"] is execution
    assert seen["egress_disposition"] == "ALLOW"


def test_ingress_hash_is_deterministic_for_same_envelope():
    env = envelope("deepseek")
    assert env.ingress_hash == env.ingress_hash
    assert len(env.ingress_hash) == 64
