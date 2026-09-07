import unittest

from llm_adapter.anthropic_intr_executor import execute_governed_transaction
from llm_adapter.anthropic_intr_transport import (
    CredentialLeak, EgressDecision, EgressRejected, HashBindingMismatch,
    IngressDecision, ProviderRequest, TransportConfig, compute_request_hash,
)


def req():
    d = ProviderRequest("anthropic", "claude-sonnet-5", "anthropic_messages", {"messages": [{"role": "user", "content": "x"}], "max_tokens": 16}, "0" * 64, "tx-a", "s-a")
    return ProviderRequest(d.provider, d.model, d.endpoint_profile, d.payload, compute_request_hash(d), d.transition_id, d.session_id)


class AnthropicAdversarialTests(unittest.TestCase):
    def test_egress_hash_substitution_rejected(self):
        r = req()
        ingress = IngressDecision("ALLOW", r.request_hash, r.transition_id, "a" * 64, "carrier://a")

        def transport(*_):
            return 200, {"id": "msg", "model": r.model, "content": [{"type": "text", "text": "ok"}], "usage": {"input_tokens": 1, "output_tokens": 1}}

        def mr(_):
            return {"accepted": True, "authority_effect": "NONE"}

        def bad_egress(_):
            return EgressDecision("ALLOW", "c" * 64, "b" * 64)

        with self.assertRaises(HashBindingMismatch):
            execute_governed_transaction(provider_request=r, ingress_decision=ingress, config=TransportConfig(), credential_resolver=lambda _: "secret", transport=transport, master_records=mr, egress_resolver=bad_egress)

    def test_provider_echo_of_secret_is_rejected(self):
        r = req()
        ingress = IngressDecision("ALLOW", r.request_hash, r.transition_id, "a" * 64, "carrier://a")

        def transport(*_):
            return 200, {"id": "msg", "model": r.model, "content": [{"type": "text", "text": "secret-value"}], "usage": {"input_tokens": 1, "output_tokens": 1}}

        with self.assertRaises(CredentialLeak):
            execute_governed_transaction(
                provider_request=r,
                ingress_decision=ingress,
                config=TransportConfig(),
                credential_resolver=lambda _: "secret-value",
                transport=transport,
                master_records=lambda _: {"accepted": True, "authority_effect": "NONE"},
                egress_resolver=lambda evidence: EgressDecision("ALLOW", evidence["response_hash"], "b" * 64),
            )


if __name__ == "__main__":
    unittest.main()
