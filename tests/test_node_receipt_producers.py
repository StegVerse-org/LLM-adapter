"""Class B pieces (1)-(3) for LC-KV-13, and the end-to-end chain into layer 1.

The pieces under test:
(1) node_existence_readback: a StegOS broker receipt becomes AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE.
(2) node_identity_binding_producer: NODE_IDENTITY_BINDING, verified against a key reference only.
(3) node_health_check_projection: a StegHealth observation becomes NODE_HEALTH_CHECK_OBSERVED
    (stegverse.node-health-check/v1).
The end-to-end path runs: StegOS observation, then (1), (2) and (3), then the #429
producer, then admit, then layer-1 ALLOW.

Every ledger here is a temporary directory. The real ledger is never read or
written, and nothing is dispatched.
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

from llm_adapter import ed25519_verify
from llm_adapter import healthy_node_evaluator as hne
from llm_adapter import node_existence_readback as readback
from llm_adapter import node_health_check_projection as health
from llm_adapter import node_health_report_producer as producer
from llm_adapter import node_identity_binding_producer as binding
from llm_adapter import node_ingress_boundary as boundary
from tests import ed25519_test_signer as signer
from tests.test_healthy_node_evaluator import write_chain

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/node_receipts"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
OTHER_SEED = hashlib.sha256(b"llm-adapter node-receipt tests: a second public fixture seed").digest()


def load(name):
    return json.loads((FIXTURES / name).read_text())


BROKER = load("stegos_existence_broker_receipt.json")
PROFILE = load("stegos_observed_profile.json")
OBSERVATION = load("steghealth_runtime_observation.json")
NODE = BROKER["node_ref"]


def reseal(receipt):
    """Re-seal a mutated broker receipt the way StegOS does, so only the mutation is under test."""
    receipt = copy.deepcopy(receipt)
    receipt["result_hash"] = readback._stegos_sha256_uri(receipt["result"])
    receipt.pop("receipt_hash", None)
    receipt["receipt_hash"] = readback._stegos_sha256_uri(receipt)
    return receipt


def claim_for(existence_sha, *, seed=signer.TEST_SEED, profile=PROFILE, **override):
    key = profile["node_identity_key"]
    public = signer.public_key(seed)
    claim = {"schema": binding.CLAIM_SCHEMA, "node_id": NODE, "existence_receipt_sha256": existence_sha,
             "profile_sha256": binding.stegos_profile_sha256(profile),
             "key_ref": {"algorithm": "Ed25519", "key_id": key["key_id"],
                         "public_key_sha256": "sha256:" + hashlib.sha256(public).hexdigest()}}
    claim.update(override)
    claim["signature_b64"] = signer.sign_b64(binding.claim_message(claim), seed)
    return claim


def attestation_for(binding_sha, observation=OBSERVATION, *, seed=signer.TEST_SEED, **override):
    att = {"schema": health.ATTESTATION_SCHEMA, "node_id": NODE, "binding_receipt_sha256": binding_sha,
           "observation_sha256": hne.sha(observation)}
    att.update(override)
    att["signature_b64"] = signer.sign_b64(health.attestation_message(att), seed)
    return att


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

    def files(self):
        return sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*") if p.is_file())

    def chain(self):
        chain, failure, _ = hne.read_chain(self.root)
        return chain if failure is None else []

    def assert_fail_closed(self, out, reason, failure_code=None):
        self.assertEqual(out["disposition"], "FAIL_CLOSED", out)
        self.assertEqual(out["reason"], reason, out)
        self.assertIs(out["receipt_emitted"], False)
        for key in SIX:
            self.assertTrue(isinstance(out[key], str) and out[key].strip(), key)
        if failure_code:
            self.assertEqual(out["failure_code"], failure_code)

    def refused_without_writing(self, call, reason, failure_code=None):
        before = self.files()
        self.assert_fail_closed(call(), reason, failure_code)
        self.assertEqual(self.files(), before)

    # the three steps
    def exist(self):
        out = readback.produce(BROKER, ledger_root=self.root)
        self.assertEqual((out["disposition"], out["outcome"]), ("ALLOW", "EMITTED"), out)
        return out["receipt_sha256"]

    def bind(self, existence_sha):
        out = binding.produce(existence_sha, claim_for(existence_sha), PROFILE, ledger_root=self.root)
        self.assertEqual((out["disposition"], out["outcome"]), ("ALLOW", "EMITTED"), out)
        return out["receipt_sha256"]

    def check(self, binding_sha, observation=OBSERVATION):
        out = health.produce(binding_sha, observation, attestation_for(binding_sha, observation), ledger_root=self.root)
        self.assertEqual((out["disposition"], out["outcome"]), ("ALLOW", "EMITTED"), out)
        return out


class FixtureProvenanceTests(unittest.TestCase):
    def test_broker_receipt_is_sealed_exactly_as_stegos_seals_it(self):
        body = {k: v for k, v in BROKER.items() if k != "receipt_hash"}
        self.assertEqual(readback._stegos_sha256_uri(body), BROKER["receipt_hash"])
        self.assertEqual(BROKER["result"]["profile_sha256"], binding.stegos_profile_sha256(PROFILE))

    def test_verifier_passes_rfc8032_test_1_and_has_no_signing_path(self):
        pk = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
        sig = bytes.fromhex("e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701c"
                            "f9b46bd25bf5f0595bbe24655141438e7a100b")
        self.assertTrue(ed25519_verify.verify(pk, b"", sig))
        self.assertFalse(ed25519_verify.verify(pk, b"\x00", sig))
        self.assertFalse(ed25519_verify.verify(pk, b"", sig[:32] + bytes(32)))
        self.assertEqual(ed25519_verify.__all__, ["verify"])
        for name in dir(ed25519_verify):
            self.assertNotIn("sign", name.lower())

    def test_cores_import_no_clock_network_randomness_or_process(self):
        banned = {"time", "datetime", "socket", "urllib", "http", "requests", "random", "secrets",
                  "subprocess", "os", "threading", "sched", "asyncio"}
        for module in ("ed25519_verify", "node_receipt_common", "node_existence_readback",
                       "node_identity_binding_producer", "node_health_check_projection"):
            tree = ast.parse((ROOT / f"llm_adapter/{module}.py").read_text())
            names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
            names |= {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            self.assertFalse(names & banned, (module, names & banned))


class ExistenceReadbackTests(_Ledger):
    def test_stegos_broker_receipt_becomes_an_existence_receipt_the_producer_reads(self):
        out = readback.produce(BROKER, ledger_root=self.root)
        self.assertEqual((out["disposition"], out["outcome"], out["node_id"]), ("ALLOW", "EMITTED", NODE))
        head = json.loads((self.root / "HEAD.json").read_text())["receipt_sha256"]
        self.assertEqual(head, out["receipt_sha256"])
        receipt = self.chain()[0]
        self.assertEqual(receipt["transition_class"], "AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE")
        ev = receipt["evidence"]
        self.assertEqual((ev["node_id"], ev["disposition"]), (NODE, "ALLOW"))
        self.assertEqual(ev["source_broker_receipt"]["receipt_hash"], BROKER["receipt_hash"])
        self.assertEqual(ev["observation"]["profile_sha256"], BROKER["result"]["profile_sha256"])
        self.assertEqual(receipt["hb_reference"]["derived_from_clock"], False)

    def test_same_broker_receipt_is_idempotent(self):
        first = self.exist()
        again = readback.produce(BROKER, ledger_root=self.root)
        self.assertEqual((again["outcome"], again["receipt_sha256"]), ("NOOP_ALREADY_CURRENT", first))
        self.assertEqual(len(self.chain()), 1)

    def test_every_unsealed_or_non_allow_input_fails_closed_and_writes_nothing(self):
        def mutate(fn, seal=True):
            r = copy.deepcopy(BROKER)
            fn(r)
            return reseal(r) if seal else r
        cases = {
            "result flipped, not resealed": (mutate(lambda r: r["result"].update(disposition="FAIL_CLOSED"), False),
                                             "BROKER_RECEIPT_HASH_MISMATCH"),
            "body edited, not resealed": (mutate(lambda r: r.update(node_ref="SV-NODE-other"), False),
                                          "BROKER_RECEIPT_HASH_MISMATCH"),
            "observation FAIL_CLOSED": (mutate(lambda r: r["result"].update(
                disposition="FAIL_CLOSED", status="RECIPROCAL_NODE_EXISTENCE_FAIL_CLOSED")), "OBSERVATION_NOT_ALLOW"),
            "credential used": (mutate(lambda r: r["result"].update(credential_used=True)), "OBSERVATION_INVALID"),
            "not https": (mutate(lambda r: r["result"].update(observed_profile_url="http://x/intr/profile")),
                          "OBSERVATION_INVALID"),
            "other capability": (mutate(lambda r: r.update(capability_adapter="something-else")),
                                 "CAPABILITY_NOT_EXISTENCE_OBSERVER"),
            "no retained node": (mutate(lambda r: r.update(node_ref="node-7")), "NODE_REF_INVALID"),
            "broker minted a claim": (mutate(lambda r: r.update(claim_or_fence_minted_by_broker=True)),
                                      "BROKER_RECEIPT_INVALID"),
            "wrong schema": (mutate(lambda r: r.update(schema="stegos.other/v1")), "BROKER_RECEIPT_INVALID"),
            "not an object": ("receipt", "BROKER_RECEIPT_INVALID"),
            "nothing": (None, "BROKER_RECEIPT_INVALID"),
        }
        for name, (receipt, reason) in cases.items():
            with self.subTest(name):
                self.refused_without_writing(lambda: readback.produce(receipt, ledger_root=self.root), reason,
                                             "NODE_EXISTENCE_NOT_READ_BACK")

    def test_broken_chain_fails_closed(self):
        self.exist()
        path = next((self.root / "receipts").glob("*.json"))
        body = json.loads(path.read_text())
        body["evidence"]["disposition"] = "DENY"
        path.write_text(json.dumps(body))
        self.refused_without_writing(lambda: readback.produce(reseal(BROKER | {"task_id": "x"}), ledger_root=self.root),
                                     "RECEIPT_HASH_MISMATCH")

    def test_never_appends_to_a_ledger_other_than_the_one_it_read(self):
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = other.name
        self.assert_fail_closed(readback.produce(BROKER, ledger_root=self.root), "LEDGER_ROOT_MISMATCH")
        self.assertFalse(any(Path(other.name).rglob("*.json")))

    def test_plan_is_deterministic_and_never_writes(self):
        self.exist()
        other = reseal(BROKER | {"task_id": "second"})
        before = self.files()
        self.assertEqual(readback.plan(other, ledger_root=self.root), readback.plan(other, ledger_root=self.root))
        self.assertEqual(self.files(), before)


class IdentityBindingTests(_Ledger):
    def test_binding_verified_by_key_reference_cites_and_follows_existence(self):
        existence = self.exist()
        out = binding.produce(existence, claim_for(existence), PROFILE, ledger_root=self.root)
        self.assertEqual((out["disposition"], out["outcome"]), ("ALLOW", "EMITTED"), out)
        receipt = self.chain()[0]
        ev = receipt["evidence"]
        self.assertEqual(receipt["transition_class"], "NODE_IDENTITY_BINDING")
        self.assertEqual((ev["node_id"], ev["disposition"], ev["existence_receipt_sha256"]), (NODE, "ALLOW", existence))
        self.assertIs(ev["signature_verified"], True)
        self.assertIs(ev["credential_held_or_minted"], False)
        self.assertEqual(receipt["previous_receipt_sha256"], existence)
        self.assertEqual(binding.produce(existence, claim_for(existence), PROFILE, ledger_root=self.root)["outcome"],
                         "NOOP_ALREADY_CURRENT")

    def test_unverifiable_or_unreceipted_bindings_fail_closed_and_write_nothing(self):
        existence = self.exist()
        good = claim_for(existence)
        tampered_profile = copy.deepcopy(PROFILE)
        tampered_profile["profiles"].append("Extra")
        other_node_profile = copy.deepcopy(PROFILE)
        other_node_profile["node_identity_key"]["node_id"] = "SV-NODE-someone-else"
        cases = {
            "existence not on chain": (("sha256:" + "0" * 64, good, PROFILE), "EXISTENCE_NOT_RECEIPTED"),
            "signature by another key": ((existence, {**claim_for(existence, seed=OTHER_SEED)}, PROFILE),
                                         "KEY_REFERENCE_INVALID"),
            "signature over other bytes": ((existence, {**good, "signature_b64": claim_for(existence, node_id=NODE,
                                            profile_sha256="0" * 64)["signature_b64"]}, PROFILE), "SIGNATURE_INVALID"),
            "no signature": ((existence, {k: v for k, v in good.items() if k != "signature_b64"}, PROFILE),
                             "SIGNATURE_INVALID"),
            "profile not the observed one": ((existence, good, tampered_profile), "PROFILE_NOT_OBSERVED"),
            "claim for another node": ((existence, claim_for(existence, node_id="SV-NODE-x"), PROFILE), "CLAIM_INVALID"),
            "key edited after observation": ((existence, good, other_node_profile), "PROFILE_NOT_OBSERVED"),
            "private key material sent": ((existence, {**good, "private_key_b64": "AAAA"}, PROFILE),
                                          "CREDENTIAL_MATERIAL_PRESENT"),
        }
        for name, (args, reason) in cases.items():
            with self.subTest(name):
                self.refused_without_writing(lambda: binding.produce(*args, ledger_root=self.root), reason,
                                             "NODE_IDENTITY_NOT_BOUND")

    def test_key_reference_checks_the_published_key_itself(self):
        # A profile whose key names another node, with the existence receipt observing that profile.
        root = self.root / "hand"
        profile = copy.deepcopy(PROFILE)
        profile["node_identity_key"]["node_id"] = "SV-NODE-someone-else"
        chain = write_chain(root, [{"transition_class": "AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE",
                                    "hb_reference": {"epoch": 64},
                                    "evidence": {"node_id": NODE, "disposition": "ALLOW",
                                                 "observation": {"profile_sha256": binding.stegos_profile_sha256(profile)}}}])
        existence = chain[0]["receipt_sha256"]
        out = binding.plan(existence, claim_for(existence, profile=profile), profile, ledger_root=root)
        self.assert_fail_closed(out, "KEY_REFERENCE_INVALID")

    def test_superseded_or_refused_existence_fails_closed(self):
        first = self.exist()
        second = readback.produce(reseal(BROKER | {"task_id": "again"}), ledger_root=self.root)["receipt_sha256"]
        self.refused_without_writing(lambda: binding.produce(first, claim_for(first), PROFILE, ledger_root=self.root),
                                     "EXISTENCE_SUPERSEDED")
        root = self.root / "hand"
        chain = write_chain(root, [{"transition_class": "AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE",
                                    "hb_reference": {"epoch": 64}, "evidence": {"node_id": NODE, "disposition": "DENY"}}])
        self.assert_fail_closed(binding.plan(chain[0]["receipt_sha256"], claim_for(chain[0]["receipt_sha256"]), PROFILE,
                                             ledger_root=root), "EXISTENCE_NOT_ALLOW")
        self.assertTrue(second)


class HealthCheckProjectionTests(_Ledger):
    def setUp(self):
        super().setUp()
        self.binding = self.bind(self.exist())

    def test_passing_observation_projects_to_a_healthy_node_health_check(self):
        out = self.check(self.binding)
        receipt = self.chain()[0]
        ev = receipt["evidence"]
        self.assertEqual(receipt["transition_class"], "NODE_HEALTH_CHECK_OBSERVED")
        self.assertEqual((ev["schema"], ev["node_id"], ev["status"]), ("stegverse.node-health-check/v1", NODE, "HEALTHY"))
        self.assertEqual(ev["failing_predicates"], [])
        self.assertEqual(out["check_status"], "HEALTHY")
        again = health.produce(self.binding, OBSERVATION, attestation_for(self.binding), ledger_root=self.root)
        self.assertEqual(again["outcome"], "NOOP_ALREADY_CURRENT")

    def test_failing_predicates_project_to_unhealthy_with_the_list(self):
        for field, value in (("continuous_runtime_live", False), ("state_reconstruction_pass", 1),
                             ("credential_authority", "OTHER"), ("third_party_runtime_required", None)):
            with self.subTest(field):
                observed = {**OBSERVATION, field: value}
                out = self.check(self.binding, observed)
                self.assertEqual(out["check_status"], "UNHEALTHY")
                self.assertEqual(out["receipt_evidence"]["failing_predicates"], [field])

    def test_unverifiable_or_unreceipted_checks_fail_closed_and_write_nothing(self):
        good = attestation_for(self.binding)
        cases = {
            "binding not on chain": (("sha256:" + "0" * 64, OBSERVATION, good), "BINDING_NOT_RECEIPTED"),
            "not a binding": ((self.chain()[1]["receipt_sha256"], OBSERVATION, good), "BINDING_NOT_RECEIPTED"),
            "signed by another key": ((self.binding, OBSERVATION, attestation_for(self.binding, seed=OTHER_SEED)),
                                      "SIGNATURE_INVALID"),
            "attests another observation": ((self.binding, {**OBSERVATION, "native_service_active": False}, good),
                                            "ATTESTATION_INVALID"),
            "attests another node": ((self.binding, OBSERVATION, attestation_for(self.binding, node_id="SV-NODE-x")),
                                     "ATTESTATION_INVALID"),
            "not a StegHealth observation": ((self.binding, {**OBSERVATION, "schema": "x"}, good), "OBSERVATION_INVALID"),
            "private key material sent": ((self.binding, OBSERVATION, {**good, "seed": "AAAA"}),
                                          "CREDENTIAL_MATERIAL_PRESENT"),
        }
        for name, (args, reason) in cases.items():
            with self.subTest(name):
                self.refused_without_writing(lambda: health.produce(*args, ledger_root=self.root), reason,
                                             "NODE_HEALTH_CHECK_NOT_OBSERVED")

    def test_superseded_binding_fails_closed(self):
        existence = readback.produce(reseal(BROKER | {"task_id": "rebind"}), ledger_root=self.root)["receipt_sha256"]
        newer = self.bind(existence)
        self.refused_without_writing(lambda: health.produce(self.binding, OBSERVATION, attestation_for(self.binding),
                                                            ledger_root=self.root), "BINDING_NOT_RECEIPTED")
        self.assertEqual(self.check(newer)["check_status"], "HEALTHY")


class EndToEndChainTests(_Ledger):
    """StegOS observation, then (1), (2) and (3), then the #429 producer, then admit, then layer-1 ALLOW."""

    def signal(self):
        return {"mode": "ESTABLISH_GENESIS", "node_ref": NODE, "predecessor": None, "node_class": "LLM_ADAPTER"}

    def test_full_chain_reaches_layer1_allow(self):
        existence = self.exist()
        bound = self.bind(existence)
        check = self.check(bound)["receipt_sha256"]
        report = producer.produce(check, ledger_root=self.root)
        self.assertEqual((report["disposition"], report["outcome"], report["report_status"]),
                         ("ALLOW", "EMITTED", "HEALTHY"), report)
        self.assertEqual(report["report_evidence"]["evidence_receipts"],
                         {"authenticated_reciprocal_node_existence": existence, "node_identity_binding": bound,
                          "health_check": check})
        admitted = boundary.admit(self.signal(), health_report_receipt_sha256=report["health_report_receipt_sha256"])
        self.assertEqual(admitted["disposition"], "ALLOW", admitted)
        self.assertIs(admitted["healthy_node_established"], True)
        layer1 = hne.evaluate(NODE, ledger_root=self.root, require_admission=True)
        self.assertEqual(layer1["disposition"], "ALLOW", layer1)
        classes = [r["transition_class"] for r in reversed(self.chain())]
        self.assertEqual(classes, ["AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE", "NODE_IDENTITY_BINDING",
                                   "NODE_HEALTH_CHECK_OBSERVED", "NODE_HEALTH_REPORTED", "NODE_INGRESS_ADMITTED"])
        self.assertTrue(all(r["hb_reference"]["derived_from_clock"] is False for r in self.chain()
                            if r["transition_class"] != "NODE_INGRESS_ADMITTED"))

    def test_registration_first_then_admit_reaches_layer1_allow(self):
        self.check(self.bind(self.exist()))
        first = boundary.admit(self.signal())
        self.assertEqual((first["disposition"], first["failed_stage"]), ("FAIL_CLOSED", "CURRENT_NODE_HEALTH"))
        report = first["health_report_production"]["health_report_receipt_sha256"]
        self.assertEqual(boundary.admit(self.signal(), health_report_receipt_sha256=report)["disposition"], "ALLOW")
        self.assertEqual(hne.evaluate(NODE, ledger_root=self.root, require_admission=True)["disposition"], "ALLOW")

    def test_unhealthy_observation_ends_in_deny_at_layer1(self):
        check = self.check(self.bind(self.exist()), {**OBSERVATION, "native_service_active": False})
        producer.produce(check["receipt_sha256"], ledger_root=self.root)
        self.assertEqual(boundary.admit(self.signal())["disposition"], "DENY")
        layer1 = hne.evaluate(NODE, ledger_root=self.root, require_admission=True)
        self.assertEqual(layer1["disposition"], "DENY")
        for key in SIX:
            self.assertTrue(layer1[key])

    def test_a_break_at_any_step_never_reaches_layer1_allow(self):
        existence = self.exist()
        bad = binding.produce(existence, claim_for(existence, seed=OTHER_SEED), PROFILE, ledger_root=self.root)
        self.assertEqual(bad["disposition"], "FAIL_CLOSED")
        self.assertEqual(boundary.admit(self.signal())["disposition"], "FAIL_CLOSED")
        layer1 = hne.evaluate(NODE, ledger_root=self.root, require_admission=True)
        self.assertEqual(layer1["disposition"], "FAIL_CLOSED")
        for key in SIX:
            self.assertTrue(layer1[key])


if __name__ == "__main__":
    unittest.main()
