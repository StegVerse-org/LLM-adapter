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
import llm_adapter_genesis_pin_ingress as R  # noqa: E402
from llm_adapter import intr_transport_carrier as carrier  # noqa: E402
from llm_adapter import org_ledger_location as location  # noqa: E402  (byte copy of #432's; LC-KV-19)
sys.path.insert(0, str(ROOT))
from tests import ed25519_test_signer as signer  # noqa: E402  (TEST-ONLY, byte copy of #432's)

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


#: TEST-ONLY append-route attester (a public seed, not a secret; TV/TVC custody holds real keys and bots never do).
ROUTE_SEED = hashlib.sha256(b"org-ledger harness: TEST-ONLY append-route attester public seed").digest()
ROUTE_REF = {"key_id": "test-org-ledger-append-route", "algorithm": "Ed25519", "custody": "TV/TVC",
             "signs": "ORG_LEDGER_HEAD", "public_key_b64": __import__("base64").b64encode(
                 signer.public_key(ROUTE_SEED)).decode()}


def attest(bare, seed=ROUTE_SEED, key_id=ROUTE_REF["key_id"], **override):
    """The append route's head attestation over what a ledger copy holds at the designated ref (TEST-ONLY)."""
    chain, obs, failure = P.read_chain(bare, NS)
    assert not failure, failure
    body = {**location.head_attestation_body(chain[-1]["receipt_sha256"], obs["namespace_head"],
                                             P.namespace_tree_oid(bare, obs["tip"], NS)), **override}
    return {**body, "key_id": key_id, "signature_b64": signer.sign_b64(location.head_attestation_message(body), seed)}


def with_append_route(cls):
    """Run each test_ method with the TEST-ONLY attester published, as an admitted append route would."""
    from unittest import mock
    for name in [n for n in vars(cls) if n.startswith("test_")]:
        def run(self, _method=getattr(cls, name)):
            with mock.patch.object(location, "load_head_signers", return_value=[dict(ROUTE_REF)]):
                return _method(self)
        run.__name__ = name
        setattr(cls, name, run)
    return cls


@with_append_route
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
        d = P.plan(org_ledger=bare, genesis_receipt_sha256=g["receipt_sha256"], contract_bytes=self.before,
                   org_ledger_head_attestation=attest(bare))
        self.assertEqual(d["disposition"], M.ALLOW, d)
        self.assertTrue(d["org_ledger_head_authenticated"])
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
        att = attest(bare)
        first = P.plan(org_ledger=bare, contract_bytes=self.before, org_ledger_head_attestation=att)
        self.assertEqual(first, P.plan(org_ledger=bare, contract_bytes=self.before, org_ledger_head_attestation=att))
        pinned = P.apply_write(first, self.before)
        again = P.plan(org_ledger=bare, genesis_receipt_sha256=g["receipt_sha256"], contract_bytes=pinned,
                       org_ledger_head_attestation=att)
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
        d = P.plan(org_ledger=bare, contract_bytes=(json.dumps(other, indent=2) + "\n").encode(),
                   org_ledger_head_attestation=attest(bare))
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
        P.plan(org_ledger=bare, org_ledger_head_attestation=attest(bare))
        self.assertEqual(self.CONTRACT.read_bytes(), self.before)
        self.assertEqual(git(self.tmp, "--git-dir", bare, "rev-parse", M.LEDGER_REF), tip)
        decl = json.loads((ROOT / ".stegverse/transition-ledger/genesis-pin-transition.v1.json").read_text())
        self.assertEqual(decl["transition_class"], P.TRANSITION_CLASS)
        self.assertEqual(decl["entrypoint"], P.ENTRYPOINT)
        self.assertEqual(decl["trigger"]["record_transition_class"], P.GENESIS_CLASS)
        self.assertEqual(decl["trigger"]["accepted_while_pin_is_null"], ["REPOSITORY_LEDGER_GENESIS_OBSERVED"])
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


