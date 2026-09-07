from types import SimpleNamespace
import pytest

import llm_adapter.external_llm_connection as mod

class DummyExecution:
    response_hash = "a" * 64
    egress_handoff = {"requested_disposition": "ALLOW"}
    def evidence(self): return {"authority_effect": "NONE", "egress_intr_required": True}

@pytest.mark.parametrize("name,canonical", [
    ("z.ai","zai"),("zai","zai"),("deepseek","deepseek"),("kimi","kimi"),("moonshot","kimi"),("anthropic","anthropic"),("claude","anthropic")
])
def test_normalize_provider(name, canonical):
    assert mod.normalize_provider(name) == canonical

def test_unknown_provider_fails_closed():
    with pytest.raises(mod.ExternalLLMConnectionError): mod.normalize_provider("unknown")

@pytest.mark.parametrize("provider,target_name", [
    ("z.ai","execute_governed_zai"),("deepseek","execute_governed_deepseek"),("kimi","execute_governed_kimi"),("anthropic","execute_governed_anthropic")
])
def test_compatibility_execution_dispatch(monkeypatch, provider, target_name):
    seen = {}
    def fake(**kwargs): seen.update(kwargs); return DummyExecution()
    monkeypatch.setattr(mod, target_name, fake)
    request = SimpleNamespace(provider=provider)
    result = mod.execute_governed_external_llm(request, session_id="s", transition_id="t", measurement_id="m", ingress_disposition="ALLOW", ingress_receipt_hash="b"*64, carrier_ref="hb32:x", credential_resolver=lambda:"secret")
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
    def fake(**kwargs): seen.update(kwargs); return DummyExecution()
    monkeypatch.setattr(mod, target_name, fake)
    request = SimpleNamespace(provider=provider)
    lease = {"decision":"ALLOW_CAPABILITY_LEASE"}
    broker = lambda operation: {"decision":"ALLOW_OPERATION_RESULT"}
    result = mod.execute_governed_external_llm(request, session_id="s", transition_id="t", measurement_id="m", ingress_disposition="ALLOW", ingress_receipt_hash="b"*64, carrier_ref="hb32:x", lease_receipt=lease, broker_submitter=broker)
    assert result.execution_path == "TVC_NON_EXPORTABLE_RUNTIME"
    assert seen["lease_receipt"] is lease
    assert seen["broker_submitter"] is broker


def test_missing_tvc_material_fails_closed():
    request = SimpleNamespace(provider="z.ai")
    with pytest.raises(mod.ExternalLLMConnectionError):
        mod.execute_governed_external_llm(request, session_id="s", transition_id="t", measurement_id="m", ingress_disposition="ALLOW", ingress_receipt_hash="b"*64, carrier_ref="hb32:x")


def test_compatibility_egress_dispatch(monkeypatch):
    execution = DummyExecution()
    result = mod.GovernedConnectionResult("kimi", execution, "TV_TVC_RESOLVER_COMPATIBILITY")
    sentinel = object()
    monkeypatch.setattr(mod, "admit_kimi_egress", lambda **kwargs: sentinel)
    assert mod.admit_external_llm_egress(result, egress_disposition="ALLOW", egress_receipt_hash="c"*64, admitted_response_hash="a"*64) is sentinel

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
    assert mod.admit_external_llm_egress(result, egress_disposition="ALLOW", egress_receipt_hash="c"*64, admitted_response_hash="a"*64) is sentinel
