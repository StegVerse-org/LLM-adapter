from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "write_ecosystem_chat_destination_activation_state.py"


def load_module():
    spec = importlib.util.spec_from_file_location("destination_state", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class DestinationActivationSovereignTests(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data").mkdir()
        (self.root / "tasks").mkdir()
        (self.root / "receipts").mkdir()
        (self.root / "reports").mkdir()
        self.m.ROOT = self.root
        self.m.SOVEREIGN_STATE = self.root / "data" / "ecosystem-chat-sovereign-orchestration-state.json"
        self.m.CARRIER_TASK = self.root / "tasks" / "LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json"
        self.m.LIVE_RECEIPT = self.root / "receipts" / "ecosystem-chat-live-activation.verified.json"
        self.m.OUTPUT = self.root / "reports" / "ecosystem-chat-destination-activation-state.json"
        self.write_source_contract()

    def tearDown(self):
        self.tmp.cleanup()

    def write_source_contract(self):
        self.m.SOVEREIGN_STATE.write_text(json.dumps({
            "canonical_micro_node_runtime": {"state": "COMPLETE_RELEASED"},
            "completed_transport_evidence_adapter": {"state": "COMPLETE_RELEASED"},
        }))
        self.m.CARRIER_TASK.write_text(json.dumps({
            "state": "COMPLETE_RELEASED",
            "validation_evidence": {"validation_matrix": "PASS"},
            "authority_contract": {
                "credential_requirement_for_local_model": "NONE",
                "github_token_required": False,
                "github_actions_production_role": False,
                "execution_authority": False,
                "model_output_authority": False,
            },
        }))

    def verified_receipt(self):
        receipt = {
            "schema": "stegverse.ecosystem_chat.live_activation.v1",
            "state": "VERIFIED",
            "blockers": [],
            "evidence": {
                "health": {"status": "ok"},
                "chat": {
                    "provider": {"used": True},
                    "provider_usage_submission": {
                        "custody_recorded": False,
                        "event_sha256": "a" * 64,
                    },
                    "master_records_usage_submission": {
                        "custody_recorded": True,
                        "reconstructability": "PASS",
                        "authority_granted": False,
                    },
                    "authority": {"provider_usage_grants_authority": False},
                },
                "transition": {
                    "master_record_status": "RECORDED",
                    "reconstruction_status": "PASS",
                },
            },
            "authority_granted": False,
            "publication_authorized": False,
            "repository_mutation_authorized": False,
        }
        receipt["result_sha256"] = self.m.canonical_sha256(receipt)
        return receipt

    def test_source_contract_is_ready_without_render(self):
        markers = self.m.source_contract_markers()
        self.assertTrue(all(markers.values()))
        self.assertNotIn("render-production.yaml", SCRIPT.read_text(encoding="utf-8"))

    def test_missing_live_receipt_stays_pending_despite_released_source(self):
        with patch.dict(os.environ, {
            "GITHUB_REPOSITORY": "StegVerse-org/LLM-adapter",
            "GITHUB_SHA": "b" * 40,
            "GITHUB_RUN_ID": "123",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_EVENT_NAME": "push",
            "VALIDATION_JOB_STATUS": "success",
        }, clear=True):
            self.assertEqual(self.m.main(), 0)
        state = json.loads(self.m.OUTPUT.read_text())
        self.assertTrue(state["source_contract"]["ready"])
        self.assertFalse(state["source_contract"]["source_readiness_is_activation"])
        self.assertEqual(state["state"], "DESTINATION_ACTIVATION_PENDING_EXTERNAL_EVIDENCE")
        self.assertFalse(state["gates"]["same_origin_authenticated_deployment"]["complete"])
        self.assertFalse(state["gates"]["automatic_provider_usage_submission"]["complete"])
        self.assertFalse(state["gates"]["retrieval_and_provider_usage_receipts"]["complete"])
        self.assertFalse(state["superseded_topology"]["render_required"])
        self.assertFalse(state["credential_boundary"]["github_token_required"])

    def test_valid_same_execution_live_receipt_completes_compatibility_gates(self):
        self.m.LIVE_RECEIPT.write_text(json.dumps(self.verified_receipt()))
        with patch.dict(os.environ, {
            "GITHUB_REPOSITORY": "StegVerse-org/LLM-adapter",
            "GITHUB_SHA": "c" * 40,
            "GITHUB_RUN_ID": "456",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_EVENT_NAME": "push",
            "VALIDATION_JOB_STATUS": "success",
        }, clear=True):
            self.assertEqual(self.m.main(), 0)
        state = json.loads(self.m.OUTPUT.read_text())
        self.assertEqual(state["state"], "DESTINATION_ACTIVATION_EVIDENCE_COMPLETE")
        self.assertTrue(all(gate["complete"] for gate in state["gates"].values()))
        self.assertTrue(state["live_receipt"]["verified"])
        self.assertEqual(
            state["gates"]["same_origin_authenticated_deployment"]["current_semantics"],
            "canonical_sovereign_runtime_service_observed",
        )

    def test_sovereign_parent_projection_completes_compatibility_gates_without_legacy_receipt(self):
        value = {
            "schema": "stegverse.ecosystem_chat.sovereign_activation_projection.v1",
            "state": "VERIFIED",
            "predicates": {
                "real_model_process_observed": True,
                "private_endpoint_only": True,
                "ephemeral_e1_e2_execution_observed": True,
                "measured_usage_persisted": True,
                "provider_usage_reconstruction_pass": True,
                "transition_reconstruction_pass": True,
                "same_execution": True,
                "persistent_conversational_runtime_ready": True,
            },
            "provider_usage": {
                "measured": True,
                "event_sha256": "d" * 64,
                "custody_recorded": True,
                "reconstructability": "PASS",
                "authority_granted": False,
            },
            "transition": {
                "custody_recorded": True,
                "reconstructability": "PASS",
                "same_execution": True,
            },
            "runtime": {
                "private_endpoint_only": True,
                "persistent_conversational_runtime_ready": True,
                "third_party_inference_required": False,
            },
            "credential_boundary": {
                "credential_authority": "TV/TVC",
                "credential_requirement": "NONE",
                "github_token_required": False,
                "github_actions_activation_role": False,
            },
            "authority_boundary": {
                "projection_grants_activation_authority": False,
                "projection_grants_execution_authority": False,
                "projection_grants_custody_authority": False,
                "projection_grants_release_authority": False,
                "projection_grants_publication_authority": False,
            },
        }
        value["projection_sha256"] = self.m.canonical_sha256(value)
        self.m.SOVEREIGN_RECEIPT.write_text(json.dumps(value))
        with patch.dict(os.environ, {
            "GITHUB_REPOSITORY": "StegVerse-org/LLM-adapter",
            "GITHUB_SHA": "e" * 40,
            "GITHUB_RUN_ID": "789",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_EVENT_NAME": "push",
            "VALIDATION_JOB_STATUS": "success",
        }, clear=True):
            self.assertEqual(self.m.main(), 0)
        state = json.loads(self.m.OUTPUT.read_text())
        self.assertEqual(state["activation_evidence_mode"], "SOVEREIGN_PARENT_PROJECTION")
        self.assertTrue(state["sovereign_parent_projection"]["verified"])
        self.assertFalse(state["live_receipt"]["verified"])
        self.assertEqual(state["state"], "DESTINATION_ACTIVATION_EVIDENCE_COMPLETE")

    def test_tampered_verified_receipt_fails_closed(self):
        receipt = self.verified_receipt()
        receipt["evidence"]["transition"]["reconstruction_status"] = "PARTIAL"
        self.m.LIVE_RECEIPT.write_text(json.dumps(receipt))
        valid, errors = self.m.verified_live_receipt(receipt)
        self.assertFalse(valid)
        self.assertIn("verified_live_receipt_hash", errors)


if __name__ == "__main__":
    unittest.main()
