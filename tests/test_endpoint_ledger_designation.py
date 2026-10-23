"""ENDPOINT-LEDGER-DESIGNATION-001: per-endpoint ledger designation and the store-reader seam.

KV independence (StegVerse-org/.github#160 comments 6371986288 and 6372216673): KV and SKAP_VAULT designate
GATEWAY_ENCRYPTED_BLOB, never GIT_REF on an org ref; their reader is Lane D's (KV-LEDGER-STORE-READER-001) and is
not installed; heads are signed by kv_ledger_head_signer (TVC#542); the newest Org-recorded endpoint_head_sha256 is
the rollback watermark; an empty ledger is never a genesis; one storage provider now, more refused. Fixtures are
this PR's (#431) only; keys are fixture keys only.
"""
from __future__ import annotations

import ast
import contextlib
import copy
import json
import unittest
from pathlib import Path
from unittest import mock

from llm_adapter import endpoint_ledger_designation as eld
from llm_adapter import healthy_node_evaluator as hne
from tests import ed25519_test_signer as signer

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / "tests/fixtures/endpoint-ledger-designation"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def load(name):
    return json.loads((F / name).read_text())


def fixture_signers():
    return [{"key_id": "kv-fixture-key", "algorithm": "Ed25519", "public_key_b64": signer.public_key_b64(),
             "custody": "TEST_FIXTURE_ONLY", "signs": "KV_LEDGER_HEAD"}]


def attest(designation, chain, key_id="kv-fixture-key", seed=signer.TEST_SEED):
    store = designation["stores"][0]
    body = eld.kv_head_attestation_body(designation, store, chain[-1]["receipt_sha256"], chain[0]["receipt_sha256"])
    return {**body, "key_id": key_id, "signature_b64": signer.sign_b64(eld.kv_head_attestation_message(body), seed)}


class Base(unittest.TestCase):
    def setUp(self):
        self.kv = load("kv.designation.json")
        self.chain = load("kv-chain.json")["chain"]
        self.org_chain = load("org-linked-receipts.json")["chain"]

    def assert_six(self, result, code, disposition="FAIL_CLOSED"):
        self.assertIsNotNone(result)
        self.assertEqual((result["disposition"], result["failure_code"]), (disposition, code), result)
        for field in SIX:
            self.assertIsInstance(result[field], str, field)
            self.assertTrue(result[field], field)
        for word in ("grant", "approved", "authorized", "merge-ready"):
            self.assertNotIn(word, json.dumps(result).lower())

    @contextlib.contextmanager
    def lane_d_reader_stub(self, chain):
        """TEST-ONLY stand-in for Lane D's GATEWAY_ENCRYPTED_BLOB reader, to exercise the seam; not a reader."""
        @contextlib.contextmanager
        def reader(designation, store, source, head_attestation):
            yield copy.deepcopy(chain), None
        with mock.patch.dict(eld._READERS, {eld.GATEWAY_ENCRYPTED_BLOB: reader}):
            yield


