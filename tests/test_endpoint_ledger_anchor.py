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
FIXTURES = ROOT / "tests/fixtures/node_receipts"
# Emitted by StegOS's own generation-time code (generate_node_ledger_opened_with_stegos.py).
STEGOS_OPENED = json.loads((FIXTURES / "stegos_node_ledger_opened.json").read_text())


def opened_for(genesis, **overrides):
    """The StegOS record re-targeted at another genesis (or altered) and resealed, for refusal cases."""
    g = genesis["evidence"]
    record = {k: v for k, v in STEGOS_OPENED.items() if k != "receipt_sha256"}
    record.update(node_id=g["node_id"], node_identity_key=g["node_identity_key"], node_kind=g.get("node_kind"),
                  genesis_receipt_sha256=genesis["receipt_sha256"])
    record.update(overrides)
    return {**record, "receipt_sha256": anchor.opened_record_sha256(record)}


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

    def endpoint(self, kind="EPHEMERAL", root=None):
        return {"endpoint_kind": kind, "ledger_root": str(root or self.node)}

    def evaluate(self, endpoint=None, prove=True, **kw):
        endpoint = endpoint or self.endpoint()
        head = kw.pop("head", None) or self.head()
        if prove and "identity_proof" not in kw:
            kw["identity_proof"] = self.prove(endpoint, head)
        return anchor.evaluate_anchored(NODE, endpoint=endpoint, org_ledger_root=self.org,
                                        org_ledger_head_receipt_sha256=head, **kw)

    def prove(self, endpoint=None, head=None, seed=signer.TEST_SEED, **override):
        """The node's identity proof: its key's signature over the current chain-bound challenge."""
        anchored = anchor.verify_anchor(NODE, endpoint=endpoint or self.endpoint(), org_ledger_root=self.org,
                                        org_ledger_head_receipt_sha256=head or self.head())
        if anchored["disposition"] != "ALLOW":
            return None
        challenge = anchor.identity_challenge(anchored)
        proof = {"schema": anchor.IDENTITY_PROOF_SCHEMA, "node_id": NODE, "key_id": KEY["key_id"],
                 "challenge_sha256": anchor.sha(challenge),
                 "signature_b64": signer.sign_b64(anchor.identity_challenge_message(challenge), seed)}
        return {**proof, **override}

    def anchored(self, endpoint):
        return anchor.verify_anchor(NODE, endpoint=endpoint, org_ledger_root=self.org,
                                    org_ledger_head_receipt_sha256=self.head())

    def open_and_anchor(self, kind="EPHEMERAL", key=KEY, root=None, node_kind="StegNode", opened=None):
        root = root or self.node
        out = anchor.open_ledger(root, NODE, kind, key, node_kind if kind == "EPHEMERAL" else None)
        self.assertEqual(out["disposition"], "ALLOW", out)
        if kind == "EPHEMERAL" and opened is None:
            opened = STEGOS_OPENED if out["receipt_sha256"] == STEGOS_OPENED["genesis_receipt_sha256"] \
                else opened_for(out["genesis"])
        return anchor.anchor(root, self.org, NODE, opened)

    def chain_to_admission(self, transport=boundary.INTERLOCK_INTR, installed=True):
        """Receipted registration to admission. E0 harness: the node arrives over InTr, with
        node_ingress_boundary.TRANSPORTS patched to INSTALLED in this scope only (main says NOT_YET_ENABLED)."""
        existence = readback.produce(BROKER, ledger_root=self.root)["receipt_sha256"]
        bound = binding.produce(existence, claim_for(existence), PROFILE, ledger_root=self.root)
        self.assertEqual(bound["disposition"], "ALLOW", bound)
        b = bound["receipt_sha256"]
        check = health.produce(b, OBSERVATION, attestation_for(b), ledger_root=self.root)["receipt_sha256"]
        report = producer.produce(check, ledger_root=self.root)
        self.assertEqual(report["report_status"], "HEALTHY", report)
        signal = {"mode": "ESTABLISH_GENESIS", "node_ref": NODE, "predecessor": None, "node_class": "LLM_ADAPTER"}
        states = {boundary.INTERLOCK_INTR: "INSTALLED"} if installed else {}
        with mock.patch.dict(boundary.TRANSPORTS, states):
            admitted = boundary.admit(signal, transport=transport,
                                      health_report_receipt_sha256=report["health_report_receipt_sha256"])
        if installed:
            self.assertEqual(admitted["disposition"], "ALLOW", admitted)
        return admitted

    def assert_refused(self, out, reason, failure_code=anchor.FAILURE_CODE):
        self.assertEqual(out["disposition"], "FAIL_CLOSED", out)
        self.assertEqual(out["reason"], reason, out)
        self.assertEqual(out["failure_code"], failure_code)
        self.assertIs(out.get("healthy_node_established", False), False)
        for key in SIX:
            self.assertTrue(isinstance(out[key], str) and out[key].strip(), key)


