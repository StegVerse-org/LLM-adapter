"""ENDPOINT-LEDGER-DESIGNATION-001: per-endpoint recorded receipt chain designation and the access-adapter seam.

KV independence (StegVerse-org/.github#160 comments 6371986288 and 6372216673; corrected by #167 comment
6372442705): KV and SKAP_VAULT designate KV_STORAGE_ENDPOINT (KV Storage Endpoint v2), never GIT_REF on an org ref;
with cvk#263 @706877b6's store keys and chains; the KV receipt-chain reader id is not documented, so a read fails
closed KV_RECEIPT_CHAIN_READER_ID_NOT_DOCUMENTED (KV-SKAP-LEDGER-LOCATION-001); no endpoint is a source of org-ledger
records (#160 comment 6372871021), and an Org crossing receipt is digest-only; both
sides record each crossing, with a supplied epoch (#162 comment 6372641743); heads are signed by kv_ledger_head_signer (TVC#542); the rollback watermark is KV's own recorded
receipt chain head (KV_RECORDED_RECEIPT_CHAIN_HEAD), read from KV's own head record, never the caller (LC-KV-23 (a),
cvk#263 @9bc54d05); the Org side is the required digest-only org_crossing_cross_check, read by the module itself
through ORG_CROSSING_READER and compared only to refuse (LC-KV-23 (b)); keys are closed (CONTRACT_KEY_SCHEMA,
LC-KV-24); the designation fixtures match cvk @9bc54d05's contracts (vendored byte copies); an empty ledger is never a genesis; one storage provider now, more refused. Fixtures are
this PR's (#431) only; keys are fixture keys only.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
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
CVK = F / "cvk263-9bc54d05"
#: StegVerse-Labs/continuity-vault-kit#263 @9bc54d05253b6377d26dd6dd3dac966dc75cdf98 .stegverse/receipt-chains/
CVK_CONTRACT_SHA256 = {
    "stegverse-kv-receipts.contract.json": "sha256:c9cc8913de21183fb23774cd155fee84fd6d275c003e71b2712ad44d30d89ce1",
    "skap-receipts.contract.json": "sha256:7f0a0536214213b6dfc74074fec9c2375d130d875fc7fcc6c7796a77b901a86f"}
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def load(name):
    return json.loads((F / name).read_text())


def fixture_signers():
    return [{"key_id": "kv-fixture-key", "algorithm": "Ed25519", "public_key_b64": signer.public_key_b64(),
             "custody": "TEST_FIXTURE_ONLY", "signs": "KV_RECORDED_RECEIPT_CHAIN_HEAD"}]


def recorded(chain, index=0, **extra):
    """The KV-recorded rollback watermark input (cvk#263 @9bc54d05 recorded_head)."""
    return {"source": "KV_RECORDED_RECEIPT_CHAIN_HEAD", "head_receipt_sha256": chain[index]["receipt_sha256"], **extra}


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

    def reseal(self, receipt, **edit):
        body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
        body.update(edit)
        return {**body, "receipt_sha256": hne.sha(body)}

    @contextlib.contextmanager
    def lane_d_reader_stub(self, chain, head_record="CURRENT", org="FIXTURE"):
        """TEST-ONLY stand-ins for a KV_STORAGE_ENDPOINT access adapter (the chain and KV's own head record) and for
        the Org-side crossing readback (ORG_CROSSING_READER), to exercise the seams; not adapters."""
        if head_record == "CURRENT":
            head_record = eld.head_record_entries([chain[0]["receipt_sha256"]]) if chain else []
        observed = self.org_chain if org == "FIXTURE" else org

        @contextlib.contextmanager
        def reader(designation, store, source, head_attestation):
            yield copy.deepcopy(chain), copy.deepcopy(head_record), None
        with mock.patch.dict(eld._READERS, {eld.KV_STORAGE_ENDPOINT: reader}), \
                mock.patch.object(eld, "ORG_CROSSING_READER",
                                  None if observed is None else (lambda d: copy.deepcopy(observed))):
            yield


class DesignationTests(Base):
    def test_fixtures_are_sealed_and_kv_designates_its_own_storage_endpoint(self):
        for r in self.chain:
            self.assertEqual(r["receipt_sha256"], hne.sha({k: v for k, v in r.items() if k != "receipt_sha256"}))
        self.assertIsNone(eld.designation_failure(self.kv))
        self.assertIsNone(eld.designation_failure(load("skap.designation.json")))
        self.assertIsNone(eld.designation_failure(load("org-git-ref.designation.json")))
        self.assertEqual(self.kv["stores"][0]["store_type"], eld.KV_STORAGE_ENDPOINT)
        self.assertEqual(eld.STORE_TYPES, ("GIT_REF", "KV_STORAGE_ENDPOINT", "NODE_STORAGE_ENDPOINT"))
        self.assertEqual(eld.store_location(self.kv["stores"][0]), "storage-endpoint:google-drive/_StegVerse/Receipts")
        # Lane D's store (cvk#263 @706877b6 kv_receipt_ledgers.STORE_KEYS); nothing claims encryption or a gateway
        self.assertEqual(self.kv["stores"][0], {
            "store_type": "KV_STORAGE_ENDPOINT", "storage_endpoint_schema": "stegverse.kv.storage-endpoint-descriptor/v2",
            "provider_id": "google-drive", "access_adapter": "provider-or-file-provider", "kv_class": "STEGVERSE_KV",
            "kv_request_id": "SITE-CLOUD-KV-4347408852127319cbda574f02e03edb", "location": "_StegVerse/Receipts"})
        self.assertEqual(load("skap.designation.json")["stores"][0]["location"], "_Vault/SKAP/Receipts")
        self.assertEqual(self.kv["rollback_watermark_source"], {
            "source": "KV_RECORDED_RECEIPT_CHAIN_HEAD", "org_crossing_cross_check": {
                "source": "ORG_LEDGER_LINKED_RECEIPTS_ENDPOINT_HEAD",
                "path_ids": ["StegVerse-org->STEGVERSE_KV:_StegVerse/Receipts:intr-destination"],
                "role": "DIGEST_ONLY_CROSS_CHECK_NEVER_WATERMARK"}})
        self.assertEqual(eld.crossing_path_ids(self.kv),
                         ["StegVerse-org->STEGVERSE_KV:_StegVerse/Receipts:intr-destination"])
        self.assertEqual(eld.kv_path_id("_Vault/SKAP/Receipts"),
                         "StegVerse-org->STEGVERSE_KV:_Vault/SKAP/Receipts:intr-destination")
        source = (ROOT / "llm_adapter/endpoint_ledger_designation.py").read_text().split('"""', 2)[2]   # code
        for withdrawn in ("GATEWAY_ENCRYPTED_BLOB", "gateway_node_id", "KV-LEDGER-STORE-READER-001", "ECOSYSTEM-OWN-KV-001",
                          "SVKV", "decrypts", "STORE_READER_NOT_INSTALLED"):
            self.assertNotIn(withdrawn, source)

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
                                             "KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY"),
            "git ref fields in a KV store": ({**self.kv, "stores": [{**store, "ref": "refs/x"}]},
                                             "KV_LEDGER_DESIGNATED_ON_GIT_REF"),
            "location traverses": ({**self.kv, "stores": [{**store, "location": "_StegVerse/../x"}]},
                                   "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "KV at the SKAP location": ({**self.kv, "stores": [{**store, "location": "_Vault/SKAP/Receipts"}]},
                                        "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "undocumented adapter": ({**self.kv, "stores": [{**store, "access_adapter": "provider-native"}]},
                                     "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "another descriptor schema": ({**self.kv, "stores": [{**store, "storage_endpoint_schema": "v1"}]},
                                          "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "another kv_class": ({**self.kv, "stores": [{**store, "kv_class": "SITE_KV"}]},
                                 "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "gateway_node_id key": ({**self.kv, "stores": [{**store, "gateway_node_id": "g"}]},
                                    "KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY"),
            "withdrawn gateway store keys": ({**self.kv, "stores": [{"store_type": "GATEWAY_ENCRYPTED_BLOB",
                                                                     "gateway_node_id": "g", "location": "01_KV_Ledger",
                                                                     "provider": "google-drive"}]},
                                             "KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY"),
            "withdrawn gateway store type": ({**self.kv, "stores": [{**store, "store_type": "GATEWAY_ENCRYPTED_BLOB"}]},
                                             "ENDPOINT_LEDGER_STORE_TYPE_UNDECLARED"),
            "org head signer for KV": ({**self.kv, "head_signer_source": "ORG_LEDGER_HEAD_SIGNER"},
                                       "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "KV without watermark": ({**self.kv, "rollback_watermark_source": None},
                                     "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "no stores": ({**self.kv, "stores": []}, "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "extra key": ({**self.kv, "ledger_root": "/x"}, "KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY"),
            "watermark source not KV's": ({**self.kv, "rollback_watermark_source": {"source": "CALLER_SUPPLIED"}},
                                          "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "cross-check as the watermark role": (
                {**self.kv, "rollback_watermark_source": {**self.kv["rollback_watermark_source"],
                                                          "org_crossing_cross_check": {
                    **self.kv["rollback_watermark_source"]["org_crossing_cross_check"], "role": "WATERMARK"}}},
                "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "cross-check with no path_ids": (
                {**self.kv, "rollback_watermark_source": {**self.kv["rollback_watermark_source"],
                                                          "org_crossing_cross_check": {
                    **self.kv["rollback_watermark_source"]["org_crossing_cross_check"], "path_ids": []}}},
                "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
            "a watermark on the Org's own designation": (
                {**load("org-git-ref.designation.json"), "rollback_watermark_source": {
                    "source": "KV_RECORDED_RECEIPT_CHAIN_HEAD"}}, "ENDPOINT_LEDGER_DESIGNATION_INVALID"),
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
    def test_the_reader_id_is_not_documented(self):
        self.assertEqual(set(eld.READERS), {eld.GIT_REF})
        with self.assertRaises(TypeError):
            eld.READERS[eld.KV_STORAGE_ENDPOINT] = object()     # the seam is read-only at runtime
        for d in (self.kv, load("skap.designation.json")):
            with eld.read_designated(d, source="/any/caller/path") as (chain, failed):
                self.assertIsNone(chain)
                self.assert_six(failed, "KV_RECEIPT_CHAIN_READER_ID_NOT_DOCUMENTED")
                self.assertEqual(failed["failed_predicate"],
                                 "SUCCESSOR_READER_ID_DEFINED_BY_THE_KV_STORAGE_ENDPOINT_V2_MODEL")
                self.assertEqual(failed["reader_id"], "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED")
                self.assertIn("KV-SKAP-LEDGER-LOCATION-001", failed["owning_existing_goal"])
                self.assertIn("KV-SKAP-VAULT-FUNCTIONAL-001", failed["owning_existing_goal"])
                self.assertIn("runtime.kv_receipt_ledgers.read_receipt_ledger", failed["reader_entrypoints"][0])
                for withdrawn in ("KV-LEDGER-STORE-READER-001", "ECOSYSTEM-OWN-KV-001"):
                    self.assertNotIn(withdrawn, json.dumps(failed))

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
            with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, self.chain)) as (chain, failed):
                self.assert_six(failed, "KV_LEDGER_HEAD_SIGNER_NOT_PUBLISHED")
                self.assertIn("TVC#542", failed["owning_existing_goal"])
            with mock.patch.object(eld, "load_head_signers", return_value=fixture_signers()):
                with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, self.chain), recorded_head=recorded(self.chain)) as (chain, failed):
                    self.assertIsNone(failed)
                    self.assertEqual(chain, self.chain)
                # the caller's recorded_head is only a claim: absent, the head record alone decides
                with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, self.chain)) as (chain, failed):
                    self.assertIsNone(failed)
            with mock.patch.object(eld, "load_head_signers", return_value=fixture_signers()):
                for absent in (None, []):
                    with self.subTest(head_record=absent), self.lane_d_reader_stub(self.chain, head_record=absent):
                        with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, self.chain),
                                                 recorded_head=recorded(self.chain)) as (chain, failed):
                            self.assert_six(failed, "KV_LEDGER_HEAD_ROLLBACK_WATERMARK_MISSING")
                            self.assertEqual(failed["failure_class"], "A")
                # the chain holds an endpoint crossing record and no Org side is observable: not observed, class B
                with self.lane_d_reader_stub(self.chain, org=None):
                    with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, self.chain),
                                             recorded_head=recorded(self.chain)) as (chain, failed):
                        self.assert_six(failed, "KV_CROSSING_RECORD_NOT_OBSERVED")
                        self.assertEqual((failed["failure_class"], failed["failed_predicate"]),
                                         ("B", "ORG_SIDE_OF_EACH_CROSSING_OBSERVED_BY_THE_READER"))


