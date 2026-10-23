"""LC-KV-13 / LC-KV-14 and the healthy_node_established security fix.

Regression for LLM-adapter node_ingress_boundary.admit @ ece815b1, which wrote
healthy_node_established true for an UNHEALTHY report, for no report, and over a
NOT_YET_ENABLED transport, and raised StandingRefused instead of returning a
disposition. Healthy now means: the healthy-node evaluator returned ALLOW from the
node's current NODE_HEALTH_REPORTED receipt, read back on the chain from HEAD.json
with its body hash matching its address. These tests exercise only the unit
surface; nothing here reaches a deployed node.
"""
from __future__ import annotations

import ast
import json
import os
import tempfile
import unittest
from pathlib import Path

from llm_adapter import healthy_node_evaluator as hne
from llm_adapter import node_ingress_boundary as boundary
from llm_adapter import node_standing
from tests.healthy_node_reports import report

ROOT = Path(__file__).resolve().parents[1]
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


def write_chain(root: Path, bodies: list[dict], repository: str = hne.REPOSITORY) -> list[dict]:
    """A hand-built ledger, so the evaluator's tests need no emitter and no clock."""
    (root / "receipts").mkdir(parents=True, exist_ok=True)
    prev, out = None, []
    for body in bodies:
        full = {"schema": "stegverse.repo-transition-receipt/v1", "repository": repository,
                "previous_receipt_sha256": prev, **body}
        digest = hne.sha(full)
        receipt = {**full, "receipt_sha256": digest}
        (root / "receipts" / (digest[7:] + ".json")).write_text(json.dumps(receipt))
        prev = digest
        out.append(receipt)
    (root / "HEAD.json").write_text(json.dumps({"receipt_sha256": prev}))
    return out


def health(node_id: str, status: str) -> dict:
    return {"transition_class": hne.HEALTH_REPORT_CLASS, "transition_id": f"r:{node_id}:{status}",
            "evidence": {"schema": hne.HEALTH_REPORT_SCHEMA, "node_id": node_id, "status": status}}