class AnchoredEndToEndTests(_Ledgers):
    def test_ephemeral_node_anchored_by_stegos_node_ledger_opened_reaches_layer1_allow(self):
        pair = self.open_and_anchor()
        genesis = hne.read_chain(self.node)[0][-1]
        # the anchor is the record StegOS emitted at generation, for exactly this genesis
        self.assertEqual(STEGOS_OPENED["emitted_by"], "stegos.ephemeral_node_ledger_open")
        self.assertEqual(STEGOS_OPENED["genesis_receipt_sha256"], genesis["receipt_sha256"])
        self.assertEqual(STEGOS_OPENED["node_identity_key"], KEY)
        self.assertEqual(STEGOS_OPENED["receipt_sha256"], anchor.opened_record_sha256(STEGOS_OPENED))
        self.assertEqual((STEGOS_OPENED["schema"], STEGOS_OPENED["transition_class"]),
                         ("stegverse.node-ledger-opened-generation/v1", "NODE_LEDGER_OPENED"))
        self.chain_to_admission()
        layer1 = self.evaluate()
        self.assertEqual(layer1["disposition"], "ALLOW", layer1)
        self.assertIs(layer1["healthy_node_established"], True)
        self.assertEqual(layer1["anchor"]["anchor"], "NODE_LEDGER_OPENED_VIA_INTR_PATH_RECEIPT_PAIR")
        self.assertEqual(layer1["anchor"]["node_ledger_opened_generation_receipt_sha256"], STEGOS_OPENED["receipt_sha256"])
        self.assertEqual(layer1["identity"]["established_by"], "NODE_IDENTITY_KEY_ED25519_PROOF")
        self.assertEqual(layer1["observed_transport"]["transport"], "INTERLOCK_INTR")
        issued = layer1["anchor"]["node_ledger_opened"]
        self.assertEqual((issued["issuer"], issued["issuer_receipt_ref"]),
                         ("ORGANIZATION_LEDGER", pair["destination_receipt_sha256"]))
        self.assertEqual((layer1["anchor"]["endpoint_kind"], layer1["anchor"]["ledger_lifetime"], layer1["anchor"]["node_kind"]),
                         ("EPHEMERAL", "BOUNDED_UNTIL_DISSOLUTION", "StegNode"))
        self.assertEqual(layer1["anchor"]["anchor_destination_receipt_sha256"], pair["destination_receipt_sha256"])
        classes = [r["transition_class"] for r in reversed(hne.read_chain(self.root)[0])]
        self.assertEqual(classes, ["REPOSITORY_LEDGER_INITIALIZATION", "INTR_MESH_PATH_TRANSFER",
                                   "AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE", "NODE_IDENTITY_BINDING",
                                   "NODE_HEALTH_CHECK_OBSERVED", "NODE_HEALTH_REPORTED", "NODE_INGRESS_ADMITTED"])
        ingress = hne.read_chain(self.org)[0][0]
        self.assertEqual((ingress["transition_class"], ingress["evidence"]["boundary_evidence"]["operation"]),
                         ("INTR_MESH_PATH_INGRESS", "ORGANIZATION_INTR_DESTINATION_INGRESS"))
        self.assertEqual(ingress["evidence"]["message"]["body"], STEGOS_OPENED)

    def test_permanent_kv_and_skap_vault_own_ledgers_reach_layer1_allow(self):
        for kind in ("PERMANENT", "KV", "SKAP_VAULT"):
            with self.subTest(kind=kind):
                self._t2 = tempfile.TemporaryDirectory()
                self.addCleanup(self._t2.cleanup)
                self.use(Path(self._t2.name))
                self.open_and_anchor(kind, root=self.root)
                self.chain_to_admission()
                layer1 = self.evaluate(self.endpoint(kind, self.root))
                self.assertEqual(layer1["disposition"], "ALLOW", layer1)
                self.assertEqual((layer1["anchor"]["anchor"], layer1["anchor"]["ledger_lifetime"]),
                                 ("INTR_PATH_RECEIPT_PAIR", "UNBOUNDED"))

    def test_gateway_node_reaches_layer1_allow_on_its_org_carried_location(self):
        self.assertEqual(anchor.open_gateway_location(self.org, NODE, KEY)["disposition"], "ALLOW")
        self.use(anchor.gateway_root(self.org, NODE))
        self.chain_to_admission()
        layer1 = self.evaluate({"endpoint_kind": "GATEWAY"})
        self.assertEqual(layer1["disposition"], "ALLOW", layer1)
        self.assertEqual(layer1["anchor"]["location"], f"node-ledger/StegVerse-org/{NODE}")
        self.assertFalse((self.org / "source-receipts").exists())
        # the root is derived, never caller-supplied
        self.assert_refused(self.evaluate({"endpoint_kind": "GATEWAY", "ledger_root": str(self.root)}),
                            "ENDPOINT_INVALID")

    def test_the_lc_kv_15_hole_is_closed(self):
        anchor.open_ledger(self.node, NODE, "EPHEMERAL", KEY, "StegNode")   # opened, never anchored
        self.chain_to_admission()
        self.assertEqual(hne.evaluate(NODE, ledger_root=self.node, require_admission=True)["disposition"], "ALLOW")
        self.assert_refused(self.evaluate(), "UNANCHORED")


