from types import SimpleNamespace
import pytest

from llm_adapter.provider_request import ProviderRequest, ProviderMessage
import llm_adapter.anthropic_intr_transport as mod


def request():
    return ProviderRequest(provider="anthropic", model="claude-opus-5", messages=(ProviderMessage(role="user", content="hello"),), temperature=0.2)


def test_envelope_requires_ingress_allow():
    with pytest.raises(mod.AnthropicTransportAdmissionError):
        mod.build_anthropic_intr_envelope(request(), transition_id="t", ingress_disposition="DENY", ingress_receipt_hash="a"*64, carrier_ref="hb32:x")


def test_envelope_binds_exact_wire_hash():
    env = mod.build_anthropic_intr_envelope(request(), transition_id="t", ingress_disposition="ALLOW", ingress_receipt_hash="a"*64, carrier_ref="hb32:x")
    assert env.protocol_version == "stegverse.intr.anthropic.transport.v1"
    assert env.request_hash == mod.anthropic_wire_request_hash(request())
    assert env.credential_authority == "TV/TVC"
    assert env.authority_effect == "NONE"
    assert env.egress_intr_required is True


def test_system_message_is_separated_from_conversation():
    req = ProviderRequest(provider="anthropic", model="claude-opus-5", messages=(ProviderMessage(role="system", content="sys"), ProviderMessage(role="user", content="hello")), temperature=0.1)
    payload = mod.anthropic_wire_payload(req)
    assert payload["system"] == "sys"
    assert payload["messages"] == [{"role":"user","content":"hello"}]
