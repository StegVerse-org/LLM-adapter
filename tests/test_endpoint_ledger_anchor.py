"""Anchored endpoint ledgers (LC-KV-13) and their dissolution (NODE-LEDGER-DISSOLUTION-DISBURSEMENT-001).

Every ledger here is a temporary directory, the "org ledger" included: the real
organization ledger is never read or written, and nothing is dispatched. The org
ledger is published to refs/stegverse/organization-ledger of a scratch git object
store, the location #431's contract designates (LC-KV-16).

E0 harness, in scope only: the contract carries #431's repository_ledger_location
(fixture copy of #431's contract.json) with a TEST genesis pin in the field #431's
REPOSITORY_LEDGER_GENESIS_PIN transition writes in production
(contract_with_431_location_and_pinned_genesis.json), and the NODE_LEDGER_OPENED
signer list holds a TEST-ONLY public key (tests/ed25519_test_signer.py seed).
Production has none of these yet.

LC-KV-16 rev 5: the org-ledger head attester is NOT patched in setUp. Each test_
method runs inside tests/org_ledger_harness.append_route() (a TEST-ONLY stand-in for
the admitted append route, @with_append_route); anything that drives setUp() and the
helpers directly gets production: FAIL_CLOSED MERGE_APPEND_PATH_NOT_ADMITTED.

Run: python -m pip install -e '.[dev]' (pyproject pins stegverse-sdk, which
node_standing imports), then python -m unittest tests.test_endpoint_ledger_anchor.
"""
from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import json
import os
import shutil
import subprocess
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
from llm_adapter import org_ledger_location as location
from tests import ed25519_test_signer as signer
from tests import org_ledger_harness as harness
from llm_adapter import intr_transport_carrier as carrier
from llm_adapter import endpoint_ledger_designation as eld
from llm_adapter import supplied_epoch
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
CONTRACT_431 = FIXTURES / "contract_with_431_repository_ledger_location.json"     # #431's contract.json, genesis pin null
CONTRACT_PINNED = harness.CONTRACT_PINNED
DESIGNATIONS = ROOT / "tests/fixtures/endpoint-ledger-designation"
KV_DESIGNATION = {kind: json.loads((DESIGNATIONS / f"{name}.designation.json").read_text())
                  for kind, name in (("KV", "kv"), ("SKAP_VAULT", "skap"))}
BOTH_ENDPOINT_CODES = ("ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE", "ENDPOINT_ORG_MEMBERSHIP_REFUSED")
# TEST-ONLY NODE_LEDGER_OPENED signer (a public seed; TV/TVC custody holds real keys).
ISSUER_SEED = hashlib.sha256(b"endpoint-ledger-anchor tests: NODE_LEDGER_OPENED signer public seed").digest()
ISSUER_REF = {"key_id": "test-node-ledger-opened-signer", "algorithm": "Ed25519", "custody": "TV/TVC",
              "signs": "NODE_LEDGER_OPENED",
              "public_key_b64": __import__("base64").b64encode(signer.public_key(ISSUER_SEED)).decode()}
GIT_ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": "/nonexistent", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@invalid", "GIT_AUTHOR_DATE": "1700000000 +0000",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@invalid",
           "GIT_COMMITTER_DATE": "1700000000 +0000"}


PRODUCTION_LOAD_OPENED_SIGNERS = anchor.load_opened_signers


def sign_opened(record, seed=ISSUER_SEED, key_id=ISSUER_REF["key_id"]):
    """The custody signer's step, done here with the TEST-ONLY seed."""
    return anchor.signed_opened(record, {"algorithm": "Ed25519", "key_id": key_id,
                                         "signature_b64": signer.sign_b64(anchor.opened_signing_message(record), seed)})


def git(git_dir, *args, env=None, input=None):
    return subprocess.run(["git", "--git-dir", str(git_dir), *args], check=True, capture_output=True,
                          env={**GIT_ENV, **(env or {})}, input=input).stdout.decode().strip()


def opened_for(genesis, **overrides):
    """The StegOS record re-targeted at another genesis (or altered) and resealed, for refusal cases."""
    g = genesis["evidence"]
    record = {k: v for k, v in STEGOS_OPENED.items() if k != "receipt_sha256"}
    record.update(node_id=g["node_id"], node_identity_key=g["node_identity_key"], node_kind=g.get("node_kind"),
                  genesis_receipt_sha256=genesis["receipt_sha256"])
    record.update(overrides)
    return {**record, "receipt_sha256": anchor.opened_record_sha256(record)}


NODE_DESIGNATION = json.loads((ROOT / "tests/fixtures/endpoint-ledger-designation/node.designation.json").read_text())


@contextlib.contextmanager
def node_reader_stub(designation, store, source, head_attestation):
    """TEST-ONLY stand-in for a NODE_STORAGE_ENDPOINT access adapter (none is documented or admitted): it reads the
    read-back root it is handed. Production has no reader (NODE_STORAGE_ENDPOINT_READER_NOT_DOCUMENTED)."""
    chain, failure, detail = hne.read_chain(Path(source)) if source else (None, "NO_SOURCE", "")
    yield (None, ("ENDPOINT_LEDGER_UNREADABLE", f"{failure}: {detail}")) if failure else (chain, None)


def node_designated(root, node_id=None):
    """The node's own designation (node.designation.json, #431's fixture) for the ledger at `root`, and its own
    recorded head (the watermark)."""
    node_id = node_id or NODE
    chain = hne.read_chain(Path(root))[0] if (Path(root) / "HEAD.json").exists() else []
    designation = {**NODE_DESIGNATION, "endpoint_id": node_id,
                   "expected_genesis_receipt_sha256": chain[-1]["receipt_sha256"] if chain else None,
                   "rollback_watermark_source": {**NODE_DESIGNATION["rollback_watermark_source"],
                                                 "org_crossing_cross_check": {
                                                     **NODE_DESIGNATION["rollback_watermark_source"][
                                                         "org_crossing_cross_check"],
                                                     "path_ids": [anchor.path_id(node_id)]}}}
    recorded_head = {"source": eld.NODE_WATERMARK_SOURCE,
                     "head_receipt_sha256": chain[0]["receipt_sha256"] if chain else None}
    return {"designation": designation, "recorded_head": recorded_head}