class AnchorRefusalTests(_Ledgers):
    def test_unanchored_scratch_ledger(self):
        self.chain_to_admission()      # a scratch ledger with no genesis at all
        self.assert_refused(self.evaluate(), "ENDPOINT_GENESIS_INVALID")
        self.assert_refused(self.evaluate(self.endpoint("KV", self.org / "nowhere")), "ENDPOINT_LEDGER_UNREADABLE")

    def test_ephemeral_needs_the_stegos_record(self):
        genesis = anchor.open_ledger(self.node, NODE, "EPHEMERAL", KEY, "StegNode")["genesis"]
        with self.assertRaises(ValueError):
            anchor.anchor(self.node, self.org, NODE)
        source = anchor.append_source(self.node, NODE, anchor.anchor_communication_id(NODE, genesis["receipt_sha256"]),
                                      anchor.anchor_body(genesis))    # a generic body, not NODE_LEDGER_OPENED
        anchor.append_destination(self.org, source)
        self.chain_to_admission()
        self.assert_refused(self.evaluate(), "UNANCHORED")

    def test_unsealed_node_ledger_opened(self):
        genesis = anchor.open_ledger(self.node, NODE, "EPHEMERAL", KEY, "StegNode")["genesis"]
        forged = {**opened_for(genesis), "emitted_at": "SOMEWHERE_ELSE"}     # seal no longer matches
        anchor.anchor(self.node, self.org, NODE, forged)
        self.assert_refused(self.evaluate(), "ANCHOR_LINK_UNVERIFIED")

    def test_mismatched_key_in_the_anchor(self):
        genesis = anchor.open_ledger(self.node, NODE, "EPHEMERAL", KEY, "StegNode")["genesis"]
        anchor.anchor(self.node, self.org, NODE, opened_for(genesis, node_identity_key=OTHER_KEY))
        self.chain_to_admission()
        self.assert_refused(self.evaluate(), "KEY_MISMATCH")

    def test_mismatched_key_in_a_permanent_anchor(self):
        anchor.open_ledger(self.node, NODE, "PERMANENT", KEY)
        genesis = hne.read_chain(self.node)[0][-1]
        body = {**anchor.anchor_body(genesis), "node_identity_key": OTHER_KEY}
        source = anchor.append_source(self.node, NODE, anchor.anchor_communication_id(NODE, genesis["receipt_sha256"]), body)
        anchor.append_destination(self.org, source)
        self.assert_refused(self.evaluate(self.endpoint("PERMANENT")), "KEY_MISMATCH")

    def test_mismatched_key_on_the_chain(self):
        self.open_and_anchor(key=OTHER_KEY)   # anchored consistently, but the node's receipts carry another key
        self.chain_to_admission()
        self.assert_refused(self.evaluate(), "KEY_MISMATCH")

    def test_mismatched_genesis(self):
        self.open_and_anchor()
        other = self.node.parent / "second-node-ledger"
        anchor.open_ledger(other, NODE, "EPHEMERAL", KEY, "StegApp")   # a different genesis, never anchored
        self.use(other)
        self.chain_to_admission()
        self.assert_refused(self.evaluate(self.endpoint(root=other)), "GENESIS_MISMATCH")

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

    def test_org_head_must_be_pinned_and_current(self):
        self.open_and_anchor()
        self.assert_refused(anchor.verify_anchor(NODE, endpoint=self.endpoint(), org_ledger_root=self.org,
                                                 org_ledger_head_receipt_sha256=None), "ORG_LEDGER_HEAD_NOT_PINNED")
        self.assert_refused(self.evaluate(head="sha256:" + "2" * 64), "ORG_LEDGER_HEAD_NOT_PINNED")

    def test_kind_names(self):
        self.assertEqual(anchor.ENDPOINT_KINDS, ("EPHEMERAL", "PERMANENT", "GATEWAY", "KV", "SKAP_VAULT", "ORG"))
        self.assert_refused(self.evaluate({"endpoint_kind": "ORG"}), "ENDPOINT_KIND_NOT_A_NODE_ROOT")
        for bad in ("permanent_node", "gateway_node", "kv", "temporary"):
            self.assert_refused(self.evaluate({"endpoint_kind": bad, "ledger_root": str(self.node)}), "ENDPOINT_INVALID")
        self.assertEqual(anchor.plan_open(NODE, "EPHEMERAL", KEY)["reason"], "ENDPOINT_INVALID")      # node_kind required
        self.assertEqual(anchor.plan_open(NODE, "PERMANENT", KEY, "StegApp")["reason"], "ENDPOINT_INVALID")