@with_append_route
class GenesisPinPrePinIngressTests(unittest.TestCase):
    """The GENESIS_PIN trigger arrives over InTr (option (b)) and is received ahead of the pin it delivers.

    The genesis and the carrying INTR_MESH_PATH_INGRESS are appended with the unchanged emit.py into a temporary
    namespace store; the INTR_MESH_PATH_TRANSFER source half is retained at <namespace>/source-receipts/. Both use
    intr_transport_carrier's own evidence builders (byte copy of #432/#433). Nothing touches the real ledger.
    """

    CARRIER_SHA = "sha256:5c410dd3fddad854f41234a112574bb361ebd2c74362765292fc8480a689efa7"   # = #432/#433

    def setUp(self):
        self.g = GenesisPinTransitionTests()
        self.g.setUp()
        self.before = self.g.before
        self.contract = json.loads(self.before)

    def tearDown(self):
        self.g.tearDown()

    def carried(self, signal_for=None, *, name="org", tamper=False, carry_other=None):
        """A ledger copy: genesis, then the InTr destination half carrying the genesis-observed signal."""
        tmp = self.g.tmp
        work = tmp / (name + "-work")
        work.mkdir()
        store = work / NS
        genesis = self.g.append(store, "REPOSITORY_LEDGER_INITIALIZATION:StegVerse-org/LLM-adapter",
                                "REPOSITORY_LEDGER_INITIALIZATION", "sha256:" + "0" * 64, "sha256:" + "1" * 64,
                                evidence={"namespace": NS}, hb_epoch=446655631)
        signal = carry_other if carry_other is not None else R.genesis_signal(
            signal_for or genesis["receipt_sha256"], self.contract)
        cid = "intr-path-v1:StegVerse-org/.github->StegVerse-org:genesis-pin"
        source = receipt({"schema": carrier.RECEIPT_SCHEMA, "repository": "StegVerse-org/.github",
                          "transition_class": carrier.SOURCE_CLASS, "previous_receipt_sha256": None,
                          "evidence": carrier.source_evidence(signal, cid)})
        (store / "source-receipts").mkdir(parents=True)
        (store / "source-receipts" / (source["receipt_sha256"][7:] + ".json")).write_text(json.dumps(source))
        dest = self.g.append(store, "INTR_MESH_PATH_INGRESS:" + cid, carrier.DESTINATION_CLASS,
                             "sha256:" + "1" * 64, "sha256:" + "2" * 64,
                             evidence=carrier.destination_evidence(source), hb_epoch=446655632)
        if tamper:
            path = store / "receipts" / (genesis["receipt_sha256"][7:] + ".json")
            forged = json.loads(path.read_text())
            forged["evidence"] = {"namespace": NS, "forged": True}
            path.write_text(json.dumps(forged))
        git(work, "init", "-q")
        git(work, "add", ".")
        git(work, "commit", "-q", "-m", "ledger")
        bare = tmp / (name + ".git")
        git(tmp, "clone", "-q", "--bare", str(work), str(bare))
        git(tmp, "--git-dir", str(bare), "update-ref", M.LEDGER_REF, "HEAD")
        cite = {"destination_receipt_sha256": dest["receipt_sha256"], "org_ledger_head_receipt_sha256": dest["receipt_sha256"],
                "org_ledger_head_attestation": attest(str(bare)) if not tamper else None}
        return str(bare), genesis, signal, cite

    def assert_six(self, d, code):
        self.assertEqual(d["disposition"], "FAIL_CLOSED", d)
        self.assertEqual(d["failure_code"], code)
        for f in SIX:
            self.assertIsInstance(d[f], str)
            self.assertTrue(d[f], f)
        self.assertIsNone(d["genesis_pin_plan"])
        for word in ("grant", "approved", "authorized", "merge-ready"):
            self.assertNotIn(word, json.dumps(d).lower())

    def test_pre_pin_genesis_signal_is_accepted_and_planned(self):
        bare, genesis, signal, cite = self.carried()
        d = R.receive(signal, intr_carrier=cite, org_ledger=bare, contract_bytes=self.before)
        self.assertEqual(d["disposition"], R.ACCEPTED, d)
        plan = d["genesis_pin_plan"]
        self.assertEqual(plan["disposition"], "ALLOW")
        self.assertEqual(plan["genesis_receipt_sha256"], genesis["receipt_sha256"])
        self.assertEqual(plan["contract_write"]["value"], genesis["receipt_sha256"])
        ev = plan["consumes_receipt"]["emit_append"]["evidence"]
        self.assertEqual(ev["consumes_receipt_sha256"], genesis["receipt_sha256"])
        self.assertEqual([c["receipt_sha256"] for c in ev["consumes"]],
                         [genesis["receipt_sha256"], cite["destination_receipt_sha256"]])
        self.assertEqual(ev["carried_by"]["destination_receipt_sha256"], cite["destination_receipt_sha256"])
        # the planned pin, applied, is the exact write the planner alone gives for this genesis
        self.assertEqual(P.apply_write(plan, self.before).decode(), plan["contract_write"]["after_text"])

    def test_pre_pin_any_other_signal_class_is_refused(self):
        bare, genesis, signal, cite = self.carried()
        others = [{**signal, "signal_class": "NODE_INGRESS_SIGNAL"}, {**signal, "extra": 1},
                  {k: v for k, v in signal.items() if k != "node_ref"}, {"node_ref": "n-1", "kind": "NODE_INGRESS"},
                  "not an object", {**signal, "transition_class": "SOMETHING_ELSE"}]
        for other in others:
            d = R.receive(other, intr_carrier=cite, org_ledger=bare, contract_bytes=self.before)
            self.assert_six(d, "PRE_PIN_SIGNAL_CLASS_NOT_ACCEPTED")
        # a node signal genuinely carried over InTr is still refused while the pin is null
        node = {"node_ref": "n-1", "signal_class": "NODE_INGRESS_SIGNAL"}
        bare2, _, _, cite2 = self.carried(name="node", carry_other=node)
        self.assert_six(R.receive(node, intr_carrier=cite2, org_ledger=bare2, contract_bytes=self.before),
                        "PRE_PIN_SIGNAL_CLASS_NOT_ACCEPTED")

    def test_forged_or_off_chain_genesis_is_refused(self):
        bare, _, signal, cite = self.carried(name="forged", tamper=True)
        self.assert_six(R.receive(signal, intr_carrier=cite, org_ledger=bare, contract_bytes=self.before),
                        "REPOSITORY_LEDGER_GENESIS_NOT_ON_CHAIN")
        off = "sha256:" + "a" * 64          # the carried record names a genesis that is not the chain's root
        bare, _, signal, cite = self.carried(off, name="offchain")
        self.assert_six(R.receive(signal, intr_carrier=cite, org_ledger=bare, contract_bytes=self.before),
                        "REPOSITORY_LEDGER_GENESIS_NOT_ON_CHAIN")
        # a real genesis delivered without its InTr pair, or with a pair for another body, is refused by the carrier
        bare, genesis, signal, cite = self.carried(name="nocarrier")
        for bad in ({"org_ledger_head_attestation": cite["org_ledger_head_attestation"]},
                    {**cite, "destination_receipt_sha256": "sha256:" + "b" * 64},
                    {**cite, "org_ledger_head_receipt_sha256": genesis["receipt_sha256"]}):
            self.assert_six(R.receive(signal, intr_carrier=bad, org_ledger=bare, contract_bytes=self.before),
                            carrier.FAILURE_CODE)
        self.assert_six(R.receive(signal, intr_carrier=cite, org_ledger=None, contract_bytes=self.before),
                        "ORGANIZATION_LEDGER_COPY_UNAVAILABLE")

    def test_once_pinned_the_exception_closes_and_normal_gates_apply(self):
        bare, genesis, signal, cite = self.carried()
        accepted = R.receive(signal, intr_carrier=cite, org_ledger=bare, contract_bytes=self.before)
        pinned = P.apply_write(accepted["genesis_pin_plan"], self.before)
        node = {"node_ref": "n-1", "signal_class": "NODE_INGRESS_SIGNAL"}
        for s in (signal, node):
            d = R.receive(s, intr_carrier=cite, org_ledger=bare, contract_bytes=pinned)
            self.assert_six(d, "PRE_PIN_INGRESS_CLOSED")
            self.assertEqual(d["retry_entrypoint"], carrier.RETRY_ENTRYPOINT)     # the normal #433 InTr gate
            self.assertEqual(d["next_attempt"], carrier.NEXT_ATTEMPT)
        conflicting = json.loads(self.before)
        conflicting["repository_ledger_location"]["expected_genesis_receipt_sha256"] = "sha256:" + "e" * 64
        self.assert_six(R.receive(signal, intr_carrier=cite, org_ledger=bare,
                                  contract_bytes=json.dumps(conflicting).encode()), "PRE_PIN_INGRESS_CLOSED")

    ORG_FIXTURE = ROOT / "tests/fixtures/org-intr-path-transfer/typed-genesis-observed.json"
    ORG_FIXTURE_SHA = "05babd7b5c38fba61050220c41b987043f1fd2c9e7c5ded072a6f9625dc13890"   # = .github's copy

    def org_emitted(self, *, name="emitted", source_edit=None):
        """A ledger copy built from the org writer's typed output (StegVerse-org/.github INTR-PATH-TRANSFER-TYPED-BODY-001).

        The genesis and the retained INTR_MESH_PATH_TRANSFER source receipt are the fixture's bytes, unchanged; the
        INTR_MESH_PATH_INGRESS is carrier.destination_evidence over that source. SYNTHETIC: nothing is ledgered."""
        fixture = json.loads(self.ORG_FIXTURE.read_text())
        genesis, source = fixture["genesis_receipt"], fixture["source_receipt"]
        if source_edit:
            source = source_edit(json.loads(json.dumps(source)))
        work = self.g.tmp / (name + "-work")
        store = work / NS
        (store / "receipts").mkdir(parents=True)
        (store / "source-receipts").mkdir()
        (store / "receipts" / (genesis["receipt_sha256"][7:] + ".json")).write_text(json.dumps(genesis))
        (store / "source-receipts" / (source["receipt_sha256"][7:] + ".json")).write_text(json.dumps(source))
        dest = receipt({"schema": carrier.RECEIPT_SCHEMA, "repository": "StegVerse-org/LLM-adapter",
                        "transition_class": carrier.DESTINATION_CLASS,
                        "transition_id": "INTR_MESH_PATH_INGRESS:" + source["evidence"]["communication_id"],
                        "previous_receipt_sha256": genesis["receipt_sha256"],
                        "evidence": carrier.destination_evidence(source),
                        "synthetic": "FIXTURE_NOT_LEDGERED_NOT_AUTHENTIC"})
        (store / "receipts" / (dest["receipt_sha256"][7:] + ".json")).write_text(json.dumps(dest))
        (store / "HEAD.json").write_text(json.dumps({"receipt_sha256": dest["receipt_sha256"]}))
        git(work, "init", "-q")
        git(work, "add", ".")
        git(work, "commit", "-q", "-m", "ledger")
        bare = self.g.tmp / (name + ".git")
        git(self.g.tmp, "clone", "-q", "--bare", str(work), str(bare))
        git(self.g.tmp, "--git-dir", str(bare), "update-ref", M.LEDGER_REF, "HEAD")
        cite = {"destination_receipt_sha256": dest["receipt_sha256"],
                "org_ledger_head_receipt_sha256": dest["receipt_sha256"], "org_ledger_head_attestation": attest(str(bare))}
        return str(bare), fixture, cite

    def test_the_org_emitters_typed_output_is_accepted_by_the_receiver(self):
        raw = self.ORG_FIXTURE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), self.ORG_FIXTURE_SHA)   # byte-identical copy
        bare, fixture, cite = self.org_emitted()
        signal = fixture["source_receipt"]["evidence"]["message"]["body"]
        self.assertEqual(signal, fixture["declaration_row"]["typed_body"])
        self.assertEqual(signal, R.genesis_signal(fixture["genesis_receipt"]["receipt_sha256"], self.contract))
        self.assertEqual(fixture["source_receipt"]["evidence"]["endpoint_kind"], "ORG")
        d = R.receive(signal, intr_carrier=cite, org_ledger=bare, contract_bytes=self.before)
        self.assertEqual(d["disposition"], R.ACCEPTED, d)
        self.assertEqual(d["carried_by"]["source_receipt_sha256"], fixture["source_receipt"]["receipt_sha256"])
        self.assertEqual(d["genesis_pin_plan"]["genesis_receipt_sha256"], fixture["genesis_receipt"]["receipt_sha256"])
        # the same emitted pair is refused once the pin is set, and a tampered emitted body is refused by the carrier
        pinned = P.apply_write(d["genesis_pin_plan"], self.before)
        self.assert_six(R.receive(signal, intr_carrier=cite, org_ledger=bare, contract_bytes=pinned),
                        "PRE_PIN_INGRESS_CLOSED")

        def tamper(source):
            source["evidence"]["message"]["body"]["node_ref"] = "n-1"
            return source
        bare2, _, cite2 = self.org_emitted(name="tampered", source_edit=tamper)
        self.assert_six(R.receive(signal, intr_carrier=cite2, org_ledger=bare2, contract_bytes=self.before),
                        carrier.FAILURE_CODE)

    def test_a_source_half_missing_endpoint_kind_fails_closed_not_keyerror(self):
        """LC-KV-20: the shared carrier refuses an incomplete source half; destination_evidence never raises."""
        signal = R.genesis_signal("sha256:" + "a" * 64, self.contract)
        cid = "intr-path-v1:StegVerse-org/.github->StegVerse-org:genesis-pin"
        for drop in carrier.SOURCE_REBUILD_KEYS:
            ev = carrier.source_evidence(signal, cid)
            ev.pop(drop)
            core = {k: v for k, v in ev.items()
                    if k not in ("payload_sha256", "disposition", "communication_id", "boundary_evidence")}
            ev["payload_sha256"] = carrier.sha(core)
            source = receipt({"schema": carrier.RECEIPT_SCHEMA, "repository": "StegVerse-org/.github",
                              "transition_class": carrier.SOURCE_CLASS, "previous_receipt_sha256": None,
                              "evidence": ev})
            dest = receipt({"schema": carrier.RECEIPT_SCHEMA, "transition_class": carrier.DESTINATION_CLASS,
                            "evidence": {"schema": carrier.DESTINATION_EVIDENCE_SCHEMA,
                                         "addressed_location": carrier.ORG_LEDGER_LOCATION,
                                         "source_repository_receipt_sha256": source["receipt_sha256"],
                                         "boundary_evidence": {"operation": carrier.DESTINATION_OPERATION}}})
            got = carrier.verify(signal, destination_receipt_sha256=dest["receipt_sha256"],
                                 org_ledger_head_receipt_sha256=dest["receipt_sha256"], org_chain=[dest],
                                 retained_source=source)
            if drop == "communication_id":
                self.assertIsNotNone(got)          # outside the payload digest; still refused, never raised
            else:
                self.assertEqual(got[0], "INTR_SOURCE_EVIDENCE_INCOMPLETE", (drop, got))

    def test_receiver_reuses_the_carrier_unchanged_and_is_wired_declaratively(self):
        got = "sha256:" + hashlib.sha256((ROOT / "llm_adapter/intr_transport_carrier.py").read_bytes()).hexdigest()
        self.assertEqual(got, self.CARRIER_SHA)        # byte copy of #432/#433's module
        source = (ROOT / "scripts/llm_adapter_genesis_pin_ingress.py").read_text()
        self.assertNotIn("designated_org_ledger(", source.replace('"', ""))  # never the pin-gated read
        self.assertNotIn("observe(", source)
        tree = ast.parse(source)
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                names.add((n.module or "").split(".")[0])
        self.assertFalse(names & {"socket", "urllib", "http", "requests", "time", "datetime", "random", "secrets",
                                  "subprocess"})
        decl = json.loads((ROOT / ".stegverse/transition-ledger/genesis-pin-transition.v1.json").read_text())
        trig = decl["trigger"]
        self.assertEqual(trig["kind"], "INTR_INGRESS_SIGNAL")
        self.assertEqual(trig["signal_class"], R.SIGNAL_CLASS)
        self.assertEqual(trig["receiver"]["entrypoint"], R.ENTRYPOINT)
        self.assertEqual(trig["carrier_classes"], [carrier.SOURCE_CLASS, carrier.DESTINATION_CLASS])
        self.assertIn("intr-path-transfer.yml", trig["org_side_emitter"])
        self.assertIs(trig["new_organization_workflow"], False)