class _Ledgers(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        base = Path(self._t.name)
        self.org = base / "org-ledger" / "repository-ledger" / "StegVerse-org" / "LLM-adapter"
        self.node = base / "node-ledger"
        self.tree = base / "org-ledger"                 # the ref's tree; self.org is its #431 namespace
        self.git = base / "org-object-store.git"
        subprocess.run(["git", "init", "-q", "--bare", str(self.git)], check=True, env=GIT_ENV)
        for patcher in (mock.patch.object(location, "CONTRACT_PATH", CONTRACT_PINNED),
                        mock.patch.object(anchor, "load_opened_signers", return_value=[dict(ISSUER_REF)]),
                        mock.patch.dict(eld._READERS, {eld.NODE_STORAGE_ENDPOINT: node_reader_stub})):
            patcher.start()
            self.addCleanup(patcher.stop)
        harness.write_genesis(self.org)      # the genesis the contract fixture pins
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
        root = root or self.node
        if kind != "PERMANENT":
            return {"endpoint_kind": kind, "ledger_root": str(root)}
        return {"endpoint_kind": kind, "ledger_root": str(root), **node_designated(root)}

    def publish(self, tree=None, git_dir=None):
        """Publish the org-ledger tree to refs/stegverse/organization-ledger (a scratch object store)."""
        git_dir = git_dir or self.git
        index = {"GIT_INDEX_FILE": str(Path(self._t.name) / "publish.index")}
        work = ["--work-tree", str(tree or self.tree)]
        git(git_dir, *work, "add", "-A", ".", env=index)
        commit = git(git_dir, "commit-tree", git(git_dir, *work, "write-tree", env=index), "-m", "org ledger fixture")
        git(git_dir, "update-ref", "refs/stegverse/organization-ledger", commit)

    def evaluate(self, endpoint=None, prove=True, publish=True, git_dir=None, **kw):
        endpoint = endpoint or self.endpoint()
        head = kw.pop("head", None) or self.head()
        kw.pop("require_admission", None)       # evaluate_anchored always requires admission
        if prove and "identity_proof" not in kw:
            kw["identity_proof"] = self.prove(endpoint, head)
        if publish:
            self.publish()
        if "org_ledger_head_attestation" not in kw:
            kw["org_ledger_head_attestation"] = self.attest(git_dir)
        return anchor.evaluate_anchored(endpoint=endpoint, org_ledger_git_dir=git_dir or self.git,
                                        org_ledger_head_receipt_sha256=head, **kw)

    def attest(self, git_dir=None):
        """Inside append_route(), the route attests the store it published (self.git) and nothing else."""
        if git_dir not in (None, self.git) or not location.load_head_signers():
            return None
        try:
            return harness.attest(self.git)
        except subprocess.CalledProcessError:
            return None

    def carry(self, signal, communication_id="node-ingress-1"):
        """The InTr path pair that carried `signal` to the boundary: the sender's own INTR_MESH_PATH_TRANSFER on the
        sender's own ledger (this node's ledger once it is open; another sender's ledger otherwise), and the Org's
        digest-only destination half on the org ledger. Nothing is retained on the org ledger."""
        own = signal.get("node_ref") == NODE and (self.root / "HEAD.json").exists()
        sender = self.root if own else Path(self._t.name) / f"intr-source-ledger-{signal.get('node_ref')}"
        chain = hne.read_chain(sender)[0] if (sender / "HEAD.json").exists() else []
        prev = chain[0]["receipt_sha256"] if chain else anchor.sha(None)
        source = anchor.append_receipt(sender, carrier.SOURCE_CLASS, f"{carrier.SOURCE_CLASS}:{communication_id}",
                                       prev, carrier.source_evidence(signal, communication_id),
                                       anchor.epoch_of(chain) if chain else 40)
        return anchor.append_receipt(self.org, carrier.DESTINATION_CLASS,
                                     f"{carrier.DESTINATION_CLASS}:{communication_id}", self.head(),
                                     carrier.destination_evidence(source), 40)

    def prove(self, endpoint=None, head=None, seed=signer.TEST_SEED, **override):
        """The node's identity proof: its key's signature over the current chain-bound challenge.

        When the ledger is not anchored there is no challenge; the proof still names the node so that the
        anchor refusal, not a missing proof, is what the wrapper reports."""
        anchored = anchor.verify_anchor(NODE, endpoint=endpoint or self.endpoint(), org_ledger_root=self.org,
                                        org_ledger_head_receipt_sha256=head or self.head())
        if anchored["disposition"] != "ALLOW":
            return {"schema": anchor.IDENTITY_PROOF_SCHEMA, "node_id": NODE, "key_id": KEY["key_id"],
                    "challenge_sha256": "sha256:" + "0" * 64, "signature_b64": "", **override}
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
            opened = sign_opened(STEGOS_OPENED if out["receipt_sha256"] == STEGOS_OPENED["genesis_receipt_sha256"]
                                 else opened_for(out["genesis"]))
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
        if installed and transport == boundary.INTERLOCK_INTR:
            self.carried = self.carry(signal)     # the pair that carried it, on the org ledger after the anchor
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


@harness.with_append_route
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
                                   "NODE_HEALTH_CHECK_OBSERVED", "NODE_HEALTH_REPORTED",
                                   # the node's own egress record of the ingress signal (the carrier's source half)
                                   "INTR_MESH_PATH_TRANSFER", "NODE_INGRESS_ADMITTED"])
        ingress = next(r for r in hne.read_chain(self.org)[0]
                       if r["receipt_sha256"] == pair["destination_receipt_sha256"])
        self.assertEqual((ingress["transition_class"], ingress["evidence"]["boundary_evidence"]["operation"]),
                         ("INTR_MESH_PATH_INGRESS", "ORGANIZATION_INTR_DESTINATION_INGRESS"))
        # rule (1): the Org's side is digest-only; the NODE_LEDGER_OPENED body is on the node's own chain only
        self.assertEqual(set(ingress["evidence"]), eld.ORG_CROSSING_EVIDENCE_KEYS)
        self.assertIsNone(eld.org_crossing_receipt_failure(ingress, {"endpoint_id": NODE}))
        self.assertIsNone(supplied_epoch.record_epoch_failure(ingress))
        # Q-PERMANENT-REPOSITORY-LEDGER: the carrier's Org record is digest-only too, its source half is on the
        # node's own ledger, and nothing is retained on the org ledger
        carried = next(r for r in hne.read_chain(self.org)[0] if r["receipt_sha256"] == self.carried["receipt_sha256"])
        self.assertEqual(set(carried["evidence"]), eld.ORG_CROSSING_EVIDENCE_KEYS)
        self.assertIsNone(anchor.crossing_record_failure(carried, NODE))
        self.assertIn(carried["evidence"]["source_repository_receipt_sha256"],
                      {r["receipt_sha256"] for r in hne.read_chain(self.node)[0]})
        self.assertFalse((self.org / "source-receipts").exists())
        own = next(r for r in hne.read_chain(self.node)[0]
                   if r["receipt_sha256"] == ingress["evidence"]["source_repository_receipt_sha256"])
        self.assertEqual(own["evidence"]["message"]["body"]["node_ledger_opened"], STEGOS_OPENED)
        self.assertEqual(layer1["anchor"]["org_side"], "DIGEST_ONLY_CROSSING_RECEIPT")
        self.assertIs(layer1["anchor"]["crossing_recorded_by_both_sides"], True)
        self.assertEqual(layer1["anchor"]["node_ledger_opened_signer_key_id"], ISSUER_REF["key_id"])
        self.assertEqual(layer1["anchor"]["org_ledger_location"], location.ORG_LEDGER_LOCATION)
        self.assertEqual(layer1["identity"]["node_id"], NODE)

    def test_permanent_own_ledger_reaches_layer1_allow(self):
        self._t2 = tempfile.TemporaryDirectory()
        self.addCleanup(self._t2.cleanup)
        self.use(Path(self._t2.name))
        self.open_and_anchor("PERMANENT", root=self.root)
        self.chain_to_admission()
        layer1 = self.evaluate(self.endpoint("PERMANENT", self.root))
        self.assertEqual(layer1["disposition"], "ALLOW", layer1)
        self.assertEqual((layer1["anchor"]["anchor"], layer1["anchor"]["ledger_lifetime"]),
                         ("INTR_PATH_RECEIPT_PAIR", "UNBOUNDED"))
        self.assertEqual(layer1["anchor"]["org_side"], "DIGEST_ONLY_CROSSING_RECEIPT")

    def test_permanent_is_designated_on_the_nodes_own_storage_endpoint(self):
        """Q-PERMANENT-REPOSITORY-LEDGER (#167 comment 6374130335) and LC-KV-25 (#167 comment 6373412055 items 3, 4):
        the node's own chain is designated on its own storage endpoint and read only through
        endpoint_ledger_designation; on an org GIT_REF it is DENY ENDPOINT_ORG_MEMBERSHIP_REFUSED, class A."""
        self._t2 = tempfile.TemporaryDirectory()
        self.addCleanup(self._t2.cleanup)
        self.use(Path(self._t2.name))
        self.open_and_anchor("PERMANENT", root=self.root)
        good = self.endpoint("PERMANENT", self.root)
        self.assertEqual(self.anchored(good)["disposition"], "ALLOW")
        org_ref = {**good, "designation": {**good["designation"],
                                           "stores": [{"store_type": "GIT_REF", "provider": "git",
                                                       "repository": "StegVerse-org/.github",
                                                       "ref": "refs/stegverse/organization-ledger",
                                                       "namespace": "repository-ledger/StegVerse-org/LLM-adapter"}]}}
        out = self.anchored(org_ref)
        self.assertEqual((out["disposition"], out["failure_code"], out["failure_class"], out["failed_predicate"]),
                         ("DENY", "ENDPOINT_ORG_MEMBERSHIP_REFUSED", "A", "ENDPOINT_NOT_A_GITHUB_ORGANIZATION_MEMBER"))
        self.assertNotIn("ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE", json.dumps(out))
        for key in SIX:
            self.assertTrue(isinstance(out[key], str) and out[key].strip(), key)
        # no designation, another node's designation, or another node's path: six fields, nothing read
        for bad in ({k: v for k, v in good.items() if k != "designation"},
                    {**good, **node_designated(self.root, "SV-NODE-another")}):
            with self.subTest(bad=sorted(bad)):
                self.assert_refused(self.anchored(bad), "ENDPOINT_LEDGER_DESIGNATION_INVALID",
                                    "ENDPOINT_LEDGER_DESIGNATION_INVALID")
        # the node's own recorded head is the watermark: absent is class A, a newer recorded head is DENY rollback
        self.assert_refused(self.anchored({**good, "recorded_head": None}), "KV_LEDGER_HEAD_ROLLBACK_WATERMARK_MISSING",
                            "KV_LEDGER_HEAD_ROLLBACK_WATERMARK_MISSING")
        newer = self.anchored({**good, "recorded_head": {"source": eld.NODE_WATERMARK_SOURCE,
                                                         "head_receipt_sha256": "sha256:" + "e" * 64}})
        self.assertEqual((newer["disposition"], newer["failure_code"]), ("DENY", "KV_LEDGER_HEAD_ROLLBACK_DETECTED"))
        # production: no NODE_STORAGE_ENDPOINT reader is documented or admitted
        with mock.patch.dict(eld._READERS, {eld.GIT_REF: eld._git_ref_reader}, clear=True):
            out = self.anchored(good)
            self.assert_refused(out, "NODE_STORAGE_ENDPOINT_READER_NOT_DOCUMENTED",
                                "NODE_STORAGE_ENDPOINT_READER_NOT_DOCUMENTED")
            self.assertEqual((out["failure_class"], out["reader_id"]), ("B", "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"))

    def test_the_kv_reader_refusal_is_documented_open(self):
        """LC-KV-21: the README states what is refused and why, with the module's own six fields."""
        readme = (ROOT / "README.md").read_text()
        section = readme.split("**Refused and documented-open: the KV receipt-chain reader (LC-KV-21).**")[1]
        section = section.split("**Common to every kind.**")[0]
        out = eld.refusal("KV_RECEIPT_CHAIN_READER_ID_NOT_DOCUMENTED", "documented-open")
        for key in ("failure_code", "failed_predicate", "owning_existing_goal", "next_attempt"):
            self.assertIn(out[key], section, key)
        for text in ("UNKNOWN_NOT_AUTHENTICALLY_OBSERVED", eld.ENTRYPOINT, eld.NODE_READER_CODE, "documented-open"):
            self.assertIn(text, section)

    def test_gateway_chain_is_never_anchored_on_the_org_ledger(self):
        """Rule (1): no gateway location is opened inside the org ledger; six fields, nothing written."""
        before = sorted(p.relative_to(self.tree) for p in self.tree.rglob("*"))
        opened = anchor.open_gateway_location(self.org, NODE, KEY)
        self.assert_refused(opened, "GATEWAY_CARRIER_LEDGER_NOT_DESIGNATED", "GATEWAY_CARRIER_LEDGER_NOT_DESIGNATED")
        self.assertEqual(sorted(p.relative_to(self.tree) for p in self.tree.rglob("*")), before)
        self.assertFalse(hasattr(anchor, "gateway_root"))
        self.chain_to_admission()
        for endpoint in ({"endpoint_kind": "GATEWAY"}, {"endpoint_kind": "GATEWAY", "ledger_root": str(self.root)}):
            with self.subTest(endpoint=endpoint):
                self.assert_refused(self.anchored(endpoint), "GATEWAY_CARRIER_LEDGER_NOT_DESIGNATED",
                                    "GATEWAY_CARRIER_LEDGER_NOT_DESIGNATED")
                self.assert_refused(self.evaluate(endpoint), "GATEWAY_CARRIER_LEDGER_NOT_DESIGNATED",
                                    "GATEWAY_CARRIER_LEDGER_NOT_DESIGNATED")

    def test_a_valid_both_sides_crossing_fires_neither_endpoint_code(self):
        """Coordination ruling (crossings): the endpoint's side is on its own chain, the Org records only its own
        digest-only side. That is not a ledger source; neither ENDPOINT_* code fires."""
        self.open_and_anchor()
        node_chain, org_chain = hne.read_chain(self.node)[0], hne.read_chain(self.org)[0]
        self.assertIsNone(eld.crossing_failure(node_chain, org_chain, {
            "endpoint_id": NODE, "rollback_watermark_source": {
                "source": "KV_RECORDED_RECEIPT_CHAIN_HEAD", "org_crossing_cross_check": {
                    "source": "ORG_LEDGER_LINKED_RECEIPTS_ENDPOINT_HEAD", "path_ids": [anchor.path_id(NODE)],
                    "role": "DIGEST_ONLY_CROSS_CHECK_NEVER_WATERMARK"}}}))
        crossing = next(r for r in org_chain if r["transition_class"] == anchor.DESTINATION_CLASS)
        own = [r for r in node_chain if r["transition_class"] == anchor.SOURCE_CLASS]
        self.assertEqual([r["receipt_sha256"] for r in own],
                         [crossing["evidence"]["source_repository_receipt_sha256"]])
        for r in (crossing, *own):
            self.assertTrue(r["observed_at"].startswith("SUPPLIED_HB_EPOCH:"), r["observed_at"])
        out = self.anchored(self.endpoint())
        self.assertEqual(out["disposition"], "ALLOW", out)
        for code in BOTH_ENDPOINT_CODES:
            self.assertNotIn(code, json.dumps(out))

    def test_kv_and_skap_name_stegverse_kv_and_never_anchor_on_the_org_ledger(self):
        signers = ROOT / ".stegverse/node-ledger/kv-ledger-head-signers.v1.json"
        self.assertEqual(hashlib.sha256(signers.read_bytes()).hexdigest()[:8], "758d7983")
        self.assertEqual(eld.HEAD_DIGEST_NAME, "KV_RECORDED_RECEIPT_CHAIN_HEAD")
        self.assertIn("signs KV_RECORDED_RECEIPT_CHAIN_HEAD", signers.read_text())
        for kind, location_ in (("KV", "_StegVerse/Receipts"), ("SKAP_VAULT", "_Vault/SKAP/Receipts")):
            with self.subTest(kind=kind):
                designation = KV_DESIGNATION[kind]
                endpoint_id = f"STEGVERSE_KV:{location_}"
                self.assertEqual(anchor.kv_endpoint_id(kind), endpoint_id)
                self.assertTrue(anchor.path_id(NODE).endswith(":intr-destination"))
                # cvk#263 @bf684aad: KV's own recorded head is the watermark; the :intr-destination path is only the
                # optional digest-only Org crossing cross-check
                self.assertEqual(designation["rollback_watermark_source"]["source"], "KV_RECORDED_RECEIPT_CHAIN_HEAD")
                self.assertEqual(eld.crossing_path_ids(designation),
                                 [f"StegVerse-org->{endpoint_id}:intr-destination"])
                self.assertEqual(set(designation["stores"][0]), {
                    "store_type", "storage_endpoint_schema", "provider_id", "access_adapter", "kv_class",
                    "kv_request_id", "location"})
                self.assertNotIn("ref", json.dumps(designation["stores"]))
                # never opened on a caller ledger_root (the org ledger is a git ref)
                self.assert_refused(anchor.plan_open(NODE, kind, KEY), "ENDPOINT_INVALID", anchor.ENDPOINT_FAILURE_CODE)
                out = anchor.verify_anchor(endpoint_id, endpoint={"endpoint_kind": kind, "designation": designation},
                                           org_ledger_root=self.org, org_ledger_head_receipt_sha256=self.head())
                self.assert_refused(out, "KV_RECEIPT_CHAIN_READER_ID_NOT_DOCUMENTED",
                                    "KV_RECEIPT_CHAIN_READER_ID_NOT_DOCUMENTED")
                self.assertEqual((out["endpoint_id"], out["path_id"]),
                                 (endpoint_id, f"StegVerse-org->{endpoint_id}:intr-destination"))
                on_ref = anchor.verify_anchor(endpoint_id, endpoint={"endpoint_kind": kind, "designation": designation,
                                                                     "ledger_root": str(self.org)},
                                              org_ledger_root=self.org, org_ledger_head_receipt_sha256=self.head())
                self.assert_refused(on_ref, "KV_LEDGER_DESIGNATED_ON_GIT_REF", "KV_LEDGER_DESIGNATED_ON_GIT_REF")
                org_ref = json.loads((DESIGNATIONS / "org-git-ref.designation.json").read_text())
                bad = anchor.verify_anchor(endpoint_id, endpoint={"endpoint_kind": kind, "designation": {
                    **org_ref, "endpoint_kind": kind}}, org_ledger_root=self.org,
                    org_ledger_head_receipt_sha256=self.head())
                self.assertEqual(bad["disposition"], "FAIL_CLOSED", bad)
                for key in SIX:
                    self.assertTrue(isinstance(bad[key], str) and bad[key].strip(), key)
                member = anchor.verify_anchor(endpoint_id, endpoint={"endpoint_kind": kind, "designation": {
                    **designation, "team_slug": "kv"}}, org_ledger_root=self.org,
                    org_ledger_head_receipt_sha256=self.head())     # LC-KV-25: never an Org member
                self.assert_refused(member, "ENDPOINT_ORG_MEMBERSHIP_REFUSED", "ENDPOINT_ORG_MEMBERSHIP_REFUSED")
                self.assertEqual(member["failed_predicate"], "ENDPOINT_NOT_A_GITHUB_ORGANIZATION_MEMBER")
                wrong = anchor.verify_anchor(NODE, endpoint={"endpoint_kind": kind, "designation": designation},
                                             org_ledger_root=self.org, org_ledger_head_receipt_sha256=self.head())
                self.assert_refused(wrong, "ENDPOINT_LEDGER_DESIGNATION_INVALID", "ENDPOINT_LEDGER_DESIGNATION_INVALID")
                # cvk#263 @bf684aad: no declared path is needed for the watermark; an Org-sourced one is refused
                bare = {**designation, "rollback_watermark_source": {"source": "KV_RECORDED_RECEIPT_CHAIN_HEAD"}}
                out = anchor.verify_anchor(endpoint_id, endpoint={"endpoint_kind": kind, "designation": bare},
                                           org_ledger_root=self.org, org_ledger_head_receipt_sha256=self.head())
                self.assert_refused(out, "KV_RECEIPT_CHAIN_READER_ID_NOT_DOCUMENTED",
                                    "KV_RECEIPT_CHAIN_READER_ID_NOT_DOCUMENTED")
                org_sourced = {**designation, "rollback_watermark_source": {
                    **designation["rollback_watermark_source"], "source": "ORG_LEDGER_LINKED_RECEIPTS_ENDPOINT_HEAD"}}
                out = anchor.verify_anchor(endpoint_id, endpoint={"endpoint_kind": kind, "designation": org_sourced},
                                           org_ledger_root=self.org, org_ledger_head_receipt_sha256=self.head())
                self.assert_refused(out, "KV_ROLLBACK_WATERMARK_ORG_LEDGER_SOURCED",
                                    "KV_ROLLBACK_WATERMARK_ORG_LEDGER_SOURCED")
                self.assertEqual(out["failure_class"], "A")
                unknown = anchor.verify_anchor(endpoint_id, endpoint={"endpoint_kind": kind, "designation": {
                    **designation, "ledger_note": "x"}}, org_ledger_root=self.org,
                    org_ledger_head_receipt_sha256=self.head())     # LC-KV-24: keys are closed
                self.assert_refused(unknown, "KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY",
                                    "KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY")

    def test_431_designation_suite_passes_against_432_anchors(self):
        """Rerun #431's designation tests here (byte-identical module), with #431's contract designation."""
        # byte copy of #431 @f29e4fbf tests/test_endpoint_ledger_designation.py, not collected on its own (#432's
        # contract.json does not designate)
        from tests import endpoint_ledger_designation_suite_431 as suite_module
        # production's reader seam (no NODE_STORAGE_ENDPOINT reader), not this class's TEST-ONLY node reader stub
        with mock.patch.object(location, "CONTRACT_PATH", CONTRACT_431), \
                mock.patch.dict(eld._READERS, {eld.GIT_REF: eld._git_ref_reader}, clear=True):
            suite = unittest.defaultTestLoader.loadTestsFromModule(suite_module)
            result = unittest.TestResult()
            suite.run(result)
        self.assertEqual((len(result.failures), len(result.errors), len(result.skipped)), (0, 0, 0),
                         [str(t) for t, _ in result.failures + result.errors])
        self.assertGreater(result.testsRun, 0)

    def test_the_lc_kv_15_hole_is_closed(self):
        anchor.open_ledger(self.node, NODE, "EPHEMERAL", KEY, "StegNode")   # opened, never anchored
        self.chain_to_admission()
        self.assertEqual(hne.evaluate(NODE, ledger_root=self.node, require_admission=True)["disposition"], "ALLOW")
        self.assert_refused(self.evaluate(), "UNANCHORED")


