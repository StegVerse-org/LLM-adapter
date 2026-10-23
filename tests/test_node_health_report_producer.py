"""LC-KV-13 producer: receipted evidence in, an evaluator-accepted NODE_HEALTH_REPORTED out.

These tests cover:
* each trigger event (registration, identity binding, receipted health check);
* the receipt shape the evaluator accepts (on the chain from HEAD.json, with
  its body hash equal to its address);
* every unreceipted input failing closed with six fields and emitting nothing;
* idempotence, supersession and determinism;
* the end-to-end path: a receipted event goes through the producer, then the
  evaluator, then admit returns ALLOW, with the negative paths returning
  FAIL_CLOSED or DENY.

Every ledger here is a temporary directory. The real ledger is never written.
"""
from __future__ import annotations

import ast
import json
import os
import tempfile
import unittest
from pathlib import Path

from llm_adapter import healthy_node_evaluator as hne
from llm_adapter import node_health_report_producer as producer
from llm_adapter import node_ingress_boundary as boundary
from tests import healthy_node_reports as fx
from tests.test_healthy_node_evaluator import write_chain

ROOT = Path(__file__).resolve().parents[1]
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
NODE = "producer-node"


class _Ledger(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.root = Path(self._t.name)
        previous = os.environ.get("STEGVERSE_REPO_LEDGER_ROOT")
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = self._t.name

        def restore():
            if previous is None:
                os.environ.pop("STEGVERSE_REPO_LEDGER_ROOT", None)
            else:
                os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = previous
            self._t.cleanup()
        self.addCleanup(restore)

    def chain(self):
        chain, failure, _ = hne.read_chain(self.root)
        return chain if failure is None else []

    def assert_fail_closed(self, out, reason, predicate=None):
        self.assertEqual(out["disposition"], "FAIL_CLOSED", out)
        self.assertEqual(out["reason"], reason)
        self.assertIs(out["report_emitted"], False)
        for key in SIX:
            self.assertTrue(isinstance(out[key], str) and out[key].strip(), key)
        self.assertEqual(out["failure_code"], "NODE_HEALTH_REPORT_NOT_PRODUCED")
        if predicate:
            self.assertEqual(out["failed_predicate"], predicate)

    def no_report(self, node_id=NODE):
        self.assertFalse([r for r in self.chain() if hne._is_report_for(r, node_id)])


class ProducerTests(_Ledger):
    def test_health_check_trigger_emits_a_report_the_evaluator_accepts(self):
        fx.identified(NODE)
        check = fx.health_check(NODE)
        out = producer.produce(check["receipt_sha256"], ledger_root=self.root)
        self.assertEqual((out["disposition"], out["outcome"], out["report_status"]), ("ALLOW", "EMITTED", "HEALTHY"))
        self.assertEqual(out["trigger_event"], producer.HEALTH_CHECK_RECEIPTED)
        address = out["health_report_receipt_sha256"]
        # On the chain from HEAD.json, and its body hashes to its address.
        head = json.loads((self.root / "HEAD.json").read_text())["receipt_sha256"]
        self.assertEqual(head, address)
        stored = json.loads((self.root / "receipts" / (address[7:] + ".json")).read_text())
        self.assertEqual(hne.sha({k: v for k, v in stored.items() if k != "receipt_sha256"}), address)
        self.assertEqual(stored["transition_class"], "NODE_HEALTH_REPORTED")
        self.assertEqual(stored["evidence"]["schema"], "stegverse.node-health-report/v1")
        self.assertEqual(stored["evidence"]["evidence_receipts"]["health_check"], check["receipt_sha256"])
        self.assertEqual(stored["hb_reference"]["derived_from_clock"], False)
        verdict = hne.evaluate(NODE, ledger_root=self.root, report_receipt_sha256=address)
        self.assertEqual(verdict["disposition"], "ALLOW")

    def test_identity_binding_trigger(self):
        exists = fx.existence(NODE)
        fx.health_check(NODE)
        bound = fx.binding(NODE, exists["receipt_sha256"])
        out = producer.produce(bound["receipt_sha256"], ledger_root=self.root)
        self.assertEqual((out["outcome"], out["trigger_event"]), ("EMITTED", producer.NODE_IDENTITY_BOUND))
        self.assertEqual(hne.evaluate(NODE, ledger_root=self.root)["disposition"], "ALLOW")

    def test_identity_binding_without_any_health_check_fails_closed(self):
        _, bound = fx.identified(NODE)
        out = producer.produce(bound["receipt_sha256"], ledger_root=self.root)
        self.assert_fail_closed(out, "HEALTH_CHECK_NOT_RECEIPTED", "HEALTH_CHECK_RECEIPTED")
        self.no_report()

    def test_unhealthy_and_non_exact_checks_produce_unhealthy_reports_the_evaluator_denies(self):
        fx.identified(NODE)
        for observed in ("UNHEALTHY", "healthy", "OK", "DEGRADED", None):
            with self.subTest(observed=observed):
                check = fx.health_check(NODE, observed)
                out = producer.produce(check["receipt_sha256"], ledger_root=self.root)
                self.assertEqual((out["outcome"], out["report_status"]), ("EMITTED", "UNHEALTHY"))
                self.assertEqual(out["report_evidence"]["observed_health_check_status"], observed)
                self.assertEqual(hne.evaluate(NODE, ledger_root=self.root)["disposition"], "DENY")

    def test_newer_unhealthy_check_supersedes_an_earlier_healthy_report(self):
        fx.identified(NODE)
        producer.produce(fx.health_check(NODE)["receipt_sha256"], ledger_root=self.root)
        self.assertEqual(hne.evaluate(NODE, ledger_root=self.root)["disposition"], "ALLOW")
        producer.produce(fx.health_check(NODE, "UNHEALTHY")["receipt_sha256"], ledger_root=self.root)
        self.assertEqual(hne.evaluate(NODE, ledger_root=self.root)["disposition"], "DENY")

    def test_same_evidence_is_idempotent(self):
        fx.identified(NODE)
        check = fx.health_check(NODE)
        first = producer.produce(check["receipt_sha256"], ledger_root=self.root)
        length = len(self.chain())
        again = producer.produce(check["receipt_sha256"], ledger_root=self.root)
        self.assertEqual(again["outcome"], "NOOP_ALREADY_CURRENT")
        self.assertEqual(again["health_report_receipt_sha256"], first["health_report_receipt_sha256"])
        self.assertEqual(len(self.chain()), length)

    def test_trigger_not_on_chain_fails_closed(self):
        fx.identified(NODE)
        fx.health_check(NODE)
        for cited in ("sha256:" + "0" * 64, None, "", 7):
            with self.subTest(cited=cited):
                self.assert_fail_closed(producer.produce(cited, ledger_root=self.root),
                                        "TRIGGER_NOT_RECEIPTED", "TRIGGER_EVENT_RECEIPTED")
        self.no_report()

    def test_a_receipt_that_is_not_a_trigger_fails_closed(self):
        exists, _ = fx.identified(NODE)
        fx.health_check(NODE)
        self.assert_fail_closed(producer.produce(exists["receipt_sha256"], ledger_root=self.root),
                                "TRIGGER_NOT_RECOGNISED")
        self.no_report()

    def test_missing_existence_fails_closed(self):
        check = fx.health_check(NODE)
        self.assert_fail_closed(producer.produce(check["receipt_sha256"], ledger_root=self.root),
                                "EXISTENCE_NOT_RECEIPTED", "AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE")
        self.no_report()

    def test_refused_existence_does_not_count(self):
        exists = fx.existence(NODE, "DENY")
        fx.binding(NODE, exists["receipt_sha256"])
        check = fx.health_check(NODE)
        self.assert_fail_closed(producer.produce(check["receipt_sha256"], ledger_root=self.root),
                                "EXISTENCE_NOT_RECEIPTED")

    def test_binding_missing_refused_uncited_or_out_of_order_fails_closed(self):
        cases = {
            "missing": lambda e: None,
            "refused": lambda e: fx.binding(NODE, e["receipt_sha256"], "DENY"),
            "uncited": lambda e: fx.binding(NODE, "sha256:" + "1" * 64),
            "other existence": lambda e: fx.binding(NODE, None),
        }
        for name, make in cases.items():
            with self.subTest(name):
                for p in list((self.root / "receipts").glob("*.json")) + [self.root / "HEAD.json"]:
                    p.unlink(missing_ok=True)
                exists = fx.existence(NODE)
                make(exists)
                check = fx.health_check(NODE)
                self.assert_fail_closed(producer.produce(check["receipt_sha256"], ledger_root=self.root),
                                        "IDENTITY_BINDING_NOT_RECEIPTED", "NODE_IDENTITY_BINDING")
                self.no_report()

    def test_binding_before_existence_fails_closed(self):
        root = self.root / "hand"
        bodies = [{"transition_class": "NODE_IDENTITY_BINDING", "hb_reference": {"epoch": 64},
                   "evidence": {"node_id": NODE, "disposition": "ALLOW", "existence_receipt_sha256": None}}]
        first = write_chain(root, bodies)
        # The existence receipt arrives after the binding that should rest on it.
        bodies += [{"transition_class": "AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE", "hb_reference": {"epoch": 64},
                    "evidence": {"node_id": NODE, "disposition": "ALLOW"}},
                   {"transition_class": "NODE_HEALTH_CHECK_OBSERVED", "hb_reference": {"epoch": 64},
                    "evidence": {"schema": producer.HEALTH_CHECK_SCHEMA, "node_id": NODE, "status": "HEALTHY"}}]
        chain = write_chain(root, bodies)
        self.assertEqual(chain[0], first[0])
        self.assert_fail_closed(producer.plan(chain[-1]["receipt_sha256"], ledger_root=root),
                                "IDENTITY_BINDING_NOT_RECEIPTED")

    def test_forged_health_check_fails_closed_and_emits_nothing(self):
        fx.identified(NODE)
        check = fx.health_check(NODE, "UNHEALTHY")
        path = self.root / "receipts" / (check["receipt_sha256"][7:] + ".json")
        forged = json.loads(path.read_text())
        forged["evidence"]["status"] = "HEALTHY"
        path.write_text(json.dumps(forged))
        before = sorted(p.name for p in (self.root / "receipts").glob("*.json"))
        self.assert_fail_closed(producer.produce(check["receipt_sha256"], ledger_root=self.root),
                                "RECEIPT_HASH_MISMATCH")
        self.assertEqual(sorted(p.name for p in (self.root / "receipts").glob("*.json")), before)

    def test_foreign_repository_chain_fails_closed(self):
        root = self.root / "foreign"
        chain = write_chain(root, [{"transition_class": "NODE_HEALTH_CHECK_OBSERVED", "hb_reference": {"epoch": 64},
                                    "evidence": {"schema": producer.HEALTH_CHECK_SCHEMA, "node_id": NODE,
                                                 "status": "HEALTHY"}}], repository="Someone/else")
        self.assert_fail_closed(producer.plan(chain[0]["receipt_sha256"], ledger_root=root),
                                "RECEIPT_REPOSITORY_MISMATCH")

    def test_missing_ledger_fails_closed(self):
        self.assert_fail_closed(producer.plan("sha256:" + "0" * 64, ledger_root=self.root / "absent"),
                                "LEDGER_HEAD_UNREADABLE")

    def test_produce_never_appends_to_a_ledger_other_than_the_one_it_read(self):
        fx.identified(NODE)
        check = fx.health_check(NODE)
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = other.name
        self.assert_fail_closed(producer.produce(check["receipt_sha256"], ledger_root=self.root),
                                "LEDGER_ROOT_MISMATCH")
        self.assertFalse((Path(other.name) / "HEAD.json").exists())
        self.no_report()

    def test_plan_is_deterministic_and_never_writes(self):
        fx.identified(NODE)
        check = fx.health_check(NODE)
        before = sorted(p.name for p in self.root.rglob("*"))
        self.assertEqual(producer.plan(check["receipt_sha256"], ledger_root=self.root),
                         producer.plan(check["receipt_sha256"], ledger_root=self.root))
        self.assertEqual(sorted(p.name for p in self.root.rglob("*")), before)

    def test_core_imports_no_clock_network_or_randomness(self):
        tree = ast.parse((ROOT / "llm_adapter/node_health_report_producer.py").read_text())
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        banned = {"time", "datetime", "socket", "urllib", "http", "requests", "random", "secrets",
                  "subprocess", "os", "threading", "sched", "asyncio"}
        self.assertFalse(names & banned, names & banned)


class EndToEndTests(_Ledger):
    """A receipted event goes through the producer, then the evaluator, then admit."""

    def signal(self):
        return {"mode": "ESTABLISH_GENESIS", "node_ref": "e2e-node", "predecessor": None, "node_class": "LLM_ADAPTER"}

    def test_registration_event_produces_a_report_then_admit_allows(self):
        fx.identified("e2e-node")
        fx.health_check("e2e-node")
        first = boundary.admit(self.signal())
        # The first registration finds no report, so it is refused and recorded.
        # That refused registration receipt is the trigger the producer fires on.
        self.assertEqual((first["disposition"], first["failed_stage"]), ("FAIL_CLOSED", "CURRENT_NODE_HEALTH"))
        self.assertEqual(first["ingress_record"]["evaluated_node_id"], "e2e-node")
        production = first["health_report_production"]
        self.assertEqual((production["disposition"], production["outcome"], production["report_status"]),
                         ("ALLOW", "EMITTED", "HEALTHY"))
        self.assertEqual(production["trigger_event"], producer.NODE_REGISTRATION)
        self.assertEqual(production["report_evidence"]["trigger"]["receipt_sha256"], first["ingress_receipt_sha256"])
        report = production["health_report_receipt_sha256"]
        self.assertEqual(hne.evaluate("e2e-node", ledger_root=self.root, report_receipt_sha256=report)["disposition"],
                         "ALLOW")
        second = boundary.admit(self.signal(), health_report_receipt_sha256=report)
        self.assertEqual(second["disposition"], "ALLOW")
        self.assertIs(second["healthy_node_established"], True)
        self.assertEqual(second["health_evaluation"]["health_report_receipt_sha256"], report)
        self.assertEqual(second["ingress_record"]["health_report_receipt_sha256"], report)
        # Layer 1 (Lane D) sees a current healthy admission.
        layer1 = hne.evaluate("e2e-node", ledger_root=self.root, require_admission=True)
        self.assertEqual(layer1["disposition"], "ALLOW")

    def test_health_check_event_then_admit_allows_over_http(self):
        from llm_adapter.combined_gateway import app
        from llm_adapter.web.testclient import TestClient
        fx.identified("e2e-node")
        produced = producer.produce(fx.health_check("e2e-node")["receipt_sha256"], ledger_root=self.root)
        response = TestClient(app).post("/api/node-standing", json={
            **self.signal(), "health_report_receipt_sha256": produced["health_report_receipt_sha256"]})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIs(response.json()["healthy_node_established"], True)

    def test_unhealthy_check_registration_then_admit_denies(self):
        fx.identified("e2e-node")
        fx.health_check("e2e-node", "UNHEALTHY")
        first = boundary.admit(self.signal())
        self.assertEqual(first["health_report_production"]["report_status"], "UNHEALTHY")
        second = boundary.admit(self.signal())
        self.assertEqual((second["disposition"], second["reason"].split(":")[0]),
                         ("DENY", "HEALTH_REPORTED_NOT_HEALTHY"))
        self.assertIs(second["healthy_node_established"], False)

    def test_unreceipted_inputs_never_reach_allow(self):
        cases = {
            "no prerequisites": (lambda: fx.health_check("e2e-node"), "EXISTENCE_NOT_RECEIPTED"),
            "no health check": (lambda: fx.identified("e2e-node"), "HEALTH_CHECK_NOT_RECEIPTED"),
            "no binding": (lambda: (fx.existence("e2e-node"), fx.health_check("e2e-node")),
                           "IDENTITY_BINDING_NOT_RECEIPTED"),
        }
        for name, (prepare, reason) in cases.items():
            with self.subTest(name):
                for p in list((self.root / "receipts").glob("*.json")) + [self.root / "HEAD.json"]:
                    p.unlink(missing_ok=True)
                prepare()
                first = boundary.admit(self.signal())
                self.assertEqual(first["disposition"], "FAIL_CLOSED")
                self.assertEqual(first["health_report_production"]["disposition"], "FAIL_CLOSED")
                self.assertEqual(first["health_report_production"]["reason"], reason)
                second = boundary.admit(self.signal())
                self.assertEqual((second["disposition"], second["reason"].split(":")[0]),
                                 ("FAIL_CLOSED", "HEALTH_REPORT_MISSING"))
                self.no_report("e2e-node")

    def test_forged_health_check_never_reaches_allow(self):
        fx.identified("e2e-node")
        check = fx.health_check("e2e-node", "UNHEALTHY")
        path = self.root / "receipts" / (check["receipt_sha256"][7:] + ".json")
        forged = json.loads(path.read_text())
        forged["evidence"]["status"] = "HEALTHY"
        path.write_text(json.dumps(forged))
        out = boundary.admit(self.signal())
        self.assertEqual(out["disposition"], "FAIL_CLOSED")
        self.assertIs(out["healthy_node_established"], False)
        self.no_report("e2e-node")

    def test_standing_refusal_does_not_fire_the_producer(self):
        out = boundary.admit({**self.signal(), "node_ref": ""})
        self.assertEqual(out["failed_stage"], "NODE_STANDING")
        self.assertIsNone(out["health_report_production"])


if __name__ == "__main__":
    unittest.main()