class EmptyLedgerTests(Base):
    def test_an_empty_or_missing_ledger_is_never_a_genesis_for_every_store_type(self):
        designations = {eld.KV_STORAGE_ENDPOINT: self.kv,
                        eld.GIT_REF: {**load("org-git-ref.designation.json"),
                                      "expected_genesis_receipt_sha256": self.chain[-1]["receipt_sha256"]},
                        eld.NODE_STORAGE_ENDPOINT: {**load("node.designation.json"),
                                                    "expected_genesis_receipt_sha256": self.chain[-1]["receipt_sha256"]}}
        self.assertEqual(set(designations), set(eld.STORE_TYPES))
        for st, d in designations.items():
            for empty in ([], None, {}):
                with self.subTest(store_type=st, empty=empty):
                    self.assert_six(eld.chain_failure(d, empty), "ENDPOINT_LEDGER_EMPTY_NOT_A_GENESIS")
                    self.assert_six(eld.chain_admission_failure(d, d["stores"][0], empty, head_attestation=None,
                                                                signers=fixture_signers(), head_record=[],
                                                                org_chain=[]),
                                    "ENDPOINT_LEDGER_EMPTY_NOT_A_GENESIS")
        with self.lane_d_reader_stub([]):
            with eld.read_designated(self.kv, source=None) as (chain, failed):
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
        self.assertEqual(eld.HEAD_SIGNER_FILES["KV_LEDGER_HEAD_SIGNER"][1], "KV_RECORDED_RECEIPT_CHAIN_HEAD")
        raw = (ROOT / ".stegverse/node-ledger/kv-ledger-head-signers.v1.json").read_bytes()
        # byte-identical to Lane D's copy (StegVerse-Labs/continuity-vault-kit#263 @706877b6)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "758d798388599171c145e3d19ca4eb155ad3d3762a3721804da65c08ebc1fe72")
        published = json.loads(raw)
        self.assertEqual(published["signers"], [])