@harness.with_append_route
class AnchorRefusalTests(_Ledgers):
    def test_unanchored_scratch_ledger(self):
        self.chain_to_admission()      # a scratch ledger with no genesis at all
        self.assert_refused(self.evaluate(), "ENDPOINT_GENESIS_INVALID")
        self.assert_refused(self.evaluate(self.endpoint("KV", self.org / "nowhere")), "KV_LEDGER_DESIGNATED_ON_GIT_REF",
                            "KV_LEDGER_DESIGNATED_ON_GIT_REF")

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
        anchor.anchor(self.node, self.org, NODE, sign_opened(forged))
        self.assert_refused(self.evaluate(), "ANCHOR_LINK_UNVERIFIED")

    def test_mismatched_key_in_the_anchor(self):
        genesis = anchor.open_ledger(self.node, NODE, "EPHEMERAL", KEY, "StegNode")["genesis"]
        anchor.anchor(self.node, self.org, NODE, sign_opened(opened_for(genesis, node_identity_key=OTHER_KEY)))
        self.chain_to_admission()
        self.assert_refused(self.evaluate(), "KEY_MISMATCH")

    def test_mismatched_key_in_a_permanent_anchor(self):
        anchor.open_ledger(self.node, NODE, "PERMANENT", KEY)
        genesis = hne.read_chain(self.node)[0][-1]
        body = {**anchor.anchor_body(genesis), "node_identity_key": OTHER_KEY}
        source = anchor.append_source(self.node, NODE, anchor.anchor_communication_id(NODE, genesis["receipt_sha256"]), body)
        anchor.append_destination(self.org, source)
        self.assert_refused(self.evaluate(self.endpoint("PERMANENT")), "KEY_MISMATCH", anchor.ENDPOINT_FAILURE_CODE)

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
        # the Org's digest-only crossing names a source on the first ledger, not on this one
        self.assert_refused(self.evaluate(self.endpoint(root=other)), "UNANCHORED")

    def test_anchor_naming_another_genesis(self):
        anchor.open_ledger(self.node, NODE, "PERMANENT", KEY)
        genesis = hne.read_chain(self.node)[0][-1]
        body = {**anchor.anchor_body(genesis), "genesis_receipt_sha256": "sha256:" + "2" * 64}
        source = anchor.append_source(self.node, NODE, anchor.anchor_communication_id(NODE, genesis["receipt_sha256"]), body)
        anchor.append_destination(self.org, source)
        self.assert_refused(self.anchored(self.endpoint("PERMANENT")), "GENESIS_MISMATCH", anchor.ENDPOINT_FAILURE_CODE)

    def test_a_message_copying_org_record_is_refused(self):
        """Rule (1): an Org record on the node's path that carries the endpoint's message is not digest-only."""
        self.open_and_anchor()
        source = next(r for r in hne.read_chain(self.node)[0] if r["transition_class"] == anchor.SOURCE_CLASS)
        copied = {**anchor.crossing_evidence(anchor.path_id(NODE), "copy-1", source["receipt_sha256"],
                                             source["receipt_sha256"]), "message": source["evidence"]["message"]}
        anchor.append_receipt(self.org, anchor.DESTINATION_CLASS, f"{anchor.DESTINATION_CLASS}:copy-1", self.head(),
                              copied, 40)
        self.assert_refused(self.anchored(self.endpoint()), "ORG_CROSSING_RECEIPT_NOT_DIGEST_ONLY",
                            "ORG_CROSSING_RECEIPT_NOT_DIGEST_ONLY")

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
        self.assert_refused(self.evaluate({"endpoint_kind": "ORG"}), "ENDPOINT_KIND_NOT_A_NODE_ROOT",
                            anchor.ENDPOINT_FAILURE_CODE)
        for bad in ("permanent_node", "gateway_node", "kv", "temporary"):
            self.assert_refused(self.evaluate({"endpoint_kind": bad, "ledger_root": str(self.node)}), "ENDPOINT_INVALID",
                                anchor.ENDPOINT_FAILURE_CODE)
        self.assertEqual(anchor.plan_open(NODE, "EPHEMERAL", KEY)["reason"], "ENDPOINT_INVALID")      # node_kind required
        self.assertEqual(anchor.plan_open(NODE, "PERMANENT", KEY, "StegApp")["reason"], "ENDPOINT_INVALID")


