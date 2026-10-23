"""LLM-adapter organization-ledger onboarding (G-8 draft): plan only, FAIL_CLOSED until admitted. Stdlib only."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import llm_adapter_ledger_merge_transfer as M  # noqa: E402
import llm_adapter_repository_ledger_genesis_pin as P  # noqa: E402

SIX = M.SIX_FIELDS
NS = "repository-ledger/StegVerse-org/LLM-adapter"
WORKFLOW = ROOT / ".github/workflows/llm-adapter-organization-ledger-merge-transfer.yml"
VALIDATION = ROOT / ".github/workflows/llm-adapter-ledger-merge-transfer-validation.yml"

# Known answers computed with merge_evidence as it stands in StegVerse-org/.github
# resident-runtime/merge_transfer.py @ 907f4305 (the pinned writer).
KAT = [
    ({"merge_commit": "1" * 40, "tree": "2" * 40, "parents": ["3" * 40, "4" * 40],
      "subject": "Merge pull request #557 from StegVerse-org/laneb/x"},
     "sha256:60523c727c43104f0e127947531daef41a56455cff5e123569af84df8ed172d0",
     "sha256:1c43183fcc16552416ed543db5d7cf616e2edb5645db0f2ca7987611ee9f56bd"),
    ({"merge_commit": "5" * 40, "tree": "6" * 40, "parents": ["7" * 40], "subject": "Squash (#9)"},
     "sha256:4a2fc31aa773532bddfa81a78a0d38818eb2e37b4e880a152929a6efa1d4a035",
     "sha256:1694e938b33523c0e41643111dfd335d86aae7b8738a52cc542cd545b62ddbc9"),
]


def git(cwd, *args):
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(cwd), "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                           "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main", *args],
                          cwd=cwd, check=True, capture_output=True, env=env, text=True).stdout.strip()


def receipt(body):
    return {**body, "receipt_sha256": M.sha(body)}


class Env:
    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.src = tmp / "llm-adapter"
        self.src.mkdir()
        git(self.src, "init", "-q")
        (self.src / "a.txt").write_text("a\n")
        git(self.src, "add", ".")
        git(self.src, "commit", "-q", "-m", "base")
        git(self.src, "checkout", "-q", "-b", "feature")
        (self.src / "b.txt").write_text("b\n")
        git(self.src, "add", ".")
        git(self.src, "commit", "-q", "-m", "feature")
        git(self.src, "checkout", "-q", "main")
        git(self.src, "merge", "-q", "--no-ff", "feature", "-m", "Merge pull request #12 from StegVerse-org/feature")
        self.merge = git(self.src, "rev-parse", "HEAD")
        self.writer = tmp / "writer"
        (self.writer / "resident-runtime").mkdir(parents=True)
        (self.writer / "resident-runtime" / "merge_transfer.py").write_bytes(b"writer\n")
        pin = {"schema": "x", "source_repository": "StegVerse-org/.github", "source_commit": "f" * 40,
               "files": [{"path": "resident-runtime/merge_transfer.py",
                          "sha256": "sha256:" + hashlib.sha256(b"writer\n").hexdigest()}]}
        self.pin = {**pin, "pin_sha256": M.sha(pin)}
        self.contract = json.loads((ROOT / ".stegverse/transition-ledger/contract.json").read_text())

    def ledger(self, *, epoch=446655631, clock=False, namespace=False, tamper_ns=False, name="org"):
        work = self.tmp / (name + "-work")
        (work / "receipts").mkdir(parents=True)
        head = receipt({"schema": "s", "hb_reference": {"epoch": epoch, "derived_from_clock": clock},
                        "previous_receipt_sha256": None})
        (work / "receipts" / (head["receipt_sha256"].split(":")[1] + ".json")).write_text(json.dumps(head))
        (work / "HEAD.json").write_text(json.dumps({"receipt_sha256": head["receipt_sha256"]}))
        if namespace:
            nd = work / NS / "receipts"
            nd.mkdir(parents=True)
            g = receipt({"schema": "stegverse.repo-transition-receipt/v1", "transition_class":
                         "REPOSITORY_LEDGER_INITIALIZATION", "previous_receipt_sha256": None})
            stored = {**g, "evidence": "tampered"} if tamper_ns else g
            (nd / (g["receipt_sha256"].split(":")[1] + ".json")).write_text(json.dumps(stored))
            (work / NS / "HEAD.json").write_text(json.dumps({"receipt_sha256": g["receipt_sha256"]}))
        git(work, "init", "-q")
        git(work, "add", ".")
        git(work, "commit", "-q", "-m", "ledger")
        bare = self.tmp / (name + ".git")
        git(self.tmp, "clone", "-q", "--bare", str(work), str(bare))
        git(self.tmp, "--git-dir", str(bare), "update-ref", M.LEDGER_REF, "HEAD")
        return str(bare)

    def plan(self, **kw):
        kw.setdefault("writer_dir", str(self.writer))
        return M.plan([self.merge], git_dir=self.src, pin=self.pin, contract=self.contract, **kw)


class LlmAdapterLedgerMergeTransferTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.e = Env(Path(self._t.name))

    def tearDown(self):
        self._t.cleanup()

    def assert_fail_closed(self, d, code):
        self.assertEqual(d["disposition"], "FAIL_CLOSED")
        for k in SIX:
            self.assertTrue(d.get(k), k)
        self.assertEqual(d["failure_code"], code)
        self.assertFalse(d["consequence_committed"])
        self.assertFalse(d["ledger_written"])
        self.assertFalse(d["credential_used"])
        self.assertEqual(d["unmet_predicates"][-1]["failure_code"], "MERGE_APPEND_PATH_NOT_ADMITTED")

    def test_copied_blocks_match_the_pinned_writer(self):
        pin = json.loads(M.PIN_PATH.read_text())
        self.assertEqual(pin["pin_sha256"], M.sha({k: v for k, v in pin.items() if k != "pin_sha256"}))
        mine = M.copied_block_digests((ROOT / "scripts/llm_adapter_ledger_merge_transfer.py").read_text())
        self.assertEqual(mine, pin["copied_blocks"]["sha256"])
        self.assertTrue(re.fullmatch(r"[0-9a-f]{40}", pin["source_commit"]))
        self.assertIn(pin["source_commit"], WORKFLOW.read_text())

    def test_evidence_known_answers_from_the_pinned_writer(self):
        for facts, payload, whole in KAT:
            self.assertIsNone(M.facts_failure(facts))
            ev = M.merge_evidence("StegVerse-org/LLM-adapter", facts)
            self.assertEqual(ev["payload_sha256"], payload)
            self.assertEqual(M.sha(ev), whole)

    def test_merge_commit_evidence_from_git(self):
        d = self.e.plan(org_ledger=self.e.ledger(namespace=True))
        ev = d["planned"][0]["evidence"]
        self.assertEqual(ev["merge_commit"], self.e.merge)
        self.assertEqual(ev["pull_request"], 12)
        self.assertEqual(ev["merge_kind"], "MERGE_COMMIT")
        self.assertEqual(ev["repository"], "StegVerse-org/LLM-adapter")

    def test_no_ledger_copy_fails_closed(self):
        d = self.e.plan(org_ledger=None)
        self.assert_fail_closed(d, "ORGANIZATION_LEDGER_COPY_UNAVAILABLE")

    def test_head_without_supplied_epoch_fails_closed(self):
        self.assert_fail_closed(self.e.plan(org_ledger=self.e.ledger(clock=True)), "HB_EPOCH_SOURCE_UNOBSERVED")

    def test_absent_namespace_is_genesis_unobserved(self):
        d = self.e.plan(org_ledger=self.e.ledger())
        self.assert_fail_closed(d, "REPOSITORY_LEDGER_GENESIS_UNOBSERVED")
        self.assertIn("REPOSITORY_LEDGER_INITIALIZATION", d["required_evidence_or_repair"])
        self.assertIn("admission transition", d["required_evidence_or_repair"])

    def test_tampered_namespace_chain_is_genesis_unobserved(self):
        d = self.e.plan(org_ledger=self.e.ledger(namespace=True, tamper_ns=True))
        self.assert_fail_closed(d, "REPOSITORY_LEDGER_GENESIS_UNOBSERVED")

    def test_everything_observed_still_fails_closed_on_the_append_path(self):
        d = self.e.plan(org_ledger=self.e.ledger(namespace=True))
        self.assert_fail_closed(d, "MERGE_APPEND_PATH_NOT_ADMITTED")
        self.assertEqual(len(d["unmet_predicates"]), 1)
        self.assertIn("TV/TVC least-privilege issuance", d["required_evidence_or_repair"])
        self.assertEqual(d["observation"]["namespace_chain_length"], 1)

    def test_writer_pin_mismatch_fails_closed(self):
        (self.e.writer / "resident-runtime" / "merge_transfer.py").write_bytes(b"changed\n")
        d = self.e.plan(org_ledger=self.e.ledger(namespace=True))
        self.assert_fail_closed(d, "WRITER_PIN_UNVERIFIED")
        self.assertFalse(d["writer_pin"]["verified"])

    def test_plan_writes_nothing_and_is_deterministic(self):
        bare = self.e.ledger(namespace=True)
        refs = lambda: git(self.e.tmp, "--git-dir", bare, "for-each-ref", "--format=%(refname) %(objectname)")
        before = refs()
        a, b = self.e.plan(org_ledger=bare), self.e.plan(org_ledger=bare)
        self.assertEqual(M.canon(a), M.canon(b))
        self.assertEqual(refs(), before)
        self.assertNotIn(NS, refs())

    def test_contract_location_is_the_org_ledger_subtree_not_a_new_root(self):
        loc = self.e.contract["repository_ledger_location"]
        self.assertEqual(loc["repository"], "StegVerse-org/.github")
        self.assertEqual(loc["namespace"], NS)
        self.assertIs(loc["new_ledger_root"], False)

    def test_workflows_have_no_schedule_dispatch_write_or_secret(self):
        for wf in (WORKFLOW, VALIDATION):
            text = wf.read_text()
            for banned in ("schedule:", "workflow_dispatch", "repository_dispatch", "workflow_call", "secrets.",
                           "git push", "contents: write", "id-token", "gh workflow run", "gh api"):
                self.assertNotIn(banned, text, (wf.name, banned))
            self.assertIn("permissions:\n  contents: read\n", text)
            for ref in re.findall(r"uses:\s*(\S+)", text):
                self.assertRegex(ref, r"@[0-9a-f]{40}$")

    def test_no_network_clock_or_randomness_imports(self):
        tree = ast.parse((ROOT / "scripts/llm_adapter_ledger_merge_transfer.py").read_text())
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                names.add((n.module or "").split(".")[0])
        self.assertFalse(names & {"socket", "urllib", "http", "requests", "time", "datetime", "random", "secrets"})


class ExpectedGenesisPinTests(unittest.TestCase):
    """repository_ledger_location.expected_genesis_receipt_sha256 is the source of #432's genesis pin.

    It is null with a note, never an invented digest, because the genesis receipt_sha256 cannot be computed before
    the genesis is observed. This test recomputes a REPOSITORY_LEDGER_INITIALIZATION genesis with the repository's own
    emit.py and shows that the digest moves with the clock-stamped observed_at, even with a supplied epoch, fixed
    inputs and an empty ledger. Only an observed, read-back genesis can be pinned.
    """

    def emit_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("repo_transition_emit_pin_test",
                                                      ROOT / ".stegverse/transition-ledger/emit.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def genesis_at(self, emit, instant):
        from datetime import datetime as real_datetime
        from unittest import mock

        class FixedClock(real_datetime):
            @classmethod
            def now(cls, tz=None):
                return instant

        with tempfile.TemporaryDirectory() as root, mock.patch.dict(os.environ, {"STEGVERSE_REPO_LEDGER_ROOT": root}), \
                mock.patch.object(emit, "datetime", FixedClock):
            anchor = int(emit.heartbeat_parameters()["anchor_epoch"])
            receipt = emit.append("REPOSITORY_LEDGER_INITIALIZATION:StegVerse-org/LLM-adapter",
                                  "REPOSITORY_LEDGER_INITIALIZATION", "sha256:" + "0" * 64, "sha256:" + "1" * 64,
                                  evidence={"namespace": NS}, hb_epoch=anchor)
        self.assertIsNone(receipt["previous_receipt_sha256"])
        return receipt

    def test_contract_pin_is_null_with_a_note_not_an_invented_digest(self):
        location = json.loads((ROOT / ".stegverse/transition-ledger/contract.json").read_text())[
            "repository_ledger_location"]
        self.assertIn("expected_genesis_receipt_sha256", location)
        pinned = location["expected_genesis_receipt_sha256"]
        if pinned is None:
            note = location["expected_genesis_note"]
            for needle in ("cannot be known before it is observed", "observed_at", "ORG_LEDGER_GENESIS_NOT_PINNED"):
                self.assertIn(needle, note)
        else:     # a later admitted change may set the observed genesis; it must then be a real digest form
            self.assertRegex(pinned, r"^sha256:[0-9a-f]{64}$")

    def test_genesis_digest_is_not_computable_before_observation(self):
        from datetime import datetime, timezone
        emit = self.emit_module()
        t1 = datetime(2026, 10, 23, 17, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 10, 23, 17, 0, 0, 1, tzinfo=timezone.utc)
        a, a_again, b = self.genesis_at(emit, t1), self.genesis_at(emit, t1), self.genesis_at(emit, t2)
        self.assertEqual(a["receipt_sha256"], a_again["receipt_sha256"])    # recomputed: same inputs, same instant
        self.assertNotEqual(a["receipt_sha256"], b["receipt_sha256"])       # one microsecond moves the digest
        self.assertFalse(a["hb_reference"]["derived_from_clock"])
        self.assertTrue(a["observed_at_is_descriptive_not_ordering"])
        self.assertEqual(a["receipt_sha256"], emit.sha({k: v for k, v in a.items() if k != "receipt_sha256"}))
        derived = emit.hb_reference()          # with no supplied epoch the reference itself is a clock sample
        self.assertTrue(derived["derived_from_clock"])


class GenesisPinTransitionTests(unittest.TestCase):
    """REPOSITORY_LEDGER_GENESIS_PIN: the pin is a manifest state transition triggered by the receipted genesis.

    The genesis is appended with this repository's own emit.py into a temporary namespace store, committed into a
    temporary bare copy of the org ledger ref, and read back by the planner. Nothing touches the real ledger.
    """

    CONTRACT = ROOT / ".stegverse/transition-ledger/contract.json"

    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.emit = ExpectedGenesisPinTests.emit_module(self)
        self.before = self.CONTRACT.read_bytes()

    def tearDown(self):
        self._t.cleanup()

    def append(self, root, *args, **kw):
        from unittest import mock
        with mock.patch.dict(os.environ, {"STEGVERSE_REPO_LEDGER_ROOT": str(root)}):
            return self.emit.append(*args, **kw)

    def org_ledger(self, *, genesis=True, extra=0, tamper=False, transition_class="REPOSITORY_LEDGER_INITIALIZATION",
                   name="org"):
        work = self.tmp / (name + "-work")
        work.mkdir()
        (work / "README").write_text("org ledger copy\n")
        receipts = []
        if genesis:
            store = work / NS
            receipts.append(self.append(store, transition_class + ":StegVerse-org/LLM-adapter", transition_class,
                                        "sha256:" + "0" * 64, "sha256:" + "1" * 64, evidence={"namespace": NS},
                                        hb_epoch=446655631))
            for i in range(extra):
                receipts.append(self.append(store, f"LATER:{i}", "LATER", "sha256:" + "1" * 64,
                                            "sha256:" + "2" * 64, hb_epoch=446655632 + i))
            if tamper:
                path = store / "receipts" / (receipts[0]["receipt_sha256"].split(":")[1] + ".json")
                forged = json.loads(path.read_text())
                forged["evidence"] = {"namespace": NS, "forged": True}
                path.write_text(json.dumps(forged))
        git(work, "init", "-q")
        git(work, "add", ".")
        git(work, "commit", "-q", "-m", "ledger")
        bare = self.tmp / (name + ".git")
        git(self.tmp, "clone", "-q", "--bare", str(work), str(bare))
        git(self.tmp, "--git-dir", str(bare), "update-ref", M.LEDGER_REF, "HEAD")
        return str(bare), receipts

    def assert_refused(self, d, code):
        self.assertEqual(d["disposition"], M.FAIL_CLOSED, d)
        self.assertEqual(d["failure_code"], code)
        for f in SIX:
            self.assertIsInstance(d[f], str)
            self.assertTrue(d[f], f)
        self.assertEqual(d["retry_entrypoint"], P.ENTRYPOINT)
        self.assertIn("StegVerse-org/LLM-adapter#431", d["owning_existing_goal"])
        self.assertIsNone(d["contract_write"])
        self.assertIsNone(d["consumes_receipt"])
        for word in ("grant", "granted", "authorized", "approved", "merge-ready"):
            self.assertNotIn(word, json.dumps(d).lower())

    def test_no_genesis_refuses_with_six_fields(self):
        self.assert_refused(P.plan(org_ledger=None, contract_bytes=self.before), "ORGANIZATION_LEDGER_COPY_UNAVAILABLE")
        bare, _ = self.org_ledger(genesis=False)
        d = P.plan(org_ledger=bare, contract_bytes=self.before)
        self.assert_refused(d, "REPOSITORY_LEDGER_GENESIS_UNOBSERVED")
        self.assertEqual(d["failed_predicate"], "REPOSITORY_LEDGER_GENESIS_RECEIPTED_ON_ORG_LEDGER")

    def test_valid_genesis_gives_the_exact_contract_write_and_consumes_receipt(self):
        bare, (g, later) = self.org_ledger(extra=1)
        d = P.plan(org_ledger=bare, genesis_receipt_sha256=g["receipt_sha256"], contract_bytes=self.before)
        self.assertEqual(d["disposition"], M.ALLOW, d)
        self.assertEqual(d["genesis_receipt_sha256"], g["receipt_sha256"])
        self.assertEqual(d["observation"]["namespace_head"], later["receipt_sha256"])
        self.assertEqual(d["observation"]["chain_length"], 2)
        self.assertFalse(d["already_pinned"])
        expected = json.loads(self.before)
        expected["repository_ledger_location"]["expected_genesis_receipt_sha256"] = g["receipt_sha256"]
        expected["repository_ledger_location"]["expected_genesis_note"] = P.PINNED_NOTE.format(
            location="StegVerse-org/.github#refs/stegverse/organization-ledger:" + NS, tip=d["observation"]["tip"])
        after = (json.dumps(expected, indent=2, ensure_ascii=False) + "\n").encode()
        w = d["contract_write"]
        self.assertEqual(w["after_text"].encode(), after)
        self.assertEqual(w["json_pointer"], "/repository_ledger_location/expected_genesis_receipt_sha256")
        self.assertEqual(w["before_sha256"], "sha256:" + hashlib.sha256(self.before).hexdigest())
        self.assertEqual(w["after_sha256"], "sha256:" + hashlib.sha256(after).hexdigest())
        self.assertEqual(P.apply_write(d, self.before), after)
        # only the pin and its note change
        old, new = json.loads(self.before), json.loads(after)
        for k in ("expected_genesis_receipt_sha256", "expected_genesis_note"):
            old["repository_ledger_location"].pop(k)
            new["repository_ledger_location"].pop(k)
        self.assertEqual(old, new)
        self.assertRegex(json.loads(after)["repository_ledger_location"]["expected_genesis_receipt_sha256"],
                         r"^sha256:[0-9a-f]{64}$")
        # the consumes receipt, appended with the unchanged emit.py into a scratch store, cites the genesis
        req = d["consumes_receipt"]["emit_append"]
        self.assertEqual(req["transition_class"], "REPOSITORY_LEDGER_GENESIS_PIN")
        self.assertEqual(req["hb_epoch"], 446655631)
        r = self.append(self.tmp / "pin-store", **req)
        self.assertEqual(r["evidence"]["consumes_receipt_sha256"], g["receipt_sha256"])
        self.assertEqual(r["evidence"]["consumes"][0]["receipt_sha256"], g["receipt_sha256"])
        self.assertEqual((r["predecessor_state_sha256"], r["successor_state_sha256"]),
                         (w["before_sha256"], w["after_sha256"]))
        self.assertFalse(r["hb_reference"]["derived_from_clock"])
        self.assertEqual(r["receipt_sha256"], self.emit.sha({k: v for k, v in r.items() if k != "receipt_sha256"}))

    def test_idempotent_re_run(self):
        bare, (g,) = self.org_ledger()
        first = P.plan(org_ledger=bare, contract_bytes=self.before)
        self.assertEqual(first, P.plan(org_ledger=bare, contract_bytes=self.before))
        pinned = P.apply_write(first, self.before)
        again = P.plan(org_ledger=bare, genesis_receipt_sha256=g["receipt_sha256"], contract_bytes=pinned)
        self.assertEqual(again["disposition"], M.ALLOW)
        self.assertTrue(again["already_pinned"])
        self.assertIsNone(again["contract_write"])
        self.assertIsNone(again["consumes_receipt"])
        self.assertEqual(P.apply_write(again, pinned), pinned)
        with self.assertRaises(ValueError):
            P.apply_write(first, pinned)       # a stale plan is never applied over a changed contract

    def test_conflicting_pin_is_refused(self):
        bare, (g,) = self.org_ledger()
        other = json.loads(self.before)
        other["repository_ledger_location"]["expected_genesis_receipt_sha256"] = "sha256:" + "e" * 64
        d = P.plan(org_ledger=bare, contract_bytes=(json.dumps(other, indent=2) + "\n").encode())
        self.assert_refused(d, "EXPECTED_GENESIS_PIN_CONFLICT")
        self.assertEqual(d["observed_genesis_receipt_sha256"], g["receipt_sha256"])

    def test_forged_or_non_chain_genesis_is_refused(self):
        bare, _ = self.org_ledger(tamper=True, name="forged")
        self.assert_refused(P.plan(org_ledger=bare, contract_bytes=self.before), "REPOSITORY_LEDGER_GENESIS_NOT_ON_CHAIN")
        bare, (g,) = self.org_ledger(name="real")
        named_elsewhere = receipt({**{k: v for k, v in g.items() if k != "receipt_sha256"}, "evidence": {"x": 1}})
        d = P.plan(org_ledger=bare, genesis_receipt_sha256=named_elsewhere["receipt_sha256"], contract_bytes=self.before)
        self.assert_refused(d, "REPOSITORY_LEDGER_GENESIS_NOT_ON_CHAIN")
        bare, _ = self.org_ledger(transition_class="SOMETHING_ELSE", name="wrongclass")
        self.assert_refused(P.plan(org_ledger=bare, contract_bytes=self.before), "REPOSITORY_LEDGER_GENESIS_MISMATCH")

    def test_planner_writes_nothing_and_declares_its_trigger(self):
        bare, _ = self.org_ledger()
        tip = git(self.tmp, "--git-dir", bare, "rev-parse", M.LEDGER_REF)
        P.plan(org_ledger=bare)
        self.assertEqual(self.CONTRACT.read_bytes(), self.before)
        self.assertEqual(git(self.tmp, "--git-dir", bare, "rev-parse", M.LEDGER_REF), tip)
        decl = json.loads((ROOT / ".stegverse/transition-ledger/genesis-pin-transition.v1.json").read_text())
        self.assertEqual(decl["transition_class"], P.TRANSITION_CLASS)
        self.assertEqual(decl["entrypoint"], P.ENTRYPOINT)
        self.assertEqual(decl["trigger"]["record_transition_class"], P.GENESIS_CLASS)
        for k in ("cron", "polling", "waits_on_a_person", "dispatch"):
            self.assertIs(decl["trigger"][k], False, k)
        tree = ast.parse((ROOT / "scripts/llm_adapter_repository_ledger_genesis_pin.py").read_text())
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                names.add((n.module or "").split(".")[0])
        self.assertFalse(names & {"socket", "urllib", "http", "requests", "time", "datetime", "random", "secrets",
                                  "subprocess"})


if __name__ == "__main__":
    unittest.main()
