"""Establishing a healthy node is ingress, and the boundary records it.

These assert the properties that made this worth building: the record exists at
all, it is a property of the crossing rather than of HTTP, a refusal leaves no
entry claiming a node was admitted, and concurrent arrivals do not fork the
chain -- which the unrepaired emitter did, orphaning seven of eight receipts.
"""
from __future__ import annotations

import glob
import importlib.util
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from llm_adapter import node_ingress_boundary, node_standing
from llm_adapter.combined_gateway import app

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "StegVerse-org/LLM-adapter"


def genesis(**overrides):
    body = {"mode": "ESTABLISH_GENESIS", "node_ref": "ingress-test-node",
            "predecessor": None, "node_class": "LLM_ADAPTER"}
    body.update(overrides)
    return body


class IngressBoundaryTests(unittest.TestCase):
    def setUp(self):
        # The ledger is durable state a deployed node uses. A test appending
        # into it writes runtime reality, so each test gets its own root.
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

    def receipts(self):
        return [json.loads(Path(p).read_text())
                for p in glob.glob(os.path.join(self._root.name, "receipts", "*.json"))]

    def register(self, **overrides):
        return self.client.post("/api/node-standing", json=genesis(**overrides))

    def test_registration_records_the_ingress_and_hands_back_its_reference(self):
        """The first receipt of an incoming state transition now exists."""
        body = self.register().json()
        self.assertEqual(body["ingress_recorded_at_boundary"], "LLM_ADAPTER_INGRESS_BOUNDARY")
        self.assertEqual(body["ingress_transition_id"],
                         "NODE_INGRESS_ADMITTED:ingress-test-node")
        self.assertTrue(body["ingress_receipt_sha256"].startswith("sha256:"))
        receipt, = self.receipts()
        self.assertEqual(receipt["receipt_sha256"], body["ingress_receipt_sha256"])
        self.assertEqual(receipt["repository"], REPOSITORY)
        self.assertEqual(receipt["transition_class"], "NODE_INGRESS_ADMITTED")

    def test_the_record_carries_what_makes_this_node_a_node(self):
        body = self.register().json()
        record = self.receipts()[0]["evidence"]
        self.assertEqual(record["node_endpoint"], {"node_id": "ingress-test-node",
                                                   "recognized": True})
        self.assertIs(record["manifest_fields_are_boundary_issued_not_caller_asserted"], True)
        self.assertEqual(record["node_class"], "LLM_ADAPTER")
        self.assertEqual(record["node_standing_mode"], "ESTABLISH_GENESIS")
        self.assertEqual(record["generation"], 1)
        self.assertIsNone(record["predecessor"])
        # What it was told to do next, so the chain shows the instruction given.
        self.assertEqual(record["continuation_profile"], body["continuation_profile"])
        self.assertIs(record["healthy_node_established"], True)
        self.assertEqual(record["node_health_status"], "ok")

    def test_the_record_grants_nothing_and_proves_no_identity(self):
        self.register()
        record = self.receipts()[0]["evidence"]
        self.assertEqual(record["authority_effect"], "NONE_INGRESS_RECORD_ONLY")
        self.assertIs(record["structural_standing_is_authenticated_standing"], False)
        self.assertEqual(record["attestation_owner_state"], "NOT_PROVEN")
        self.assertIs(record["caller_supplied_identity_is_not_authenticated"], True)
        self.assertIs(record["ingress_classification_is_authoritative"], False)

    def test_a_refused_registration_records_nothing(self):
        """A refusal established no node, so the chain carries no entry for one."""
        for refusal in ({"node_class": None}, {"predecessor": "not-a-predecessor"},
                        {"node_ref": ""}):
            with self.subTest(refusal=refusal):
                body = dict(genesis())
                body.update(refusal)
                if refusal.get("node_class") is None:
                    body.pop("node_class")
                response = self.client.post("/api/node-standing", json=body)
                self.assertIn(response.status_code, (403, 422))
        self.assertEqual(self.receipts(), [])

    def test_the_chain_continues_rather_than_forking(self):
        first = self.register().json()
        second = self.register(node_ref="second-node").json()
        self.assertNotEqual(first["ingress_receipt_sha256"], second["ingress_receipt_sha256"])
        by = {receipt["receipt_sha256"]: receipt for receipt in self.receipts()}
        self.assertEqual(len(by), 2)
        self.assertIsNone(by[first["ingress_receipt_sha256"]]["previous_receipt_sha256"])
        self.assertEqual(by[second["ingress_receipt_sha256"]]["previous_receipt_sha256"],
                         first["ingress_receipt_sha256"])

    def test_concurrent_arrivals_do_not_orphan_receipts(self):
        """The defect this ledger had: eight concurrent appends, one reachable."""
        results, errors = [], []

        def register(index):
            try:
                response = self.client.post("/api/node-standing",
                                            json=genesis(node_ref=f"concurrent-{index}"))
                results.append(response.json()["ingress_receipt_sha256"])
            except Exception as exc:  # surfaced below rather than swallowed
                errors.append(exc)

        threads = [threading.Thread(target=register, args=(i,)) for i in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        receipts = self.receipts()
        self.assertEqual(len(receipts), 8)
        # Exactly one genesis, and every receipt reachable from the head.
        genesis_count = sum(1 for r in receipts if r["previous_receipt_sha256"] is None)
        self.assertEqual(genesis_count, 1)
        by = {r["receipt_sha256"]: r for r in receipts}
        head = json.loads((Path(self._root.name) / "HEAD.json").read_text())
        cursor, reachable = head["receipt_sha256"], 0
        while cursor in by:
            reachable += 1
            cursor = by[cursor]["previous_receipt_sha256"]
        self.assertEqual(reachable, 8)

    def test_the_chain_is_ordered_by_the_oscillator_not_a_clock(self):
        self.register()
        receipt = self.receipts()[0]
        self.assertEqual(receipt["ordering"], "OSCILLATOR_HEARTBEAT_EPOCH_ONLY")
        self.assertIs(receipt["observed_at_is_descriptive_not_ordering"], True)
        reference = receipt["hb_reference"]
        self.assertEqual(reference["progression_dependency"], "OSCILLATOR_ONLY")
        self.assertEqual(reference["authority_effect"], "NONE")
        # A reference derived from a clock sample says so rather than passing
        # itself off as a supplied oscillator count.
        self.assertIs(reference["derived_from_clock"], True)
        self.assertIn("sampled_unix_ns", reference)

    def test_a_supplied_epoch_is_reproducible_and_not_marked_derived(self):
        ledger = importlib.util.spec_from_file_location(
            "emit", ROOT / ".stegverse/transition-ledger/emit.py")
        module = importlib.util.module_from_spec(ledger)
        ledger.loader.exec_module(module)
        reference = module.hb_reference(epoch=64)
        self.assertEqual(reference["epoch"], 64)
        self.assertIs(reference["derived_from_clock"], False)
        self.assertNotIn("sampled_unix_ns", reference)
        with self.assertRaises(SystemExit):
            module.hb_reference(epoch=1)  # precedes the declared anchor

    def test_the_heartbeat_is_read_from_the_owners_declaration_not_restated(self):
        ledger = importlib.util.spec_from_file_location(
            "emit", ROOT / ".stegverse/transition-ledger/emit.py")
        module = importlib.util.module_from_spec(ledger)
        ledger.loader.exec_module(module)
        declared = json.loads((ROOT / ".stegverse/heartbeat-awareness.json").read_text())
        self.assertEqual(module.heartbeat_parameters(), declared["heartbeat"])
        self.assertEqual(declared["canonical_owner"], "StegVerse-Labs/.github")


class TransportIsNotTheBoundaryTests(unittest.TestCase):
    """The record is a property of the crossing, so the transport is a field."""

    def test_http_is_installed_and_intr_is_the_next_stage(self):
        self.assertEqual(node_ingress_boundary.transport_state("HTTP"), "INSTALLED")
        self.assertEqual(node_ingress_boundary.transport_state("INTERLOCK_INTR"),
                         "NOT_YET_ENABLED")

    def test_an_unrecognised_transport_fails_closed(self):
        with self.assertRaises(node_standing.StandingRefused) as refused:
            node_ingress_boundary.transport_state("SMOKE_SIGNAL")
        self.assertEqual(refused.exception.disposition, node_standing.FAIL_CLOSED)

    def test_the_same_record_is_produced_whichever_transport_carried_it(self):
        signal = genesis()
        disposition = node_standing.resolve(signal)
        shapes = {}
        for transport in ("HTTP", "INTERLOCK_INTR"):
            record = node_ingress_boundary.ingress_record(
                signal, disposition, "LLM_MACHINE_CONTINUATION", "LLM_ADAPTER",
                transport, {"status": "ok"})
            shapes[transport] = {k: v for k, v in record.items()
                                 if k not in ("transport", "transport_state")}
        self.assertEqual(shapes["HTTP"], shapes["INTERLOCK_INTR"])


if __name__ == "__main__":
    unittest.main()