@harness.with_append_route
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
                            ("stale chain head", stale),
                            ("garbled signature", self.prove(signature_b64="AAAA"))):
            with self.subTest(name):
                self.assert_identity_refused(self.evaluate(identity_proof=proof), "NODE_IDENTITY_PROOF_INVALID")
        # a proof naming another node selects that node's (absent) ledger, never this one
        self.assert_refused(self.evaluate(identity_proof=self.prove(node_id="SV-NODE-ffffffffffffffffffffffff")),
                            "ENDPOINT_GENESIS_INVALID")

    def test_asserted_transport_is_refused(self):
        self.open_and_anchor()
        self.chain_to_admission(transport=boundary.HTTP)     # the boundary records HTTP, not InTr
        out = self.evaluate(transport_state="INSTALLED")
        self.assert_transport_refused(out)
        self.assertEqual((out["asserted_transport_state"], out["asserted_transport_state_decides"]), ("INSTALLED", False))
        self.assertEqual(out["observed_transport"]["transport"], "HTTP")

    def test_transport_unobserved_without_an_installed_intr_ingress(self):
        self.open_and_anchor()
        refused = self.chain_to_admission(installed=False)   # main: INTERLOCK_INTR is NOT_YET_ENABLED
        self.assertEqual(refused["disposition"], "FAIL_CLOSED")
        # refused at ingress: the most specific predicate is admission, not transport (precedence, below)
        self.assert_refused(self.evaluate(transport_state="INSTALLED"), "NODE_NOT_ADMITTED", hne.FAILURE_CODE)
        self.assertEqual(boundary.TRANSPORTS[boundary.INTERLOCK_INTR], "NOT_YET_ENABLED")


