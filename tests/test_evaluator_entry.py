from __future__ import annotations

import copy
import hashlib
import json
import unittest

from llm_adapter.evaluator_entry import execute_evaluator_entry, verify_evaluator_entry_receipt, verify_sdk_evaluator_request, verify_sdk_relationship


def h(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def relationship():
    value = {
        "schema":"stegverse.sdk.evaluation-relationship-result.v1",
        "request_id":"eval-rel-1",
        "participant_id":"evaluator:example",
        "terms_acceptance_receipt_hash":"1"*64,
        "objectives":["evaluate LLM behavior"],
        "matched_by_objective":{},
        "admitted_capabilities":[{"capability_id":"llm_adapter.evaluator_interaction","title":"SDK-scoped LLM evaluation interaction","interaction":"sandbox","route":"sdk://StegVerse-org/LLM-adapter/evaluator-entry"}],
        "denied_or_unavailable":[],
        "unresolved_objectives":[],
        "maximum_interaction":"sandbox",
        "recipient_specific_package":False,
        "identity_bound_package":False,
        "execution_authority_granted":False,
        "mutation_authority_granted":False,
        "publication_authority_granted":False,
        "wallet_authority_granted":False,
        "credential_authority_granted":False,
        "repository_access_granted":False,
        "unknown_interest_auto_admitted":False,
    }
    value["receipt_hash"] = h(value)
    return value


def request(rel):
    value = {
        "schema":"stegverse.sdk.evaluator-llm-entry-request.v1",
        "request_id":"llm-eval-1",
        "participant_id":rel["participant_id"],
        "relationship_receipt_hash":rel["receipt_hash"],
        "terms_acceptance_receipt_hash":rel["terms_acceptance_receipt_hash"],
        "capability_id":"llm_adapter.evaluator_interaction",
        "route":"sdk://StegVerse-org/LLM-adapter/evaluator-entry",
        "evaluation_model_scope":"local_reference_only",
        "prompt":"Explain the observed governance decision.",
        "max_output_tokens":128,
        "provider_selection_authority":False,
        "credential_access_granted":False,
        "execution_authority_granted":False,
        "repository_access_granted":False,
    }
    value["request_hash"] = h(value)
    return value


class EvaluatorEntryTests(unittest.TestCase):
    def test_relationship_and_request_validate(self):
        rel = relationship(); req = request(rel)
        self.assertTrue(verify_sdk_relationship(rel))
        self.assertTrue(verify_sdk_evaluator_request(req, rel))

    def test_scope_or_authority_escalation_fails(self):
        rel = relationship(); req = request(rel)
        escalated = copy.deepcopy(req); escalated["evaluation_model_scope"] = "arbitrary_provider"
        self.assertFalse(verify_sdk_evaluator_request(escalated, rel))
        escalated = copy.deepcopy(req); escalated["credential_access_granted"] = True
        self.assertFalse(verify_sdk_evaluator_request(escalated, rel))

    def test_execution_receipt_is_bounded_and_non_authorizing(self):
        rel = relationship(); req = request(rel)
        def local_reference(prompt, max_tokens):
            self.assertEqual(prompt, req["prompt"]); self.assertEqual(max_tokens, 128)
            return {"text":"bounded answer","model_id":"stegverse-reference-lm-v1","measured_usage":{"prompt_tokens":5,"completion_tokens":2,"total_tokens":7}}
        receipt = execute_evaluator_entry(request=req, relationship=rel, local_reference_executor=local_reference)
        self.assertTrue(verify_evaluator_entry_receipt(receipt))
        self.assertFalse(receipt["provider_credentials_exposed"])
        self.assertFalse(receipt["provider_selection_authority"])
        self.assertFalse(receipt["github_token_required"])
        self.assertFalse(receipt["third_party_execution_platform_required"])
        self.assertEqual(receipt["authority_effect"], "NONE")

    def test_relationship_without_capability_fails(self):
        rel = relationship(); rel["admitted_capabilities"] = []; rel["receipt_hash"] = h({k:v for k,v in rel.items() if k != "receipt_hash"})
        self.assertFalse(verify_sdk_relationship(rel))


if __name__ == "__main__":
    unittest.main()
