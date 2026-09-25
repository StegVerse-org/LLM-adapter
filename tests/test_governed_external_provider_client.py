from types import SimpleNamespace
from dataclasses import replace

import pytest

from llm_adapter.provider_request import ProviderRequest, ProviderMessage
from llm_adapter.provider_client import ProviderResponse
import llm_adapter.governed_external_provider_client as mod


def test_provider_response_is_returned_only_after_exact_ingress_and_egress(monkeypatch):
    request = ProviderRequest(provider="z.ai", model="glm-5.3-flash", messages=(ProviderMessage(role="user", content="hello"),), temperature=0.0)
    wire_hash = mod.external_wire_request_hash(request)
    order = []

    def ingress(req, exact_hash):
        order.append("ingress")
        assert req is request
        assert exact_hash == wire_hash
        return {"disposition":"ALLOW","request_hash":wire_hash,"transition_id":"tx-1","receipt_hash":"a"*64,"carrier_ref":"hb32:test"}

    def tvc(req, ingress_reply):
        order.append("tvc")
        return {"credential_authority":"TV/TVC","credential_material_present":False,"credential_resolver":lambda:"secret"}

    fake_response = ProviderResponse(provider="z.ai", model="glm-5.3-flash", output="ok", request_hash=wire_hash, metadata={})
    fake_result = SimpleNamespace(execution_path="TV_TVC_RESOLVER_COMPATIBILITY", response_hash=fake_response.response_hash, egress_handoff={"response_hash":fake_response.response_hash}, response=fake_response, execution=SimpleNamespace())

    def execute(*args, **kwargs):
        order.append("provider")
        assert kwargs["ingress_disposition"] == "ALLOW"
        return fake_result

    def egress(handoff):
        order.append("egress")
        assert handoff["response_hash"] == fake_response.response_hash
        return {"disposition":"ALLOW","response_hash":fake_response.response_hash,"receipt_hash":"c"*64}

    def admit(*args, **kwargs):
        order.append("admit")
        assert kwargs["admitted_response_hash"] == fake_response.response_hash
        return object()

    monkeypatch.setattr(mod, "execute_governed_external_llm", execute)
    monkeypatch.setattr(mod, "admit_external_llm_egress", admit)
    client = mod.GovernedExternalProviderClient(session_id="s-1", measurement_id_factory=lambda req:"m-1", ingress_evaluator=ingress, tvc_material_resolver=tvc, egress_evaluator=egress)
    response = client.complete(request)
    assert response.output == "ok"
    assert response.metadata["governed_external_connection"] is True
    assert response.metadata["ingress_intr_admitted"] is True
    assert response.metadata["egress_intr_admitted"] is True
    assert response.metadata["authority_effect"] == "NONE"
    assert order == ["ingress","tvc","provider","egress","admit"]


@pytest.mark.parametrize("provider,canonical,model", [
    ("zai", "z.ai", "glm-5.3-flash"),
    ("deepseek_http", "deepseek", "deepseek-v4-flash"),
    ("moonshot", "kimi", "kimi-k3"),
    ("claude", "anthropic", "claude-opus-5"),
])
def test_existing_provider_aliases_return_envelope_binding_and_wire_provenance(monkeypatch, provider, canonical, model):
    request = ProviderRequest(provider=provider, model=model, messages=(ProviderMessage("user", "hello"),))
    wire = mod.external_wire_request_hash(request)
    response = ProviderResponse(canonical, model, "answer", wire, {"usage_refs": ["existing-usage-ref"]})
    execution = SimpleNamespace(provider_usage_event={"event_sha256": "e" * 64})
    result = SimpleNamespace(response=response, response_hash=response.response_hash,
                             egress_handoff={"response_hash": response.response_hash},
                             execution_path="TVC_NON_EXPORTABLE_RUNTIME", execution=execution)
    monkeypatch.setattr(mod, "execute_governed_external_llm", lambda *a, **kw: result)
    monkeypatch.setattr(mod, "admit_external_llm_egress", lambda *a, **kw: None)
    client = mod.GovernedExternalProviderClient(
        "session", lambda _: "measurement",
        lambda req, digest: {"disposition": "ALLOW", "request_hash": digest, "transition_id": "tx",
                             "receipt_hash": "a" * 64, "carrier_ref": "test-only"},
        lambda *a: {"credential_authority": "TV/TVC", "credential_material_present": False,
                    "lease_receipt": {"fixture_only": True}, "broker_submitter": lambda _: None},
        lambda handoff: {"disposition": "ALLOW", "response_hash": handoff["response_hash"], "receipt_hash": "b" * 64},
    )
    returned = client.complete(request)
    assert returned.provider == provider
    assert returned.request_hash == request.request_hash != wire
    assert returned.metadata["admitted_provider_response_hash"] == response.response_hash
    assert returned.metadata["usage_refs"] == ["existing-usage-ref", "provider-usage-event:" + "e" * 64]


@pytest.mark.parametrize("drift", ["provider", "model", "request_hash", "response_hash"])
def test_wrong_provider_result_is_rejected_before_egress(monkeypatch, drift):
    request = ProviderRequest("z.ai", "glm-5.3-flash", (ProviderMessage("user", "hello"),))
    response = ProviderResponse("z.ai", request.model, "answer", mod.external_wire_request_hash(request), {})
    if drift != "response_hash":
        response = replace(response, **{drift: {"provider": "deepseek", "model": "wrong-model", "request_hash": "0" * 64}[drift]})
    result = SimpleNamespace(response=response, response_hash="0" * 64 if drift == "response_hash" else response.response_hash)
    monkeypatch.setattr(mod, "execute_governed_external_llm", lambda *a, **kw: result)
    def forbidden_egress(*args):
        pytest.fail("invalid provider result reached egress")
    client = mod.GovernedExternalProviderClient(
        "session", lambda _: "measurement",
        lambda req, digest: {"disposition": "ALLOW", "request_hash": digest, "transition_id": "tx",
                             "receipt_hash": "a" * 64, "carrier_ref": "test-only"},
        lambda *a: {"credential_authority": "TV/TVC", "credential_material_present": False,
                    "credential_resolver": lambda: "fixture-only"},
        forbidden_egress,
    )
    with pytest.raises(mod.GovernedExternalProviderClientError, match="mismatch"):
        client.complete(request)