class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.root = Path(self._t.name)

    def assert_non_allow(self, out, disposition, reason):
        self.assertEqual(out["disposition"], disposition)
        self.assertEqual(out["reason"], reason)
        self.assertIs(out["healthy_node_established"], False)
        for key in SIX:
            self.assertTrue(isinstance(out[key], str) and out[key].strip(), key)
        self.assertEqual(out["failure_code"], "NODE_NOT_CURRENTLY_ADMITTED_HEALTHY")
        self.assertEqual(out["failed_predicate"], "REQUESTER_IS_CURRENTLY_ADMITTED_HEALTHY_NODE")

    def test_allow_only_for_the_current_receipted_healthy_report(self):
        chain = write_chain(self.root, [health("n1", "HEALTHY")])
        out = hne.evaluate("n1", ledger_root=self.root)
        self.assertEqual(out["disposition"], "ALLOW")
        self.assertIs(out["healthy_node_established"], True)
        self.assertEqual(out["health_report_receipt_sha256"], chain[0]["receipt_sha256"])
        self.assertEqual(out["health_report_authenticated"], "NOT_PROVEN")

    def test_unhealthy_report_is_deny(self):
        write_chain(self.root, [health("n1", "UNHEALTHY")])
        self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root), "DENY", "HEALTH_REPORTED_NOT_HEALTHY")

    def test_anything_but_exactly_healthy_is_refused(self):
        for status in ("ok", "healthy", "DEGRADED", None, ""):
            with self.subTest(status=status):
                root = self.root / str(status)
                write_chain(root, [health("n1", status)])
                self.assertNotEqual(hne.evaluate("n1", ledger_root=root)["disposition"], "ALLOW")

    def test_a_newer_unhealthy_report_supersedes_a_healthy_one(self):
        chain = write_chain(self.root, [health("n1", "HEALTHY"), health("n1", "UNHEALTHY")])
        self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root), "DENY", "HEALTH_REPORTED_NOT_HEALTHY")
        self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root,
                                           report_receipt_sha256=chain[0]["receipt_sha256"]),
                              "FAIL_CLOSED", "HEALTH_REPORT_SUPERSEDED")

    def test_missing_report_fails_closed(self):
        write_chain(self.root, [health("other", "HEALTHY")])
        self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root), "FAIL_CLOSED", "HEALTH_REPORT_MISSING")

    def test_missing_ledger_fails_closed(self):
        self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root / "absent"),
                              "FAIL_CLOSED", "LEDGER_HEAD_UNREADABLE")

    def test_unreceipted_report_fails_closed(self):
        """A well-formed report that is not on the chain from HEAD.json counts for nothing."""
        write_chain(self.root, [health("other", "HEALTHY")])
        stray = write_chain(self.root / "elsewhere", [health("n1", "HEALTHY")])[0]
        (self.root / "receipts" / (stray["receipt_sha256"][7:] + ".json")).write_text(json.dumps(stray))
        self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root), "FAIL_CLOSED", "HEALTH_REPORT_MISSING")
        self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root,
                                           report_receipt_sha256=stray["receipt_sha256"]),
                              "FAIL_CLOSED", "HEALTH_REPORT_NOT_RECEIPTED")

    def test_forged_hash_fails_closed(self):
        """An UNHEALTHY report edited to HEALTHY no longer hashes to its address."""
        chain = write_chain(self.root, [health("n1", "UNHEALTHY")])
        path = self.root / "receipts" / (chain[0]["receipt_sha256"][7:] + ".json")
        forged = json.loads(path.read_text())
        forged["evidence"]["status"] = "HEALTHY"
        path.write_text(json.dumps(forged))
        self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root), "FAIL_CLOSED", "RECEIPT_HASH_MISMATCH")

    def test_forged_receipt_sha_field_fails_closed(self):
        chain = write_chain(self.root, [health("n1", "HEALTHY")])
        path = self.root / "receipts" / (chain[0]["receipt_sha256"][7:] + ".json")
        forged = json.loads(path.read_text())
        forged["receipt_sha256"] = "sha256:" + "1" * 64
        path.write_text(json.dumps(forged))
        self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root), "FAIL_CLOSED", "RECEIPT_HASH_MISMATCH")

    def test_broken_link_and_foreign_repository_fail_closed(self):
        chain = write_chain(self.root, [health("n1", "HEALTHY"), health("n2", "HEALTHY")])
        (self.root / "receipts" / (chain[0]["receipt_sha256"][7:] + ".json")).unlink()
        self.assert_non_allow(hne.evaluate("n2", ledger_root=self.root), "FAIL_CLOSED", "RECEIPT_MISSING_ON_CHAIN")
        other = self.root / "foreign"
        write_chain(other, [health("n1", "HEALTHY")], repository="Someone/else")
        self.assert_non_allow(hne.evaluate("n1", ledger_root=other), "FAIL_CLOSED", "RECEIPT_REPOSITORY_MISMATCH")

    def test_a_report_of_another_class_or_schema_does_not_count(self):
        body = health("n1", "HEALTHY")
        write_chain(self.root, [{**body, "transition_class": "NODE_INGRESS_ADMITTED"}])
        self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root), "FAIL_CLOSED", "HEALTH_REPORT_MISSING")

    def test_transport_not_installed_fails_closed(self):
        write_chain(self.root, [health("n1", "HEALTHY")])
        for state in ("NOT_YET_ENABLED", None, "installed"):
            with self.subTest(state=state):
                self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root, transport_state=state),
                                      "FAIL_CLOSED", "TRANSPORT_NOT_INSTALLED")

    def test_require_admission_needs_a_current_healthy_admission(self):
        chain = write_chain(self.root, [health("n1", "HEALTHY")])
        self.assert_non_allow(hne.evaluate("n1", ledger_root=self.root, require_admission=True),
                              "FAIL_CLOSED", "NODE_NOT_ADMITTED")
        admitted = {"transition_class": "NODE_INGRESS_ADMITTED", "transition_id": "a",
                    "evidence": {"node_endpoint": {"node_id": "n1"}, "healthy_node_established": True,
                                 "health_report_receipt_sha256": chain[0]["receipt_sha256"]}}
        root2 = self.root / "admitted"
        chain2 = write_chain(root2, [health("n1", "HEALTHY")])
        admitted["evidence"]["health_report_receipt_sha256"] = chain2[0]["receipt_sha256"]
        write_chain(root2, [health("n1", "HEALTHY"), admitted])
        self.assertEqual(hne.evaluate("n1", ledger_root=root2, require_admission=True)["disposition"], "ALLOW")

    def test_deterministic(self):
        write_chain(self.root, [health("n1", "HEALTHY"), health("n2", "UNHEALTHY")])
        for node in ("n1", "n2", "n3"):
            a, b = hne.evaluate(node, ledger_root=self.root), hne.evaluate(node, ledger_root=self.root)
            self.assertEqual(hne.canon(a), hne.canon(b))

    def test_no_clock_network_or_randomness(self):
        tree = ast.parse((ROOT / "llm_adapter/healthy_node_evaluator.py").read_text())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or "").split(".")[0])
        self.assertFalse(names & {"time", "datetime", "socket", "urllib", "http", "requests", "random",
                                  "secrets", "subprocess", "os"})