class IdentityAndTransportTests(_Ledgers):
    """LC-KV-15 inside the wrapper: identity only from a node_identity_key proof, transport only from receipts."""

    def assert_identity_refused(self, out, reason):
        self.assert_refused(out, reason, anchor.IDENTITY_FAILURE_CODE)

    def assert_transport_refused(self, out):
        self.assert_refused(out, "INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED", "INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED")

    def test_asserted_identity_with_no_proof_is_refused(self):
        self.open_and_anchor()
        self.chain_to_admission()
        self.assert_identity_refused(self.evaluate(prove=False), "NODE_IDENTITY_PROOF_ABSENT")
        asserted = {"node_id": NODE, "node_identity_key": KEY, "source_identity_ref": NODE}
        self.assert_identity_refused(self.evaluate(identity_proof=asserted), "NODE_IDENTITY_PROOF_ABSENT")
        self.assertEqual(self.evaluate()["disposition"], "ALLOW")

    def test_a_proof_must_verify_under_the_anchored_key_over_the_current_challenge(self):
        self.open_and_anchor()
        other_seed = hashlib.sha256(b"endpoint-ledger-anchor tests: another public seed").digest()
        stale = self.prove(self.endpoint())          # signed before the node's receipts were appended
        self.chain_to_admission()
        for name, proof in (("another key's signature", self.prove(seed=other_seed)),
                            ("another key_id", self.prove(key_id="other-test-key")),
                            ("another node", self.prove(node_id="SV-NODE-ffffffffffffffffffffffff")),
                            ("stale chain head", stale),
                            ("garbled signature", self.prove(signature_b64="AAAA"))):
            with self.subTest(name):
                self.assert_identity_refused(self.evaluate(identity_proof=proof), "NODE_IDENTITY_PROOF_INVALID")

    def test_asserted_transport_is_refused(self):
        self.open_and_anchor()
        self.chain_to_admission(transport=boundary.HTTP)     # the boundary records HTTP, not InTr
        out = self.evaluate(transport_state="INSTALLED")
        self.assert_transport_refused(out)
        self.assertEqual((out["asserted_transport_state"], out["asserted_transport_state_decides"]), ("INSTALLED", False))
        self.assertEqual(out["observed_transport"]["transport"], "HTTP")

    def test_transport_unobserved_without_an_installed_intr_ingress(self):
        self.open_and_anchor()
        self.assert_transport_refused(self.evaluate(transport_state="INSTALLED"))     # no ingress record at all
        refused = self.chain_to_admission(installed=False)   # main: INTERLOCK_INTR is NOT_YET_ENABLED
        self.assertEqual(refused["disposition"], "FAIL_CLOSED")
        self.assert_transport_refused(self.evaluate())
        self.assertEqual(boundary.TRANSPORTS[boundary.INTERLOCK_INTR], "NOT_YET_ENABLED")


