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

    def test_end_to_end_gateway_uses_exact_tvc_admitted_private_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proof = {"schema": "runtime-proof", "endpoint": "http://127.0.0.1:8088"}
            route = {
                "state": "ROUTE_ADMITTED",
                "route_authority": "StegVerse-Labs/TVC",
                "runtime_proof_hash": stable_hash(proof),
                "credential_requirement": "NONE",
                "github_token_required": False,
                "third_party_execution_platform_required": False,
                "execution_authority": False,
                "authority_effect": "NONE",
                "endpoint": "http://127.0.0.1:8088",
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
                response=SimpleNamespace(output="Start by checking your eligibility and getting a Certificate of Eligibility. Are you buying a home, refinancing, or only checking eligibility?"),
                binding_receipt={
                    "receipt_hash": "a" * 64,
                    "provider_usage_custody_recorded": True,
                    "provider_usage_reconstruction_pass": True,
                },
            )
            with patch.dict(os.environ, env, clear=False), patch(
                "llm_adapter.va_claims_runtime_gateway.execute_verified_local_model",
                return_value=fake_execution,
            ) as execute:
                result = execute_chat(ChatRequest(message="How do I get a VA home loan?", session_id="session-1"))
            self.assertEqual(result["route"], "home_loan")
            self.assertTrue(result["response"].startswith("Start by checking"))
            self.assertEqual(result["citations"][0]["url"], "https://www.va.gov/housing-assistance/home-loans/")
            self.assertTrue(result["provider_usage_custody_recorded"])
            self.assertTrue(result["provider_usage_reconstruction_pass"])
            self.assertFalse(result["authority_effect"])
            self.assertFalse(result["activation_effect"])
            self.assertFalse(result["github_token_required"])
            self.assertEqual(result["credential_requirement"], "NONE")
            self.assertEqual(execute.call_args.kwargs["endpoint"], "http://127.0.0.1:8088/v1/chat/completions")

    def test_fails_closed_for_unadmitted_source_policy(self):
        with self.assertRaisesRegex(RuntimeError, "source_policy_not_admitted"):
            execute_chat(ChatRequest(message="hello", source_policy="ANY_SOURCE"))

    def test_fails_closed_for_private_document_or_filing_request(self):
        with self.assertRaisesRegex(RuntimeError, "private_document_or_filing_route_not_active"):
            execute_chat(ChatRequest(message="submit this", filing_requested=True))


if __name__ == "__main__":
    unittest.main()
