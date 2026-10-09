from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from llm_adapter.va_claims_runtime_core import readiness_record
from llm_adapter.va_claims_runtime_gateway import ChatRequest, chat, classify_route, execute_chat

SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


class VAClaimsRuntimeGatewayTests(unittest.TestCase):
    def test_route_classification_covers_user_facing_va_questions(self):
        self.assertEqual(classify_route("How do I get a VA home loan?"), "home_loan")
        self.assertEqual(classify_route("My community care provider cannot find the authorization"), "community_care")
        self.assertEqual(classify_route("What evidence do I need for my claim?"), "evidence_requirement")
        self.assertEqual(classify_route("How do I appeal a denial?"), "appeal_or_supplemental_claim")
        self.assertEqual(classify_route("I need help with my GI Bill"), "education")
        self.assertEqual(classify_route("I need VR&E help"), "vre")

    def materialize(self, root: Path, *, model_output: str = "reference model text") -> tuple[dict, SimpleNamespace]:
        proof = {"schema": "runtime-proof", "endpoint": "http://127.0.0.1:8088", "proof_hash": "p" * 64}
        route = {
            "state": "ROUTE_ADMITTED",
            "route_authority": "StegVerse-Labs/TVC",
            "runtime_proof_hash": stable_hash(proof),
            "canonical_micro_node_proof_consumed": True,
            "credential_requirement": "NONE",
            "github_token_required": False,
            "third_party_execution_platform_required": False,
            "execution_authority": False,
            "authority_effect": "NONE",
            "endpoint": "http://127.0.0.1:8088",
            "receipt_hash": "r" * 64,
        }
        registry = {
            "last_verified": "2026-08-21",
            "sources": [{
                "source_id": "VA-HOME-LOANS",
                "name": "VA Home Loans",
                "authority_class": "OFFICIAL_OPERATIONAL",
                "publisher": "U.S. Department of Veterans Affairs",
                "url": "https://www.va.gov/housing-assistance/home-loans/",
                "admitted": True,
            }],
        }
        paths = {}
        for name, value in (("proof", proof), ("route", route), ("registry", registry)):
            path = root / f"{name}.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            paths[name] = str(path)
        env = {
            "STEGVERSE_CANONICAL_RUNTIME_PROOF_FILE": paths["proof"],
            "STEGVERSE_TVC_ROUTE_RECEIPT_FILE": paths["route"],
            "STEGVERSE_VA_SOURCE_REGISTRY_FILE": paths["registry"],
            "STEGVERSE_REPO_LEDGER_ROOT": str(root / "ledger"),
            "STEGVERSE_VA_RUNTIME_RECEIPT_DIR": str(root / "va-receipts"),
            "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": str(root / "no-capsule"),
        }
        fake_execution = SimpleNamespace(
            response=SimpleNamespace(output=model_output),
            usage_event={"event_sha256": "u" * 64},
            provider_usage_record={"status": "NOT_CONFIGURED"},
            binding_receipt={
                "model_id": "stegverse-reference-lm-v1",
                "model_hash": "m" * 64,
                "request_hash": "q" * 64,
                "response_hash": "s" * 64,
                "measured_usage": {
                    "prompt_tokens": {"value": "10", "unit": "tokens", "evidence_class": "MEASURED", "source_ref": "provider_response:" + "s" * 64},
                    "completion_tokens": {"value": "4", "unit": "tokens", "evidence_class": "MEASURED", "source_ref": "provider_response:" + "s" * 64},
                    "total_tokens": {"value": "14", "unit": "tokens", "evidence_class": "MEASURED", "source_ref": "provider_response:" + "s" * 64},
                    "latency_ms": {"value": "2", "unit": "milliseconds", "evidence_class": "MEASURED", "source_ref": "provider_response:" + "s" * 64},
                },
                "provider_usage_custody_recorded": False,
                "provider_usage_reconstruction_pass": False,
                "reference_model_only": True,
            },
        )
        return env, fake_execution

    def run_turn(self, env, fake_execution, **patches):
        with patch.dict(os.environ, env, clear=False), patch(
            "llm_adapter.va_claims_runtime_core.execute_verified_local_model",
            return_value=fake_execution,
        ) as execute:
            if "reconstruction" in patches:
                with patch("llm_adapter.va_claims_runtime_core._reconstruct_turn",
                           return_value=patches["reconstruction"]) as reconstruct:
                    result = execute_chat(ChatRequest(message="How do I get a VA home loan?", session_id="session-1"))
                return result, execute, reconstruct
            result = execute_chat(ChatRequest(message="How do I get a VA home loan?", session_id="session-1"))
            return result, execute, None

    def ledger_chain(self, env):
        root = Path(env["STEGVERSE_REPO_LEDGER_ROOT"])
        return [json.loads(path.read_text()) for path in sorted((root / "receipts").glob("*.json"))]

    def assert_closed_on_transition_receipt(self, env, result):
        self.assertEqual(result["disposition"], "ALLOW")
        self.assertEqual(result["turn_closed_on"], "ORGANIZATION_LEDGER_TRANSITION_RECEIPT")
        chain = self.ledger_chain(env)
        self.assertEqual([r["transition_class"] for r in chain], ["VA_CLAIMS_TURN_EXECUTED"])
        self.assertEqual(chain[0]["receipt_sha256"], result["transition_receipt_sha256"])
        self.assertEqual(chain[0]["evidence"]["disposition"], "ALLOW")
        self.assertIs(chain[0]["evidence"]["master_records_gates_turn"], False)
        self.assertEqual(chain[0]["evidence"]["execution_receipt_hash"], result["execution_receipt_hash"])

    def test_end_to_end_gateway_uses_exact_tvc_route_and_same_execution_reconstruction(self):
        with tempfile.TemporaryDirectory() as tmp:
            env, fake_execution = self.materialize(Path(tmp))
            reconstruction = {
                "state": "PASS",
                "gates_turn": False,
                "receipt_hash": "z" * 64,
                "provider_usage_custody_recorded": True,
                "provider_usage_reconstruction_pass": True,
                "transition_reconstruction_pass": True,
                "same_execution": True,
            }
            result, execute, reconstruct = self.run_turn(env, fake_execution, reconstruction=reconstruction)
            self.assertEqual(result["route"], "home_loan")
            self.assertIn("Certificate of Eligibility", result["response"])
            self.assertIn("buying a home", result["response"])
            self.assertEqual(result["citations"][0]["url"], "https://www.va.gov/housing-assistance/home-loans/")
            self.assertTrue(result["provider_usage_custody_recorded"])
            self.assertTrue(result["provider_usage_reconstruction_pass"])
            self.assertTrue(result["transition_reconstruction_pass"])
            self.assertTrue(result["same_execution"])
            self.assertEqual(result["reconstruction_receipt_hash"], "z" * 64)
            self.assertTrue(result["reference_model_fallback_renderer_used"])
            self.assertFalse(result["authority_effect"])
            self.assertFalse(result["activation_effect"])
            self.assertFalse(result["github_token_required"])
            self.assertEqual(result["credential_requirement"], "NONE")
            self.assertEqual(execute.call_args.kwargs["endpoint"], "http://127.0.0.1:8088/v1/chat/completions")
            self.assertEqual(reconstruct.call_count, 1)
            self.assert_closed_on_transition_receipt(env, result)

    def test_turn_closes_without_a_materialized_master_records_capsule(self):
        with tempfile.TemporaryDirectory() as tmp:
            env, fake_execution = self.materialize(Path(tmp))
            result, _, _ = self.run_turn(env, fake_execution)
            self.assert_closed_on_transition_receipt(env, result)
            self.assertIn("Certificate of Eligibility", result["response"])
            evidence = result["master_records_reconstruction"]
            self.assertEqual(evidence["state"], "NOT_MATERIALIZED")
            self.assertIs(evidence["gates_turn"], False)
            self.assertEqual(evidence["failure_code"], "master_records_local_capsule_not_materialized")
            for key in SIX:
                self.assertTrue(evidence[key], key)
            self.assertEqual(evidence["owning_existing_goal"], "LLMA-DECLARED-PATH-CONFORMANCE-368")
            self.assertIsNone(result["reconstruction_receipt_hash"])
            self.assertFalse(result["provider_usage_reconstruction_pass"])
            self.assertFalse(result["same_execution"])

    def capsule(self, root: Path, body: str) -> Path:
        capsule = root / "capsule"
        script = capsule / "scripts" / "reconstruct_ecosystem_chat_sovereign_execution.py"
        script.parent.mkdir(parents=True)
        script.write_text(body, encoding="utf-8")
        return capsule

    def test_failed_reconstruction_does_not_withhold_the_closed_turn(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, fake_execution = self.materialize(root)
            env["STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT"] = str(self.capsule(root, "raise SystemExit(1)\n"))
            result, _, _ = self.run_turn(env, fake_execution)
            self.assert_closed_on_transition_receipt(env, result)
            evidence = result["master_records_reconstruction"]
            self.assertEqual(evidence["state"], "FAILED")
            self.assertEqual(evidence["failure_code"], "master_records_turn_reconstruction_receipt_missing")
            self.assertIs(evidence["gates_turn"], False)

    def test_master_records_packet_keys_are_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, fake_execution = self.materialize(root)
            echo = (
                "import argparse, json\n"
                "p = argparse.ArgumentParser(); p.add_argument('--packet'); p.add_argument('--output')\n"
                "a = p.parse_args(); packet = json.load(open(a.packet))\n"
                "receipt = packet['llm_adapter_execution_receipt']\n"
                "json.dump({'state': 'PASS', 'packet_keys': sorted(packet),\n"
                "  'session_id': receipt['session_id'], 'transition_id': receipt['transition_id'],\n"
                "  'measurement_id': receipt['measurement_id'], 'provider_usage_custody_recorded': True,\n"
                "  'provider_usage_reconstruction_pass': True, 'transition_reconstruction_pass': True,\n"
                "  'same_execution': True, 'github_token_required': False, 'execution_authority': False,\n"
                "  'authority_effect': 'NONE', 'reconstruction_receipt_hash': 'h' * 64}, open(a.output, 'w'))\n"
            )
            env["STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT"] = str(self.capsule(root, echo))
            result, _, _ = self.run_turn(env, fake_execution)
            self.assert_closed_on_transition_receipt(env, result)
            self.assertEqual(result["master_records_reconstruction"]["state"], "PASS")
            self.assertEqual(result["reconstruction_receipt_hash"], "h" * 64)
            self.assertTrue(result["same_execution"])
            written = next(Path(env["STEGVERSE_VA_RUNTIME_RECEIPT_DIR"]).glob("session-1/*.reconstruction.json"))
            self.assertEqual(json.loads(written.read_text())["packet_keys"],
                             ["llm_adapter_execution_receipt", "runtime_proof", "tvc_route_receipt"])

    def test_readiness_does_not_require_master_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            env, _ = self.materialize(Path(tmp))
            with patch.dict(os.environ, env, clear=False):
                ready = readiness_record()
            self.assertEqual(ready["state"], "READY")
            self.assertEqual(ready["per_turn_reconstruction"], "OPTIONAL_NON_GATING")
            self.assertIs(ready["master_records_capsule_materialized"], False)
            self.assertEqual(ready["turn_closes_on"], "ORGANIZATION_LEDGER_TRANSITION_RECEIPT")

    def test_empty_model_output_is_a_six_field_non_allow(self):
        with tempfile.TemporaryDirectory() as tmp:
            env, fake_execution = self.materialize(Path(tmp), model_output="   ")
            result, _, _ = self.run_turn(env, fake_execution)
            self.assertEqual(result["disposition"], "FAIL_CLOSED")
            self.assertEqual(result["failure_code"], "model_response_empty")
            for key in SIX:
                self.assertTrue(result[key], key)
            self.assertEqual(self.ledger_chain(env), [])

    def test_gateway_refusal_carries_the_six_fields(self):
        with self.assertRaises(HTTPException) as refused:
            chat(ChatRequest(message="hello", source_policy="ANY_SOURCE"))
        self.assertEqual(refused.exception.status_code, 503)
        detail = refused.exception.detail
        self.assertEqual(detail["disposition"], "FAIL_CLOSED")
        self.assertEqual(detail["failure_code"], "source_policy_not_admitted")
        for key in SIX:
            self.assertTrue(detail[key], key)

    def test_fails_closed_for_unadmitted_source_policy(self):
        with self.assertRaisesRegex(RuntimeError, "source_policy_not_admitted"):
            execute_chat(ChatRequest(message="hello", source_policy="ANY_SOURCE"))

    def test_fails_closed_for_private_document_or_filing_request(self):
        with self.assertRaisesRegex(RuntimeError, "private_document_or_filing_route_not_active"):
            execute_chat(ChatRequest(message="submit this", filing_requested=True))


if __name__ == "__main__":
    unittest.main()
