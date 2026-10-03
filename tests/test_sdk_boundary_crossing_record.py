"""Every crossing of the SDK boundary is recorded, and claims only what it did.

The four SDK surfaces ran behind standing and recorded nothing, so the chain
began and ended at ingress: a node could discover the contract, build a
manifest and hand it off with no record that any of it happened.

The properties worth asserting are the ones that make the chain honest. A read
is not a state transition. A refused crossing of a state-changing surface
changed nothing. A refusal is still a crossing, because discovery happens by
being refused and a chain that dropped refusals would show only the attempts
that succeeded. And payloads stay out: digests bind the request and result
without copying a caller's arguments into the record.
"""
from __future__ import annotations

import glob
import json
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from llm_adapter import node_standing, sdk_boundary
from llm_adapter.combined_gateway import app

STANDING = {"mode": "ESTABLISH_GENESIS", "node_ref": "sdk-crossing-node",
            "predecessor": None, "node_class": "LLM_ADAPTER"}


def arguments():
    return {"data": {"probe": True}, "source_framework": "crossing-test",
            "source_output_id": "sdk-boundary-crossing",
            "processor_request": {"candidate": {"action": "inspect"}, "judgment": {},
                                  "signal": {}, "execution": {}, "capability": {},
                                  "continuity": {}, "approval": {},
                                  "permission_present": False},
            "created_at": "2026-10-03T00:00:00Z"}