@harness.with_append_route
class FailurePrecedenceTests(_Ledgers):
    """Steering 5:31 PM: report the most specific failed predicate, deterministically; nothing new ALLOWs."""

    def assert_stage(self, out, reason, failure_code, stage):
        self.assert_refused(out, reason, failure_code)
        self.assertEqual(out["failed_stage"], stage)
        self.assertEqual(out["failure_precedence"], anchor.FAILURE_PRECEDENCE)

    def test_the_order_is_fixed_and_documented(self):
        self.assertEqual(anchor.FAILURE_PRECEDENCE, ("ORG_LEDGER_LOCATION_AND_STORE", "PINNED_CODE_AND_ANCHOR",
                                                     "IDENTITY", "HEALTH_AND_ADMISSION", "TRANSPORT_RECORD",
                                                     "TRANSPORT_INTR_CARRIER"))
        self.assertIn("Failure precedence", anchor.evaluate_anchored.__doc__)
        readme = (ROOT / "README.md").read_text()
        self.assertIn("failure precedence", readme.lower())
        self.assertIn("HEALTH_REPORT_MISSING", readme)

    def test_no_health_report_is_health_report_missing_not_transport(self):
        self.open_and_anchor()          # anchored, proven identity, no NODE_HEALTH_REPORTED, no ingress
        for asserted in (None, "INSTALLED"):
            out = self.evaluate(transport_state=asserted)
            self.assert_stage(out, "HEALTH_REPORT_MISSING", hne.FAILURE_CODE, "HEALTH_AND_ADMISSION")
            self.assertIsNone(out["observed_transport"])

    def test_refused_at_ingress_is_node_not_admitted_not_transport(self):
        self.open_and_anchor()
        self.assertEqual(self.chain_to_admission(installed=False)["disposition"], "FAIL_CLOSED")
        out = self.evaluate(transport_state="INSTALLED")
        self.assert_stage(out, "NODE_NOT_ADMITTED", hne.FAILURE_CODE, "HEALTH_AND_ADMISSION")
        self.assertEqual(out["observed_transport"]["transition_class"], boundary.REFUSED_CLASS)

    def test_transport_is_reported_only_when_health_and_admission_pass(self):
        self.open_and_anchor()
        self.chain_to_admission(transport=boundary.HTTP)      # healthy and admitted, but over HTTP
        self.assertEqual(hne.evaluate(NODE, ledger_root=self.root, require_admission=True)["disposition"], "ALLOW")
        self.assert_stage(self.evaluate(transport_state="INSTALLED"), "INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED",
                          "INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED", "TRANSPORT_RECORD")

    def test_carrier_stage_is_last_and_fails_closed(self):
        self.open_and_anchor()
        with mock.patch.object(self, "carry", lambda *a, **k: None):     # admitted over InTr, no carrier pair
            self.chain_to_admission()
        out = self.evaluate()
        self.assert_stage(out, "INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED", "INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED",
                          "TRANSPORT_INTR_CARRIER")
        self.assertEqual(out["intr_carrier_refusal"], "INTR_CARRIER_NOT_ON_AUTHENTICATED_ORG_LEDGER")

    def test_repository_is_passed_through_to_the_evaluator_and_ingress_read(self):
        self.open_and_anchor()
        self.chain_to_admission()
        calls = []
        real = hne.evaluate

        def spy(*args, **kwargs):
            calls.append(kwargs)
            return real(*args, **kwargs)
        with mock.patch.object(anchor.hne, "evaluate", spy):
            self.assertEqual(self.evaluate()["disposition"], "ALLOW")
            self.assert_refused(self.evaluate(repository="StegVerse-org/Elsewhere"), "RECEIPT_REPOSITORY_MISMATCH",
                                hne.FAILURE_CODE)
        self.assertEqual([c["repository"] for c in calls], [hne.REPOSITORY, "StegVerse-org/Elsewhere"])

    def test_not_designated_six_fields_name_431(self):
        with mock.patch.object(location, "CONTRACT_PATH", CONTRACT_431.parent / "no-such-contract.json"):
            out = self.evaluate()
        self.assert_refused(out, "ORG_LEDGER_LOCATION_NOT_DESIGNATED")
        for key in ("required_evidence_or_repair", "retry_entrypoint", "owning_existing_goal", "next_attempt"):
            self.assertIn("StegVerse-org/LLM-adapter#431", out[key], key)
        with mock.patch.object(location, "CONTRACT_PATH", CONTRACT_431):     # #431's shape, no genesis pin yet
            pinless = self.evaluate()
        self.assert_refused(pinless, "ORG_LEDGER_GENESIS_NOT_PINNED")
        self.assertIn("StegVerse-org/LLM-adapter#431", pinless["next_attempt"])
        self.assertNotIn("REPOSITORY_LEDGER_GENESIS_PIN", out["next_attempt"])   # not designated waits on #431 itself

    def test_not_pinned_next_attempt_is_the_genesis_pin_transition(self):
        with mock.patch.object(location, "CONTRACT_PATH", CONTRACT_431):
            out = self.evaluate()
        self.assert_refused(out, "ORG_LEDGER_GENESIS_NOT_PINNED")
        self.assertEqual(out["next_attempt"], anchor.NEXT_PIN)
        self.assertEqual(out["retry_entrypoint"], anchor.RETRY_PIN)
        for needle in ("REPOSITORY_LEDGER_GENESIS_PIN", "scripts/llm_adapter_repository_ledger_genesis_pin.py plan",
                       "receipted REPOSITORY_LEDGER_INITIALIZATION genesis record", "StegVerse-org/LLM-adapter#431",
                       "no cron", "no polling", "no person"):
            self.assertIn(needle, out["next_attempt"], needle)
        self.assertIn("REPOSITORY_LEDGER_GENESIS_PIN", out["required_evidence_or_repair"])
        self.assertIn("REPOSITORY_LEDGER_GENESIS_PIN", out["retry_entrypoint"])
        for word in ("grant", "approved", "merge-ready", "timer elapses"):
            self.assertNotIn(word, json.dumps(out).lower())

    def test_431s_null_genesis_pin_is_six_field_not_pinned(self):
        """#431 sets expected_genesis_receipt_sha256 to null (it cannot be known before observation)."""
        real = json.loads(CONTRACT_431.read_text())
        self.assertIn("expected_genesis_receipt_sha256", real["repository_ledger_location"])
        self.assertIsNone(real["repository_ledger_location"]["expected_genesis_receipt_sha256"])
        with mock.patch.object(location, "CONTRACT_PATH", CONTRACT_431):
            designated = location.org_ledger_location()
        self.assertEqual(designated["namespace"], "repository-ledger/StegVerse-org/LLM-adapter")
        self.assertIsNone(designated["expected_genesis_receipt_sha256"])
        pinned = json.loads(CONTRACT_PINNED.read_text())
        self.assertEqual(set(pinned["repository_ledger_location"]), set(real["repository_ledger_location"]))
        self.assertEqual({k: v for k, v in pinned.items() if k != "repository_ledger_location"},
                         {k: v for k, v in real.items() if k != "repository_ledger_location"})
        for missing in ("null", "absent"):
            contract = json.loads(CONTRACT_431.read_text())
            if missing == "absent":
                del contract["repository_ledger_location"]["expected_genesis_receipt_sha256"]
            path = Path(self._t.name) / f"contract-{missing}.json"
            path.write_text(json.dumps(contract))
            with mock.patch.object(location, "CONTRACT_PATH", path):
                out = self.evaluate()
            self.assert_refused(out, "ORG_LEDGER_GENESIS_NOT_PINNED")
            self.assertEqual(out["failed_predicate"], "ORG_LEDGER_GENESIS_PINNED_BY_CONTRACT")
            self.assertIn("StegVerse-org/LLM-adapter#431", out["next_attempt"])


@harness.with_append_route
class SelfMintAndAssertionTests(_Ledgers):
    """LC-KV-16 (StegVerse-Labs/.github#3330 @c8b8d156): the three holes in evaluate_anchored, closed."""

    def assert_location_refused(self, out, reason):
        self.assert_refused(out, reason)
        self.assertTrue(out["failed_predicate"] == "ORG_LEDGER_LOCATION_FROM_CONTRACT")

    def test_caller_minted_anchor_is_refused(self):
        genesis = anchor.open_ledger(self.node, NODE, "EPHEMERAL", KEY, "StegNode")["genesis"]
        minted_seed = hashlib.sha256(b"endpoint-ledger-anchor tests: a caller's own seed").digest()
        anchor.anchor(self.node, self.org, NODE, sign_opened(STEGOS_OPENED, seed=minted_seed, key_id="callers-own-key"))
        self.chain_to_admission()
        self.assert_refused(self.evaluate(), "NODE_LEDGER_OPENED_SIGNER_NOT_PUBLISHED")
        self.assertEqual(STEGOS_OPENED["genesis_receipt_sha256"], genesis["receipt_sha256"])

    def test_anchor_signed_under_a_published_key_id_by_another_key_is_refused(self):
        anchor.open_ledger(self.node, NODE, "EPHEMERAL", KEY, "StegNode")
        minted_seed = hashlib.sha256(b"endpoint-ledger-anchor tests: a caller's own seed").digest()
        anchor.anchor(self.node, self.org, NODE, sign_opened(STEGOS_OPENED, seed=minted_seed))
        self.chain_to_admission()
        self.assert_refused(self.evaluate(), "NODE_LEDGER_OPENED_SIGNATURE_INVALID")

    def test_unsigned_anchor_is_refused(self):
        anchor.open_ledger(self.node, NODE, "EPHEMERAL", KEY, "StegNode")
        anchor.anchor(self.node, self.org, NODE, STEGOS_OPENED)        # StegOS's record, no signature
        self.chain_to_admission()
        self.assert_refused(self.evaluate(), "NODE_LEDGER_OPENED_UNSIGNED")

    def test_production_publishes_no_signer_yet(self):
        self.assertEqual(PRODUCTION_LOAD_OPENED_SIGNERS(), [])
        self.open_and_anchor()
        self.chain_to_admission()
        with mock.patch.object(anchor, "load_opened_signers", PRODUCTION_LOAD_OPENED_SIGNERS):
            self.assert_refused(self.evaluate(), "NODE_LEDGER_OPENED_SIGNER_NOT_PUBLISHED")
        self.assertEqual(self.evaluate()["disposition"], "ALLOW")

    def test_wrong_org_ledger_is_refused(self):
        self.open_and_anchor()
        self.chain_to_admission()
        self.assertEqual(self.evaluate()["disposition"], "ALLOW")
        base = Path(self._t.name)
        # a caller-chosen path: the org ledger directory itself, not an object store holding the designated ref
        self.assert_location_refused(self.evaluate(git_dir=self.tree), "ORG_LEDGER_LOCATION_UNREADABLE")
        # an object store without the ref
        empty = base / "empty.git"
        subprocess.run(["git", "init", "-q", "--bare", str(empty)], check=True, env=GIT_ENV)
        self.assert_location_refused(self.evaluate(git_dir=empty), "ORG_LEDGER_LOCATION_UNREADABLE")
        # the same chain published under another namespace than the contract designates
        other_tree = base / "other-tree"
        shutil.copytree(self.org, other_tree / "repository-ledger/StegVerse-org/Other")
        moved = base / "moved.git"
        subprocess.run(["git", "init", "-q", "--bare", str(moved)], check=True, env=GIT_ENV)
        self.publish(tree=other_tree, git_dir=moved)
        self.assert_location_refused(self.evaluate(git_dir=moved, publish=False), "ORG_LEDGER_LOCATION_UNREADABLE")
        # a chain at the designated namespace that does not open with REPOSITORY_LEDGER_INITIALIZATION
        foreign = base / "foreign-tree" / "repository-ledger/StegVerse-org/LLM-adapter"
        anchor.append_receipt(foreign, "INTR_MESH_PATH_INGRESS", "INTR_MESH_PATH_INGRESS:minted",
                              anchor.sha({"minted": True}), {"schema": "minted"}, 32)
        forged_git = base / "foreign.git"
        subprocess.run(["git", "init", "-q", "--bare", str(forged_git)], check=True, env=GIT_ENV)
        self.publish(tree=base / "foreign-tree", git_dir=forged_git)
        out = anchor.evaluate_anchored(endpoint=self.endpoint(), org_ledger_git_dir=forged_git,
                                       org_ledger_head_receipt_sha256=json.loads((foreign / "HEAD.json").read_text())
                                       ["receipt_sha256"], identity_proof=self.prove())
        self.assert_location_refused(out, "ORG_LEDGER_LOCATION_UNREADABLE")
        # no designation: main's contract has no repository_ledger_location until #431
        with mock.patch.object(location, "CONTRACT_PATH", ROOT / ".stegverse/transition-ledger/contract.json"):
            if "repository_ledger_location" not in json.loads(location.CONTRACT_PATH.read_text()):
                self.assert_location_refused(self.evaluate(), "ORG_LEDGER_LOCATION_NOT_DESIGNATED")
        redirected = base / "redirected-contract.json"
        contract = json.loads(CONTRACT_431.read_text())
        contract["repository_ledger_location"]["namespace"] = "repository-ledger/StegVerse-org/Elsewhere"
        redirected.write_text(json.dumps(contract))
        with mock.patch.object(location, "CONTRACT_PATH", redirected):
            self.assert_location_refused(self.evaluate(), "ORG_LEDGER_LOCATION_NOT_DESIGNATED")
        with self.assertRaises(TypeError):     # there is no caller-chosen org ledger path any more
            anchor.evaluate_anchored(endpoint=self.endpoint(), org_ledger_root=self.org,
                                     org_ledger_head_receipt_sha256=self.head(), identity_proof=self.prove())

    def test_asserted_node_id_decides_nothing(self):
        self.open_and_anchor()
        self.chain_to_admission()
        other = "SV-NODE-ffffffffffffffffffffffff"
        out = self.evaluate(claimed_node_id=other)
        self.assert_refused(out, "NODE_IDENTITY_PROOF_INVALID", anchor.IDENTITY_FAILURE_CODE)
        self.assertEqual((out["claimed_node_id"], out["claimed_node_id_decides"]), (other, False))
        self.assert_refused(self.evaluate(claimed_node_id=NODE, prove=False), "NODE_IDENTITY_PROOF_ABSENT",
                            anchor.IDENTITY_FAILURE_CODE)
        allowed = self.evaluate(claimed_node_id=NODE)
        self.assertEqual((allowed["disposition"], allowed["identity"]["node_id"]), ("ALLOW", NODE))
        self.assertEqual(self.evaluate()["identity"]["node_id"], NODE)      # derived from the proof alone

    def test_defaulted_transport_is_refused(self):
        self.open_and_anchor()
        self.chain_to_admission(transport=boundary.HTTP)
        self.assert_refused(self.evaluate(), anchor.TRANSPORT_FAILURE_CODE, anchor.TRANSPORT_FAILURE_CODE)
        # an InTr ingress record that does not say transport_state: nothing defaults it to INSTALLED
        self._t2 = tempfile.TemporaryDirectory()
        self.addCleanup(self._t2.cleanup)
        self.use(Path(self._t2.name))
        self.open_and_anchor(root=self.root)
        self.chain_to_admission()
        admitted = hne.read_chain(self.root)[0][0]
        self.assertEqual(admitted["transition_class"], boundary.ADMITTED_CLASS)
        silent = {k: v for k, v in admitted["evidence"].items() if k != "transport_state"}
        anchor._emitter().append(admitted["transition_id"] + ":again", boundary.ADMITTED_CLASS,
                                 admitted["receipt_sha256"], hne.sha(silent), silent, "NONE", hb_epoch=10**12)
        out = self.evaluate(self.endpoint(root=self.root))
        self.assert_refused(out, anchor.TRANSPORT_FAILURE_CODE, anchor.TRANSPORT_FAILURE_CODE)
        self.assertIsNone(out["observed_transport"]["transport_state"])

    def test_the_evaluator_gets_the_receipts_transport_explicitly(self):
        self.open_and_anchor()
        self.chain_to_admission()
        calls = []
        real = hne.evaluate

        def spy(*args, **kwargs):
            calls.append(kwargs)
            return real(*args, **kwargs)
        with mock.patch.object(anchor.hne, "evaluate", spy):
            self.assertEqual(self.evaluate()["disposition"], "ALLOW")
            self.assertEqual(self.evaluate(transport_state="NOT_YET_ENABLED")["disposition"], "ALLOW")  # decides nothing
        # one evaluator run per call; the transport stage is passed explicitly, and its ALLOW is returned only after
        # the transport record and the InTr carrier verify (FailurePrecedenceTests)
        self.assertEqual(len(calls), 2)
        self.assertEqual({(c["transport_state"], c["require_admission"]) for c in calls}, {("INSTALLED", True)})
        tree = ast.parse((ROOT / "llm_adapter/endpoint_ledger_anchor.py").read_text())
        wrapper = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "evaluate_anchored")
        evaluator_calls = [c for c in ast.walk(wrapper) if isinstance(c, ast.Call)
                           and isinstance(c.func, ast.Attribute) and c.func.attr == "evaluate"]
        self.assertEqual(len(evaluator_calls), 1)
        self.assertIn("transport_state", [k.arg for k in evaluator_calls[0].keywords])
        defaults = [d for d in wrapper.args.kw_defaults if isinstance(d, ast.Constant)]
        self.assertNotIn("INSTALLED", [d.value for d in defaults])


