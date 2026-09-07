from types import SimpleNamespace
import pytest

import llm_adapter.external_llm_connection as mod
from llm_adapter.provider_request import AIIngressContext, build_provider_request


class DummyExecution:
    response_hash = "a" * 64
    egress_handoff = {"requested_disposition": "ALLOW"}

    def evidence(self):
        return {"authority_effect": "NONE", "egress_intr_required": True}


@pytest.mark.parametrize("name,canonical", [
    ("z.ai","zai"),("zai","zai"),("deepseek","deepseek"),("kimi","kimi"),("moonshot","kimi"),("anthropic","anthropic"),("claude","anthropic"),("openai","openai"),("chatgpt","openai"),("stegverse-local","stegverse-local"),("local-sovereign","stegverse-local")
])
def test_normalize_provider(name, canonical):
    assert mod.normalize_provider(name) == canonical


def test_unknown_provider_fails_closed():
    with pytest.raises(mod.ExternalLLMConnectionError):
        mod.normalize_provider("unknown")


def test_single_adapter_registry_is_compatibility_not_authority():
    registry = mod.adapter_registry()
    assert set(registry) == {"zai", "deepseek", "kimi", "anthropic", "openai", "stegverse-local"}
    for provider, descriptor in registry.items():
        assert descriptor.provider == provider
        assert descriptor.authority_effect == "NONE"
        assert descriptor.confinement_compatible is True
        assert "transport" in descriptor.semantic_capabilities
        assert not any(provider in capability for capability in descriptor.semantic_capabilities)

    for provider in ("zai", "deepseek", "kimi", "anthropic"):
        descriptor = registry[provider]
        assert descriptor.credential_requirement == "TV_TVC_NON_EXPORTABLE"
        assert descriptor.tvc_executor
        assert descriptor.tvc_egress
        assert descriptor.execution_owner == "EXTERNAL_TVC_CONNECTION"

    assert registry["openai"].credential_requirement == "TV_TVC_NON_EXPORTABLE"
    assert registry["openai"].status == "BLOCKED"
    assert registry["openai"].tvc_executor is None
    assert registry["openai"].execution_owner == "TVC_PROVIDER_OPERATION_REQUIRED"

    assert registry["stegverse-local"].credential_requirement == "NONE"
    assert registry["stegverse-local"].execution_owner == "CANONICAL_SOVEREIGN_PROVIDER_CLIENT"
    assert "local_model_inference" in registry["stegverse-local"].semantic_capabilities


def test_adapter_descriptor_aliases_resolve_to_same_record():
    assert mod.adapter_descriptor("moonshot") is mod.adapter_descriptor("kimi")
    assert mod.adapter_descriptor("claude") is mod.adapter_descriptor("anthropic")
    assert mod.adapter_descriptor("chatgpt") is mod.adapter_descriptor("openai")
    assert mod.adapter_descriptor("local-sovereign") is mod.adapter_descriptor("stegverse-local")


def test_blocked_or_non_external_adapter_cannot_enter_external_tvc_dispatch():
    common = dict(
        session_id="s",
        transition_id="t",
        measurement_id="m",
        ingress_disposition="ALLOW",
        ingress_receipt_hash="b" * 64,
        carrier_ref="hb32:x",
        lease_receipt={"decision":"ALLOW_CAPABILITY_LEASE"},
        broker_submitter=lambda operation: {"decision":"ALLOW_OPERATION_RESULT"},
    )
    with pytest.raises(mod.ExternalLLMConnectionError, match="TVC_PROVIDER_OPERATION_REQUIRED"):
        mod.execute_governed_external_llm(SimpleNamespace(provider="openai"), **common)
    with pytest.raises(mod.ExternalLLMConnectionError, match="CANONICAL_SOVEREIGN_PROVIDER_CLIENT"):
        mod.execute_governed_external_llm(SimpleNamespace(provider="stegverse-local"), **common)


def test_universal_ai_ingress_context_keeps_identity_classes_distinct():
    context = AIIngressContext(
        entity_id="UNKNOWN",
        provider_identity="moonshot",
        model_identity="kimi-k3",
        transport_id="transport-123",
        session_id="session-1",
        transition_id="transition-1",
        requested_capabilities=("conversational_inference",),
        network_permissions=("proxy:tvc-provider-operation",),
        filesystem_permissions=(),
        tool_permissions=("semantic:conversational_inference",),
        evidence_requirements=("intr_ingress_receipt", "intr_egress_receipt"),
    )
    request = build_provider_request(
        provider="kimi",
        model="kimi-k3",
        messages=[{"role": "user", "content": "hello"}],
        ingress_context=context,
    )
    serialized = request.to_dict()
    assert serialized["ingress_context"]["entity_id"] == "UNKNOWN"
    assert serialized["ingress_context"]["provider_identity"] == "moonshot"
    assert serialized["ingress_context"]["model_identity"] == "kimi-k3"
    assert serialized["ingress_context"]["authority_declaration"] == "NONE"
    assert serialized["ingress_context"]["failure_mode"] == "FAIL_CLOSED"