class AdmitRegressionTests(unittest.TestCase):
    """admit @ ece815b1 established a healthy node in each of these cases. It must not."""

    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        previous = os.environ.get("STEGVERSE_REPO_LEDGER_ROOT")
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = self._t.name

        def restore():
            if previous is None:
                os.environ.pop("STEGVERSE_REPO_LEDGER_ROOT", None)
            else:
                os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = previous
            self._t.cleanup()
        self.addCleanup(restore)

    def signal(self, node_ref="regression-node", **extra):
        return {"mode": "ESTABLISH_GENESIS", "node_ref": node_ref, "predecessor": None,
                "node_class": "LLM_ADAPTER", **extra}

    def admitted_records(self):
        receipts = [json.loads(p.read_text()) for p in (Path(self._t.name) / "receipts").glob("*.json")]
        return [r for r in receipts if r["transition_class"] == boundary.ADMITTED_CLASS]

    def assert_refused(self, out, disposition, stage, reason=None):
        self.assertEqual(out["disposition"], disposition)
        self.assertEqual(out["failed_stage"], stage)
        self.assertIs(out["healthy_node_established"], False)
        self.assertIs(out["ingress_record"]["healthy_node_established"], False)
        self.assertEqual(out["ingress_transition_class"], boundary.REFUSED_CLASS)
        for key in SIX:
            self.assertTrue(isinstance(out[key], str) and out[key].strip(), key)
        self.assertEqual(out["failure_code"], "NODE_NOT_CURRENTLY_ADMITTED_HEALTHY")
        if reason:
            self.assertEqual(out["health_evaluation"]["reason"], reason)
        self.assertEqual(self.admitted_records(), [])

    def test_unhealthy_report(self):
        report("regression-node", "UNHEALTHY")
        out = boundary.admit(self.signal(), health=lambda: {"status": "UNHEALTHY"})
        self.assert_refused(out, "DENY", boundary.STAGE_HEALTH, "HEALTH_REPORTED_NOT_HEALTHY")

    def test_unhealthy_receipt_is_not_overridden_by_a_healthy_observation(self):
        report("regression-node", "UNHEALTHY")
        out = boundary.admit(self.signal(), health=lambda: {"status": "HEALTHY"})
        self.assert_refused(out, "DENY", boundary.STAGE_HEALTH, "HEALTH_REPORTED_NOT_HEALTHY")

    def test_missing_report(self):
        out = boundary.admit(self.signal())
        self.assert_refused(out, "FAIL_CLOSED", boundary.STAGE_HEALTH, "LEDGER_HEAD_UNREADABLE")
        report("someone-else")
        out = boundary.admit(self.signal())
        self.assert_refused(out, "FAIL_CLOSED", boundary.STAGE_HEALTH, "HEALTH_REPORT_MISSING")

    def test_unreceipted_report(self):
        """A HEALTHY observation with no receipt, and a cited receipt not on the chain, both fail closed."""
        report("someone-else")
        out = boundary.admit(self.signal(), health=lambda: {"status": "HEALTHY"})
        self.assert_refused(out, "FAIL_CLOSED", boundary.STAGE_HEALTH, "HEALTH_REPORT_MISSING")
        out = boundary.admit(self.signal(), health_report_receipt_sha256="sha256:" + "a" * 64)
        self.assert_refused(out, "FAIL_CLOSED", boundary.STAGE_HEALTH, "HEALTH_REPORT_NOT_RECEIPTED")

    def test_forged_hash(self):
        receipt = report("regression-node", "UNHEALTHY")
        path = Path(self._t.name) / "receipts" / (receipt["receipt_sha256"][7:] + ".json")
        forged = json.loads(path.read_text())
        forged["evidence"]["status"] = "HEALTHY"
        path.write_text(json.dumps(forged))
        out = boundary.admit(self.signal())
        self.assert_refused(out, "FAIL_CLOSED", boundary.STAGE_HEALTH, "RECEIPT_HASH_MISMATCH")

    def test_named_only_intr_transport_is_refused(self):
        """INTERLOCK_INTR is INSTALLED only for a verified carrier; naming it is refused at TRANSPORT."""
        report("regression-node")
        out = boundary.admit(self.signal(), transport=boundary.INTERLOCK_INTR)
        self.assertEqual((out["disposition"], out["failed_stage"]), ("FAIL_CLOSED", boundary.STAGE_TRANSPORT))
        self.assertEqual(out["failure_code"], "INTR_TRANSPORT_NOT_AUTHENTICALLY_OBSERVED")
        self.assertEqual(out["ingress_record"]["transport_state"], boundary.NOT_AUTHENTICALLY_OBSERVED)
        for key in SIX:
            self.assertTrue(isinstance(out[key], str) and out[key].strip(), key)
        self.assertEqual(self.admitted_records(), [])

    def test_refused_standing_returns_six_fields_instead_of_raising(self):
        out = boundary.admit(self.signal(mode="NOT_A_MODE"))
        self.assert_refused(out, "DENY", boundary.STAGE_STANDING)
        self.assertEqual(out["standing_refusal"]["failure_code"], "NODE_STANDING_DENY")
        out = boundary.admit(self.signal(), transport="SMOKE_SIGNAL")
        self.assert_refused(out, "FAIL_CLOSED", boundary.STAGE_TRANSPORT)

    def test_healthy_receipted_report_is_the_only_allow(self):
        receipt = report("regression-node")
        out = boundary.admit(self.signal(), health=lambda: {"status": "UNHEALTHY"})
        self.assertEqual(out["disposition"], "ALLOW")
        self.assertIs(out["healthy_node_established"], True)
        self.assertEqual(out["health_evaluation"]["health_report_receipt_sha256"], receipt["receipt_sha256"])
        record = out["ingress_record"]
        self.assertIs(record["healthy_node_established"], True)
        self.assertEqual(record["health_report_receipt_sha256"], receipt["receipt_sha256"])
        # The unreceipted observation is recorded and decides nothing.
        self.assertEqual(record["observed_health_unreceipted_status"], "UNHEALTHY")
        # Layer 1 can now require this admission.
        self.assertEqual(hne.evaluate("regression-node", ledger_root=self._t.name,
                                      require_admission=True)["disposition"], "ALLOW")

    def test_admit_never_raises_standing_refused(self):
        for sig in (None, {}, self.signal(node_ref=""), self.signal(node_class="NOPE"), self.signal(mode=7)):
            with self.subTest(signal=sig):
                try:
                    out = boundary.admit(sig)
                except node_standing.StandingRefused as exc:  # pragma: no cover - the regression
                    self.fail(f"admit raised StandingRefused: {exc}")
                self.assertIn(out["disposition"], ("DENY", "FAIL_CLOSED"))
                self.assertIs(out["healthy_node_established"], False)

    def test_ingress_record_never_establishes_health_from_a_bare_observation(self):
        sig = self.signal()
        disposition = node_standing.resolve(sig)
        for evaluation in (None, {"status": "HEALTHY"}, {"disposition": "DENY"},
                           {"disposition": "ALLOW", "healthy_node_established": "yes"}):
            with self.subTest(evaluation=evaluation):
                record = boundary.ingress_record(sig, disposition, "LLM_MACHINE_CONTINUATION",
                                                 "LLM_ADAPTER", boundary.HTTP, evaluation)
                self.assertIs(record["healthy_node_established"], False)


if __name__ == "__main__":
    unittest.main()