class CallerStoreAndIngressTests(_Ledgers):
    """LC-KV-16 rev 5 (StegVerse-Labs/.github#3330 @8abd5741): the three rows that ALLOWed on #432 @1cbad77e.

    Each row runs twice: under production (no head attester published: the append route is not admitted) and
    inside the TEST-ONLY append_route() harness, where it must still refuse, for its own reason.
    """

    def assert_transport_refused(self, out):
        self.assert_refused(out, "INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED", "INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED")

    def caller_appended_ingress(self, base_receipt=None):
        """The caller appends its own NODE_INGRESS_ADMITTED claiming installed InTr to its own node ledger."""
        chain = hne.read_chain(self.root)[0]
        ev = {"schema": "stegverse.node-ingress-record/v1", "node_endpoint": {"node_id": NODE}, "evaluated_node_id": NODE,
              "healthy_node_established": True, "transport": boundary.INTERLOCK_INTR, "transport_state": "INSTALLED",
              "signal_sha256": anchor.sha({"mode": "ESTABLISH_GENESIS", "node_ref": NODE, "predecessor": None,
                                           "node_class": "LLM_ADAPTER"})}
        report = next((r for r in chain if r["transition_class"] == "NODE_HEALTH_REPORTED"), None)
        if report:
            ev["health_report_receipt_sha256"] = report["receipt_sha256"]
        anchor._emitter().append("NODE_INGRESS_ADMITTED:caller-appended", boundary.ADMITTED_CLASS,
                                 (base_receipt or chain[0])["receipt_sha256"], hne.sha(ev), ev, "NONE", hb_epoch=10**12)

    def caller_store(self, name, *, own_genesis=False, with_anchor_of=None):
        """A git object store the caller created and filled, at the designated ref and namespace."""
        base = Path(self._t.name) / name
        org = base / "tree" / "repository-ledger/StegVerse-org/LLM-adapter"
        if own_genesis:
            anchor.append_receipt(org, anchor.GENESIS_CLASS, "REPOSITORY_LEDGER_INITIALIZATION:caller",
                                  anchor.sha({"repository": anchor.REPOSITORY, "ledger": "caller"}),
                                  {"schema": "stegverse.repository-ledger-initialization/v1",
                                   "repository": anchor.REPOSITORY, "authority_effect": "NONE_TEST_FIXTURE"}, 32)
        else:
            shutil.copytree(self.org, org)     # starts from the real chain, then adds what it likes
        if with_anchor_of is not None:
            anchor.anchor(with_anchor_of, org, NODE)
        store = base / "store.git"
        subprocess.run(["git", "init", "-q", "--bare", str(store)], check=True, env=GIT_ENV)
        self.publish(tree=base / "tree", git_dir=store)
        return store, json.loads((org / "HEAD.json").read_text())["receipt_sha256"]

    def evaluate_on(self, store, head, root, attestation):
        return anchor.evaluate_anchored(endpoint=self.endpoint("PERMANENT", root), org_ledger_git_dir=store,
                                        org_ledger_head_receipt_sha256=head, org_ledger_head_attestation=attestation,
                                        identity_proof=self.prove(self.endpoint("PERMANENT", root), head))

    def permanent_node(self, name):
        self.use(Path(self._t.name) / name)
        out = anchor.open_ledger(self.root, NODE, "PERMANENT", KEY, None)
        self.assertEqual(out["disposition"], "ALLOW", out)
        return self.root

    def test_a_permanent_root_on_a_caller_created_store_is_refused(self):
        """Row (a), PERMANENT_ROOT_ON_CALLER_CREATED_ORG_OBJECT_STORE."""
        root = self.permanent_node("perm-node")
        own_seed = hashlib.sha256(b"endpoint-ledger-anchor tests: a caller's own head attester").digest()
        # production: no attester is published, so no store is ever accepted
        store, head = self.caller_store("copy", with_anchor_of=root)
        self.chain_to_admission()
        out = self.evaluate_on(store, head, root, None)
        self.assert_refused(out, "MERGE_APPEND_PATH_NOT_ADMITTED", "MERGE_APPEND_PATH_NOT_ADMITTED")
        self.assertEqual(out["failed_predicate"], "ORG_LEDGER_HEAD_AUTHENTICATED_BY_APPEND_ROUTE")
        self.assertEqual(self.evaluate_on(store, head, root, harness.attest(store, seed=own_seed,
                                                                            key_id="callers-own"))["reason"],
                         "MERGE_APPEND_PATH_NOT_ADMITTED")
        with harness.append_route():
            # a store that minted its own genesis is not the org ledger, whatever it holds
            minted, minted_head = self.caller_store("minted", own_genesis=True)
            self.assert_refused(self.evaluate_on(minted, minted_head, root, harness.attest(minted)),
                                "ORG_LEDGER_GENESIS_MISMATCH", "ORG_LEDGER_GENESIS_MISMATCH")
            # the real genesis copied, plus the caller's own anchor pair: its head is not one the route attested
            self.assert_refused(self.evaluate_on(store, head, root, None), "ORG_LEDGER_HEAD_NOT_AUTHENTICATED", "ORG_LEDGER_HEAD_NOT_AUTHENTICATED")
            self.assert_refused(self.evaluate_on(store, head, root, harness.attest(store, seed=own_seed,
                                                                                    key_id="callers-own")),
                                "ORG_LEDGER_HEAD_NOT_AUTHENTICATED", "ORG_LEDGER_HEAD_NOT_AUTHENTICATED")
            self.assert_refused(self.evaluate_on(store, head, root, harness.attest(
                store, seed=own_seed, key_id=harness.ROUTE_REF["key_id"])), "ORG_LEDGER_HEAD_NOT_AUTHENTICATED", "ORG_LEDGER_HEAD_NOT_AUTHENTICATED")
            self.publish()
            route = harness.attest(self.git)          # the route's attestation of the real store, replayed
            self.assert_refused(self.evaluate_on(store, head, root, route), "ORG_LEDGER_HEAD_NOT_AUTHENTICATED", "ORG_LEDGER_HEAD_NOT_AUTHENTICATED")
            # an attestation of a head and tree the store does not hold
            self.assert_refused(self.evaluate_on(store, head, root, {**harness.attest(store), "namespace_tree_oid":
                                                                     route["namespace_tree_oid"]}),
                                "ORG_LEDGER_HEAD_NOT_AUTHENTICATED", "ORG_LEDGER_HEAD_NOT_AUTHENTICATED")
        # #431's contract copy carries no genesis pin: refused before the store is read
        with mock.patch.object(location, "CONTRACT_PATH", CONTRACT_431), harness.append_route():
            self.assert_refused(self.evaluate_on(store, head, root, harness.attest(store)),
                                "ORG_LEDGER_GENESIS_NOT_PINNED", "ORG_LEDGER_GENESIS_NOT_PINNED")

    def test_a_stale_head_attestation_is_refused(self):
        with harness.append_route():
            self.open_and_anchor()
            self.chain_to_admission()
            self.publish()
            stale = harness.attest(self.git)
            self.assertEqual(self.evaluate(org_ledger_head_attestation=stale)["disposition"], "ALLOW")
            self.carry({"mode": "ESTABLISH_GENESIS", "node_ref": "SV-NODE-another", "predecessor": None,
                        "node_class": "LLM_ADAPTER"}, "another-node-1")
            self.assert_refused(self.evaluate(org_ledger_head_attestation=stale), "ORG_LEDGER_HEAD_NOT_AUTHENTICATED")
            self.assertEqual(self.evaluate()["disposition"], "ALLOW")

    def test_b_a_caller_appended_ingress_record_claiming_installed_intr_is_refused(self):
        """Row (b), CALLER_APPENDED_INGRESS_RECORD_CLAIMING_INSTALLED_INTR: the anchor passes, transport refuses."""
        self.open_and_anchor()
        self.chain_to_admission(transport=boundary.HTTP)
        self.caller_appended_ingress()
        self.assert_refused(self.evaluate(), "MERGE_APPEND_PATH_NOT_ADMITTED")     # production
        with harness.append_route():
            out = self.evaluate()
            self.assert_transport_refused(out)
            self.assertEqual(out["anchor"]["disposition"], "ALLOW")
            self.assertEqual(out["intr_carrier_refusal"], "INTR_CARRIER_NOT_ON_AUTHENTICATED_ORG_LEDGER")
            self.assertEqual((out["observed_transport"]["transport"], out["observed_transport"]["transport_state"]),
                             ("INTERLOCK_INTR", "INSTALLED"))     # what the node's own record says; it decides nothing
            # a carrier for another node's signal on the authenticated chain does not carry this node
            self.carry({"mode": "ESTABLISH_GENESIS", "node_ref": "SV-NODE-another", "predecessor": None,
                        "node_class": "LLM_ADAPTER"}, "another-node-1")
            self.assertEqual(self.evaluate()["intr_carrier_refusal"], "INTR_CARRIER_NOT_ON_AUTHENTICATED_ORG_LEDGER")

    def test_c_caller_store_and_caller_appended_ingress_without_the_transport_patch_is_refused(self):
        """Row (c), PERMANENT_CALLER_STORE_AND_CALLER_APPENDED_INGRESS_NO_TRANSPORT_PATCH."""
        root = self.permanent_node("perm-node-2")
        anchor.anchor(root, self.org, NODE)
        refused = self.chain_to_admission(installed=False)
        self.assertEqual(refused["disposition"], "FAIL_CLOSED")
        self.caller_appended_ingress()
        self.assert_refused(self.evaluate(self.endpoint("PERMANENT", root)), "MERGE_APPEND_PATH_NOT_ADMITTED",
                            "MERGE_APPEND_PATH_NOT_ADMITTED")
        store, head = self.caller_store("caller-everything")
        with harness.append_route():
            self.assert_refused(self.evaluate_on(store, head, root, None), "ORG_LEDGER_HEAD_NOT_AUTHENTICATED", "ORG_LEDGER_HEAD_NOT_AUTHENTICATED")
            # even on the route-attested store, the caller's own record is not an InTr crossing
            out = self.evaluate(self.endpoint("PERMANENT", root))
            self.assert_transport_refused(out)
            self.assertEqual(out["anchor"]["disposition"], "ALLOW")
            self.assertEqual(out["intr_carrier_refusal"], "INTR_CARRIER_NOT_ON_AUTHENTICATED_ORG_LEDGER")

    def test_transport_only_row_passes_the_anchor_then_fails_on_transport(self):
        with harness.append_route():
            self.open_and_anchor()
            self.chain_to_admission(transport=boundary.HTTP)
            out = self.evaluate(transport_state="INSTALLED")
            self.assert_transport_refused(out)
            self.assertEqual(out["anchor"]["disposition"], "ALLOW")
            self.assertEqual(out["anchor"]["org_ledger_location"], location.ORG_LEDGER_LOCATION)
            self.assertEqual(out["observed_transport"]["transport"], "HTTP")

    def test_a_carrier_older_than_the_anchor_does_not_count(self):
        with harness.append_route():
            signal = {"mode": "ESTABLISH_GENESIS", "node_ref": NODE, "predecessor": None, "node_class": "LLM_ADAPTER"}
            self.carry(signal, "before-the-anchor")
            self.open_and_anchor()
            self.chain_to_admission(transport=boundary.HTTP)
            self.caller_appended_ingress()
            self.assertEqual(self.evaluate()["intr_carrier_refusal"], "INTR_CARRIER_NOT_ON_AUTHENTICATED_ORG_LEDGER")

    def test_production_refuses_every_positive_control(self):
        """Nothing ALLOWs until the append route is admitted: the E0 positive controls, without the harness."""
        self.assertEqual(location.load_head_signers(), [])
        published = json.loads(location.HEAD_SIGNERS_PATH.read_text())
        self.assertEqual((published["signers"], published["state"].split(":")[0]), ([], "NONE_PUBLISHED"))
        self.open_and_anchor()
        self.chain_to_admission()
        out = self.evaluate()
        self.assert_refused(out, "MERGE_APPEND_PATH_NOT_ADMITTED")
        self.assertIs(out["healthy_node_established"], False)
        with harness.append_route():
            self.assertEqual(self.evaluate()["disposition"], "ALLOW")