class DesignationTests(Base):
    def test_fixtures_are_sealed_and_kv_designates_its_own_blob_store(self):
        for r in self.chain:
            self.assertEqual(r["receipt_sha256"], hne.sha({k: v for k, v in r.items() if k != "receipt_sha256"}))
        self.assertIsNone(eld.designation_failure(self.kv))
        self.assertIsNone(eld.designation_failure(load("skap.designation.json")))
        self.assertIsNone(eld.designation_failure(load("org-git-ref.designation.json")))
        self.assertEqual(self.kv["stores"][0]["store_type"], eld.GATEWAY_ENCRYPTED_BLOB)
        self.assertEqual(eld.STORE_TYPES, ("GIT_REF", "GATEWAY_ENCRYPTED_BLOB"))
        self.assertEqual(eld.store_location(self.kv["stores"][0]), "gateway:gw-kv-fixture-1/01_KV_Ledger")

    def test_kv_and_skap_on_a_git_ref_are_refused(self):
        self.assert_six(eld.designation_failure(load("kv-on-org-git-ref.designation.json")),
                        "KV_LEDGER_DESIGNATED_ON_GIT_REF")
        skap = load("skap.designation.json")
        skap["stores"] = load("kv-on-org-git-ref.designation.json")["stores"]
        self.assert_six(eld.designation_failure(skap), "KV_LEDGER_DESIGNATED_ON_GIT_REF")
        org = load("org-git-ref.designation.json")
        org["stores"] = self.kv["stores"]
        self.assert_six(eld.designation_failure(org), "ENDPOINT_LEDGER_DESIGNATION_INVALID")

    def test_malformed_designations_are_refused_with_six_fields(self):
        store = self.kv["stores"][0]
        cases = {
            "unknown store_type": ({**self.kv, "stores": [{**store, "store_type": "S3"}]},
                                   "ENDPOINT_LEDGER_STORE_TYPE_UNDECLARED"),
            "external ledger ref in store": ({**self.kv, "stores": [{**store, "ledger_root": "/drive/x"}]},
                                             "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "location not ##_<name>": ({**self.kv, "stores": [{**store, "location": "KV/../x"}]},
                                       "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "org head signer for KV": ({**self.kv, "head_signer_source": "ORG_LEDGER_HEAD_SIGNER"},
                                       "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "KV without watermark": ({**self.kv, "rollback_watermark_source": None},
                                     "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "no stores": ({**self.kv, "stores": []}, "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "extra key": ({**self.kv, "ledger_root": "/x"}, "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "EPHEMERAL is not designated here": ({**self.kv, "endpoint_kind": "EPHEMERAL"},
                                                 "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
        }
        for name, (d, code) in cases.items():
            with self.subTest(name=name):
                self.assert_six(eld.designation_failure(d), code)

    def test_one_provider_now_more_than_one_is_not_yet_supported(self):
        store, failed = eld.select_store(self.kv)
        self.assertIsNone(failed)
        self.assertEqual(store, self.kv["stores"][0])
        store, failed = eld.select_store(load("kv-two-providers.designation.json"))
        self.assertIsNone(store)
        self.assert_six(failed, "ENDPOINT_LEDGER_MULTI_PROVIDER_NOT_SUPPORTED")
        with eld.read_designated(load("kv-two-providers.designation.json"), source=None) as (chain, failed):
            self.assertIsNone(chain)
            self.assert_six(failed, "ENDPOINT_LEDGER_MULTI_PROVIDER_NOT_SUPPORTED")


class ReaderSeamTests(Base):
    def test_the_blob_reader_is_not_installed(self):
        self.assertEqual(set(eld.READERS), {eld.GIT_REF})
        with self.assertRaises(TypeError):
            eld.READERS[eld.GATEWAY_ENCRYPTED_BLOB] = object()     # the seam is read-only at runtime
        for d in (self.kv, load("skap.designation.json")):
            with eld.read_designated(d, source="/any/caller/path", org_chain=self.org_chain) as (chain, failed):
                self.assertIsNone(chain)
                self.assert_six(failed, "ENDPOINT_LEDGER_STORE_READER_NOT_INSTALLED")
                self.assertIn("KV-LEDGER-STORE-READER-001", failed["owning_existing_goal"])
                self.assertIn("Lane D", failed["owning_existing_goal"])

    def test_git_ref_uses_the_unchanged_git_reader(self):
        self.assertIs(eld.READERS[eld.GIT_REF], eld._git_ref_reader)
        source = (ROOT / "llm_adapter/endpoint_ledger_designation.py").read_text()
        self.assertIn("org_ledger_location.designated_org_ledger(source, head_attestation)", source)
        # this contract's designation has a null pin: the git reader's own refusal comes through, six fields
        with eld.read_designated(load("org-git-ref.designation.json"), source="/nonexistent") as (chain, failed):
            self.assertIsNone(chain)
            self.assert_six(failed, "ORG_LEDGER_GENESIS_NOT_PINNED")
        # a GIT_REF store other than the contract's location is not designated
        other = load("org-git-ref.designation.json")
        other["stores"] = [{**other["stores"][0], "namespace": "repository-ledger/StegVerse-org/other"}]
        with eld.read_designated(other, source="/nonexistent") as (chain, failed):
            self.assert_six(failed, "ORG_LEDGER_LOCATION_NOT_DESIGNATED")

    def test_a_plugged_in_reader_still_passes_every_check(self):
        with self.lane_d_reader_stub(self.chain):
            # no kv_ledger_head_signer is published in production
            with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, self.chain),
                                     org_chain=self.org_chain) as (chain, failed):
                self.assert_six(failed, "KV_LEDGER_HEAD_SIGNER_NOT_PUBLISHED")
                self.assertIn("TVC#542", failed["owning_existing_goal"])
            with mock.patch.object(eld, "load_head_signers", return_value=fixture_signers()):
                with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, self.chain),
                                         org_chain=self.org_chain) as (chain, failed):
                    self.assertIsNone(failed)
                    self.assertEqual(chain, self.chain)
                with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, self.chain),
                                         org_chain=None) as (chain, failed):
                    self.assert_six(failed, "KV_LEDGER_ROLLBACK_WATERMARK_UNREAD")


