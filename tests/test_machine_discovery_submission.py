"""Source seam tests; injected receiving results are fixtures, not runtime proof."""
from copy import deepcopy
import unittest

from llm_adapter.machine_instructions import machine_instruction_advertisement
from llm_adapter.governed_manifest_ingress import process_manifest
from stegverse.machine_contract import sdk_machine_contract
from stegverse.manifest_builder import build_manifest
from stegverse.manifest_contract import validate_ingress_manifest
from stegverse.external_framework_runner import prepare_external_framework_manifest


class DiscoverySubmissionTests(unittest.TestCase):
    def request(self):
        # Builder validates shape and hashes, not truth of caller authority claims.
        return {"candidate": {"action": "inspect-source-fixture"}, "judgment": {},
                "signal": {}, "execution": {}, "capability": {}, "continuity": {},
                "approval": {}, "permission_present": False}

    def manifest(self, framework):
        build = prepare_external_framework_manifest if framework else build_manifest
        manifest = build(data={"fixture": True}, source_framework="source-test",
                         source_output_id="discovery-submission", processor_request=self.request(),
                         created_at="2026-10-02T00:00:00Z")
        validate_ingress_manifest(manifest)
        manifest.update(generation=1, predecessor=None,
                        node_endpoint={"node_id": "fixture-node", "recognized": True})
        return manifest

    def test_both_discovery_paths_reach_submission_and_retain_denial(self):
        advertisement = machine_instruction_advertisement()
        self.assertEqual(advertisement["SDK_MACHINE_CONTRACT"], sdk_machine_contract())
        for framework, profile_id in ((False, "LLM_MACHINE_CONTINUATION"),
                                      (True, "EXTERNAL_FRAMEWORK_MANIFEST_CONTINUATION")):
            profile = advertisement["machine_readable_instructions"][profile_id]
            self.assertEqual(profile["steps"][-2:], ["SUBMIT_CANONICAL_MANIFEST", "RETAIN_SUBMISSION_RESULT_AND_EVIDENCE"])
            value = self.manifest(framework)
            before = deepcopy(value)
            seen = []
            def receiver(transfer):
                seen.append(transfer)
                return {"disposition": "DENY", "manifest_receipt_id": "MR-SOURCE-FIXTURE",
                        "verification_refs": ["fixture:denial"], "consequence_executed": False}
            result = process_manifest(value, mode="TEST", sdk_manifest_endpoint=receiver)
            self.assertEqual(len(seen), 1)
            self.assertEqual(seen[0]["requested_processing"], value["processing"])
            self.assertEqual(result["governance_state"], "DENY")
            self.assertEqual(result["verification_refs"], ["fixture:denial"])
            self.assertEqual(value, before)

    def test_missing_standing_prevents_both_paths_from_calling_receiver(self):
        for framework in (False, True):
            value = self.manifest(framework)
            del value["predecessor"]
            seen = []
            result = process_manifest(value, mode="TEST", sdk_manifest_endpoint=lambda t: seen.append(t))
            self.assertEqual(result["governance_state"], "FAIL_CLOSED")
            self.assertEqual(seen, [])

    def test_missing_runtime_binding_is_not_success(self):
        def unavailable(_):
            raise RuntimeError("source fixture: no authentic endpoint binding")
        for framework in (False, True):
            result = process_manifest(self.manifest(framework), mode="TEST", sdk_manifest_endpoint=unavailable)
            self.assertEqual(result["governance_state"], "FAIL_CLOSED")
            self.assertIsNone(result["manifest_receipt_id"])
