from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from llm_adapter.va_claims_runtime_gateway import ChatRequest, classify_route, execute_chat


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

    def test_end_to_end_gateway_uses_exact_tvc_route_and_same_execution_reconstruction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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
            }
            fake_execution = SimpleNamespace(
                response=SimpleNamespace(output="reference model text"),
                usage_event={"event_sha256": "u" * 64},
                master_records_usage={"status": "NOT_CONFIGURED"},
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
            reconstruction = {
                "state": "PASS",
                "receipt_hash": "z" * 64,
                "provider_usage_custody_recorded": True,
                "provider_usage_reconstruction_pass": True,
                "transition_reconstruction_pass": True,
                "same_execution": True,
            }
            with patch.dict(os.environ, env, clear=False), patch(
                "llm_adapter.va_claims_runtime_core.execute_verified_local_model",
                return_value=fake_execution,
            ) as execute, patch(
                "llm_adapter.va_claims_runtime_core._reconstruct_turn",
                return_value=reconstruction,
            ) as reconstruct:
                result = execute_chat(ChatRequest(message="How do I get a VA home loan?", session_id="session-1"))
            self.assertEqual(result["route"], "home_loan")
            self.assertIn("Certificate of Eligibility", result["response"])
            self.assertIn("buying a home", result["response"])
            self.assertEqual(result["citations"][0]["url"], "https://www.va.gov/housing-assistance/home-loans/")
            self.assertTrue(result["provider_usage_custody_recorded"])
            self.assertTrue(result["provider_usage_reconstruction_pass"])
            self.assertTrue(result["transition_reconstruction_pass"])
            self.assertTrue(result["same_execution"])
            self.assertTrue(result["reference_model_fallback_renderer_used"])
            self.assertFalse(result["authority_effect"])
            self.assertFalse(result["activation_effect"])
            self.assertFalse(result["github_token_required"])
            self.assertEqual(result["credential_requirement"], "NONE")
            self.assertEqual(execute.call_args.kwargs["endpoint"], "http://127.0.0.1:8088/v1/chat/completions")
            self.assertEqual(reconstruct.call_count, 1)

    def test_fails_closed_for_unadmitted_source_policy(self):
        with self.assertRaisesRegex(RuntimeError, "source_policy_not_admitted"):
            execute_chat(ChatRequest(message="hello", source_policy="ANY_SOURCE"))

    def test_fails_closed_for_private_document_or_filing_request(self):
        with self.assertRaisesRegex(RuntimeError, "private_document_or_filing_route_not_active"):
            execute_chat(ChatRequest(message="submit this", filing_requested=True))


if __name__ == "__main__":
    unittest.main()
