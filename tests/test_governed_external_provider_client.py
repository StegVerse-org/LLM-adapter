from types import SimpleNamespace

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
    fake_result = SimpleNamespace(execution_path="TV_TVC_RESOLVER_COMPATIBILITY", response_hash="b"*64, egress_handoff={"response_hash":"b"*64}, response=fake_response)

    def execute(*args, **kwargs):
        order.append("provider")
        assert kwargs["ingress_disposition"] == "ALLOW"
        return fake_result

    def egress(handoff):
        order.append("egress")
        assert handoff["response_hash"] == "b"*64
        return {"disposition":"ALLOW","response_hash":"b"*64,"receipt_hash":"c"*64}

    def admit(*args, **kwargs):
        order.append("admit")
        assert kwargs["admitted_response_hash"] == "b"*64
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