@harness.with_append_route
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
        self.publish()
        verify = lambda a, git_dir=self.git: anchor.verify_node_ledger_opened_anchor(   # noqa: E731
            a, ledger_root=self.node, org_ledger_git_dir=git_dir, org_ledger_head_receipt_sha256=self.head(),
            org_ledger_head_attestation=self.attest(git_dir))
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
        # the issuer verifier reads only the designated location, never a caller-chosen path
        self.assert_refused(verify(issued, git_dir=self.tree), "ORG_LEDGER_LOCATION_UNREADABLE")

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
        signed = json.loads((ROOT / "schemas/node-ledger-opened-signed.v1.json").read_text())
        envelope = sign_opened(STEGOS_OPENED)
        self.assertEqual(sorted(signed["required"]), sorted(envelope))
        self.assertEqual(sorted(signed["properties"]["signature"]["required"]), sorted(envelope["signature"]))
        self.assertEqual(signed["properties"]["schema"]["const"], anchor.SIGNED_OPENED_SCHEMA)
        self.assertEqual(len(envelope["signature"]["signature_b64"]), 88)
        kinds = json.loads((ROOT / "schemas/endpoint-kind.v1.json").read_text())
        self.assertEqual(tuple(kinds["$defs"]["endpoint_kind"]["enum"]), anchor.ENDPOINT_KINDS)
        self.assertEqual(kinds["properties"]["schema"]["const"], anchor.ENDPOINT_KIND_SCHEMA)


