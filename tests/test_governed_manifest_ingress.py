import ast
from pathlib import Path
import unittest

from stegverse.manifest_builder import build_manifest
from stegverse.manifest_contract import validate_ingress_manifest as sdk_validate_ingress_manifest

from llm_adapter import governed_manifest_ingress
from llm_adapter.governed_manifest_ingress import (
    NON_ALLOW_FIELDS,
    OWNING_EXISTING_GOAL,
    GovernedStreamSession,
    process_manifest,
    validate_ingress_manifest,
)

GOVERNANCE_REQUEST = {
    "candidate": {"action": "evaluate"}, "judgment": {}, "signal": {}, "execution": {},
    "capability": {}, "continuity": {}, "approval": {}, "permission_present": False,
}

DIAGNOSTIC_REQUEST = {
    "schema": "stegverse.ecosystem-diagnostic-request.v1",
    "diagnostic_request_id": "diag-1",
    "scope": "component",
    "mutation_permitted": False,
    "tests": [{"test_id": "t1", "component_id": "llm-adapter", "predicate_id": "p1",
               "authority_owner": "StegVerse-org/LLM-adapter", "observation": None}],
}


def manifest(output_id="evt-1", return_projection=None, process="governance"):
    """A manifest built by the SDK, which is what a caller submits.

    The adapter is not the authority on manifest shape, so its fixtures are
    the SDK builder's output rather than a hand-written approximation of it.
    """
    request = GOVERNANCE_REQUEST if process == "governance" else DIAGNOSTIC_REQUEST
    value = build_manifest(data={"value": 7}, source_framework="external.ai",
                           source_output_id=output_id, processor_request=request,
                           process=process, created_at="2026-08-12T19:00:00Z")
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
        right = manifest("evt-right", process="ecosystem_diagnostic")
        left["source_framework"] = "provider.alpha"
        right["source_framework"] = "provider.beta"
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
        value = manifest()
        # An absent projection defaults to ALL.
        value.pop("return_projection")
        result = process_manifest(value, mode="TEST", standing=standing(), sdk_manifest_endpoint=allow_handler)
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

    def test_sdk_built_non_governance_manifest_passes_adapter_validation(self):
        # F1: the SDK requires a candidate only for governance processing. An
        # SDK-built ecosystem_diagnostic manifest carries none, and the adapter
        # must not refuse what the SDK accepts.
        value = manifest("evt-diag", process="ecosystem_diagnostic")
        self.assertNotIn("candidate", value)
        sdk_validate_ingress_manifest(value)
        canonical = validate_ingress_manifest(value)
        self.assertEqual(canonical["sdk_declared_processing"], {
            "capability": "ecosystem_diagnostic", "route_id": value["processing"]["route_id"]})
        seen = []
        result = process_manifest(value, mode="TEST", standing=standing(),
                                  sdk_manifest_endpoint=lambda transfer: seen.append(transfer) or allow_handler(transfer))
        self.assertEqual(result["governance_state"], "ALLOW")
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]["requested_processing"], value["processing"])
        self.assertEqual(seen[0]["manifest"], {**value, "return_projection": seen[0]["manifest"]["return_projection"]})
        self.assertNotIn("sdk_declared_processing", seen[0]["manifest"])

    def test_sdk_refusal_is_carried_verbatim(self):
        value = manifest()
        value["unexpected_top_level"] = True
        result = process_manifest(value, mode="TEST", standing=standing(), sdk_manifest_endpoint=allow_handler)
        self.assertEqual(result["governance_state"], "FAIL_CLOSED")
        self.assertEqual(result["reason"], "unknown top-level manifest fields: unexpected_top_level")

    def assert_six_fields(self, result):
        for key in NON_ALLOW_FIELDS:
            self.assertIsInstance(result.get(key), str, key)
            self.assertTrue(result[key].strip(), key)
        self.assertEqual(result["owning_existing_goal"], OWNING_EXISTING_GOAL)

    def test_every_non_allow_carries_the_six_standard_fields(self):
        # F2: adapter fail-closed results at every stage.
        unsupported = process_manifest(manifest(), mode="BATCH", standing=standing(), sdk_manifest_endpoint=allow_handler)
        no_standing = process_manifest(manifest(), mode="TEST", standing={}, sdk_manifest_endpoint=allow_handler)
        invalid = process_manifest({}, mode="TEST", standing=standing(), sdk_manifest_endpoint=allow_handler)
        def raises(_transfer):
            raise RuntimeError("binding missing")
        handoff = process_manifest(manifest(), mode="TEST", standing=standing(), sdk_manifest_endpoint=raises)
        no_receipt = process_manifest(manifest(), mode="TEST", standing=standing(),
                                      sdk_manifest_endpoint=lambda _t: {"governance_state": "ALLOW"})
        stages = {
            "INGRESS_MODE_UNSUPPORTED": unsupported,
            "NODE_STANDING_NOT_ESTABLISHED": no_standing,
            "MANIFEST_REFUSED_BY_SDK_CONTRACT": invalid,
            "SDK_RUNTIME_HANDOFF_RAISED": handoff,
            "SDK_RUNTIME_RESULT_NOT_ADMISSIBLE": no_receipt,
        }
        for code, result in stages.items():
            self.assertEqual(result["governance_state"], "FAIL_CLOSED")
            self.assertEqual(result["failure_code"], code)
            self.assertEqual(result["failed_predicate"], result["reason"])
            self.assert_six_fields(result)
        self.assertFalse(handoff["reached_sdk_runtime"])
        self.assertTrue(no_receipt["reached_sdk_runtime"])
        session = GovernedStreamSession("stream-six", allow_handler, standing())
        out_of_order = session.process(manifest("evt-9"), sequence=3, idempotency_key="k9")
        self.assertEqual(out_of_order["failure_code"], "LIVE_STREAM_ORDERING_REFUSED")
        self.assert_six_fields(out_of_order)

    def test_runtime_non_allow_carries_six_fields_preferring_far_side_values(self):
        def deny(_transfer):
            return {"disposition": "DENY", "failure_code": "FAR_SIDE_DENY",
                    "failed_predicate": "far_side_predicate", "consequence_executed": False}
        result = process_manifest(manifest(), mode="TEST", standing=standing(), sdk_manifest_endpoint=deny)
        self.assertEqual(result["governance_state"], "DENY")
        self.assert_six_fields(result)
        self.assertEqual(result["failure_code"], "FAR_SIDE_DENY")
        self.assertEqual(result["failed_predicate"], "far_side_predicate")
        allowed = process_manifest(manifest(), mode="TEST", standing=standing(), sdk_manifest_endpoint=allow_handler)
        for key in NON_ALLOW_FIELDS:
            self.assertNotIn(key, allowed)

    def test_ingress_module_imports_no_master_records_heartbeat_or_socket_module(self):
        # The generic ingress path is transport only: nothing on it waits on
        # Master Records, a heartbeat or a socket receiver.
        tree = ast.parse(Path(governed_manifest_ingress.__file__).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(("." * node.level) + (node.module or ""))
        for name in imported:
            lowered = name.lower()
            self.assertNotIn("master_records", lowered, name)
            self.assertNotIn("heartbeat", lowered, name)
            self.assertNotIn("socket", lowered, name)

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
