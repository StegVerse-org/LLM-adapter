from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "project_independent_parent_activation.py"


def load_module():
    spec = importlib.util.spec_from_file_location("parent_projection", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ParentActivationProjectionTests(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.receipts = self.root / "receipts" / "ecosystem-chat-sovereign-inference"
        self.receipts.mkdir(parents=True)
        self.output = self.root / "adapter-projection.json"
        self.write_chain()

    def tearDown(self):
        self.tmp.cleanup()

    def write_chain(self):
        route = {"receipt_hash": "route-hash-001"}
        usage = {"event_sha256": "a" * 64}
        execution = {
            "state": "EXECUTED",
            "provider_usage_event": usage,
            "measured_usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        }
        reconstruction = {
            "reconstruction_receipt_hash": "reconstruction-hash-001",
            "provider_usage_reconstruction_pass": True,
            "transition_reconstruction_pass": True,
            "same_execution": True,
        }
        activation = {
            "schema": "stegverse.ecosystem-chat-independent-parent-activation/v1",
            "task_id": "SHWP-ECOSYSTEM-CHAT-INFERENCE-001",
            "claim_id": "claim-23",
            "fencing_token": 23,
            "heartbeat_reference_epoch": 4000,
            "heartbeat_reference_is_causal": False,
            "state": "PASS",
            "transition_id": "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED",
            "real_model_process_observed": True,
            "private_endpoint_only": True,
            "ephemeral_e1_e2_execution_observed": True,
            "measured_usage_persisted": True,
            "provider_usage_reconstruction_pass": True,
            "transition_reconstruction_pass": True,
            "same_execution": True,
            "credential_authority": "TV/TVC",
            "credential_requirement": "NONE",
            "github_token_required": False,
            "github_actions_activation_role": False,
            "third_party_inference_required": False,
            "persistent_conversational_runtime_ready": True,
            "runtime_proof_hash": "runtime-proof-hash-001",
            "tvc_route_receipt_hash": route["receipt_hash"],
            "provider_usage_event_sha256": usage["event_sha256"],
            "reconstruction_receipt_hash": reconstruction["reconstruction_receipt_hash"],
            "authority_effect": "NONE_BEYOND_ADMITTED_PARENT_TASK_CONTROL",
        }
        activation["activation_receipt_hash"] = self.m.stable_hash(activation)
        base = {
            "completed": True,
            "same_execution": True,
            "github_token_required": False,
            "third_party_inference_required": False,
        }

        files = {
            "independent_parent_activation.latest.json": activation,
            "SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json": base,
            "tvc_local_model_route.json": route,
            "llm_adapter_sovereign_execution.json": execution,
            "master_records_same_execution_reconstruction.json": reconstruction,
        }
        for name, value in files.items():
            (self.receipts / name).write_text(json.dumps(value), encoding="utf-8")

    def test_terminal_parent_chain_projects_verified_non_authorizing_evidence(self):
        chain = self.m.verify_chain(self.root)
        projection = self.m.build_projection(chain)
        self.assertEqual(projection["state"], "VERIFIED")
        self.assertEqual(projection["fencing_token"], 23)
        self.assertTrue(all(projection["predicates"].values()))
        self.assertFalse(projection["credential_boundary"]["github_token_required"])
        self.assertTrue(all(value is False for value in projection["authority_boundary"].values()))
        self.assertEqual(
            projection["projection_sha256"],
            self.m.stable_hash({k: v for k, v in projection.items() if k != "projection_sha256"}),
        )

    def test_old_or_reused_fence_is_rejected(self):
        path = self.receipts / "independent_parent_activation.latest.json"
        value = json.loads(path.read_text())
        value["fencing_token"] = 22
        binding = dict(value)
        binding.pop("activation_receipt_hash", None)
        value["activation_receipt_hash"] = self.m.stable_hash(binding)
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "fresh_parent_fence_gt22"):
            self.m.verify_chain(self.root)

    def test_hash_binding_drift_is_rejected(self):
        path = self.receipts / "llm_adapter_sovereign_execution.json"
        value = json.loads(path.read_text())
        value["provider_usage_event"]["event_sha256"] = "b" * 64
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "provider_usage_binding"):
            self.m.verify_chain(self.root)

    def test_immutable_projection_refuses_different_terminal_execution(self):
        chain = self.m.verify_chain(self.root)
        first = self.m.build_projection(chain)
        self.assertEqual(self.m.immutable_write(self.output, first), "CREATED")
        self.assertEqual(self.m.immutable_write(self.output, first), "UNCHANGED")
        second = json.loads(json.dumps(first))
        second["fencing_token"] = 24
        binding = dict(second)
        binding.pop("projection_sha256", None)
        second["projection_sha256"] = self.m.stable_hash(binding)
        with self.assertRaisesRegex(ValueError, "immutable sovereign activation projection"):
            self.m.immutable_write(self.output, second)


if __name__ == "__main__":
    unittest.main()