def test_legacy_provider_request_shape_is_preserved_without_ingress_context():
    request = build_provider_request(
        provider="zai",
        model="glm-test",
        messages=[{"role": "user", "content": "hello"}],
    )
    assert "ingress_context" not in request.to_dict()


@pytest.mark.parametrize("provider,target_name", [
    ("z.ai","execute_governed_zai"),("deepseek","execute_governed_deepseek"),("kimi","execute_governed_kimi")
])
def test_compatibility_execution_dispatch(monkeypatch, provider, target_name):
    seen = {}

    def fake(**kwargs):
        seen.update(kwargs)
        return DummyExecution()

    monkeypatch.setattr(mod, target_name, fake)
    request = SimpleNamespace(provider=provider)
    result = mod.execute_governed_external_llm(
        request,
        session_id="s",
        transition_id="t",
        measurement_id="m",
        ingress_disposition="ALLOW",
        ingress_receipt_hash="b"*64,
        carrier_ref="hb32:x",
        credential_resolver=lambda:"secret",
    )
    assert result.provider == mod.normalize_provider(provider)
    assert result.execution_path == "TV_TVC_RESOLVER_COMPATIBILITY"
    assert result.authority_effect == "NONE"
    assert result.egress_intr_required is True
    assert seen["ingress_disposition"] == "ALLOW"
    assert seen["credential_resolver"]() == "secret"


@pytest.mark.parametrize("provider,target_name", [
    ("z.ai","execute_governed_zai_via_tvc_runtime"),
    ("deepseek","execute_governed_deepseek_via_tvc_runtime"),
    ("kimi","execute_governed_kimi_via_tvc_runtime"),
    ("anthropic","execute_governed_anthropic_via_tvc_runtime"),
])
def test_tvc_runtime_execution_dispatch(monkeypatch, provider, target_name):
    seen = {}

    def fake(**kwargs):
        seen.update(kwargs)
        return DummyExecution()

    monkeypatch.setattr(mod, target_name, fake)
    request = SimpleNamespace(provider=provider)
    lease = {"decision":"ALLOW_CAPABILITY_LEASE"}
    broker = lambda operation: {"decision":"ALLOW_OPERATION_RESULT"}
    result = mod.execute_governed_external_llm(
        request,
        session_id="s",
        transition_id="t",
        measurement_id="m",
        ingress_disposition="ALLOW",
        ingress_receipt_hash="b"*64,
        carrier_ref="hb32:x",
        lease_receipt=lease,
        broker_submitter=broker,
    )
    assert result.execution_path == "TVC_NON_EXPORTABLE_RUNTIME"
    assert seen["lease_receipt"] is lease
    assert seen["broker_submitter"] is broker


def test_missing_tvc_material_fails_closed():
    request = SimpleNamespace(provider="z.ai")
    with pytest.raises(mod.ExternalLLMConnectionError):
        mod.execute_governed_external_llm(
            request,
            session_id="s",
            transition_id="t",
            measurement_id="m",
            ingress_disposition="ALLOW",
            ingress_receipt_hash="b"*64,
            carrier_ref="hb32:x",
        )


def test_anthropic_rejects_direct_credential_compatibility_path():
    request = SimpleNamespace(provider="anthropic")
    with pytest.raises(mod.ExternalLLMConnectionError, match="canonical TVC non-exportable"):
        mod.execute_governed_external_llm(
            request,
            session_id="s",
            transition_id="t",
            measurement_id="m",
            ingress_disposition="ALLOW",
            ingress_receipt_hash="b"*64,
            carrier_ref="hb32:x",
            credential_resolver=lambda:"secret",
        )


def test_compatibility_egress_dispatch(monkeypatch):
    execution = DummyExecution()
    result = mod.GovernedConnectionResult("kimi", execution, "TV_TVC_RESOLVER_COMPATIBILITY")
    sentinel = object()
    monkeypatch.setattr(mod, "admit_kimi_egress", lambda **kwargs: sentinel)
    assert mod.admit_external_llm_egress(
        result,
        egress_disposition="ALLOW",
        egress_receipt_hash="c"*64,
        admitted_response_hash="a"*64,
    ) is sentinel


@pytest.mark.parametrize("provider,target_name", [
    ("zai","admit_zai_tvc_runtime_egress"),
    ("deepseek","admit_deepseek_tvc_runtime_egress"),
    ("kimi","admit_kimi_tvc_runtime_egress"),
    ("anthropic","admit_anthropic_tvc_runtime_egress"),
])
def test_tvc_egress_dispatch(monkeypatch, provider, target_name):
    execution = DummyExecution()
    result = mod.GovernedConnectionResult(provider, execution, "TVC_NON_EXPORTABLE_RUNTIME")
    sentinel = object()
    monkeypatch.setattr(mod, target_name, lambda **kwargs: sentinel)
    assert mod.admit_external_llm_egress(
        result,
        egress_disposition="ALLOW",
        egress_receipt_hash="c"*64,
        admitted_response_hash="a"*64,
    ) is sentinel