@with_append_route
class GenesisPinContractPathTests(unittest.TestCase):
    """Lane D finding 5: REPOSITORY_LEDGER_GENESIS_PIN can target StegVerse-Labs/continuity-vault-kit's KV and SKAP
    Vault ledger contracts (designated in cvk#263 @20451a0c, #431 shape, genesis null) through an allowlisted,
    repo-relative contract path. The fixtures are byte copies of cvk#263's two contracts."""

    CVK = ROOT / "tests/fixtures/cvk-receipt-ledger-contracts"
    CVK_SHA = {"01_KV_Ledger": "81dbc78b0cb21c8ce06faadbca0b9b0521636800ca99a886c24742a2aa35af57",
               "02_SKAP_Vault_Ledger": "153c32e62450b105805abb9e1d366bb32ece768b5caf497ca2dc54e095565c7f"}

    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.tmp = Path(self._t.name)

    def cvk_checkout(self):
        checkout = self.tmp / "cvk"
        (checkout / ".stegverse/receipt-ledgers").mkdir(parents=True)
        for name, want in self.CVK_SHA.items():
            raw = (self.CVK / (name + ".contract.json")).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), want)            # byte copy of cvk#263
            (checkout / ".stegverse/receipt-ledgers" / (name + ".contract.json")).write_bytes(raw)
        return checkout

    def ledger_for(self, repository, name):
        namespace = "repository-ledger/" + repository
        work = self.tmp / (name + "-work")
        store = work / namespace
        (store / "receipts").mkdir(parents=True)
        g = receipt({"schema": "stegverse.repo-transition-receipt/v1", "repository": repository,
                     "transition_id": "REPOSITORY_LEDGER_INITIALIZATION:" + repository,
                     "transition_class": "REPOSITORY_LEDGER_INITIALIZATION", "previous_receipt_sha256": None,
                     "evidence": {"namespace": namespace}, "hb_reference": {"epoch": 446655631,
                                                                            "derived_from_clock": False}})
        (store / "receipts" / (g["receipt_sha256"][7:] + ".json")).write_text(json.dumps(g))
        (store / "HEAD.json").write_text(json.dumps({"receipt_sha256": g["receipt_sha256"]}))
        git(work, "init", "-q")
        git(work, "add", ".")
        git(work, "commit", "-q", "-m", "ledger")
        bare = self.tmp / (name + ".git")
        git(self.tmp, "clone", "-q", "--bare", str(work), str(bare))
        git(self.tmp, "--git-dir", str(bare), "update-ref", M.LEDGER_REF, "HEAD")
        tip = git(self.tmp, "--git-dir", str(bare), "rev-parse", M.LEDGER_REF)
        tree = git(self.tmp, "--git-dir", str(bare), "rev-parse", f"{tip}:{namespace}")
        body = {**location.head_attestation_body(g["receipt_sha256"], g["receipt_sha256"], tree),
                "org_ledger_location": "refs/stegverse/organization-ledger:" + namespace}
        att = {**body, "key_id": ROUTE_REF["key_id"],
               "signature_b64": signer.sign_b64(location.head_attestation_message(body), ROUTE_SEED)}
        return str(bare), g, att

    def test_both_cvk_contracts_are_planned_through_the_allowlisted_path(self):
        checkout = self.cvk_checkout()
        for name in self.CVK_SHA:
            rel = f".stegverse/receipt-ledgers/{name}.contract.json"
            self.assertIn(rel, P.CONTRACT_PATHS)
            before = (checkout / rel).read_bytes()
            repository = json.loads(before)["repository"]
            bare, g, att = self.ledger_for(repository, name)
            d = P.plan(org_ledger=bare, genesis_receipt_sha256=g["receipt_sha256"], org_ledger_head_attestation=att,
                       contract_path=rel, checkout=checkout)
            self.assertEqual(d["disposition"], M.ALLOW, d)
            self.assertEqual(d["contract_write"]["path"], rel)
            self.assertEqual(d["consumes_receipt"]["emit_append"]["evidence"]["contract_path"], rel)
            after = json.loads(P.apply_write(d, before))
            self.assertEqual(after["repository_ledger_location"]["expected_genesis_receipt_sha256"], g["receipt_sha256"])
            self.assertEqual(json.loads(before)["repository_ledger_location"]["expected_genesis_receipt_sha256"], None)
            # the attestation binds the location: LLM-adapter's location, or the other cvk ledger's, does not verify
            for other in (location.ORG_LEDGER_LOCATION, "refs/stegverse/organization-ledger:repository-ledger/x"):
                forged = {**att, "org_ledger_location": other}
                r = P.plan(org_ledger=bare, org_ledger_head_attestation=forged, contract_path=rel, checkout=checkout)
                self.assertEqual(r["failure_code"], "ORG_LEDGER_HEAD_NOT_AUTHENTICATED")
            # production (no published head signer) refuses MERGE_APPEND_PATH_NOT_ADMITTED for cvk too
            from unittest import mock
            with mock.patch.object(location, "load_head_signers", return_value=[]):
                r = P.plan(org_ledger=bare, org_ledger_head_attestation=att, contract_path=rel, checkout=checkout)
            self.assertEqual(r["failure_code"], "MERGE_APPEND_PATH_NOT_ADMITTED")
            # the pre-pin receiver carries the same parameter
            signal = R.genesis_signal(g["receipt_sha256"], json.loads(before))
            r = R.receive(signal, intr_carrier={"org_ledger_head_attestation": att}, org_ledger=bare,
                          contract_path=rel, checkout=checkout)
            self.assertEqual(r["failure_code"], carrier.FAILURE_CODE)   # planned, then the LLM-adapter-bound carrier
            self.assertNotEqual(r["failure_code"], "CONTRACT_PATH_NOT_ALLOWLISTED")

    def test_traversal_and_unlisted_contract_paths_are_refused_with_six_fields(self):
        checkout = self.cvk_checkout()
        for bad in ("../.stegverse/receipt-ledgers/01_KV_Ledger.contract.json",
                    ".stegverse/receipt-ledgers/../../etc/passwd", "/etc/passwd",
                    "./.stegverse/transition-ledger/contract.json", ".stegverse//transition-ledger/contract.json",
                    ".stegverse\\receipt-ledgers\\01_KV_Ledger.contract.json", "C:/x.json",
                    ".stegverse/receipt-ledgers/03_Other.contract.json", "", None, 7):
            d = P.plan(org_ledger=None, contract_path=bad, checkout=checkout)
            self.assertEqual((d["disposition"], d["failure_code"]), (M.FAIL_CLOSED, "CONTRACT_PATH_NOT_ALLOWLISTED"), bad)
            for f in SIX:
                self.assertTrue(isinstance(d[f], str) and d[f], f)
            r = R.receive({}, intr_carrier={}, org_ledger=None, contract_path=bad, checkout=checkout)
            self.assertEqual(r["failure_code"], "CONTRACT_PATH_NOT_ALLOWLISTED", bad)
        # an allowlisted path whose bytes lack the #431 shape is refused too
        shaped = json.loads((checkout / P.CONTRACT_PATHS[1]).read_text())
        shaped["repository_ledger_location"]["namespace"] = "repository-ledger/StegVerse-org/LLM-adapter"
        d = P.plan(org_ledger=None, contract_path=P.CONTRACT_PATHS[1], contract_bytes=json.dumps(shaped).encode())
        self.assertEqual(d["failure_code"], "CONTRACT_NOT_431_SHAPE")
        self.assertEqual(P.contract_path_failure(P.CONTRACT_REL), None)    # the default is unchanged