class IssuedAnchorTests(_Ledgers):
    """The stegverse.node-ledger-opened/v1 anchor KV consumes (continuity-vault-kit#258) and its schemas."""

    def test_issued_anchor_shape_and_organization_ledger_verifier(self):
        pair = self.open_and_anchor()
        self.chain_to_admission()
        issued = self.anchored(self.endpoint())["node_ledger_opened"]
        self.assertEqual(sorted(issued), sorted(anchor.OPENED_ANCHOR_FIELDS))
        self.assertEqual(sorted(anchor.OPENED_ANCHOR_FIELDS), sorted(
            ("schema", "transition_class", "node_id", "node_identity_key", "genesis_receipt_sha256", "issuer",
             "issuer_receipt_ref", "receipt_sha256")))
        self.assertEqual((issued["schema"], issued["transition_class"], issued["genesis_receipt_sha256"]),
                         ("stegverse.node-ledger-opened/v1", "NODE_LEDGER_OPENED", STEGOS_OPENED["genesis_receipt_sha256"]))
        self.assertEqual(issued["issuer_receipt_ref"], pair["destination_receipt_sha256"])
        verify = lambda a: anchor.verify_node_ledger_opened_anchor(   # noqa: E731
            a, ledger_root=self.node, org_ledger_root=self.org, org_ledger_head_receipt_sha256=self.head())
        self.assertEqual(verify(issued)["disposition"], "ALLOW")

        def resealed(**change):
            body = {k: v for k, v in {**issued, **change}.items() if k != "receipt_sha256"}
            return {**body, "receipt_sha256": anchor.opened_record_sha256(body)}
        for name, forged in (("TV/TVC issuer, unverifiable", resealed(issuer="TV/TVC")),
                             ("another issuer receipt", resealed(issuer_receipt_ref="sha256:" + "3" * 64)),
                             ("another genesis", resealed(genesis_receipt_sha256="sha256:" + "4" * 64)),
                             ("unsealed", {**issued, "node_id": "SV-NODE-ffffffffffffffffffffffff"}),
                             ("extra field", resealed(endpoint_kind="EPHEMERAL"))):
            with self.subTest(name):
                self.assert_refused(verify(forged), "NODE_LEDGER_OPENED_ANCHOR_NOT_ISSUED")

    def test_pinned_digests_match_lane_d(self):
        self.open_and_anchor()
        self.assertEqual(self.anchored(self.endpoint())["pinned_digests"], {
            "evaluator_source_sha256": "sha256:fdaa20053c527927067d16b011889ca84089b9750e95e291021310c669451f58",
            "producer_source_sha256": "sha256:21249f2505505afd60eb14188ea638202f2926b207d64cfcf8c3bc5db2d9f361"})

    def test_published_schemas_match_the_code(self):
        opened = json.loads((ROOT / "schemas/node-ledger-opened.v1.json").read_text())
        self.assertEqual(sorted(opened["required"]), sorted(anchor.OPENED_ANCHOR_FIELDS))
        self.assertEqual(sorted(opened["properties"]), sorted(anchor.OPENED_ANCHOR_FIELDS))
        self.assertIs(opened["additionalProperties"], False)
        self.assertEqual(opened["properties"]["schema"]["const"], anchor.OPENED_ANCHOR_SCHEMA)
        self.assertEqual(tuple(opened["properties"]["issuer"]["enum"]), anchor.ANCHOR_ISSUERS)
        generation = json.loads((ROOT / "schemas/node-ledger-opened-generation.v1.json").read_text())
        self.assertEqual(sorted(generation["required"]), sorted(STEGOS_OPENED))
        self.assertEqual(generation["properties"]["schema"]["const"], anchor.GENERATION_SCHEMA)
        kinds = json.loads((ROOT / "schemas/endpoint-kind.v1.json").read_text())
        self.assertEqual(tuple(kinds["$defs"]["endpoint_kind"]["enum"]), anchor.ENDPOINT_KINDS)
        self.assertEqual(kinds["properties"]["schema"]["const"], anchor.ENDPOINT_KIND_SCHEMA)


