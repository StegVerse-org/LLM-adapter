"""Anchored endpoint ledgers (LC-KV-13) and their dissolution (NODE-LEDGER-DISSOLUTION-DISBURSEMENT-001).

Every ledger here is a temporary directory, the "org ledger" included: the real
organization ledger is never read or written, and nothing is dispatched.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from llm_adapter import endpoint_ledger_anchor as anchor
from llm_adapter import healthy_node_evaluator as hne
from llm_adapter import node_existence_readback as readback
from llm_adapter import node_health_check_projection as health
from llm_adapter import node_health_report_producer as producer
from llm_adapter import node_identity_binding_producer as binding
from llm_adapter import node_ingress_boundary as boundary
from llm_adapter import node_ledger_dissolution as dissolution
from tests import ed25519_test_signer as signer
from tests.test_node_receipt_producers import BROKER, NODE, OBSERVATION, PROFILE, attestation_for, claim_for

ROOT = Path(__file__).resolve().parents[1]
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
KEY = PROFILE["node_identity_key"]
OTHER_KEY = {**KEY, "key_id": "other-test-key", "public_key_b64": __import__("base64").b64encode(
    signer.public_key(hashlib.sha256(b"endpoint-ledger-anchor tests: another public seed").digest())).decode()}
EVENT = {"event": "NODE_DISSOLUTION", "node_id": NODE}


class _Ledgers(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        base = Path(self._t.name)
        self.org = base / "org-ledger" / "repository-ledger" / "StegVerse-org" / "LLM-adapter"
        self.node = base / "node-ledger"
        anchor.append_receipt(self.org, anchor.GENESIS_CLASS, "REPOSITORY_LEDGER_INITIALIZATION:test-fixture",
                              anchor.sha({"repository": anchor.REPOSITORY, "ledger": None}),
                              {"schema": "stegverse.repository-ledger-initialization/v1", "repository": anchor.REPOSITORY,
                               "authority_effect": "NONE_TEST_FIXTURE"}, 32)
        previous = os.environ.get("STEGVERSE_REPO_LEDGER_ROOT")

        def restore():
            if previous is None:
                os.environ.pop("STEGVERSE_REPO_LEDGER_ROOT", None)
            else:
                os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = previous
            self._t.cleanup()
        self.addCleanup(restore)
        self.use(self.node)

    def use(self, root):
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = str(root)
        self.root = Path(root)

    def head(self, root=None):
        return json.loads(((root or self.org) / "HEAD.json").read_text())["receipt_sha256"]

    def endpoint(self, kind="permanent_node", root=None):
        return {"endpoint_kind": kind, "ledger_root": str(root or self.node)}

    def evaluate(self, endpoint=None, **kw):
        return anchor.evaluate_anchored(NODE, endpoint=endpoint or self.endpoint(), org_ledger_root=self.org,
                                        org_ledger_head_receipt_sha256=kw.pop("head", None) or self.head(), **kw)

    def open_and_anchor(self, kind="permanent_node", key=KEY, lifetime=anchor.BOUNDED, root=None):
        root = root or self.node
        out = anchor.open_ledger(root, NODE, kind, key, lifetime)
        self.assertEqual(out["disposition"], "ALLOW", out)
        return anchor.anchor(root, self.org, NODE)

    def chain_to_admission(self):
        existence = readback.produce(BROKER, ledger_root=self.root)["receipt_sha256"]
        bound = binding.produce(existence, claim_for(existence), PROFILE, ledger_root=self.root)
        self.assertEqual(bound["disposition"], "ALLOW", bound)
        b = bound["receipt_sha256"]
        check = health.produce(b, OBSERVATION, attestation_for(b), ledger_root=self.root)["receipt_sha256"]
        report = producer.produce(check, ledger_root=self.root)
        self.assertEqual(report["report_status"], "HEALTHY", report)
        signal = {"mode": "ESTABLISH_GENESIS", "node_ref": NODE, "predecessor": None, "node_class": "LLM_ADAPTER"}
        admitted = boundary.admit(signal, health_report_receipt_sha256=report["health_report_receipt_sha256"])
        self.assertEqual(admitted["disposition"], "ALLOW", admitted)

    def assert_refused(self, out, reason, failure_code=anchor.FAILURE_CODE):
        self.assertEqual(out["disposition"], "FAIL_CLOSED", out)
        self.assertEqual(out["reason"], reason, out)
        self.assertEqual(out["failure_code"], failure_code)
        self.assertIs(out.get("healthy_node_established", False), False)
        for key in SIX:
            self.assertTrue(isinstance(out[key], str) and out[key].strip(), key)


class AnchoredEndToEndTests(_Ledgers):
    def test_own_ledger_anchored_reaches_layer1_allow(self):
        for kind in ("permanent_node", "kv", "skap_vault"):
            with self.subTest(kind=kind):
                self._t2 = tempfile.TemporaryDirectory()
                self.addCleanup(self._t2.cleanup)
                self.use(Path(self._t2.name))
                pair = self.open_and_anchor(kind, root=self.root)
                self.chain_to_admission()
                layer1 = self.evaluate(self.endpoint(kind, self.root), require_admission=True)
                self.assertEqual(layer1["disposition"], "ALLOW", layer1)
                self.assertIs(layer1["healthy_node_established"], True)
                self.assertEqual(layer1["anchor"]["anchor"], "INTR_PATH_RECEIPT_PAIR")
                self.assertEqual(layer1["anchor"]["anchor_destination_receipt_sha256"], pair["destination_receipt_sha256"])
                classes = [r["transition_class"] for r in reversed(hne.read_chain(self.root)[0])]
                self.assertEqual(classes, ["REPOSITORY_LEDGER_INITIALIZATION", "INTR_MESH_PATH_TRANSFER",
                                           "AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE", "NODE_IDENTITY_BINDING",
                                           "NODE_HEALTH_CHECK_OBSERVED", "NODE_HEALTH_REPORTED", "NODE_INGRESS_ADMITTED"])
                org_classes = [r["transition_class"] for r in hne.read_chain(self.org)[0]]
                self.assertEqual(org_classes[0], "INTR_MESH_PATH_INGRESS")

    def test_gateway_node_reaches_layer1_allow_on_its_org_carried_location(self):
        self.assertEqual(anchor.open_gateway_location(self.org, NODE, KEY)["disposition"], "ALLOW")
        self.use(anchor.gateway_root(self.org, NODE))
        self.chain_to_admission()
        layer1 = self.evaluate({"endpoint_kind": "gateway_node"}, require_admission=True)
        self.assertEqual(layer1["disposition"], "ALLOW", layer1)
        self.assertEqual(layer1["anchor"]["location"], f"node-ledger/StegVerse-org/{NODE}")
        self.assertFalse((self.org / "source-receipts").exists())
        # the root is derived, never caller-supplied
        self.assert_refused(self.evaluate({"endpoint_kind": "gateway_node", "ledger_root": str(self.root)}),
                            "ENDPOINT_INVALID")

    def test_the_lc_kv_15_hole_is_closed(self):
        anchor.open_ledger(self.node, NODE, "permanent_node", KEY)   # opened, never anchored
        self.chain_to_admission()
        self.assertEqual(hne.evaluate(NODE, ledger_root=self.node, require_admission=True)["disposition"], "ALLOW")
        self.assert_refused(self.evaluate(require_admission=True), "UNANCHORED")


class AnchorRefusalTests(_Ledgers):
    def test_unanchored_scratch_ledger(self):
        self.chain_to_admission()      # a scratch ledger with no genesis at all
        self.assert_refused(self.evaluate(require_admission=True), "ENDPOINT_GENESIS_INVALID")
        self.assert_refused(self.evaluate(self.endpoint("kv", self.org / "nowhere")), "ENDPOINT_LEDGER_UNREADABLE")

    def test_mismatched_key_in_the_anchor(self):
        anchor.open_ledger(self.node, NODE, "permanent_node", KEY)
        genesis = hne.read_chain(self.node)[0][-1]
        body = {**anchor.anchor_body(genesis), "node_identity_key": OTHER_KEY}
        source = anchor.append_source(self.node, NODE, anchor.anchor_communication_id(NODE, genesis["receipt_sha256"]), body)
        anchor.append_destination(self.org, source)
        self.chain_to_admission()
        self.assert_refused(self.evaluate(require_admission=True), "KEY_MISMATCH")

    def test_mismatched_key_on_the_chain(self):
        self.open_and_anchor(key=OTHER_KEY)   # anchored consistently, but the node's receipts carry another key
        self.chain_to_admission()
        self.assert_refused(self.evaluate(require_admission=True), "KEY_MISMATCH")

    def test_mismatched_genesis(self):
        self.open_and_anchor()
        other = self.node.parent / "second-node-ledger"
        anchor.open_ledger(other, NODE, "permanent_node", KEY, anchor.UNBOUNDED)   # different genesis, not anchored
        self.use(other)
        self.chain_to_admission()
        self.assert_refused(self.evaluate(self.endpoint(root=other), require_admission=True), "GENESIS_MISMATCH")

    def test_foreign_producer_receipts(self):
        emit = anchor._emitter()
        for name, cls, evidence in (
                ("forged report", "NODE_HEALTH_REPORTED", {"schema": hne.HEALTH_REPORT_SCHEMA, "node_id": NODE,
                                                           "status": "HEALTHY"}),
                ("unknown class", "NODE_HEALTH_SELF_DECLARED", {"node_id": NODE, "status": "HEALTHY"})):
            with self.subTest(name):
                self._t2 = tempfile.TemporaryDirectory()
                self.addCleanup(self._t2.cleanup)
                self.use(Path(self._t2.name))
                self.open_and_anchor(root=self.root)
                self.chain_to_admission()
                emit.append(f"{cls}:{NODE}:forged", cls, "sha256:" + "0" * 64, hne.sha(evidence), evidence, "NONE",
                            hb_epoch=10**12)
                if cls == "NODE_HEALTH_REPORTED":   # the bare evaluator would take it as current
                    self.assertEqual(hne.evaluate(NODE, ledger_root=self.root)["disposition"], "ALLOW")
                self.assert_refused(self.evaluate(self.endpoint(root=self.root)), "FOREIGN_PRODUCER_RECEIPT")

    def test_report_that_does_not_re_derive_is_foreign(self):
        self.open_and_anchor()
        self.chain_to_admission()
        chain = hne.read_chain(self.node)[0]
        report = next(r for r in chain if r["transition_class"] == "NODE_HEALTH_REPORTED")
        forged = copy.deepcopy(report["evidence"])
        forged["observed_health_check_status"] = "UNHEALTHY"
        anchor._emitter().append("NODE_HEALTH_REPORTED:" + NODE + ":again", "NODE_HEALTH_REPORTED",
                                 report["receipt_sha256"], hne.sha(forged), forged, "NONE", hb_epoch=10**12)
        self.assert_refused(self.evaluate(), "FOREIGN_PRODUCER_RECEIPT")

    def test_pinned_code_digests(self):
        self.open_and_anchor()
        self.chain_to_admission()
        pins = anchor.load_pins()
        tampered = {**pins, "digests": {**pins["digests"], "llm_adapter/node_health_report_producer.py": "sha256:" + "1" * 64}}
        with mock.patch.object(anchor, "load_pins", return_value=tampered):
            self.assert_refused(self.evaluate(), "PINNED_CODE_DIGEST_MISMATCH")
        self.assertEqual(pins["digests"]["llm_adapter/healthy_node_evaluator.py"], anchor.EVALUATOR_SHA256)
        self.assertEqual("sha256:" + hashlib.sha256((ROOT / "llm_adapter/healthy_node_evaluator.py").read_bytes()).hexdigest(),
                         "sha256:fdaa20053c527927067d16b011889ca84089b9750e95e291021310c669451f58")

    def test_org_head_must_be_pinned_and_current(self):
        self.open_and_anchor()
        self.assert_refused(anchor.verify_anchor(NODE, endpoint=self.endpoint(), org_ledger_root=self.org,
                                                 org_ledger_head_receipt_sha256=None), "ORG_LEDGER_HEAD_NOT_PINNED")
        self.assert_refused(self.evaluate(head="sha256:" + "2" * 64), "ORG_LEDGER_HEAD_NOT_PINNED")

    def test_org_kind_is_not_a_node_root(self):
        self.assert_refused(self.evaluate({"endpoint_kind": "org"}), "ENDPOINT_KIND_NOT_A_NODE_ROOT")


class DissolutionTests(_Ledgers):
    def dissolve(self, endpoint=None, head=None):
        return dissolution.dissolve(NODE, endpoint=endpoint or self.endpoint(), org_ledger_root=self.org,
                                    org_ledger_head_receipt_sha256=head or self.head(), dissolution_event=EVENT)

    def test_disburse_read_back_then_root_inadmissible(self):
        self.open_and_anchor()
        self.chain_to_admission()
        self.assertEqual(self.evaluate(require_admission=True)["disposition"], "ALLOW")
        before = self.head()
        out = self.dissolve()
        self.assertEqual((out["disposition"], out["outcome"], out["read_back"]),
                         ("ALLOW", "DISSOLVED", "FULL_CHAIN_RETAINED"), out)
        node_chain = hne.read_chain(self.node)[0]
        self.assertEqual(out["retained_receipts"], len(node_chain))
        for r in node_chain:   # the full chain is at the destination, verbatim
            self.assertEqual(anchor.read_retained(self.org, r["receipt_sha256"]), r)
        org_classes = [r["transition_class"] for r in hne.read_chain(self.org)[0]]
        self.assertEqual(org_classes[:2], ["NODE_LEDGER_DISSOLVED", "INTR_MESH_PATH_INGRESS"])
        self.assert_refused(self.evaluate(require_admission=True), "TEMP_NODE_LEDGER_DISSOLVED")
        self.assert_refused(self.evaluate(require_admission=True, head=before), "ORG_LEDGER_HEAD_NOT_PINNED")
        self.assertEqual(self.dissolve()["reason"], "ENDPOINT_NOT_ANCHORED")

    def test_disbursement_not_read_back_fails_closed(self):
        self.open_and_anchor()
        self.chain_to_admission()
        planned = dissolution.plan(NODE, endpoint=self.endpoint(), org_ledger_root=self.org,
                                   org_ledger_head_receipt_sha256=self.head(), dissolution_event=EVENT)
        self.assertEqual(planned["disposition"], "ALLOW", planned)
        self.assert_refused(dissolution.finalize(planned, org_ledger_root=self.org),
                            "DISBURSEMENT_RECEIPT_NOT_READ_BACK", dissolution.FAILURE_CODE)
        dissolution.disburse(planned, org_ledger_root=self.org)
        missing = planned["disbursement_body"]["receipt_sha256s"][3]
        (self.org / "source-receipts" / (missing[7:] + ".json")).unlink()
        out = dissolution.finalize(planned, org_ledger_root=self.org)
        self.assert_refused(out, "DISBURSED_CHAIN_INCOMPLETE", dissolution.FAILURE_CODE)
        self.assertIs(out["dissolved"], False)
        org_classes = [r["transition_class"] for r in hne.read_chain(self.org)[0]]
        self.assertNotIn("NODE_LEDGER_DISSOLVED", org_classes)
        # not stranded: the ledger is still anchored and admissible until a read-back succeeds
        self.assertEqual(self.evaluate(require_admission=True)["disposition"], "ALLOW")
        anchor.retain(self.org, next(r for r in hne.read_chain(self.node)[0] if r["receipt_sha256"] == missing))
        self.assertEqual(dissolution.finalize(planned, org_ledger_root=self.org)["outcome"], "DISSOLVED")

    def test_gateway_dissolution_closes_the_location_without_import(self):
        anchor.open_gateway_location(self.org, NODE, KEY)
        self.use(anchor.gateway_root(self.org, NODE))
        self.chain_to_admission()
        out = self.dissolve({"endpoint_kind": "gateway_node"})
        self.assertEqual((out["disposition"], out["read_back"]), ("ALLOW", "LOCATION_CLOSED"), out)
        self.assertFalse((self.org / "source-receipts").exists())
        self.assert_refused(self.evaluate({"endpoint_kind": "gateway_node"}), "TEMP_NODE_LEDGER_DISSOLVED")

    def test_unbounded_and_bad_events_do_not_dissolve(self):
        self.open_and_anchor("kv", lifetime=anchor.UNBOUNDED)
        self.assert_refused(self.dissolve(self.endpoint("kv")), "LIFETIME_NOT_BOUNDED", dissolution.FAILURE_CODE)
        self.assert_refused(dissolution.dissolve(NODE, endpoint=self.endpoint("kv"), org_ledger_root=self.org,
                                                 org_ledger_head_receipt_sha256=self.head(),
                                                 dissolution_event={"event": "TIMER"}),
                            "DISSOLUTION_EVENT_INVALID", dissolution.FAILURE_CODE)


class DeterminismTests(unittest.TestCase):
    def test_no_clock_network_or_randomness(self):
        banned = {"datetime", "time", "random", "secrets", "socket", "urllib", "http", "requests", "httpx", "uuid",
                  "subprocess"}
        for name in ("llm_adapter/endpoint_ledger_anchor.py", "llm_adapter/node_ledger_dissolution.py"):
            tree = ast.parse((ROOT / name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                    for n in names:
                        self.assertNotIn(n.split(".")[0], banned, f"{name} imports {n}")

    def test_evaluator_is_untouched(self):
        digest = hashlib.sha256((ROOT / "llm_adapter/healthy_node_evaluator.py").read_bytes()).hexdigest()
        self.assertEqual(digest, "fdaa20053c527927067d16b011889ca84089b9750e95e291021310c669451f58")


if __name__ == "__main__":
    unittest.main()
