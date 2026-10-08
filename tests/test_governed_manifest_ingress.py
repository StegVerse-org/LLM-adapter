import unittest

from llm_adapter.governed_manifest_ingress import GovernedStreamSession, _hash, process_manifest


def manifest(output_id="evt-1", return_projection=None):
    payload = {"value": 7}
    candidate = {"action": "evaluate"}
    value = {
        "manifest_profile": "stegverse.ingress-manifest.v1",
        "manifest_profile_version": "1",
        "source_framework": "external.ai",
        "source_output_id": output_id,
        "created_at": "2026-08-12T19:00:00Z",
        "payload": payload,
        "candidate": candidate,
        "declared_intent": "evaluation",
        "requested_consequence": "none",
        "processing": {"capability": "governance", "route_id": "stegverse.route.canonical-governed.v1"},
        "hashes": {"payload_sha256": _hash(payload), "candidate_sha256": _hash(candidate)},
    }
    if return_projection is not None:
        value["return_projection"] = return_projection
    return value


def standing(**overrides):
    """Standing is declared on the crossing, not carried in the manifest.

    The rules it is held to are unchanged -- predecessor present, null means
    explicit generation-1 genesis, an unrecognized endpoint fails closed. Only
    where they are declared has moved, because the SDK's runtime refuses these
    as manifest fields and recognition is a property of the crossing rather
    than of a portable document.
    """
    value = {"node_endpoint": {"node_id": "node-external-ai-1", "recognized": True},
             "generation": 1, "predecessor": None}
    value.update(overrides)
    return value


def allow_handler(_transfer):
    return {
        "governance_state": "ALLOW",
        "governed_result": {"answer": "accepted"},
        "manifest_receipt_id": "MR-0123456789ABCDEF",
        "organization_receipt_observed": True,
        "verification_refs": ["verify:1"],
        "receipt_refs": ["receipt:1"],
        "transition_evidence": [
            {"transition_class": "ingestion", "state": "MANIFEST_ADMITTED"},
            {"transition_class": "governance", "state": "ALLOW"},
        ],
        "consequence_executed": False,
    }