class DissolutionTests(_Ledgers):
    def dissolve(self, endpoint=None, head=None):
        return dissolution.dissolve(NODE, endpoint=endpoint or self.endpoint(), org_ledger_root=self.org,
                                    org_ledger_head_receipt_sha256=head or self.head(), dissolution_event=EVENT)

    def test_disburse_read_back_then_root_inadmissible(self):
        self.open_and_anchor()
        self.chain_to_admission()
        self.assertEqual(self.evaluate()["disposition"], "ALLOW")
        before = self.head()
        out = self.dissolve()
        self.assertEqual((out["disposition"], out["outcome"], out["read_back"]),
                         ("ALLOW", "DISSOLVED", "FULL_CHAIN_RETAINED"), out)
        node_chain = hne.read_chain(self.node)[0]
        self.assertEqual(out["retained_receipts"], len(node_chain))
        for r in node_chain:   # the full chain is at the destination, verbatim
            self.assertEqual(anchor.read_retained(self.org, r["receipt_sha256"]), r)
        org_chain = hne.read_chain(self.org)[0]
        self.assertEqual([r["transition_class"] for r in org_chain][:2], ["NODE_LEDGER_DISSOLVED", "INTR_MESH_PATH_INGRESS"])
        self.assertEqual(org_chain[0]["evidence"]["node_kind"], "StegNode")
        self.assertIs(org_chain[0]["evidence"]["root_admissible_after"], False)
        self.assert_refused(self.evaluate(), "EPHEMERAL_NODE_LEDGER_DISSOLVED")
        self.assert_refused(self.evaluate(head=before), "ORG_LEDGER_HEAD_NOT_PINNED")
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
        self.assertEqual(self.evaluate()["disposition"], "ALLOW")
        anchor.retain(self.org, next(r for r in hne.read_chain(self.node)[0] if r["receipt_sha256"] == missing))
        self.assertEqual(dissolution.finalize(planned, org_ledger_root=self.org)["outcome"], "DISSOLVED")

    def test_only_ephemeral_dissolves(self):
        for kind in ("PERMANENT", "KV", "SKAP_VAULT"):
            with self.subTest(kind=kind):
                self._t2 = tempfile.TemporaryDirectory()
                self.addCleanup(self._t2.cleanup)
                self.use(Path(self._t2.name))
                self.open_and_anchor(kind, root=self.root)
                self.assert_refused(self.dissolve(self.endpoint(kind, self.root)), "NOT_EPHEMERAL", dissolution.FAILURE_CODE)
                self.assertEqual(self.anchored(self.endpoint(kind, self.root))["disposition"], "ALLOW")
        anchor.open_gateway_location(self.org, NODE, KEY)
        self.assert_refused(self.dissolve({"endpoint_kind": "GATEWAY"}), "NOT_EPHEMERAL", dissolution.FAILURE_CODE)
        self.assertEqual(self.anchored({"endpoint_kind": "GATEWAY"})["disposition"], "ALLOW")

    def test_dissolution_is_an_event_not_a_timer(self):
        self.open_and_anchor()
        self.assert_refused(dissolution.dissolve(NODE, endpoint=self.endpoint(), org_ledger_root=self.org,
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