@harness.with_append_route
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
                         ("ALLOW", "DISSOLVED", "FULL_CHAIN_RECORDED_DIGEST_ONLY"), out)
        node_chain = hne.read_chain(self.node)[0]
        self.assertEqual(out["recorded_receipts"], len(node_chain))
        org_chain = hne.read_chain(self.org)[0]
        crossings = {r["evidence"]["source_repository_receipt_sha256"]: r for r in org_chain
                     if r["transition_class"] == anchor.DESTINATION_CLASS
                     and r["evidence"]["communication_id"].startswith("node-ledger-disbursement:")}
        for r in node_chain:   # every receipt crossed digest-only: the Org holds its digest, never a copy
            self.assertIn(r["receipt_sha256"], crossings)
            self.assertFalse((self.org / "source-receipts" / (r["receipt_sha256"][7:] + ".json")).exists())
            self.assertIsNone(anchor.crossing_record_failure(crossings[r["receipt_sha256"]], NODE))
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
        missing = planned["disbursement_body"]["receipt_sha256s"][3]
        real_append = anchor.append_receipt

        def skip_one(root, cls, transition_id, previous, evidence, *a, **kw):
            if evidence.get("source_repository_receipt_sha256") == missing:   # this crossing never lands
                return {"receipt_sha256": previous}
            return real_append(root, cls, transition_id, previous, evidence, *a, **kw)
        with mock.patch.object(anchor, "append_receipt", side_effect=skip_one):
            dissolution.disburse(planned, org_ledger_root=self.org)
        out = dissolution.finalize(planned, org_ledger_root=self.org)
        self.assert_refused(out, "DISBURSED_CHAIN_INCOMPLETE", dissolution.FAILURE_CODE)
        self.assertIs(out["dissolved"], False)
        org_classes = [r["transition_class"] for r in hne.read_chain(self.org)[0]]
        self.assertNotIn("NODE_LEDGER_DISSOLVED", org_classes)
        # not stranded: the ledger is still anchored and admissible until a read-back succeeds
        self.assertEqual(self.evaluate()["disposition"], "ALLOW", self.evaluate())
        self.assertEqual(self.dissolve()["outcome"], "DISSOLVED")

    def test_only_ephemeral_dissolves(self):
        self._t2 = tempfile.TemporaryDirectory()
        self.addCleanup(self._t2.cleanup)
        self.use(Path(self._t2.name))
        self.open_and_anchor("PERMANENT", root=self.root)
        self.assert_refused(self.dissolve(self.endpoint("PERMANENT", self.root)), "NOT_EPHEMERAL", dissolution.FAILURE_CODE)
        self.assertEqual(self.anchored(self.endpoint("PERMANENT", self.root))["disposition"], "ALLOW")
        for kind in ("KV", "SKAP_VAULT"):
            with self.subTest(kind=kind):
                endpoint = {"endpoint_kind": kind, "designation": KV_DESIGNATION[kind]}
                self.assert_refused(self.dissolve(endpoint), "NOT_EPHEMERAL", dissolution.FAILURE_CODE)
        self.assert_refused(self.dissolve({"endpoint_kind": "GATEWAY"}), "NOT_EPHEMERAL", dissolution.FAILURE_CODE)
        self.assert_refused(self.anchored({"endpoint_kind": "GATEWAY"}), "GATEWAY_CARRIER_LEDGER_NOT_DESIGNATED",
                            "GATEWAY_CARRIER_LEDGER_NOT_DESIGNATED")

    def test_dissolution_is_an_event_not_a_timer(self):
        self.open_and_anchor()
        self.assert_refused(dissolution.dissolve(NODE, endpoint=self.endpoint(), org_ledger_root=self.org,
                                                 org_ledger_head_receipt_sha256=self.head(),
                                                 dissolution_event={"event": "TIMER"}),
                            "DISSOLUTION_EVENT_INVALID", dissolution.FAILURE_CODE)


class FailureCodePerKindTests(_Ledgers):
    """Lane D finding 3: EPHEMERAL_NODE_LEDGER_NOT_ANCHORED for EPHEMERAL only; every other kind surfaces the
    specific org-ledger code, else ENDPOINT_LEDGER_NOT_ANCHORED."""
    NON_EPHEMERAL = ("PERMANENT", "KV", "SKAP_VAULT", "GATEWAY")

    def kind_endpoint(self, kind):
        if kind in KV_DESIGNATION:
            return {"endpoint_kind": kind, "designation": KV_DESIGNATION[kind]}
        return {"endpoint_kind": "GATEWAY"} if kind == "GATEWAY" else self.endpoint(kind)

    def kind_node(self, kind):
        return anchor.kv_endpoint_id(kind) if kind in KV_DESIGNATION else NODE

    def test_the_rule(self):
        for reason in anchor.ORG_LEDGER_REASONS:
            self.assertIn(reason, anchor.REASONS)
            self.assertEqual(anchor.anchor_failure_code("EPHEMERAL", reason), anchor.FAILURE_CODE)
            for kind in self.NON_EPHEMERAL:
                self.assertEqual(anchor.anchor_failure_code(kind, reason), reason)
        for kind in self.NON_EPHEMERAL + ("ORG", None):
            self.assertEqual(anchor.anchor_failure_code(kind, "UNANCHORED"), anchor.ENDPOINT_FAILURE_CODE)

    def test_production_store_without_an_append_route_per_kind(self):
        """No head signer published: MERGE_APPEND_PATH_NOT_ADMITTED is the code for every kind but EPHEMERAL."""
        self.chain_to_admission()
        for kind in ("EPHEMERAL",) + self.NON_EPHEMERAL:
            with self.subTest(kind=kind):
                out = self.evaluate(self.kind_endpoint(kind), org_ledger_head_attestation=None)
                self.assert_refused(out, "MERGE_APPEND_PATH_NOT_ADMITTED",
                                    anchor.FAILURE_CODE if kind == "EPHEMERAL" else "MERGE_APPEND_PATH_NOT_ADMITTED")

    @harness.with_append_route
    def test_org_ledger_head_not_pinned_per_kind(self):
        self.chain_to_admission()
        stale = "sha256:" + "1" * 64
        for kind in ("EPHEMERAL",) + self.NON_EPHEMERAL:
            with self.subTest(kind=kind):
                out = anchor.verify_anchor(self.kind_node(kind), endpoint=self.kind_endpoint(kind),
                                           org_ledger_root=self.org, org_ledger_head_receipt_sha256=stale)
                if kind == "GATEWAY":    # rule (1): refused before the org ledger is read
                    self.assert_refused(out, "GATEWAY_CARRIER_LEDGER_NOT_DESIGNATED",
                                        "GATEWAY_CARRIER_LEDGER_NOT_DESIGNATED")
                    continue
                self.assert_refused(out, "ORG_LEDGER_HEAD_NOT_PINNED",
                                    anchor.FAILURE_CODE if kind == "EPHEMERAL" else "ORG_LEDGER_HEAD_NOT_PINNED")

    @harness.with_append_route
    def test_an_unanchored_ledger_per_kind(self):
        for kind in ("KV", "SKAP_VAULT"):     # never opened on a caller ledger root
            self.assert_refused(anchor.open_ledger(self.root, NODE, kind, KEY), "ENDPOINT_INVALID",
                                anchor.ENDPOINT_FAILURE_CODE)
        for kind in ("EPHEMERAL", "PERMANENT"):
            with self.subTest(kind=kind):
                self._t2 = tempfile.TemporaryDirectory()
                self.addCleanup(self._t2.cleanup)
                self.use(Path(self._t2.name))
                out = anchor.open_ledger(self.root, NODE, kind, KEY, "StegNode" if kind == "EPHEMERAL" else None)
                self.assertEqual(out["disposition"], "ALLOW", out)
                self.assert_refused(self.anchored(self.endpoint(kind, self.root)), "UNANCHORED",
                                    anchor.FAILURE_CODE if kind == "EPHEMERAL" else anchor.ENDPOINT_FAILURE_CODE)


class DeterminismTests(unittest.TestCase):
    def test_no_production_module_imports_a_test_module(self):
        """Lane D finding 1: tests/org_ledger_harness.py and the other test helpers are test-only."""
        for path in sorted((ROOT / "llm_adapter").glob("*.py")):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                    for n in names:
                        self.assertNotEqual(n.split(".")[0], "tests", f"{path.name} imports {n}")

    def test_the_dissolution_writer_is_what_the_anchor_reads(self):
        """Lane D finding 2: node_ledger_dissolution is the event-driven write side (it imports the anchor, so
        the anchor cannot import it); verify_anchor's dissolution_on is its read side, keyed on the same class."""
        self.assertEqual(dissolution.anchor, anchor)
        src = (ROOT / "llm_adapter/node_ledger_dissolution.py").read_text()
        self.assertIn("anchor.DISSOLVED_CLASS", src)
        tree = ast.parse((ROOT / "llm_adapter/endpoint_ledger_anchor.py").read_text())
        imported = [a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names]
        self.assertNotIn("node_ledger_dissolution", imported)
        # live, not dead-listed: DissolutionTests drives dissolve() and evaluate_anchored then refuses the root
        self.assertTrue(hasattr(DissolutionTests, "test_disburse_read_back_then_root_inadmissible"))

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

    def test_the_org_ledger_reader_is_the_one_local_io_boundary(self):
        tree = ast.parse((ROOT / "llm_adapter/org_ledger_location.py").read_text())
        banned = {"datetime", "time", "random", "secrets", "socket", "urllib", "http", "requests", "httpx", "uuid"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                for n in names:
                    self.assertNotIn(n.split(".")[0], banned, n)
        runs = [c for c in ast.walk(tree) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                and isinstance(c.func.value, ast.Name) and c.func.value.id == "subprocess"]
        # three local git reads, all through the one argv prefix: rev-parse the ref's commit, rev-parse the
        # namespace tree (what the head attestation names), archive that commit
        self.assertEqual([c.func.attr for c in runs], ["run", "run", "run"])
        source = (ROOT / "llm_adapter/org_ledger_location.py").read_text()
        self.assertIn('"protocol.allow=never"', source)
        self.assertIn('"archive"', source)
        self.assertEqual(source.count('"rev-parse", "--verify", "--quiet"'), 2)
        self.assertEqual(source.count("git + ["), 3)

    def test_evaluator_is_untouched(self):
        digest = hashlib.sha256((ROOT / "llm_adapter/healthy_node_evaluator.py").read_bytes()).hexdigest()
        self.assertEqual(digest, "fdaa20053c527927067d16b011889ca84089b9750e95e291021310c669451f58")


if __name__ == "__main__":
    unittest.main()
