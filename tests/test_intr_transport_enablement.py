"""INTERLOCK_INTR is INSTALLED, gated on a verified InTr path pair (LLM-ADAPTER-INTERLOCK-INTR-TRANSPORT-ENABLEMENT-001).

A transport the caller merely names stays refused, six-field
INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED. A crossing whose carrying pair
(INTR_MESH_PATH_TRANSFER, then INTR_MESH_PATH_INGRESS /
ORGANIZATION_INTR_DESTINATION_INGRESS at #431's location, body digest = signal
digest) reads back and verifies is admitted. HTTP is unchanged.

The organization ledger is a scratch bare git object store with fixed dates; the
contract is #432's copy of #431's designation. No network, no clock in the core.
"""
from __future__ import annotations

import ast
import glob
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from llm_adapter import healthy_node_evaluator as hne
from llm_adapter import intr_transport_carrier as carrier
from llm_adapter import node_ingress_boundary as boundary
from llm_adapter import org_ledger_location as location
from tests.healthy_node_reports import report

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_431 = ROOT / "tests/fixtures/node_receipts/contract_with_431_repository_ledger_location.json"
EVALUATOR_SHA256 = "fdaa20053c527927067d16b011889ca84089b9750e95e291021310c669451f58"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
GIT_ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": "/nonexistent", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@invalid", "GIT_AUTHOR_DATE": "1700000000 +0000",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@invalid",
           "GIT_COMMITTER_DATE": "1700000000 +0000"}


def git(git_dir, *args, env=None):
    return subprocess.run(["git", "--git-dir", str(git_dir), *args], check=True, capture_output=True,
                          env={**GIT_ENV, **(env or {})}).stdout.decode().strip()


def append(root, transition_class, transition_id, evidence, hb_epoch=40):
    """One stegverse.repo-transition-receipt/v1 in emit.py's shape, at a supplied epoch (observed_at null)."""
    emit = boundary._ledger()
    root = Path(root)
    with emit._exclusive(root):
        head_path = root / "HEAD.json"
        prev = json.loads(head_path.read_text()).get("receipt_sha256") if head_path.is_file() else None
        body = {"schema": carrier.RECEIPT_SCHEMA, "repository": carrier.REPOSITORY, "transition_id": transition_id,
                "transition_class": transition_class, "predecessor_state_sha256": carrier.sha(None),
                "successor_state_sha256": carrier.sha(dict(evidence)), "evidence": dict(evidence),
                "authority_effect": "NONE", "hb_reference": emit.hb_reference(hb_epoch), "ordering": emit.ORDERING,
                "observed_at": None, "observed_at_is_descriptive_not_ordering": True, "previous_receipt_sha256": prev}
        receipt = {**body, "receipt_sha256": carrier.sha(body)}
        emit._put(root / "receipts" / (receipt["receipt_sha256"][7:] + ".json"), receipt)
        emit._put(head_path, {"repository": carrier.REPOSITORY, "receipt_sha256": receipt["receipt_sha256"]})
        return receipt


def sealed(body):
    body = {k: v for k, v in body.items() if k != "receipt_sha256"}
    return {**body, "receipt_sha256": carrier.sha(body)}


def signal(node_ref="intr-node", **extra):
    return {"mode": "ESTABLISH_GENESIS", "node_ref": node_ref, "predecessor": None,
            "node_class": "LLM_ADAPTER", **extra}


