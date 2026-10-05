"""Every crossing of the SDK boundary is recorded, and claims only what it did.

The four SDK surfaces ran behind standing and recorded nothing, so the chain
began and ended at ingress: a node could discover the contract, build a
manifest and hand it off with no record that any of it happened.

A state transition is the disposition of an intended action, not only a
successful one, so every crossing is a transition and every crossing is
recorded with its disposition. An earlier version of these tests asserted a
second test -- did some store change? -- which marked a contract read and a
refused build as not transitions; that definition is not the one the ecosystem
holds and the assertions here replace it. The same correction applies to a
crossing refused for want of standing: it arrived, so it is recorded, under its
own transition class and naming nothing the boundary did not issue.

Payloads stay out: digests bind the request and result without copying a
caller's arguments into the record.
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


def capability_descriptor(**override):
    value = {
        "capability_id": "text-generate",
        "work_class": "text",
        "input_media": ["text"],
        "output_media": ["text"],
        "provider": "example-provider",
        "model": "example-model",
        "entitlement_state": "ENTITLED",
        "routing_disposition": "AVAILABLE",
        "required_tier": None,
        "execution_constraints": {"ephemeral_surface": True, "network_required": True},
        "evidence_return": "RETAINED_OBSERVATION_REQUIRED",
        "authority_effect": "NONE",
    }
    value.update(override)
    return value


def stegbrowser_arguments():
    return {
        "data": {"probe": True},
        "source_framework": "ecosystem-chat",
        "source_output_id": "capability-routing",
        "processor_request": {
            "schema": "stegbrowser.llm-profile-request.v1",
            "profile": "llm.v1",
            "prompt": "Return marker.",
            "response_marker": "MARKER",
            "provider": "example-provider",
            "model": "example-model",
            "secure_url": "https://example.invalid/ai",
            "journey": {
                "schema": "stegverse.packet-carried-endpoint-receipt-journey/v1",
                "journey_id": "capability-routing",
                "origin_endpoint": "stegverse:ecosystem-chat",
                "ephemeral_endpoint": "stegbrowser:ephemeral:capability-routing",
                "outbound_manifest_sha256": "sha256:" + "a" * 64,
                "return_manifest_sha256": "sha256:" + "c" * 64,
                "return_predecessor_manifest_sha256": "sha256:" + "a" * 64,
            },
            "browser_actions": [
                {"op": "fill", "frame_selector": "iframe", "selector": "#input", "value": "Return marker."},
                {"op": "click", "frame_selector": "iframe", "selector": "#send"},
                {"op": "wait_for", "frame_selector": "iframe", "selector": ".msg.ai .bubble", "state": "visible", "timeout_ms": 120000},
                {"op": "read_text", "frame_selector": "iframe", "selector": ".msg.ai .bubble", "timeout_ms": 120000},
            ],
        },
        "created_at": "2026-10-04T00:00:00Z",
    }


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

    def test_every_crossing_records_the_disposition_of_its_intended_action(self):
        """The disposition is the transition, so every crossing carries one."""
        self.cross("/api/sdk/contract", {})
        self.cross("/api/sdk/manifest/validate", {"manifest": {}})
        self.cross("/api/sdk/manifest/build", {"arguments": arguments()})
        for transition_class, action in (
                ("SDK_CONTRACT_DISCOVERED", "DISCOVER_THE_SDK_CONTRACT"),
                ("SDK_MANIFEST_VALIDATED", "VALIDATE_A_CANONICAL_MANIFEST"),
                ("SDK_MANIFEST_BUILT", "BUILD_A_CANONICAL_MANIFEST")):
            receipt, = self.receipts(transition_class)
            record = receipt["evidence"]
            self.assertEqual(record["intended_action"], action, transition_class)
            self.assertIn(record["disposition"], ("ALLOW", "DENY"), transition_class)
            self.assertIs(record["transition_is_the_disposition_of_the_intended_action"], True)
            # The definition this replaced: a read is still a transition.
            self.assertNotIn("state_changed", record, transition_class)
            self.assertNotIn("surface_can_change_state", record, transition_class)

    def test_a_refused_build_is_a_transition_whose_disposition_is_deny(self):
        """Not an absence. A refused intended action is still a transition."""
        refused = self.cross("/api/sdk/manifest/build", {"arguments": {"data": {"x": 1}}}).json()
        self.assertIs(refused["accepted"], False)
        receipt, = self.receipts("SDK_MANIFEST_BUILT")
        record = receipt["evidence"]
        self.assertIs(record["accepted"], False)
        self.assertEqual(record["disposition"], "DENY")
        self.assertEqual(record["intended_action"], "BUILD_A_CANONICAL_MANIFEST")

    def test_the_correction_round_trip_records_both_transitions(self):
        """A refusal naming what was wrong, then the corrected build: two transitions."""
        self.cross("/api/sdk/manifest/build", {"arguments": {"data": {"x": 1}}})
        self.cross("/api/sdk/manifest/build", {"arguments": arguments()})
        builds = self.receipts("SDK_MANIFEST_BUILT")
        self.assertEqual(len(builds), 2)
        by_digest = {r["receipt_sha256"]: r for r in builds}
        ordered = sorted(builds, key=lambda r: r["previous_receipt_sha256"] is not None)
        dispositions = [r["evidence"]["disposition"] for r in ordered]
        self.assertEqual(sorted(dispositions), ["ALLOW", "DENY"])
        self.assertEqual(len(by_digest), 2)

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

    def test_a_crossing_refused_for_want_of_standing_is_still_recorded(self):
        """The intended action arrived. Its disposition is the transition."""
        response = self.client.post("/api/sdk/contract", json={})
        self.assertEqual(response.status_code, 422)
        receipt, = self.receipts(sdk_boundary.REFUSED_CLASS)
        record = receipt["evidence"]
        self.assertEqual(record["surface"], "CONTRACT")
        self.assertEqual(record["intended_action"], "DISCOVER_THE_SDK_CONTRACT")
        self.assertEqual(record["disposition"], "DENY")
        self.assertIs(record["refused_for_want_of_standing"], True)
        self.assertIs(record["surface_was_run"], False)
        self.assertIn("direct_bypass_without_standing", record["refusal_reason"])
        self.assertIs(record["transition_is_the_disposition_of_the_intended_action"], True)

    def test_the_refused_record_names_no_node_the_boundary_never_issued(self):
        """A record naming an endpoint would read as a crossing that had standing."""
        self.client.post("/api/sdk/manifest/build", json={"arguments": arguments()})
        record = self.receipts(sdk_boundary.REFUSED_CLASS)[0]["evidence"]
        for issued in ("node_endpoint", "generation", "predecessor", "result_sha256"):
            self.assertNotIn(issued, record, issued)
        self.assertEqual(record["attestation_owner_state"], "NOT_PROVEN")

    def test_the_refused_caller_is_handed_its_own_refusal_receipt(self):
        """A refused caller cites its refusal rather than being told nothing happened."""
        detail = self.client.post("/api/sdk/contract", json={}).json()["detail"]
        self.assertEqual(detail["crossing_recorded_at_boundary"], "LLM_ADAPTER_SDK_BOUNDARY")
        self.assertEqual(detail["crossing_transition_class"], sdk_boundary.REFUSED_CLASS)
        receipt, = self.receipts(sdk_boundary.REFUSED_CLASS)
        self.assertEqual(receipt["receipt_sha256"], detail["crossing_receipt_sha256"])
        self.assertEqual(receipt["transition_id"], detail["crossing_transition_id"])

    def test_a_refused_crossing_is_never_recorded_under_an_admitted_class(self):
        """No reader can mistake a refusal for a crossing the boundary let through."""
        self.client.post("/api/sdk/contract", json={})
        self.assertEqual([r["transition_class"] for r in self.receipts()],
                         [sdk_boundary.REFUSED_CLASS])

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

    def test_every_declared_surface_names_a_class_and_an_intended_action(self):
        self.assertEqual(set(sdk_boundary.SURFACES),
                         {"CONTRACT", "MANIFEST_BUILD", "MANIFEST_VALIDATE", "MANIFEST_SUBMIT"})
        for surface, declared in sdk_boundary.SURFACES.items():
            self.assertTrue(declared["transition_class"].startswith("SDK_"), surface)
            self.assertTrue(declared["intended_action"].strip(), surface)
            # No surface declares whether it is "really" a transition. They all are.
            self.assertNotIn("state_changed", declared, surface)

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


class EcosystemChatCapabilityRoutingTests(SdkBoundaryCrossingRecordTests):
    def test_available_text_descriptor_selects_existing_stegbrowser_route(self):
        body = self.cross("/api/sdk/manifest/build", {
            "arguments": stegbrowser_arguments(),
            "capability_descriptor": capability_descriptor(),
        }).json()
        self.assertTrue(body["accepted"])
        self.assertEqual(body["manifest"]["processing"], {
            "capability": "stegbrowser",
            "route_id": "stegverse.route.stegbrowser.v1",
        })
        self.assertEqual(body["capability_selection"]["execution_primitive"],
                         "llm_adapter.external_llm_connection")
        self.assertIs(body["capability_selection"]["fallback_selected"], False)

    def test_upgrade_required_is_recorded_deny_without_provider_execution(self):
        body = self.cross("/api/sdk/manifest/build", {
            "arguments": stegbrowser_arguments(),
            "capability_descriptor": capability_descriptor(
                entitlement_state="NOT_ENTITLED",
                routing_disposition="UPGRADE_REQUIRED",
                required_tier="pro",
            ),
        }).json()
        self.assertFalse(body["accepted"])
        self.assertEqual(body["stage"], "CAPABILITY_ENTITLEMENT")
        self.assertEqual(body["routing_disposition"], "UPGRADE_REQUIRED")
        self.assertIs(body["provider_execution_performed"], False)
        self.assertIs(body["fallback_selected"], False)
        receipt = self.receipts("SDK_MANIFEST_BUILT")[-1]
        self.assertEqual(receipt["evidence"]["disposition"], "DENY")

    def test_purchase_required_is_not_provider_unavailable(self):
        body = self.cross("/api/sdk/manifest/build", {
            "arguments": stegbrowser_arguments(),
            "capability_descriptor": capability_descriptor(
                entitlement_state="NOT_ENTITLED",
                routing_disposition="PURCHASE_REQUIRED",
            ),
        }).json()
        self.assertEqual(body["routing_disposition"], "PURCHASE_REQUIRED")
        self.assertNotEqual(body["routing_disposition"], "PROVIDER_UNAVAILABLE")
        self.assertIs(body["provider_execution_performed"], False)

    def test_unsupported_media_class_does_not_fallback_to_text(self):
        body = self.cross("/api/sdk/manifest/build", {
            "arguments": stegbrowser_arguments(),
            "capability_descriptor": capability_descriptor(
                capability_id="image-generate",
                work_class="image",
                output_media=["image"],
            ),
        }).json()
        self.assertFalse(body["accepted"])
        self.assertEqual(body["stage"], "CAPABILITY_ADAPTER")
        self.assertEqual(body["routing_disposition"], "NO_COMPATIBLE_EXECUTION_ADAPTER")
        self.assertIs(body["fallback_selected"], False)

    def test_provider_mismatch_is_denied_without_substitution(self):
        bad = stegbrowser_arguments()
        bad["processor_request"]["provider"] = "different-provider"
        body = self.cross("/api/sdk/manifest/build", {
            "arguments": bad,
            "capability_descriptor": capability_descriptor(),
        }).json()
        self.assertFalse(body["accepted"])
        self.assertEqual(body["stage"], "CAPABILITY_PROVIDER_MISMATCH")
        self.assertIs(body["fallback_selected"], False)