class RollbackTests(Base):
    """cvk#263 @9bc54d05: the watermark is KV's own recorded receipt chain head; it is required, never Org-sourced,
    and does not depend on any Org chain or declared path."""

    def test_the_watermark_is_kvs_own_recorded_head_and_is_required(self):
        """LC-KV-23 (a): the watermark is read from KV's own head record; the caller's recorded_head is a claim."""
        self.assertEqual(eld.WATERMARK_SOURCE, "KV_RECORDED_RECEIPT_CHAIN_HEAD")
        self.assertEqual((eld.HEAD_RECORD, eld.HEAD_RECORD_SCHEMA, eld.HEAD_RECORD_KEYS),
                         ("head-record.v1.jsonl", "stegverse.kv-recorded-head/v1",
                          ("schema", "head_receipt_sha256", "previous_record_sha256", "record_sha256")))
        heads = [r["receipt_sha256"] for r in reversed(self.chain)]
        record = eld.head_record_entries(heads)
        self.assertEqual(eld.recorded_head_failure(self.chain, record), (self.chain[0]["receipt_sha256"], None))
        self.assertIsNone(record[0]["previous_record_sha256"])
        self.assertEqual(record[1]["previous_record_sha256"], record[0]["record_sha256"])
        for name, bad in {"absent": None, "empty": [], "not a list": {"x": 1},
                          "relinked": [record[0], {**record[1], "previous_record_sha256": None}],
                          "resealed": [{**record[0], "record_sha256": "sha256:" + "0" * 64}],
                          "extra key": [{**record[0], "extra": 1}],
                          "another schema": [{**record[0], "schema": "x"}],
                          "backwards": eld.head_record_entries(list(reversed(heads)))}.items():
            with self.subTest(name=name):
                got = eld.recorded_head_failure(self.chain, bad)[1]
                self.assert_six(got, "KV_LEDGER_HEAD_ROLLBACK_WATERMARK_MISSING")
                self.assertEqual((got["failed_predicate"], got["failure_class"]), ("ROLLBACK_WATERMARK_SUPPLIED", "A"))
        off = eld.head_record_entries(heads + ["sha256:" + "e" * 64])
        got = eld.recorded_head_failure(self.chain, off)[1]
        self.assert_six(got, "KV_LEDGER_HEAD_ROLLBACK_DETECTED", "DENY")
        self.assertEqual(got["failure_class"], "C")
        # the claim
        self.assertEqual(eld.kv_watermark(None), (None, None))
        claim, failed = eld.kv_watermark(recorded(self.chain, org_crossing_cross_check=self.org_chain[2]["receipt_sha256"]))
        self.assertIsNone(failed)
        self.assertEqual(claim, {"source": "KV_RECORDED_RECEIPT_CHAIN_HEAD",
                                 "head_receipt_sha256": self.chain[0]["receipt_sha256"]})
        for missing in ("sha256:" + "a" * 64, {"head_receipt_sha256": self.chain[0]["receipt_sha256"]},
                        {**recorded(self.chain), "head_receipt_sha256": "abc"},
                        {**recorded(self.chain), "org_crossing_cross_check": "x"},
                        {**recorded(self.chain), "extra": 1}, {**recorded(self.chain), "source": "CALLER"}):
            with self.subTest(missing=missing):
                got = eld.kv_watermark(missing)[1]
                self.assert_six(got, "KV_LEDGER_HEAD_ROLLBACK_WATERMARK_MISSING")
                self.assertEqual((got["failed_predicate"], got["failure_class"]), ("ROLLBACK_WATERMARK_SUPPLIED", "A"))

    def test_an_org_sourced_watermark_is_refused_class_a(self):
        for source in ("ORG_LEDGER_LINKED_RECEIPTS_ENDPOINT_HEAD", "ORG_RECORDED_HEAD", "StegVerse-org/.github",
                       "refs/stegverse/organization-ledger", "GIT_REF"):
            with self.subTest(source=source):
                got = eld.kv_watermark({**recorded(self.chain), "source": source})[1]
                self.assert_six(got, "KV_ROLLBACK_WATERMARK_ORG_LEDGER_SOURCED")
                self.assertEqual((got["failed_predicate"], got["failure_class"]),
                                 ("ROLLBACK_WATERMARK_SOURCED_FROM_KV_OWN_RECEIPT_CHAIN", "A"))
                for name in ("kv.designation.json", "skap.designation.json"):
                    d = load(name)
                    d["rollback_watermark_source"]["source"] = source
                    self.assert_six(eld.designation_failure(d), "KV_ROLLBACK_WATERMARK_ORG_LEDGER_SOURCED")

    def test_the_org_cross_check_is_required_on_intr_destination_path_ids(self):
        """LC-KV-23 (b) (cvk#263 @9bc54d05): the cross-check is required; every path_id ends :intr-destination."""
        self.assertEqual(eld.PATH_ID_SUFFIX, ":intr-destination")
        xc = self.kv["rollback_watermark_source"]["org_crossing_cross_check"]
        for name in ("kv.designation.json", "skap.designation.json", "node.designation.json"):
            d = load(name)
            self.assertIsNone(eld.designation_failure(d))
            source = d["rollback_watermark_source"]["source"]
            for bad in ({"source": source}, {"source": source, "org_crossing_cross_check": None},
                        {"source": source, "org_crossing_cross_check": {**xc, "path_ids": ["a->b:intr-source"]}},
                        {"source": source, "org_crossing_cross_check": {**xc, "path_ids": ["x", 1]}}):
                with self.subTest(name=name, bad=bad):
                    self.assert_six(eld.designation_failure({**d, "rollback_watermark_source": bad}),
                                    "ENDPOINT_LEDGER_DESIGNATION_INVALID")
        head_only = [r for r in self.chain if r.get("transition_class") not in eld.CROSSING_CLASSES]
        self.assertEqual(head_only, self.chain[-1:])
        with mock.patch.object(eld, "load_head_signers", return_value=fixture_signers()):
            # a never-crossed chain with nothing observable skips the comparison; the head record alone decides
            self.assertIsNone(eld.chain_admission_failure(
                self.kv, self.kv["stores"][0], head_only, head_attestation=attest(self.kv, head_only),
                signers=fixture_signers(), head_record=eld.head_record_entries([head_only[0]["receipt_sha256"]]),
                org_chain=None))
            self.assert_six(eld.chain_admission_failure(
                self.kv, self.kv["stores"][0], head_only, head_attestation=attest(self.kv, head_only),
                signers=fixture_signers(), head_record=None, org_chain=None, recorded_head=recorded(head_only)),
                "KV_LEDGER_HEAD_ROLLBACK_WATERMARK_MISSING")

    def test_the_org_side_is_read_by_the_module_never_the_caller(self):
        """LC-KV-23 (b): no org_chain argument; production ORG_CROSSING_READER is None (not observable)."""
        self.assertIsNone(eld.ORG_CROSSING_READER)
        self.assertNotIn("org_chain", eld.read_designated.__wrapped__.__code__.co_varnames[:5])
        with self.assertRaises(TypeError):
            with eld.read_designated(self.kv, source=None, org_chain=self.org_chain):
                pass
        self.assertIsNone(eld.observe_org_crossings(self.kv))
        for broken in (lambda d: "not a list", lambda d: 1 / 0):
            with mock.patch.object(eld, "ORG_CROSSING_READER", broken):
                self.assertIsNone(eld.observe_org_crossings(self.kv))
        seen = []
        with mock.patch.object(eld, "ORG_CROSSING_READER", lambda d: seen.append(d) or list(self.org_chain)):
            self.assertEqual(eld.observe_org_crossings(self.kv), self.org_chain)
        self.assertEqual(seen, [self.kv])

    def test_a_head_older_than_the_kv_recorded_head_is_rollback_detected(self):
        newest = eld.kv_watermark(recorded(self.chain))[0]
        self.assertIsNone(eld.rollback_failure(self.chain, newest))
        got = eld.rollback_failure(self.chain[1:], newest)
        self.assert_six(got, "KV_LEDGER_HEAD_ROLLBACK_DETECTED", "DENY")
        self.assertEqual(got["failed_predicate"], "ENDPOINT_HEAD_NOT_OLDER_THAN_THE_NEWEST_KV_RECORDED_HEAD")
        self.assertIsNone(eld.rollback_failure(self.chain[1:], eld.kv_watermark(recorded(self.chain, 1))[0]))
        older = self.chain[1:]
        # KV's own head record names the newest head; the read-back chain is older
        with self.lane_d_reader_stub(older, head_record=eld.head_record_entries(
                [self.chain[1]["receipt_sha256"], self.chain[0]["receipt_sha256"]])), \
                mock.patch.object(eld, "load_head_signers", return_value=fixture_signers()):
            with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, older)) as (chain, failed):
                self.assertIsNone(chain)
                self.assert_six(failed, "KV_LEDGER_HEAD_ROLLBACK_DETECTED", "DENY")
                self.assertEqual(failed["recorded_head_sha256"], self.chain[0]["receipt_sha256"])
        # the read-back is behind its own last recorded head (the record names a head the chain holds, not its head)
        with self.lane_d_reader_stub(self.chain, head_record=eld.head_record_entries(
                [self.chain[1]["receipt_sha256"]])), \
                mock.patch.object(eld, "load_head_signers", return_value=fixture_signers()):
            with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, self.chain)) as (_, failed):
                self.assert_six(failed, "KV_LEDGER_HEAD_ROLLBACK_DETECTED", "DENY")
        # a caller's claim that differs from the recorded head is DENY, never relied on
        with self.lane_d_reader_stub(self.chain), \
                mock.patch.object(eld, "load_head_signers", return_value=fixture_signers()):
            for claim in (recorded(self.chain, 1), {**recorded(self.chain), "head_receipt_sha256": "sha256:" + "e" * 64}):
                with self.subTest(claim=claim):
                    with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, self.chain),
                                             recorded_head=claim) as (chain, failed):
                        self.assertIsNone(chain)
                        self.assert_six(failed, "KV_LEDGER_HEAD_ROLLBACK_DETECTED", "DENY")
        # an Org-recorded head is never the watermark, even with a valid cross-check digest
        with self.lane_d_reader_stub(self.chain), \
                mock.patch.object(eld, "load_head_signers", return_value=fixture_signers()):
            with eld.read_designated(self.kv, source=None, head_attestation=attest(self.kv, self.chain), recorded_head={
                                         **recorded(self.chain), "source": "ORG_LEDGER_LINKED_RECEIPTS_ENDPOINT_HEAD"}
                                     ) as (chain, failed):
                self.assertIsNone(chain)
                self.assert_six(failed, "KV_ROLLBACK_WATERMARK_ORG_LEDGER_SOURCED")