class EmptyLedgerTests(Base):
    def test_an_empty_or_missing_ledger_is_never_a_genesis_for_every_store_type(self):
        designations = {eld.GATEWAY_ENCRYPTED_BLOB: self.kv,
                        eld.GIT_REF: {**load("org-git-ref.designation.json"),
                                      "expected_genesis_receipt_sha256": self.chain[-1]["receipt_sha256"]}}
        self.assertEqual(set(designations), set(eld.STORE_TYPES))
        for st, d in designations.items():
            for empty in ([], None, {}):
                with self.subTest(store_type=st, empty=empty):
                    self.assert_six(eld.chain_failure(d, empty), "ENDPOINT_LEDGER_EMPTY_NOT_A_GENESIS")
                    self.assert_six(eld.chain_admission_failure(d, d["stores"][0], empty, head_attestation=None,
                                                                signers=fixture_signers(), org_chain=[]),
                                    "ENDPOINT_LEDGER_EMPTY_NOT_A_GENESIS")
        with self.lane_d_reader_stub([]):
            with eld.read_designated(self.kv, source=None, org_chain=self.org_chain) as (chain, failed):
                self.assert_six(failed, "ENDPOINT_LEDGER_EMPTY_NOT_A_GENESIS")
        # a chain that does not end at a genesis of the designated class is not taken as one
        headless = self.chain[:-1]
        self.assertIn(eld.chain_failure(self.kv, headless)["failure_code"],
                      ("ENDPOINT_LEDGER_UNREADABLE", "ENDPOINT_LEDGER_EMPTY_NOT_A_GENESIS"))

    def test_genesis_pin_and_seals(self):
        self.assertIsNone(eld.chain_failure(self.kv, self.chain))
        self.assert_six(eld.chain_failure({**self.kv, "expected_genesis_receipt_sha256": None}, self.chain),
                        "ENDPOINT_LEDGER_GENESIS_NOT_PINNED")
        self.assert_six(eld.chain_failure({**self.kv, "expected_genesis_receipt_sha256": "sha256:" + "0" * 64},
                                          self.chain), "ENDPOINT_LEDGER_GENESIS_MISMATCH")
        tampered = copy.deepcopy(self.chain)
        tampered[1]["sequence"] = 9
        self.assert_six(eld.chain_failure(self.kv, tampered), "ENDPOINT_LEDGER_UNREADABLE")


