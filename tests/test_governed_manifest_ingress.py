import unittest

from llm_adapter.governed_manifest_ingress import GovernedStreamSession, _hash, process_manifest


def manifest(output_id="evt-1"):
    payload = {"value": 7}
    candidate = {"action": "evaluate"}
    return {
        "manifest_profile": "stegverse.ingress-manifest.v1",
        "manifest_profile_version": "1",
        "source_framework": "external.ai",
        "source_output_id": output_id,
        "created_at": "2026-08-12T19:00:00Z",
        "payload": payload,
        "candidate": candidate,
        "declared_intent": "evaluation",
        "requested_consequence": "none",
        "hashes": {"payload_sha256": _hash(payload), "candidate_sha256": _hash(candidate)},
    }


def allow_handler(_manifest):
    return {
        "governance_state": "ALLOW",
        "governed_result": {"answer": "accepted"},
        "manifest_receipt_id": "MR-0123456789ABCDEF",
        "verification_refs": ["verify:1"],
        "receipt_refs": ["receipt:1"],
        "consequence_executed": False,
    }


class GovernedManifestIngressTests(unittest.TestCase):
    def test_test_mode_returns_governed_model_envelope(self):
        result = process_manifest(manifest(), mode="TEST", governance_handler=allow_handler)
        self.assertEqual(result["governance_state"], "ALLOW")
        self.assertEqual(result["manifest_receipt_id"], "MR-0123456789ABCDEF")
        self.assertFalse(result["adapter_is_governance_authority"])

    def test_invalid_manifest_fails_closed_without_calling_governance(self):
        called = []
        result = process_manifest({}, mode="TEST", governance_handler=lambda value: called.append(value))
        self.assertEqual(result["governance_state"], "FAIL_CLOSED")
        self.assertEqual(called, [])

    def test_non_allow_cannot_claim_consequence(self):
        def bad(_manifest):
            return {"governance_state": "DENY", "manifest_receipt_id": "MR-0123456789ABCDEF", "consequence_executed": True}
        result = process_manifest(manifest(), mode="TEST", governance_handler=bad)
        self.assertEqual(result["governance_state"], "FAIL_CLOSED")

    def test_live_stream_preserves_order_and_idempotency(self):
        session = GovernedStreamSession("stream-1", allow_handler)
        first = session.process(manifest("evt-1"), sequence=0, idempotency_key="k1")
        duplicate = session.process(manifest("evt-1"), sequence=0, idempotency_key="k1")
        out_of_order = session.process(manifest("evt-3"), sequence=2, idempotency_key="k3")
        second = session.process(manifest("evt-2"), sequence=1, idempotency_key="k2")
        self.assertEqual(first["result_hash"], duplicate["result_hash"])
        self.assertEqual(out_of_order["governance_state"], "FAIL_CLOSED")
        self.assertEqual(second["sequence"], 1)


if __name__ == "__main__":
    unittest.main()