class BothSidesRecordTests(Base):
    """Each crossing is recorded by both endpoints, each pointing at the other's record by digest, each with a
    supplied epoch (#162 comment 6372641743). A one-sided crossing is refused with six fields."""

    def admit(self, chain, org_chain):
        return eld.chain_admission_failure(self.kv, self.kv["stores"][0], chain,
                                           head_attestation=attest(self.kv, chain), signers=fixture_signers(),
                                           head_record=eld.head_record_entries([chain[0]["receipt_sha256"]]),
                                           org_chain=org_chain, recorded_head=recorded(chain))

    def test_the_paired_records_are_admitted(self):
        self.assertIsNone(self.admit(self.chain, self.org_chain))
        self.assertIsNone(eld.crossing_failure(self.chain, self.org_chain, self.kv))
        for org in self.org_chain:       # the Org record carries a digest pointer, never the egress body
            self.assertNotIn("message", org["evidence"])
            self.assertEqual(org["evidence"]["source_repository_receipt_sha256"],
                             org["evidence"]["boundary_evidence"]["endpoint_head_sha256"])

    def test_an_org_crossing_receipt_is_digest_only_and_never_endpoint_originated(self):
        """No endpoint is an Organization member or a source of org-ledger records (#160 comment 6372871021)."""
        rec = self.org_chain[2]
        copied = self.reseal(rec, evidence={**rec["evidence"], "message": {"body": {"copied": True}}})
        got = eld.crossing_failure(self.chain, [self.org_chain[0], self.org_chain[1], copied], self.kv)
        self.assert_six(got, "ORG_CROSSING_RECEIPT_NOT_DIGEST_ONLY")
        self.assertEqual(got["failed_predicate"], "ORG_CHAIN_CROSSING_RECEIPT_IS_DIGEST_ONLY_ON_THE_ORGS_OWN_PATH")
        body = self.reseal(rec, evidence={**rec["evidence"], "boundary_evidence": {
            **rec["evidence"]["boundary_evidence"], "endpoint_head_body": {"x": 1}}})
        self.assert_six(eld.crossing_failure(self.chain, [body], self.kv), "ORG_CROSSING_RECEIPT_NOT_DIGEST_ONLY")
        for key in ("node_id", "repository", "originator"):
            with self.subTest(key=key):
                by_kv = self.reseal(rec, evidence={**rec["evidence"], key: self.kv["endpoint_id"]})
                got = eld.crossing_failure(self.chain, [by_kv], self.kv)
                self.assert_six(got, "ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE")
                self.assertEqual(got["failed_predicate"],
                                 "NO_ENDPOINT_IS_A_SOURCE_OF_ORG_LEDGER_RECORDS")
        self.assertIsNone(eld.crossing_failure(self.chain, self.org_chain, self.kv))

    def test_a_node_ledger_is_never_designated_on_the_org_ledger(self):
        """LC-KV-25 (Coordination, #167 comment 6373412055 items 3 and 4): a PERMANENT ledger on an org GIT_REF is
        DENY ENDPOINT_ORG_MEMBERSHIP_REFUSED, failure_class A, never FAIL_CLOSED ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE."""
        node = {**load("org-git-ref.designation.json"), "endpoint_kind": "PERMANENT", "endpoint_id": "node-1"}
        got = eld.designation_failure(node)
        self.assert_six(got, "ENDPOINT_ORG_MEMBERSHIP_REFUSED", "DENY")
        self.assertEqual((got["failed_predicate"], got["failure_class"], got["membership_basis"]),
                         ("ENDPOINT_NOT_A_GITHUB_ORGANIZATION_MEMBER", "A", "LOCATION_ORG_GIT_REF"))
        self.assertIn("NODE_STORAGE_ENDPOINT", got["required_evidence_or_repair"])
        self.assertIn("6373412055", got["required_evidence_or_repair"])
        self.assertNotIn("ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE", json.dumps(got))
        # any git-ref key on a PERMANENT store is the same location-based membership
        for store in ({**load("node.designation.json")["stores"][0], "ref": "refs/stegverse/organization-ledger"},
                      {**load("org-git-ref.designation.json")["stores"][0], "store_type": "NODE_STORAGE_ENDPOINT"}):
            with self.subTest(store=store):
                self.assert_six(eld.designation_failure({**load("node.designation.json"), "stores": [store]}),
                                "ENDPOINT_ORG_MEMBERSHIP_REFUSED", "DENY")
        self.assertIsNone(eld.designation_failure(load("org-git-ref.designation.json")))
        self.assertIsNone(eld.designation_failure(load("node.designation.json")))

    def test_an_org_side_record_without_the_endpoint_record_is_refused(self):
        stray = self.reseal(self.org_chain[2], evidence={
            **self.org_chain[2]["evidence"], "source_repository_receipt_sha256": "sha256:" + "a" * 64,
            "boundary_evidence": {**self.org_chain[2]["evidence"]["boundary_evidence"],
                                  "endpoint_head_sha256": "sha256:" + "a" * 64}})
        # LC-KV-23 (cvk#263 @9bc54d05): an Org record naming a newer or non-ancestor head is DENY rollback
        got = eld.crossing_failure(self.chain, [self.org_chain[0], self.org_chain[1], stray], self.kv)
        self.assert_six(got, "KV_LEDGER_HEAD_ROLLBACK_DETECTED", "DENY")
        self.assertEqual((got["failure_class"], got["org_named_head_sha256"]), ("C", "sha256:" + "a" * 64))
        self.assertIsNone(self.admit(self.chain, self.org_chain))
        self.assert_six(self.admit(self.chain[1:], self.org_chain), "KV_LEDGER_HEAD_ROLLBACK_DETECTED", "DENY")
        self.assertNotIn("KV_ROLLBACK_CROSSING_RECORD_AHEAD_OF_KV_HEAD",
                         (ROOT / "llm_adapter/endpoint_ledger_designation.py").read_text())
        no_head = self.reseal(self.org_chain[2], evidence={
            **self.org_chain[2]["evidence"], "boundary_evidence": {"operation": "ORGANIZATION_INTR_DESTINATION_INGRESS",
                                                                   "path_id": self.org_chain[2]["evidence"]["path_id"]}})
        self.assert_six(eld.crossing_failure(self.chain, [self.org_chain[0], no_head], self.kv),
                        "KV_CROSSING_RECORD_NOT_OBSERVED")

    def test_a_crossed_chain_with_no_org_record_observed_is_not_observed(self):
        """LC-KV-23 (b): KV crossed, no Org record observable -> FAIL_CLOSED KV_CROSSING_RECORD_NOT_OBSERVED (B);
        INTR_CROSSING_NOT_RECORDED_BY_BOTH_SIDES is kept for an observed Org side missing the ingress peer."""
        other, ev = "other->StegVerse-org:intr-destination", self.org_chain[2]["evidence"]
        elsewhere = self.reseal(self.org_chain[2], evidence={**ev, "path_id": other, "boundary_evidence": {
            **ev["boundary_evidence"], "path_id": other}})
        for observed in (None, [], [elsewhere]):
            with self.subTest(observed=observed):
                got = eld.crossing_failure(self.chain, observed, self.kv)
                self.assert_six(got, "KV_CROSSING_RECORD_NOT_OBSERVED")
                self.assertEqual((got["failure_class"], got["owning_existing_goal"]),
                                 ("B", eld.CODES["INTR_CROSSING_NOT_RECORDED_BY_BOTH_SIDES"][2]))
                self.assertIn("read by the reader itself", got["required_evidence_or_repair"])
                self.assertEqual(got["next_attempt"], "on the read-back of the Org side of the crossing (event-triggered)")
        self.assertEqual(eld.FAILURE_CLASS["INTR_CROSSING_NOT_RECORDED_BY_BOTH_SIDES"], "B")
        never = self.chain[-1:]
        self.assertIsNone(eld.crossing_failure(never, None, self.kv))

    def test_an_endpoint_ingress_record_without_the_org_record_is_refused(self):
        org_egress = self.org_chain[1]
        ingress = {"schema": "stegverse.kv-recorded-receipt/v1", "endpoint_id": self.kv["endpoint_id"], "sequence": 3,
                   "transition_class": "INTR_MESH_PATH_INGRESS", "hb_reference": self.chain[0]["hb_reference"],
                   "observed_at": self.chain[0]["observed_at"], "previous_receipt_sha256": self.chain[0]["receipt_sha256"],
                   "synthetic": "SYNTHETIC_FIXTURE_NOT_LEDGERED",
                   "evidence": {"source_repository_receipt_sha256": org_egress["receipt_sha256"]}}
        ingress = {**ingress, "receipt_sha256": hne.sha(ingress)}
        self.assertIsNone(eld.crossing_failure([ingress] + self.chain, self.org_chain, self.kv))
        got = eld.crossing_failure([ingress] + self.chain, [self.org_chain[0], self.org_chain[2]], self.kv)
        self.assert_six(got, "INTR_CROSSING_NOT_RECORDED_BY_BOTH_SIDES")
        self.assertEqual(got["one_sided"], "ENDPOINT_ONLY")

    def test_a_crossing_record_without_a_supplied_epoch_is_refused(self):
        clock = self.reseal(self.org_chain[0], hb_reference={**self.org_chain[0]["hb_reference"],
                                                              "derived_from_clock": True})
        self.assert_six(eld.crossing_failure(self.chain, [clock] + self.org_chain[1:], self.kv), "HB_EPOCH_INVALID")
        none = self.reseal(self.org_chain[0], hb_reference=None)
        got = eld.crossing_failure(self.chain, [none] + self.org_chain[1:], self.kv)
        self.assert_six(got, "HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(got["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
        stamped = [dict(r) for r in self.chain]
        stamped[0] = self.reseal(stamped[0], observed_at="2026-10-23T19:00:00+00:00")
        self.assert_six(eld.crossing_failure(stamped, [self.org_chain[2]], self.kv), "HB_EPOCH_INVALID")


class OrgMembershipTests(Base):
    """LC-KV-25 (P1 rev 10): no endpoint is a GitHub Organization member; LC-KV-24: keys are closed. Lane D's codes,
    predicates and token set (StegVerse-Labs/continuity-vault-kit#263 @9bc54d05 runtime/kv_receipt_ledgers.py)."""
    CVK_BF684AAD_MEMBERSHIP_TOKENS = {
        "org", "orgs", "organization", "organizations", "organisation", "member", "members", "membership",
        "memberships", "team", "teams", "install", "installation", "installations", "app", "apps", "permission",
        "permissions", "owner", "owners", "ownership", "collaborator", "collaborators", "role", "roles", "github",
        "enterprise", "admin", "admins", "seat", "seats", "scope", "scopes"}
    #: cvk#263 @9bc54d05 CONTRACT_KEY_SCHEMA as read at that head (a tuple leaf written {"__values__": [...]})
    CVK_BF684AAD_CONTRACT_KEY_SCHEMA = json.loads(
        '{"schema": null, "repository": null, "ledger_level": null, "receipt_schema": null, "append_only_receipts": '
        'null, "required_fields": null, "replay_rule": null, "repository_ledger_location": {"repository": null, "ref": '
        'null, "namespace": null, "locator_form": null, "new_ledger_root": null, "designation_source": null, '
        '"initialization": null, "rule": null, "expected_genesis_receipt_sha256": null, "expected_genesis_note": '
        'null}, "ledger_designation": {"schema": null, "endpoint_id": null, "endpoint_kind": null, "stores": '
        '[{"store_type": null, "storage_endpoint_schema": null, "provider_id": null, "access_adapter": null, '
        '"kv_class": null, "kv_request_id": null, "location": null}], "provider_selection": null, "genesis_class": '
        'null, "expected_genesis_receipt_sha256": null, "head_signer_source": null, "rollback_watermark_source": '
        '{"source": {"__values__": ["KV_RECORDED_RECEIPT_CHAIN_HEAD"]}, "org_crossing_cross_check": {"source": '
        '{"__values__": ["ORG_LEDGER_LINKED_RECEIPTS_ENDPOINT_HEAD"]}, "path_ids": null, "role": {"__values__": '
        '["DIGEST_ONLY_CROSS_CHECK_NEVER_WATERMARK"]}}}}, "designation_notes": {"store_type_note": null, '
        '"head_signers_path": null, "append_route": null, "path_ids_note": null, "refuses": null, '
        '"org_crossing_receipts": null, "head_digest_name": null, "genesis_crossing": null, "org_membership": null}, '
        '"propagation_rule": null, "authority_effect": null}')

    @staticmethod
    def norm(o):
        if isinstance(o, tuple):
            return {"__values__": list(o)}
        if isinstance(o, list):
            return [OrgMembershipTests.norm(x) for x in o]
        if hasattr(o, "items"):
            return {k: OrgMembershipTests.norm(v) for k, v in o.items()}
        return o

    def test_the_code_predicate_and_keys_are_lane_ds(self):
        self.assertEqual(eld.MEMBERSHIP_CODE, "ENDPOINT_ORG_MEMBERSHIP_REFUSED")
        self.assertEqual(eld.CODES[eld.MEMBERSHIP_CODE][0], "ENDPOINT_NOT_A_GITHUB_ORGANIZATION_MEMBER")
        self.assertEqual(set(eld.MEMBERSHIP_TOKENS), self.CVK_BF684AAD_MEMBERSHIP_TOKENS)
        self.assertFalse(hasattr(eld, "MEMBERSHIP_KEYS"))       # cvk @543e8c32's key set, superseded
        self.assertNotEqual(eld.CODES[eld.MEMBERSHIP_CODE][0], eld.CODES["ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE"][0])
        self.assertEqual(json.dumps(self.norm(eld.CONTRACT_KEY_SCHEMA)),
                         json.dumps(self.CVK_BF684AAD_CONTRACT_KEY_SCHEMA))
        self.assertEqual(self.norm(eld.CONTRACT_KEY_SCHEMA["ledger_designation"]["rollback_watermark_source"]),
                         self.norm(eld.DESIGNATION_KEY_SCHEMA["rollback_watermark_source"]))
        for code, predicate, cls in (
                ("KV_ROLLBACK_WATERMARK_ORG_LEDGER_SOURCED", "ROLLBACK_WATERMARK_SOURCED_FROM_KV_OWN_RECEIPT_CHAIN", "A"),
                ("KV_LEDGER_HEAD_ROLLBACK_WATERMARK_MISSING", "ROLLBACK_WATERMARK_SUPPLIED", "A"),
                ("KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY", "KV_RECEIPT_CHAIN_DESIGNATION_KEYS_CLOSED", "C"),
                ("ENDPOINT_ORG_MEMBERSHIP_REFUSED", "ENDPOINT_NOT_A_GITHUB_ORGANIZATION_MEMBER", "C")):
            got = eld.refusal(code, "x")
            self.assert_six(got, code)
            self.assertEqual((got["failed_predicate"], got["failure_class"]), (predicate, cls))
        self.assertNotIn("KV_LEDGER_ROLLBACK_WATERMARK_UNREAD", eld.CODES)

    def test_fixtures_match_cvks_contracts_at_9bc54d05(self):
        for name, sha in CVK_CONTRACT_SHA256.items():
            raw = (CVK / name).read_bytes()
            self.assertEqual("sha256:" + hashlib.sha256(raw).hexdigest(), sha)
            contract = json.loads(raw)
            self.assertIsNone(eld.contract_key_failure(contract))
            fixture = load("kv.designation.json" if name.startswith("stegverse-kv") else "skap.designation.json")
            ld = contract["ledger_designation"]
            self.assertIsNone(eld.designation_failure(ld))
            self.assertEqual(ld["expected_genesis_receipt_sha256"], None)
            # the only difference is this PR's genesis pin for the synthetic test chain (the KV fixture)
            diff = {k for k in set(ld) | set(fixture) if ld.get(k) != fixture.get(k)}
            self.assertEqual(diff, {"expected_genesis_receipt_sha256"} if "kv" in name else set(), name)
        kv = load("kv.designation.json")
        self.assertEqual(kv["expected_genesis_receipt_sha256"], load("kv-chain.json")["chain"][-1]["receipt_sha256"])
        # the negative fixtures differ from kv only in their targeted fields
        for name, targeted in (("kv-two-providers.designation.json", {"stores"}),
                               ("kv-on-org-git-ref.designation.json", {"stores", "expected_genesis_receipt_sha256"})):
            neg = load(name)
            self.assertEqual({k for k in set(kv) | set(neg) if kv.get(k) != neg.get(k)}, targeted, name)
        self.assertEqual(load("kv-two-providers.designation.json")["stores"][0], kv["stores"][0])

    def test_unknown_keys_are_refused_at_every_level(self):
        """LC-KV-24: an unknown membership-like key is ENDPOINT_ORG_MEMBERSHIP_REFUSED, any other unknown key
        KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY, at the top, in a store, in the watermark and in the cross-check."""
        contract = json.loads((CVK / "stegverse-kv-receipts.contract.json").read_bytes())
        levels = {
            "top": lambda d: d,
            "store": lambda d: d["stores"][0],
            "watermark": lambda d: d["rollback_watermark_source"],
            "cross-check": lambda d: d["rollback_watermark_source"]["org_crossing_cross_check"]}
        for level, at in levels.items():
            for key, code in (("teamSlug", "ENDPOINT_ORG_MEMBERSHIP_REFUSED"),
                              ("github_installation_id", "ENDPOINT_ORG_MEMBERSHIP_REFUSED"),
                              ("ownerScopes", "ENDPOINT_ORG_MEMBERSHIP_REFUSED"),
                              ("ledger_root", "KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY"),
                              ("note", "KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY")):
                with self.subTest(level=level, key=key):
                    d = copy.deepcopy(self.kv)
                    at(d)[key] = "x"
                    self.assert_six(eld.designation_failure(d), code)
                    c = copy.deepcopy(contract)
                    at(c["ledger_designation"])[key] = "x"
                    self.assert_six(eld.contract_key_failure(c), code)
        for where in ("repository_ledger_location", "designation_notes", None):
            c = copy.deepcopy(contract)
            (c[where] if where else c)["membership_note"] = "x"
            self.assert_six(eld.contract_key_failure(c), "ENDPOINT_ORG_MEMBERSHIP_REFUSED")
            c = copy.deepcopy(contract)
            (c[where] if where else c)["extra_note"] = "x"
            self.assert_six(eld.contract_key_failure(c), "KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY")
        # a leaf never carries keys
        c = copy.deepcopy(contract)
        c["ledger_designation"]["endpoint_id"] = {"x": 1}
        self.assert_six(eld.contract_key_failure(c), "KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY")

    def test_a_membership_team_or_app_installation_binding_is_refused_with_six_fields(self):
        for name in ("kv.designation.json", "skap.designation.json"):
            base = load(name)
            for where, key, edit in (
                    ("top", "org_membership", lambda d: d.update(org_membership={"org": "StegVerse-org"})),
                    ("top", "team_slug", lambda d: d.update(team_slug="kv-team")),
                    ("store", "installation_id", lambda d: d["stores"][0].update(installation_id="1")),
                    ("store", "github_app", lambda d: d["stores"][0].update(github_app="kv")),
                    ("watermark", "Members", lambda d: d["rollback_watermark_source"].update(Members=["kv"]))):
                with self.subTest(name=name, key=key):
                    d = copy.deepcopy(base)
                    edit(d)
                    got = eld.designation_failure(d)
                    self.assert_six(got, "ENDPOINT_ORG_MEMBERSHIP_REFUSED")
                    self.assertEqual(got["failed_predicate"], "ENDPOINT_NOT_A_GITHUB_ORGANIZATION_MEMBER")
                    self.assertIn(key, got["required_evidence_or_repair"])
                    with eld.read_designated(d, source=None,
                                             recorded_head=recorded(self.chain)) as (chain, failed):
                        self.assertIsNone(chain)
                        self.assertEqual(failed["failure_code"], "ENDPOINT_ORG_MEMBERSHIP_REFUSED")
        node = {**load("org-git-ref.designation.json"), "endpoint_kind": "PERMANENT", "endpoint_id": "node-1",
                "team": "x"}
        # a node ledger on an org ref is a location-based membership first: DENY, class A (LC-KV-25)
        self.assert_six(eld.designation_failure(node), "ENDPOINT_ORG_MEMBERSHIP_REFUSED", "DENY")
        self.assert_six(eld.designation_failure({**load("node.designation.json"), "team": "x"}),
                        "ENDPOINT_ORG_MEMBERSHIP_REFUSED")
        # the Org's own designation is not an endpoint; the unbound fixtures pass
        for name in ("kv.designation.json", "skap.designation.json", "org-git-ref.designation.json"):
            self.assertIsNone(eld.org_membership_binding(load(name)))
            self.assertIsNone(eld.designation_failure(load(name)))

    def test_a_valid_both_sides_crossing_fires_neither_endpoint_code(self):
        """Coordination ruling (crossings): the endpoint's side is in its own chain, the Org records only its own side,
        digest-only. That is not a ledger source; neither code fires."""
        self.assertIsNone(eld.crossing_failure(self.chain, self.org_chain, self.kv))
        self.assertIsNone(eld.designation_failure(self.kv))
        for org in self.org_chain:
            self.assertIsNone(eld.org_crossing_receipt_failure(org, self.kv))
        with self.lane_d_reader_stub(self.chain), \
                mock.patch.object(eld, "load_head_signers", return_value=fixture_signers()):
            with eld.read_designated(self.kv, source=None,
                                     head_attestation=attest(self.kv, self.chain),
                                     recorded_head=recorded(self.chain)) as (chain, failed):
                self.assertIsNone(failed)
                text = json.dumps(failed)
        for code in ("ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE", "ENDPOINT_ORG_MEMBERSHIP_REFUSED"):
            self.assertNotIn(code, text)


class NodeStorageEndpointTests(Base):
    """Q-PERMANENT-REPOSITORY-LEDGER (#167 comment 6374130335) and LC-KV-25: a PERMANENT (node) ledger is the node's
    own recorded receipt chain on the node's own storage endpoint, the same way as STEGVERSE_KV: the minimal shape
    mirroring cvk's v2 descriptor (no node descriptor is documented), its own recorded head as the watermark, the
    Org-side digest-only cross-check of its own path, and no reader yet (six-field FAIL_CLOSED, class B)."""

    def setUp(self):
        super().setUp()
        self.node = {**load("node.designation.json"), "expected_genesis_receipt_sha256": self.chain[-1]["receipt_sha256"]}

    def node_head(self, chain, index=0, **extra):
        return {"source": "NODE_RECORDED_RECEIPT_CHAIN_HEAD", "head_receipt_sha256": chain[index]["receipt_sha256"],
                **extra}

    def test_the_two_predicates_stay_distinct(self):
        self.assertNotEqual(eld.CODES[eld.MEMBERSHIP_CODE][0], eld.CODES["ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE"][0])
        self.assertEqual(eld.STORE_TYPE_OF["PERMANENT"], eld.NODE_STORAGE_ENDPOINT)
        self.assertEqual(eld.HEAD_SIGNER_OF["PERMANENT"], eld.NODE_IDENTITY_KEY)
        self.assertEqual(eld.load_head_signers(eld.NODE_IDENTITY_KEY), [])
        # key-based membership stays Lane D's FAIL_CLOSED class C
        got = eld.designation_failure({**self.node, "team": "x"})
        self.assert_six(got, "ENDPOINT_ORG_MEMBERSHIP_REFUSED")
        self.assertEqual(got["failure_class"], "C")
        # the originator predicate still guards Org records naming an endpoint as originator
        rec = self.org_chain[2]
        self.assertEqual(eld.org_crossing_receipt_failure(
            {**rec, "evidence": {**rec["evidence"], "node_id": self.node["endpoint_id"]}}, self.node)["failure_code"],
            "ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE")

    def test_the_minimal_node_store_shape(self):
        self.assertIsNone(eld.designation_failure(self.node))
        self.assertEqual(eld.store_location(self.node["stores"][0]), "storage-endpoint:device-local/Receipts")
        store = self.node["stores"][0]
        bad = {"kv": {**store, "kv_class": "STEGVERSE_KV"}, "schema": {**store, "storage_endpoint_schema": "x/v1"},
               "adapter": {**store, "access_adapter": "provider-or-file-provider"},
               "kv-location": {**store, "location": "_StegVerse/Receipts"},
               "org-namespace": {**store, "location": "repository-ledger/StegVerse-org/LLM-adapter"},
               "absolute": {**store, "location": "/var/node"}, "parent": {**store, "location": "a/../b"},
               "ref": {**store, "location": "refs/heads/main"}}
        for name, s in bad.items():
            with self.subTest(name=name):
                code = "KV_RECEIPT_CHAIN_DESIGNATION_UNKNOWN_KEY" if name == "kv" else "ENDPOINT_LEDGER_DESIGNATION_INVALID"
                self.assert_six(eld.designation_failure({**self.node, "stores": [s]}), code)
        for field, value in (("head_signer_source", "ORG_LEDGER_HEAD_SIGNER"), ("rollback_watermark_source", None),
                             ("rollback_watermark_source", {"source": "KV_RECORDED_RECEIPT_CHAIN_HEAD"}),
                             ("rollback_watermark_source", {"source": "NODE_RECORDED_RECEIPT_CHAIN_HEAD",
                                                            "org_crossing_cross_check": {
                                                                **self.node["rollback_watermark_source"][
                                                                    "org_crossing_cross_check"],
                                                                "path_ids": ["other->StegVerse-org:intr-destination"]}})):
            with self.subTest(field=field, value=value):
                self.assert_six(eld.designation_failure({**self.node, field: value}),
                                "ENDPOINT_LEDGER_DESIGNATION_INVALID")
        self.assert_six(eld.designation_failure({**self.node, "rollback_watermark_source": {
            "source": "ORG_LEDGER_LINKED_RECEIPTS_ENDPOINT_HEAD"}}), "KV_ROLLBACK_WATERMARK_ORG_LEDGER_SOURCED")
        self.assert_six(eld.designation_failure({**self.node, "rollback_watermark_source": {
            "source": "NODE_RECORDED_RECEIPT_CHAIN_HEAD"}}), "ENDPOINT_LEDGER_DESIGNATION_INVALID")

    def test_production_has_no_node_reader(self):
        self.assertNotIn(eld.NODE_STORAGE_ENDPOINT, eld.READERS)
        with eld.read_designated(self.node, source=None,
                                 recorded_head=self.node_head(self.chain)) as (chain, failed):
            self.assertIsNone(chain)
            self.assert_six(failed, "NODE_STORAGE_ENDPOINT_READER_NOT_DOCUMENTED")
            self.assertEqual((failed["failure_class"], failed["reader_id"], failed["failed_predicate"]),
                             ("B", "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED",
                              "NODE_STORAGE_ENDPOINT_DESCRIPTOR_AND_READER_DOCUMENTED"))
            self.assertIn("NODE-STORAGE-ENDPOINT-DESCRIPTOR", failed["owning_existing_goal"])
            self.assertFalse(failed["ledger_written"])

    def test_the_watermark_is_the_nodes_own_recorded_head(self):
        """With a TEST-ONLY reader stub: the node's own head is the watermark; an older chain is DENY rollback."""
        head_record = [eld.head_record_entries([self.chain[0]["receipt_sha256"]])]

        @contextlib.contextmanager
        def reader(designation, store, source, head_attestation):
            yield copy.deepcopy(self.chain), copy.deepcopy(head_record[0]), None
        node = self.node
        path = node["rollback_watermark_source"]["org_crossing_cross_check"]["path_ids"][0]
        kv_path = eld.crossing_path_ids(self.kv)[0]
        org = [self.reseal(r, evidence={**r["evidence"], "path_id": path, "boundary_evidence": {
            **r["evidence"]["boundary_evidence"], "path_id": path}})
            if r["evidence"].get("path_id") == kv_path else r for r in self.org_chain]
        with mock.patch.dict(eld._READERS, {eld.NODE_STORAGE_ENDPOINT: reader}), \
                mock.patch.object(eld, "ORG_CROSSING_READER", lambda d: copy.deepcopy(org)):
            with eld.read_designated(node, source=None,
                                     recorded_head=self.node_head(self.chain)) as (chain, failed):
                self.assertIsNone(failed)
                self.assertEqual(chain, self.chain)
            with eld.read_designated(node, source=None) as (chain, failed):
                self.assertIsNone(failed)
            for head, code in ((recorded(self.chain), "KV_LEDGER_HEAD_ROLLBACK_WATERMARK_MISSING"),
                               ({"source": "ORG_LEDGER_LINKED_RECEIPTS_ENDPOINT_HEAD",
                                 "head_receipt_sha256": self.chain[0]["receipt_sha256"]},
                                "KV_ROLLBACK_WATERMARK_ORG_LEDGER_SOURCED")):
                with self.subTest(head=head):
                    with eld.read_designated(node, source=None,
                                             recorded_head=head) as (chain, failed):
                        self.assert_six(failed, code)
            newer = {"source": "NODE_RECORDED_RECEIPT_CHAIN_HEAD", "head_receipt_sha256": "sha256:" + "e" * 64}
            with eld.read_designated(node, source=None,
                                     recorded_head=newer) as (chain, failed):
                self.assert_six(failed, "KV_LEDGER_HEAD_ROLLBACK_DETECTED", "DENY")
            head_record[0] = None      # the node's own head record not read back
            with eld.read_designated(node, source=None,
                                     recorded_head=self.node_head(self.chain)) as (chain, failed):
                self.assert_six(failed, "KV_LEDGER_HEAD_ROLLBACK_WATERMARK_MISSING")


class DeterminismTests(unittest.TestCase):
    def test_no_clock_network_randomness_or_new_dependency(self):
        tree = ast.parse((ROOT / "llm_adapter/endpoint_ledger_designation.py").read_text())
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertFalse(names & {"time", "datetime", "random", "secrets", "socket", "urllib", "http", "requests",
                                  "subprocess", "uuid"}, names)
        self.assertTrue(names <= {"__future__", "base64", "binascii", "contextlib", "json", "re", "pathlib", "types",
                                  "typing", "llm_adapter"}, names)
        epoch = ast.parse((ROOT / "llm_adapter/supplied_epoch.py").read_text())
        names = {(n.module or "").split(".")[0] for n in ast.walk(epoch) if isinstance(n, ast.ImportFrom)}
        names |= {a.name.split(".")[0] for n in ast.walk(epoch) if isinstance(n, ast.Import) for a in n.names}
        self.assertTrue(names <= {"__future__", "typing"}, names)