class GovernedManifestIngressTests(unittest.TestCase):
    def test_transfer_reaches_generic_sdk_endpoint_with_manifest_declared_route(self):
        seen = []
        def endpoint(transfer):
            seen.append(transfer)
            return allow_handler(transfer)
        result = process_manifest(manifest(), mode="TEST", standing=standing(), sdk_manifest_endpoint=endpoint)
        self.assertEqual(result["governance_state"], "ALLOW")
        self.assertEqual(seen[0]["protocol"], "InTr")
        self.assertTrue(seen[0]["interlock_required"])
        self.assertEqual(seen[0]["destination"], "DISTRIBUTED_SDK_MANIFEST_ENDPOINT")
        self.assertEqual(seen[0]["requested_processing"]["capability"], "governance")
        self.assertEqual(seen[0]["requested_processing"]["route_id"], "stegverse.route.canonical-governed.v1")
        self.assertFalse(seen[0]["adapter_selects_processing"])
        self.assertFalse(seen[0]["source_identity_selects_processing"])

    def test_source_identity_cannot_select_processing_or_bypass_declared_route(self):
        left = manifest("evt-left")
        right = manifest("evt-right")
        left["source_framework"] = "provider.alpha"
        right["source_framework"] = "provider.beta"
        right["processing"] = {"capability": "analysis", "route_id": "route.analysis.v1"}
        seen = []
        def endpoint(transfer):
            seen.append(transfer["requested_processing"])
            return allow_handler(transfer)
        process_manifest(left, mode="TEST", standing=standing(), sdk_manifest_endpoint=endpoint)
        process_manifest(right, mode="TEST", standing=standing(), sdk_manifest_endpoint=endpoint)
        self.assertEqual(seen[0], left["processing"])
        self.assertEqual(seen[1], right["processing"])


    def test_genesis_requires_present_null_predecessor(self):
        declared = standing()
        declared.pop("predecessor")
        result = process_manifest(manifest(), mode="TEST", standing=declared, sdk_manifest_endpoint=allow_handler)
        self.assertEqual(result["governance_state"], "FAIL_CLOSED")
        self.assertIn("predecessor", result["reason"])

    def test_genesis_standing_is_carried_to_sdk_endpoint(self):
        seen = []
        process_manifest(manifest(), mode="TEST", standing=standing(), sdk_manifest_endpoint=lambda transfer: seen.append(transfer) or allow_handler(transfer))
        self.assertEqual(seen[0]["canonical_node_standing"]["mode"], "ESTABLISH_GENESIS")
        self.assertIsNone(seen[0]["canonical_node_standing"]["predecessor"])

    def test_established_node_requires_validated_predecessor(self):
        declared = standing(generation=2, predecessor={
            "generation": 1,
            "manifest_sha256": "a" * 64,
            "result_sha256": "b" * 64,
            "heartbeat_epoch": 4096,
        })
        seen = []
        result = process_manifest(manifest(), mode="TEST", standing=declared, sdk_manifest_endpoint=lambda transfer: seen.append(transfer) or allow_handler(transfer))
        self.assertEqual(result["governance_state"], "ALLOW")
        self.assertEqual(seen[0]["canonical_node_standing"]["mode"], "VERIFY_EXISTING")
        self.assertEqual(seen[0]["canonical_node_standing"]["predecessor"], declared["predecessor"])

    def test_failed_existing_verification_does_not_reenroll(self):
        seen = []
        result = process_manifest(manifest(), mode="TEST",
                                  standing=standing(generation=2, predecessor=None),
                                  sdk_manifest_endpoint=lambda transfer: seen.append(transfer))
        self.assertEqual(result["governance_state"], "FAIL_CLOSED")
        self.assertEqual(result["reason"], "genesis_requires_generation_one")
        self.assertEqual(seen, [])

    def test_llm_machine_instruction_path_reaches_existing_sdk_transfer(self):
        value = manifest()
        seen = []
        result = process_manifest(value, mode="TEST", standing=standing(), sdk_manifest_endpoint=lambda transfer: seen.append(transfer) or allow_handler(transfer))
        self.assertEqual(result["governance_state"], "ALLOW")
        self.assertEqual(seen[0]["canonical_node_standing"]["mode"], "ESTABLISH_GENESIS")
        self.assertEqual(seen[0]["requested_processing"], value["processing"])
        self.assertEqual(seen[0]["destination"], "DISTRIBUTED_SDK_MANIFEST_ENDPOINT")

    def test_existing_node_instruction_path_reaches_same_sdk_transfer(self):
        value = manifest()
        declared = standing(generation=2, predecessor={
            "generation": 1,
            "manifest_sha256": "c" * 64,
            "result_sha256": "d" * 64,
            "heartbeat_epoch": 7,
        })
        seen = []
        result = process_manifest(value, mode="TEST", standing=declared, sdk_manifest_endpoint=lambda transfer: seen.append(transfer) or allow_handler(transfer))
        self.assertEqual(result["governance_state"], "ALLOW")
        self.assertEqual(seen[0]["canonical_node_standing"]["mode"], "VERIFY_EXISTING")
        self.assertEqual(seen[0]["requested_processing"], value["processing"])
        self.assertEqual(seen[0]["destination"], "DISTRIBUTED_SDK_MANIFEST_ENDPOINT")

    def test_unrecognized_node_fails_closed_before_sdk_endpoint(self):
        declared = standing()
        declared["node_endpoint"]["recognized"] = False
        seen = []
        result = process_manifest(manifest(), mode="TEST", standing=declared,
                                  sdk_manifest_endpoint=lambda transfer: seen.append(transfer))
        self.assertEqual(result["governance_state"], "FAIL_CLOSED")
        self.assertEqual(result["reason"], "recognized_node_endpoint_required")
        self.assertEqual(seen, [])

    def test_test_mode_returns_governed_model_envelope(self):
        result = process_manifest(manifest(), mode="TEST", standing=standing(), sdk_manifest_endpoint=allow_handler)
        self.assertEqual(result["governance_state"], "ALLOW")
        self.assertEqual(result["manifest_receipt_id"], "MR-0123456789ABCDEF")
        self.assertFalse(result["adapter_is_governance_authority"])
        self.assertEqual(result["return_projection"]["mode"], "ALL")

    def test_none_projection_suppresses_only_caller_transition_detail(self):
        result = process_manifest(
            manifest(return_projection={"mode": "NONE"}),
            mode="TEST",
            standing=standing(),
            sdk_manifest_endpoint=allow_handler,
        )
        self.assertEqual(result["governance_state"], "ALLOW")
        self.assertEqual(result["manifest_receipt_id"], "MR-0123456789ABCDEF")
        self.assertEqual(result["transition_evidence"], [])
        self.assertEqual(result["verification_refs"], [])
        self.assertEqual(result["receipt_refs"], [])
        self.assertTrue(result["master_records_transition_custody_independent_of_return_projection"])
        self.assertFalse(result["return_projection"]["suppresses_master_records_organization_record"])

    def test_selected_projection_filters_transition_detail(self):
        result = process_manifest(
            manifest(return_projection={"mode": "SELECTED", "transition_classes": ["governance"]}),
            mode="TEST",
            standing=standing(),
            sdk_manifest_endpoint=allow_handler,
        )
        self.assertEqual(result["transition_evidence"], [
            {"transition_class": "governance", "state": "ALLOW"}
        ])

    def test_invalid_manifest_fails_closed_without_calling_governance(self):
        called = []
        result = process_manifest({}, mode="TEST", standing=standing(), sdk_manifest_endpoint=lambda value: called.append(value))
        self.assertEqual(result["governance_state"], "FAIL_CLOSED")
        self.assertEqual(called, [])

    def test_non_allow_cannot_claim_consequence(self):
        def bad(_manifest):
            return {"governance_state": "DENY", "manifest_receipt_id": "MR-0123456789ABCDEF", "consequence_executed": True}
        result = process_manifest(manifest(), mode="TEST", standing=standing(), sdk_manifest_endpoint=bad)
        self.assertEqual(result["governance_state"], "FAIL_CLOSED")

    def test_live_stream_preserves_order_and_idempotency(self):
        session = GovernedStreamSession("stream-1", allow_handler, standing())
        first = session.process(manifest("evt-1"), sequence=0, idempotency_key="k1")
        duplicate = session.process(manifest("evt-1"), sequence=0, idempotency_key="k1")
        out_of_order = session.process(manifest("evt-3"), sequence=2, idempotency_key="k3")
        second = session.process(manifest("evt-2"), sequence=1, idempotency_key="k2")
        self.assertEqual(first["result_hash"], duplicate["result_hash"])
        self.assertEqual(out_of_order["governance_state"], "FAIL_CLOSED")
        self.assertEqual(second["sequence"], 1)


if __name__ == "__main__":
    unittest.main()