class SignedHeadTests(Base):
    def test_every_kv_head_is_signed_by_kv_ledger_head_signer(self):
        store = self.kv["stores"][0]
        g, h = self.chain[-1]["receipt_sha256"], self.chain[0]["receipt_sha256"]
        self.assertIsNone(eld.kv_head_failure(self.kv, store, g, h, attest(self.kv, self.chain), fixture_signers()))
        self.assertEqual(eld.load_head_signers("KV_LEDGER_HEAD_SIGNER"), [])     # production: none published
        self.assert_six(eld.kv_head_failure(self.kv, store, g, h, attest(self.kv, self.chain), []),
                        "KV_LEDGER_HEAD_SIGNER_NOT_PUBLISHED")
        cases = {
            "no attestation": None,
            "another head": attest(self.kv, self.chain[1:]),
            "unpublished key": attest(self.kv, self.chain, key_id="caller-key"),
            "another key under the published id": attest(self.kv, self.chain, seed=bytes(range(32))),
            "another endpoint": attest(load("skap.designation.json"), self.chain),
        }
        for name, att in cases.items():
            with self.subTest(name=name):
                self.assert_six(eld.kv_head_failure(self.kv, store, g, h, att, fixture_signers()),
                                "KV_LEDGER_HEAD_NOT_AUTHENTICATED")
        # the org head signers never sign a KV head
        self.assertEqual(self.kv["head_signer_source"], "KV_LEDGER_HEAD_SIGNER")
        self.assertEqual(eld.HEAD_SIGNER_FILES["KV_LEDGER_HEAD_SIGNER"][1], "KV_LEDGER_HEAD")
        published = json.loads((ROOT / ".stegverse/node-ledger/kv-ledger-head-signers.v1.json").read_text())
        self.assertEqual(published["signers"], [])


class RollbackTests(Base):
    def test_the_watermark_is_the_newest_org_recorded_head_for_this_endpoint(self):
        heads = eld.org_recorded_endpoint_heads(self.org_chain, self.kv)
        self.assertEqual(heads, [self.chain[0]["receipt_sha256"], self.chain[1]["receipt_sha256"]])
        self.assertEqual(eld.org_recorded_endpoint_heads(self.org_chain, load("skap.designation.json")), [])

    def test_a_head_older_than_the_newest_recorded_is_rollback_detected(self):
        heads = eld.org_recorded_endpoint_heads(self.org_chain, self.kv)
        self.assertIsNone(eld.rollback_failure(self.chain, heads))
        self.assert_six(eld.rollback_failure(self.chain[1:], heads), "KV_LEDGER_HEAD_ROLLBACK_DETECTED", "DENY")
        self.assertIsNone(eld.rollback_failure(self.chain[1:], heads[1:]))   # older watermark: fine
        self.assertIsNone(eld.rollback_failure(self.chain, []))             # nothing recorded yet
        older = self.chain[1:]
        with self.lane_d_reader_stub(older), \
                mock.patch.object(eld, "load_head_signers", return_value=fixture_signers()):
            with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, older),
                                     org_chain=self.org_chain) as (chain, failed):
                self.assertIsNone(chain)
                self.assert_six(failed, "KV_LEDGER_HEAD_ROLLBACK_DETECTED", "DENY")
                self.assertEqual(failed["recorded_head_sha256"], self.chain[0]["receipt_sha256"])


class DeterminismTests(unittest.TestCase):
    def test_no_clock_network_randomness_or_new_dependency(self):
        tree = ast.parse((ROOT / "llm_adapter/endpoint_ledger_designation.py").read_text())
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertFalse(names & {"time", "datetime", "random", "secrets", "socket", "urllib", "http", "requests",
                                  "subprocess", "uuid"}, names)
        self.assertTrue(names <= {"__future__", "base64", "binascii", "contextlib", "json", "re", "pathlib", "types",
                                  "typing", "llm_adapter"}, names)