class _OrgLedger(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        base = Path(self._t.name)
        self.tree = base / "org-ledger"
        self.org = self.tree / "repository-ledger" / "StegVerse-org" / "LLM-adapter"
        self.git = base / "org-object-store.git"
        self.node = base / "node-ledger"
        subprocess.run(["git", "init", "-q", "--bare", str(self.git)], check=True, env=GIT_ENV)
        patcher = mock.patch.object(location, "CONTRACT_PATH", CONTRACT_431)
        patcher.start()
        self.addCleanup(patcher.stop)
        append(self.org, location.GENESIS_CLASS, "REPOSITORY_LEDGER_INITIALIZATION:test-fixture",
               {"schema": "stegverse.repository-ledger-initialization/v1", "repository": carrier.REPOSITORY,
                "authority_effect": "NONE_TEST_FIXTURE"}, 32)
        previous = os.environ.get("STEGVERSE_REPO_LEDGER_ROOT")
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = str(self.node)

        def restore():
            if previous is None:
                os.environ.pop("STEGVERSE_REPO_LEDGER_ROOT", None)
            else:
                os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = previous
            self._t.cleanup()
        self.addCleanup(restore)

    def publish(self):
        index = {"GIT_INDEX_FILE": str(Path(self._t.name) / "publish.index")}
        work = ["--work-tree", str(self.tree)]
        git(self.git, *work, "add", "-A", ".", env=index)
        commit = git(self.git, "commit-tree", git(self.git, *work, "write-tree", env=index), "-m", "org ledger fixture")
        git(self.git, "update-ref", "refs/stegverse/organization-ledger", commit)

    def head(self):
        return json.loads((self.org / "HEAD.json").read_text())["receipt_sha256"]

    def carry(self, sig, *, body=None, location_override=None, link=True, retain=True, publish=True,
              message_override=None):
        """The InTr path pair for `sig`: source half retained, destination half on the org ledger."""
        source_ev = carrier.source_evidence(body if body is not None else sig, "comm-1")
        scratch = Path(self._t.name) / "source-ledger"
        source = append(scratch, carrier.SOURCE_CLASS, "INTR_MESH_PATH_TRANSFER:comm-1", source_ev)
        if retain:
            boundary._ledger()._put(self.org / "source-receipts" / (source["receipt_sha256"][7:] + ".json"), source)
        dest_ev = carrier.destination_evidence(source)
        if not link:
            other = sealed({**source, "transition_id": "INTR_MESH_PATH_TRANSFER:other"})
            dest_ev = carrier.destination_evidence(other)
        if location_override or message_override:
            dest_ev = {**dest_ev}
            if location_override:
                dest_ev["addressed_location"] = location_override
            if message_override:
                dest_ev["message"] = message_override
                dest_ev["message_sha256"] = carrier.sha(message_override)
            core = {k: v for k, v in dest_ev.items()
                    if k not in ("payload_sha256", "disposition", "communication_id", "boundary_evidence")}
            dest_ev["payload_sha256"] = carrier.sha(core)
        dest = append(self.org, carrier.DESTINATION_CLASS, "INTR_MESH_PATH_INGRESS:comm-1", dest_ev)
        if publish:
            self.publish()
        return {"destination_receipt_sha256": dest["receipt_sha256"], "org_ledger_head_receipt_sha256": self.head()}

    def admit(self, sig, cite, **kw):
        return boundary.admit(sig, transport=boundary.INTERLOCK_INTR, intr_carrier=cite,
                              org_ledger_git_dir=str(self.git), **kw)

    def ingress(self, transition_class):
        found = [json.loads(Path(p).read_text()) for p in glob.glob(str(self.node / "receipts" / "*.json"))]
        return [r for r in found if r["transition_class"] == transition_class]

    def assert_unobserved(self, out, reason=None):
        self.assertEqual(out["disposition"], "FAIL_CLOSED")
        self.assertEqual(out["failed_stage"], boundary.STAGE_TRANSPORT)
        self.assertEqual(out["failure_code"], "INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED")
        self.assertEqual(out["failed_predicate"], "INSTALLED_INTR_TRANSPORT_OBSERVED_ON_RECEIPTS")
        self.assertIn("StegVerse-org/.github#162", out["owning_existing_goal"])
        for key in SIX:
            self.assertTrue(isinstance(out[key], str) and out[key].strip(), key)
        record = out["ingress_record"]
        self.assertEqual(record["transport"], boundary.INTERLOCK_INTR)
        self.assertEqual(record["transport_state"], boundary.NOT_AUTHENTICALLY_OBSERVED)
        self.assertIsNone(record["intr_carrier"])
        self.assertEqual(record["failure_code"], "INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED")
        self.assertIs(out["healthy_node_established"], False)
        self.assertEqual(self.ingress(boundary.ADMITTED_CLASS), [])
        self.assertEqual(len(self.ingress(boundary.REFUSED_CLASS)), 1)
        if reason:
            self.assertTrue(out["reason"].startswith(reason + ":"), out["reason"])


class UnverifiedInTrIsRefusedTests(_OrgLedger):
    def test_named_only(self):
        report("intr-node")
        self.assert_unobserved(boundary.admit(signal(), transport=boundary.INTERLOCK_INTR), "INTR_CARRIER_NOT_CITED")

    def test_named_with_a_cite_but_no_object_store(self):
        report("intr-node")
        cite = self.carry(signal())
        self.assert_unobserved(boundary.admit(signal(), transport=boundary.INTERLOCK_INTR, intr_carrier=cite),
                               "ORG_LEDGER_LOCATION_UNREADABLE")

    def test_production_contract_has_no_designation(self):
        report("intr-node")
        cite = self.carry(signal())
        production = ROOT / ".stegverse/transition-ledger/contract.json"
        if "repository_ledger_location" in json.loads(production.read_text()):
            self.fail("production contract now designates a location; revisit this test with #431")
        with mock.patch.object(location, "CONTRACT_PATH", production):
            self.assert_unobserved(self.admit(signal(), cite), "ORG_LEDGER_LOCATION_NOT_DESIGNATED")

    def test_body_digest_is_not_the_signal(self):
        report("intr-node")
        cite = self.carry(signal(), body=signal(node_class="SOMETHING_ELSE"))
        self.assert_unobserved(self.admit(signal(), cite), "INTR_BODY_IS_NOT_THE_SIGNAL")

    def test_wrong_location(self):
        report("intr-node")
        cite = self.carry(signal(), location_override="refs/stegverse/organization-ledger:repository-ledger/x/y")
        self.assert_unobserved(self.admit(signal(), cite), "INTR_DESTINATION_WRONG_LOCATION")

    def test_unlinked_source(self):
        report("intr-node")
        cite = self.carry(signal(), link=False)
        self.assert_unobserved(self.admit(signal(), cite), "INTR_SOURCE_NOT_RETAINED")

    def test_destination_message_is_not_the_source_message(self):
        report("intr-node")
        swapped = {"message_class": carrier.MESSAGE_CLASS, "communication_id": "comm-1", "body": signal()}
        swapped["body"]["extra"] = True
        cite = self.carry(signal(), message_override=swapped)
        self.assert_unobserved(self.admit(signal(), cite), "INTR_PAIR_NOT_LINKED")

    def test_source_not_retained(self):
        report("intr-node")
        cite = self.carry(signal(), retain=False)
        self.assert_unobserved(self.admit(signal(), cite), "INTR_SOURCE_NOT_RETAINED")

    def test_destination_not_on_the_published_ref(self):
        report("intr-node")
        cite = self.carry(signal(), publish=False)       # the object store exists; the ref was never published
        self.assert_unobserved(self.admit(signal(), cite), "ORG_LEDGER_LOCATION_UNREADABLE")

    def test_head_not_pinned(self):
        report("intr-node")
        cite = self.carry(signal())
        cite = {**cite, "org_ledger_head_receipt_sha256": "sha256:" + "0" * 64}
        self.assert_unobserved(self.admit(signal(), cite), "ORG_LEDGER_HEAD_NOT_PINNED")

    def test_tampered_destination_breaks_its_seal(self):
        report("intr-node")
        cite = self.carry(signal(), publish=False)
        path = self.org / "receipts" / (cite["destination_receipt_sha256"][7:] + ".json")
        forged = json.loads(path.read_text())
        forged["evidence"]["message"]["body"]["node_class"] = "FORGED"
        path.write_text(json.dumps(forged))
        self.publish()
        # The designated read-back walks the chain with seals checked, so a forged half is unreadable.
        self.assert_unobserved(self.admit(signal(), cite), "ORG_LEDGER_LOCATION_UNREADABLE")

    def test_unsealed_source_copy(self):
        report("intr-node")
        cite = self.carry(signal(), publish=False)
        retained = next((self.org / "source-receipts").glob("*.json"))
        copy = json.loads(retained.read_text())
        copy["transition_id"] = "tampered"
        retained.write_text(json.dumps(copy))
        self.publish()
        self.assert_unobserved(self.admit(signal(), cite), "INTR_SOURCE_NOT_RETAINED")

    def test_pure_verify_refuses_a_non_ingress(self):
        cite = self.carry(signal())
        chain, failure, _ = hne.read_chain(self.org)
        self.assertIsNone(failure)
        genesis = chain[-1]["receipt_sha256"]
        self.assertEqual(carrier.verify(signal(), destination_receipt_sha256=genesis,
                                        org_ledger_head_receipt_sha256=cite["org_ledger_head_receipt_sha256"],
                                        org_chain=chain, retained_source=None)[0],
                         "INTR_DESTINATION_NOT_AN_INGRESS")


class VerifiedInTrIsAdmittedTests(_OrgLedger):
    def test_verified_pair_is_admitted(self):
        report("intr-node")
        cite = self.carry(signal())
        out = self.admit(signal(), cite)
        self.assertEqual(out["disposition"], "ALLOW", out.get("reason"))
        self.assertIs(out["healthy_node_established"], True)
        record = out["ingress_record"]
        self.assertEqual((record["transport"], record["transport_state"]), ("INTERLOCK_INTR", "INSTALLED"))
        self.assertEqual(record["intr_carrier"]["destination_receipt_sha256"], cite["destination_receipt_sha256"])
        self.assertEqual(record["intr_carrier"]["org_ledger_location"], carrier.ORG_LEDGER_LOCATION)
        self.assertEqual(record["intr_carrier"]["carrier_classes"],
                         ["INTR_MESH_PATH_TRANSFER", "INTR_MESH_PATH_INGRESS"])
        self.assertEqual(record["signal_sha256"], carrier.sha(signal()))
        self.assertEqual(len(self.ingress(boundary.ADMITTED_CLASS)), 1)
        self.assertEqual(out["health_evaluation"]["disposition"], "ALLOW")

    def test_verified_carrier_does_not_bypass_health(self):
        report("intr-node", "UNHEALTHY")
        cite = self.carry(signal())
        out = self.admit(signal(), cite)
        self.assertEqual((out["disposition"], out["failed_stage"]), ("DENY", boundary.STAGE_HEALTH))
        self.assertEqual(out["failure_code"], "NODE_NOT_CURRENTLY_ADMITTED_HEALTHY")
        self.assertEqual(out["ingress_record"]["transport_state"], "INSTALLED")
        self.assertIsNotNone(out["ingress_record"]["intr_carrier"])

    def test_the_pair_for_one_signal_does_not_carry_another(self):
        report("intr-node")
        report("other-node")
        cite = self.carry(signal())
        self.assert_unobserved(self.admit(signal("other-node"), cite), "INTR_BODY_IS_NOT_THE_SIGNAL")


class CarrierBindingTests(_OrgLedger):
    """Coordination ruling on #433 item (3): reuse for the same node at the same head is idempotent;
    a carrier never admits a different node, and never outlives the node's dissolution."""

    def dissolve(self, node_id, genesis="sha256:" + "d" * 64):
        append(self.org, carrier.DISSOLVED_CLASS, f"{carrier.DISSOLVED_CLASS}:{node_id}:{genesis}",
               {"schema": "stegverse.node-ledger-dissolution/v1", "node_id": node_id,
                "genesis_receipt_sha256": genesis, "authority_effect": "NONE_TEST_FIXTURE"})

    def test_same_node_same_head_is_idempotent(self):
        report("intr-node")
        cite = self.carry(signal())
        first, second = self.admit(signal(), cite), self.admit(signal(), cite)
        self.assertEqual((first["disposition"], second["disposition"]), ("ALLOW", "ALLOW"))
        self.assertEqual(first["ingress_record"], second["ingress_record"])

    def test_a_carrier_for_node_a_does_not_admit_node_b(self):
        """(a) B is healthy on its own receipts; A's carrier still refuses it, six fields."""
        report("node-a")
        report("node-b")
        cite = self.carry(signal("node-a"))
        out = self.admit(signal("node-b"), cite)
        self.assert_unobserved(out, "INTR_BODY_IS_NOT_THE_SIGNAL")
        # Replaying A's exact signal admits A, never B: node_id comes from the carried body.
        replay = self.admit(signal("node-a"), cite)
        self.assertEqual(replay["disposition"], "ALLOW")
        self.assertEqual(replay["ingress_record"]["node_endpoint"]["node_id"], "node-a")
        admitted = [r["evidence"]["node_endpoint"]["node_id"] for r in self.ingress(boundary.ADMITTED_CLASS)]
        self.assertEqual(admitted, ["node-a"])

    def test_a_carrier_does_not_readmit_after_dissolution(self):
        """(b) A pre-dissolution carrier is refused once NODE_LEDGER_DISSOLVED for the node is on the org ledger."""
        report("intr-node")
        cite = self.carry(signal(), publish=False)
        self.dissolve("intr-node")
        self.publish()
        cite = {**cite, "org_ledger_head_receipt_sha256": self.head()}
        self.assert_unobserved(self.admit(signal(), cite), "INTR_CARRIER_NODE_DISSOLVED")

    def test_another_nodes_dissolution_does_not_refuse(self):
        report("intr-node")
        cite = self.carry(signal(), publish=False)
        self.dissolve("someone-else")
        self.publish()
        out = self.admit(signal(), {**cite, "org_ledger_head_receipt_sha256": self.head()})
        self.assertEqual(out["disposition"], "ALLOW", out.get("reason"))


class HttpIsUnchangedTests(_OrgLedger):
    def test_http_admits_without_a_carrier_and_records_no_carrier(self):
        report("intr-node")
        out = boundary.admit(signal())
        self.assertEqual(out["disposition"], "ALLOW", out.get("reason"))
        record = out["ingress_record"]
        self.assertEqual((record["transport"], record["transport_state"]), ("HTTP", "INSTALLED"))
        self.assertIsNone(record["intr_carrier"])

    def test_http_ignores_a_cited_carrier(self):
        report("intr-node")
        out = boundary.admit(signal(), intr_carrier={"destination_receipt_sha256": "sha256:" + "1" * 64})
        self.assertEqual(out["disposition"], "ALLOW")
        self.assertIsNone(out["ingress_record"]["intr_carrier"])

    def test_http_refusal_keeps_the_health_six(self):
        out = boundary.admit(signal())
        self.assertEqual(out["failure_code"], "NODE_NOT_CURRENTLY_ADMITTED_HEALTHY")
        self.assertEqual(out["ingress_record"]["transport_state"], "INSTALLED")


class InvariantTests(unittest.TestCase):
    def test_transport_table(self):
        self.assertEqual(boundary.TRANSPORTS, {"HTTP": "INSTALLED", "INTERLOCK_INTR": "INSTALLED"})

    def test_evaluator_is_pinned(self):
        digest = hashlib.sha256((ROOT / "llm_adapter/healthy_node_evaluator.py").read_bytes()).hexdigest()
        self.assertEqual(digest, EVALUATOR_SHA256)

    def test_org_ledger_location_is_432s_copy(self):
        # Byte-identical to #432's file, so the two drafts merge without a conflict.
        self.assertEqual(hashlib.sha256((ROOT / "llm_adapter/org_ledger_location.py").read_bytes()).hexdigest(),
                         "2ffaa91a606d18c45f239930e0e50292cb12461be22dc370fb6343037e3fce78")

    def test_carrier_core_reads_no_clock_network_or_process(self):
        tree = ast.parse((ROOT / "llm_adapter/intr_transport_carrier.py").read_text())
        banned = {"time", "datetime", "socket", "urllib", "http", "requests", "subprocess", "random", "secrets"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertFalse({a.name.split(".")[0] for a in node.names} & banned)
            elif isinstance(node, ast.ImportFrom):
                self.assertNotIn((node.module or "").split(".")[0], banned)
        verify = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "verify")
        names = {n.id for n in ast.walk(verify) if isinstance(n, ast.Name)}
        self.assertFalse(names & {"open", "Path", "json", "location", "hne"})

    def test_classes_are_the_existing_intr_classes(self):
        self.assertEqual((carrier.SOURCE_CLASS, carrier.DESTINATION_CLASS, carrier.DESTINATION_OPERATION),
                         ("INTR_MESH_PATH_TRANSFER", "INTR_MESH_PATH_INGRESS", "ORGANIZATION_INTR_DESTINATION_INGRESS"))
        self.assertEqual(carrier.ORG_LEDGER_LOCATION, location.ORG_LEDGER_LOCATION)


if __name__ == "__main__":
    unittest.main()