class SdkBoundaryCrossingRecordTests(unittest.TestCase):
    def setUp(self):
        self._root = tempfile.TemporaryDirectory()
        self._previous = os.environ.get("STEGVERSE_REPO_LEDGER_ROOT")
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = self._root.name
        self.addCleanup(self._restore)
        self.client = TestClient(app)

    def _restore(self):
        if self._previous is None:
            os.environ.pop("STEGVERSE_REPO_LEDGER_ROOT", None)
        else:
            os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = self._previous
        self._root.cleanup()

    def receipts(self, transition_class=None):
        found = [json.loads(Path(p).read_text())
                 for p in glob.glob(os.path.join(self._root.name, "receipts", "*.json"))]
        if transition_class is not None:
            found = [r for r in found if r["transition_class"] == transition_class]
        return found

    def cross(self, path, body):
        return self.client.post(path, json={"standing": STANDING, **body})

    def test_every_surface_records_its_crossing(self):
        self.cross("/api/sdk/contract", {})
        self.cross("/api/sdk/manifest/build", {"arguments": arguments()})
        self.cross("/api/sdk/manifest/validate", {"manifest": {}})
        recorded = {r["transition_class"] for r in self.receipts()}
        self.assertEqual(recorded, {"SDK_CONTRACT_DISCOVERED", "SDK_MANIFEST_BUILT",
                                    "SDK_MANIFEST_VALIDATED"})

    def test_the_caller_is_handed_the_crossing_reference(self):
        body = self.cross("/api/sdk/contract", {}).json()
        self.assertEqual(body["crossing_recorded_at_boundary"], "LLM_ADAPTER_SDK_BOUNDARY")
        self.assertTrue(body["crossing_receipt_sha256"].startswith("sha256:"))
        self.assertEqual(body["crossing_transition_id"],
                         "SDK_CONTRACT_DISCOVERED:sdk-crossing-node")
        receipt, = self.receipts("SDK_CONTRACT_DISCOVERED")
        self.assertEqual(receipt["receipt_sha256"], body["crossing_receipt_sha256"])

    def test_a_read_is_not_recorded_as_a_state_transition(self):
        """The contract is the SDK's declaration and validation is side-effect free."""
        self.cross("/api/sdk/contract", {})
        self.cross("/api/sdk/manifest/validate", {"manifest": {}})
        for transition_class in ("SDK_CONTRACT_DISCOVERED", "SDK_MANIFEST_VALIDATED"):
            receipt, = self.receipts(transition_class)
            record = receipt["evidence"]
            self.assertIs(record["state_changed"], False, transition_class)
            self.assertIs(record["surface_can_change_state"], False, transition_class)
            self.assertIs(record["surface_is_side_effect_free"], True, transition_class)

    def test_a_refused_crossing_of_a_state_changing_surface_changed_nothing(self):
        """A build that was refused produced no manifest."""
        refused = self.cross("/api/sdk/manifest/build", {"arguments": {"data": {"x": 1}}}).json()
        self.assertIs(refused["accepted"], False)
        receipt, = self.receipts("SDK_MANIFEST_BUILT")
        record = receipt["evidence"]
        self.assertIs(record["accepted"], False)
        self.assertIs(record["state_changed"], False)
        # The surface's declared capability and what this crossing did are
        # different claims, and both are kept.
        self.assertIs(record["surface_can_change_state"], True)

    def test_an_accepted_build_did_change_state(self):
        built = self.cross("/api/sdk/manifest/build", {"arguments": arguments()}).json()
        self.assertIs(built["accepted"], True)
        record = self.receipts("SDK_MANIFEST_BUILT")[0]["evidence"]
        self.assertIs(record["accepted"], True)
        self.assertIs(record["state_changed"], True)

    def test_a_refusal_is_still_a_crossing(self):
        """Discovery happens by being refused; a chain that dropped those lies."""
        refused = self.cross("/api/sdk/manifest/build", {"arguments": {"data": {"x": 1}}}).json()
        receipt, = self.receipts("SDK_MANIFEST_BUILT")
        record = receipt["evidence"]
        # Whichever layer refused is the SDK's to say, so the record carries the
        # stage the response carried rather than a stage named here.
        self.assertEqual(record["refusal_stage"], refused["stage"])
        self.assertTrue(record["refusal_stage"])
        self.assertIs(record["sdk_refusal_is_verbatim"], True)

    def test_an_accepted_crossing_records_no_refusal_stage(self):
        self.cross("/api/sdk/manifest/build", {"arguments": arguments()})
        record = self.receipts("SDK_MANIFEST_BUILT")[0]["evidence"]
        self.assertIsNone(record["refusal_stage"])

    def test_no_standing_records_nothing(self):
        """Refused for want of standing leaves no entry claiming it happened."""
        response = self.client.post("/api/sdk/contract", json={})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.receipts(), [])

    def test_the_record_carries_digests_rather_than_payloads(self):
        self.cross("/api/sdk/manifest/build", {"arguments": arguments()})
        record = self.receipts("SDK_MANIFEST_BUILT")[0]["evidence"]
        self.assertTrue(record["request_sha256"].startswith("sha256:"))
        self.assertTrue(record["result_sha256"].startswith("sha256:"))
        rendered = json.dumps(record)
        self.assertNotIn("crossing-test", rendered)
        self.assertNotIn("probe", rendered)

    def test_the_record_identifies_the_node_and_proves_no_identity(self):
        self.cross("/api/sdk/contract", {})
        record = self.receipts("SDK_CONTRACT_DISCOVERED")[0]["evidence"]
        self.assertEqual(record["node_endpoint"],
                         {"node_id": "sdk-crossing-node", "recognized": True})
        self.assertEqual(record["generation"], 1)
        self.assertIsNone(record["predecessor"])
        self.assertIs(record["structural_standing_is_authenticated_standing"], False)
        self.assertEqual(record["attestation_owner_state"], "NOT_PROVEN")
        self.assertEqual(record["authority_effect"], "NONE_CROSSING_RECORD_ONLY")

    def test_the_crossings_chain_in_the_order_they_happened(self):
        self.cross("/api/sdk/contract", {})
        self.cross("/api/sdk/manifest/build", {"arguments": arguments()})
        self.cross("/api/sdk/manifest/validate", {"manifest": {}})
        by = {r["receipt_sha256"]: r for r in self.receipts()}
        head = json.loads((Path(self._root.name) / "HEAD.json").read_text())["receipt_sha256"]
        order, cursor = [], head
        while cursor in by:
            order.append(by[cursor]["transition_class"])
            cursor = by[cursor]["previous_receipt_sha256"]
        order.reverse()
        self.assertEqual(order, ["SDK_CONTRACT_DISCOVERED", "SDK_MANIFEST_BUILT",
                                 "SDK_MANIFEST_VALIDATED"])


class SurfaceTableTests(unittest.TestCase):
    """One seam records every surface, so a surface cannot be added unrecorded."""

    def test_every_declared_surface_names_a_class_and_a_state_claim(self):
        self.assertEqual(set(sdk_boundary.SURFACES),
                         {"CONTRACT", "MANIFEST_BUILD", "MANIFEST_VALIDATE", "MANIFEST_SUBMIT"})
        for surface, declared in sdk_boundary.SURFACES.items():
            self.assertTrue(declared["transition_class"].startswith("SDK_"), surface)
            self.assertIsInstance(declared["state_changed"], bool, surface)

    def test_submit_is_recorded_as_a_handoff_not_a_completion(self):
        """A receipt reading SUBMITTED would imply the transition completed here."""
        self.assertEqual(sdk_boundary.SURFACES["MANIFEST_SUBMIT"]["transition_class"],
                         "SDK_MANIFEST_HANDED_OFF")

    def test_an_unrecorded_surface_cannot_be_recorded(self):
        standing = node_standing.resolve(STANDING)
        with self.assertRaises(ValueError) as refused:
            sdk_boundary.record("SOMETHING_NEW", standing, {}, {})
        self.assertIn("unrecorded SDK boundary surface", str(refused.exception))


if __name__ == "__main__":
    unittest.main()