class CallerWrittenLedgerCopyTests(unittest.TestCase):
    """LC-KV-19, P1 probe row CALLER_WRITTEN_GENESIS_AND_CARRIER_ON_A_CALLER_LEDGER_COPY (negative).

    A caller builds its own copy of refs/stegverse/organization-ledger holding its own REPOSITORY_LEDGER_INITIALIZATION
    genesis and its own INTR_MESH_PATH_TRANSFER / INTR_MESH_PATH_INGRESS pair carrying a well-formed genesis-observed
    signal. Before LC-KV-19 the planner and the pre-pin receiver accepted it. The genesis may now be authenticated only
    from the published ref read-back plus the head-signer attestation (ORG-LEDGER-HEAD-SIGNER-001); both are required.
    """

    PROBE_ROW = "CALLER_WRITTEN_GENESIS_AND_CARRIER_ON_A_CALLER_LEDGER_COPY"

    def setUp(self):
        self.i = GenesisPinPrePinIngressTests()
        self.i.setUp()
        self.addCleanup(self.i.tearDown)
        self.bare, self.genesis, self.signal, self.cite = self.i.carried(name="caller-copy")

    def receive(self, cite):
        return R.receive(self.signal, intr_carrier=cite, org_ledger=self.bare, contract_bytes=self.i.before)

    def test_production_refuses_the_caller_copy_merge_append_path_not_admitted(self):
        # production publishes no head signer: an attestation of any kind decides nothing
        self.assertEqual(location.load_head_signers(), [])
        for cite in (self.cite, {**self.cite, "org_ledger_head_attestation": None},
                     {**self.cite, "org_ledger_head_attestation": attest(self.bare, seed=b"c" * 32, key_id="caller")}):
            d = self.receive(cite)
            self.i.assert_six(d, "MERGE_APPEND_PATH_NOT_ADMITTED")
            self.assertEqual(d["failed_predicate"], P.HEAD_PREDICATE)
            self.assertIn("ORG-LEDGER-HEAD-SIGNER-001", d["required_evidence_or_repair"])
            self.assertEqual(d["next_attempt"], P.HEAD_NEXT)
        p = P.plan(org_ledger=self.bare, genesis_receipt_sha256=self.genesis["receipt_sha256"],
                   contract_bytes=self.i.before, org_ledger_head_attestation=self.cite["org_ledger_head_attestation"])
        self.assertEqual((p["disposition"], p["failure_code"]), ("FAIL_CLOSED", "MERGE_APPEND_PATH_NOT_ADMITTED"))
        self.assertIsNone(p["contract_write"])
        self.assertIsNone(p["consumes_receipt"])

    def test_with_a_published_signer_only_its_attestation_of_this_copy_counts(self):
        from unittest import mock
        with mock.patch.object(location, "load_head_signers", return_value=[dict(ROUTE_REF)]):
            caller_key = attest(self.bare, seed=b"c" * 32)                        # signed by an unpublished key
            caller_id = attest(self.bare, seed=b"c" * 32, key_id="caller-key")
            other_tree = attest(self.bare, namespace_tree_oid="0" * 40)           # a genuine signer, another tree
            other_genesis = attest(self.bare, genesis_receipt_sha256="sha256:" + "a" * 64)
            for att in (None, {}, caller_key, caller_id, other_tree, other_genesis):
                d = self.receive({**self.cite, "org_ledger_head_attestation": att})
                self.i.assert_six(d, "ORG_LEDGER_HEAD_NOT_AUTHENTICATED")
                self.assertEqual(d["failed_predicate"], P.HEAD_PREDICATE)
            # a genuine attestation of another ledger copy does not carry over to the caller's copy
            bare2, _, _, cite2 = self.i.carried(name="published")
            d = self.receive({**self.cite, "org_ledger_head_attestation": cite2["org_ledger_head_attestation"]})
            self.i.assert_six(d, "ORG_LEDGER_HEAD_NOT_AUTHENTICATED")
            # the positive control: the same copy with the published signer's attestation of exactly it
            self.assertEqual(self.receive(self.cite)["disposition"], R.ACCEPTED)

    def test_the_head_check_is_network_free_and_reuses_432s_module_byte_identically(self):
        pins = {"llm_adapter/org_ledger_location.py": "b51e6a8bd39ba6fd83044222a3858a2cb0c437020e3e9abbe97c4494d41f2681",
                "llm_adapter/ed25519_verify.py": "ab05e39a3e40b99f02ff199b178554e0ba435c3ff387dca3f896619770770232",
                "llm_adapter/healthy_node_evaluator.py":
                    "fdaa20053c527927067d16b011889ca84089b9750e95e291021310c669451f58",
                "tests/ed25519_test_signer.py": "3173bfcfca33129cd31942783b9e3e4c9380022f308f2fc31ccdda3dc2f6fe52"}
        for rel, want in pins.items():
            self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), want, rel)
        signers = json.loads((ROOT / ".stegverse/node-ledger/org-ledger-head-signers.v1.json").read_text())
        self.assertEqual(signers["signers"], [])
        for rel in ("llm_adapter/org_ledger_location.py", "llm_adapter/ed25519_verify.py",
                    "scripts/llm_adapter_repository_ledger_genesis_pin.py", "scripts/llm_adapter_genesis_pin_ingress.py"):
            names = set()
            for n in ast.walk(ast.parse((ROOT / rel).read_text())):
                if isinstance(n, ast.Import):
                    names |= {a.name.split(".")[0] for a in n.names}
                elif isinstance(n, ast.ImportFrom):
                    names.add((n.module or "").split(".")[0])
            self.assertFalse(names & {"socket", "urllib", "http", "requests", "time", "datetime", "random", "secrets"},
                             rel)


if __name__ == "__main__":
    unittest.main()
