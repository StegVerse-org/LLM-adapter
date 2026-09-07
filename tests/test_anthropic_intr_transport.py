import unittest

from llm_adapter.anthropic_intr_transport import (
    ProviderRequest, IngressDecision, TransportConfig, HashBindingMismatch,
    PayloadRejected, build_transport_envelope, compute_request_hash,
    compute_transport_id, map_request_to_anthropic,
)


def request(model="claude-sonnet-5", payload=None):
    payload = payload or {"messages": [{"role": "user", "content": "ping"}], "max_tokens": 32}
    draft = ProviderRequest("anthropic", model, "anthropic_messages", payload, "0" * 64, "tx-1", "session-1")
    return ProviderRequest(draft.provider, draft.model, draft.endpoint_profile, draft.payload, compute_request_hash(draft), draft.transition_id, draft.session_id)


class AnthropicTransportTests(unittest.TestCase):
    def test_request_hash_and_transport_id_are_deterministic(self):
        r = request()
        ingress = IngressDecision("ALLOW", r.request_hash, r.transition_id, "a" * 64, "carrier://test")
        e1 = build_transport_envelope(r, ingress, TransportConfig())
        e2 = build_transport_envelope(r, ingress, TransportConfig())
        self.assertEqual(e1, e2)
        self.assertEqual(e1["transport_id"], compute_transport_id(transition_id="tx-1", request_hash=r.request_hash, ingress_receipt_hash="a" * 64, carrier_ref="carrier://test", endpoint_profile="anthropic_messages"))
        self.assertEqual(e1["authority_effect"], "NONE")
        self.assertTrue(e1["egress_intr_required"])

    def test_ingress_hash_mismatch_fails_closed(self):
        r = request()
        ingress = IngressDecision("ALLOW", "b" * 64, r.transition_id, "a" * 64, "carrier://test")
        with self.assertRaises(HashBindingMismatch):
            build_transport_envelope(r, ingress, TransportConfig())

    def test_claude5_manual_thinking_and_sampling_fail_closed(self):
        p = {"messages": [{"role": "user", "content": "ping"}], "max_tokens": 32, "thinking": {"type": "enabled", "budget_tokens": 10}}
        with self.assertRaises(PayloadRejected):
            map_request_to_anthropic(request(payload=p), TransportConfig())
        p2 = {"messages": [{"role": "user", "content": "ping"}], "max_tokens": 32, "temperature": 0.2}
        with self.assertRaises(PayloadRejected):
            map_request_to_anthropic(request(payload=p2), TransportConfig())

    def test_claude5_assistant_prefill_rejected(self):
        p = {"messages": [{"role": "user", "content": "ping"}, {"role": "assistant", "content": "prefill"}], "max_tokens": 32}
        with self.assertRaises(PayloadRejected):
            map_request_to_anthropic(request(payload=p), TransportConfig())


if __name__ == "__main__":
    unittest.main()
