import unittest

from llm_adapter.anthropic_intr_executor import execute_governed_transaction
from llm_adapter.anthropic_intr_transport import (
    EgressDecision, IngressDecision, ProviderRequest, TransportConfig,
    compute_request_hash,
)


def make_request():
    draft = ProviderRequest(
        "anthropic", "claude-sonnet-5", "anthropic_messages",
        {"messages": [{"role": "user", "content": "ping"}], "max_tokens": 32},
        "0" * 64, "tx-exec", "session-exec",
    )
    return ProviderRequest(draft.provider, draft.model, draft.endpoint_profile, draft.payload, compute_request_hash(draft), draft.transition_id, draft.session_id)


class AnthropicExecutorTests(unittest.TestCase):
    def test_full_offline_transaction_preserves_authority_boundaries(self):
        req = make_request()
        ingress = IngressDecision("ALLOW", req.request_hash, req.transition_id, "a" * 64, "carrier://exec")
        calls = []

        def transport(method, url, headers, body):
            calls.append((method, url, dict(headers), body))
            return 200, {
                "id": "msg_1",
                "model": req.model,
                "content": [{"type": "text", "text": "pong"}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 5, "output_tokens": 2},
            }

        def master_records(handoff):
            self.assertEqual(handoff["authority_effect"], "NONE")
            self.assertFalse(handoff["credential_material_present"])
            return {"accepted": True, "authority_effect": "NONE", "receipt_id": "mr-test"}

        def egress(evidence):
            return EgressDecision("ALLOW", evidence["response_hash"], "b" * 64)

        result = execute_governed_transaction(
            provider_request=req,
            ingress_decision=ingress,
            config=TransportConfig(),
            credential_resolver=lambda _: "test-secret-value",
            transport=transport,
            master_records=master_records,
            egress_resolver=egress,
        )
        self.assertEqual(result.state, "EGRESS_ADMITTED")
        self.assertEqual(result.provider_response["output"], "pong")
        self.assertEqual(result.authority_effect, "NONE")
        self.assertEqual(len(calls), 1)
        durable = str(result.durable_artifacts())
        self.assertNotIn("test-secret-value", durable)


if __name__ == "__main__":
    unittest.main()
