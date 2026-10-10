"""VACC is manifest-bound transport (SDK-MANIFEST-COLLAB-INGRESS-CONFORMANCE-001).

A VA claims turn is translated into the SDK's `stegverse.route.va-scoped-chat.v1`
manifest with this deployment's VA scope declared as manifest policy, handed to
`stegverse.manifest_execution.execute_manifest`, and answered with the SDK
disposition: DENY for a topic outside the declared scope, otherwise FAIL_CLOSED
until the canonical organization boundary resolves.
"""
from __future__ import annotations

import inspect
import json
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from llm_adapter import va_claims_runtime_core
from llm_adapter.va_claims_runtime_core import VA_SCOPE_POLICY, readiness_record
from llm_adapter.va_claims_runtime_gateway import ChatRequest, chat, classify_route, execute_chat

SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
VA_ROUTE = "stegverse.route.va-scoped-chat.v1"
PLANTED = {
    "STEGVERSE_TVC_ROUTE_RECEIPT_FILE": "/planted/tvc-route.json",
    "STEGVERSE_CANONICAL_RUNTIME_PROOF_FILE": "/planted/proof.json",
    "STEGVERSE_VA_SOURCE_REGISTRY_FILE": "/planted/registry.json",
    "STEGVERSE_PROVIDER_TOKEN": "planted-provider-token",
}


def _no_network(*_args, **_kwargs):
    raise AssertionError("VACC must not open a network connection")


class _Isolated(unittest.TestCase):
    def setUp(self):
        for patcher in (patch.dict(os.environ, PLANTED),
                        patch("urllib.request.urlopen", _no_network),
                        patch("socket.create_connection", _no_network)):
            patcher.start()
            self.addCleanup(patcher.stop)


class _AdmittingFarSide:
    """Far-side double for an organization that admitted the manifest."""

    def __init__(self):
        self.handed = []

    def __call__(self, payload):
        from llm_adapter import sdk_boundary
        manifest = dict(payload["manifest"])
        assert sdk_boundary.validate({"manifest": manifest})["accepted"] is True
        self.handed.append(manifest)
        return {"schema": sdk_boundary.BOUNDARY_SCHEMA, "handed_off": True, "disposition": "ALLOW",
                "envelope": {"governance_state": "ALLOW", "organization_receipt_observed": True}}


class VAClaimsManifestBindingTests(_Isolated):
    def test_keyword_classifier_is_a_topic_hint_only(self):
        self.assertEqual(classify_route("How do I get a VA home loan?"), "home_loan")
        self.assertEqual(classify_route("My community care provider cannot find the authorization"), "community_care")
        self.assertEqual(classify_route("What evidence do I need for my claim?"), "evidence_requirement")
        self.assertEqual(classify_route("How do I appeal a denial?"), "appeal_or_supplemental_claim")
        self.assertEqual(classify_route("I need help with my GI Bill"), "education")
        self.assertEqual(classify_route("I need VR&E help"), "vre")
        source = inspect.getsource(va_claims_runtime_core.execute_chat)
        self.assertNotIn("_build_grounded_answer", source)
        self.assertEqual(readiness_record()["keyword_classifier_role"], "MANIFEST_DRAFT_TOPIC_HINT_ONLY")

    def test_refused_without_an_admitted_manifest(self):
        result = execute_chat(ChatRequest(message="How do I get a VA home loan?", session_id="session-1"))
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], "CANONICAL_ORGANIZATION_INGRESS_ENDPOINT_NOT_RESOLVED")
        for key in SIX:
            self.assertTrue(result[key], key)
        self.assertEqual(result["route_id"], VA_ROUTE)
        self.assertIs(result["handed_off"], True)
        self.assertIsNone(result["response"])
        self.assertEqual(result["turn_closed_on"], "SDK_MANIFEST_DISPOSITION")
        self.assertIs(result["local_receipt_is_organization_observation"], False)
        self.assertIs(result["master_records_gating"], False)
        self.assertIs(result["local_model_called"], False)
        self.assertIs(result["provider_usage_attributed"], False)
        self.assertNotIn("ORGANIZATION_LEDGER_TRANSITION_RECEIPT", json.dumps(result))

    def test_out_of_scope_request_is_a_governed_deny(self):
        result = execute_chat(ChatRequest(message="Help me run payroll", session_id="session-2",
                                          requested_topic="payroll"))
        self.assertEqual(result["disposition"], "DENY")
        self.assertEqual(result["failed_predicate"], "REQUESTED_TOPIC_WITHIN_MANIFEST_DECLARED_VA_SCOPE")
        far_side = result["sdk_boundary"]["envelope"]["far_side_disposition"]
        self.assertEqual(far_side["disposition"], "DENY")
        self.assertIs(result["sdk_boundary"]["envelope"]["consequence_executed"], False)
        with self.assertRaises(HTTPException) as refused:
            chat(ChatRequest(message="Help me run payroll", requested_topic="payroll"))
        self.assertEqual(refused.exception.status_code, 403)
        self.assertEqual(refused.exception.detail["disposition"], "DENY")

    def test_in_scope_topic_is_not_denied(self):
        result = execute_chat(ChatRequest(message="question", requested_topic="home_loan"))
        self.assertNotEqual(result["disposition"], "DENY")

    def test_manifest_is_bound_before_processing_with_manifest_declared_scope(self):
        far_side = _AdmittingFarSide()
        with patch("llm_adapter.sdk_boundary.submit", far_side):
            result = execute_chat(ChatRequest(message="How do I get a VA home loan?", session_id="session-3",
                                              route_scope="ANYTHING", requested_capability="OTHER"))
        self.assertEqual(result["disposition"], "ALLOW")
        [manifest] = far_side.handed
        self.assertEqual(manifest["processing"], {"capability": "va_scoped_chat", "route_id": VA_ROUTE})
        va = manifest["extensions"]["stegverse_va_scoped_chat_request"]
        self.assertEqual(va["requested_topic"], "home_loan")
        self.assertEqual(va["va_scope"]["policy_id"], VA_SCOPE_POLICY["policy_id"])
        self.assertEqual(va["va_scope"]["allowed_topics"], VA_SCOPE_POLICY["allowed_topics"])
        self.assertNotIn("ANYTHING", json.dumps(manifest))

    def test_execute_manifest_path_is_used(self):
        import stegverse.manifest_execution as canonical

        calls = []
        real = canonical.execute_manifest

        def spy(manifest, **kwargs):
            calls.append(manifest)
            return real(manifest, **kwargs)

        with patch.object(canonical, "execute_manifest", spy):
            result = execute_chat(ChatRequest(message="How do I appeal a denial?"))
        self.assertEqual(result["canonical_entrypoint"], "stegverse.manifest_execution.execute_manifest")
        self.assertEqual([m["processing"]["route_id"] for m in calls], [VA_ROUTE])

    def test_no_environment_credential_or_input_is_read(self):
        result = execute_chat(ChatRequest(message="How do I get a VA home loan?"))
        for value in PLANTED.values():
            self.assertNotIn(value, json.dumps(result))
        self.assertIs(result["credential_read_from_environment"], False)
        source = inspect.getsource(va_claims_runtime_core)
        for marker in ("os.environ", "getenv", "load_object_env", "STEGVERSE_TVC_ROUTE_RECEIPT_FILE",
                       "execute_verified_local_model", "emit.py"):
            self.assertNotIn(marker, source)

    def test_readiness_reads_no_environment_and_claims_no_ready_runtime(self):
        ready = readiness_record()
        self.assertEqual(ready["state"], "MANIFEST_BOUND_TRANSPORT")
        self.assertEqual(ready["route_id"], VA_ROUTE)
        self.assertEqual(ready["va_scope_policy_source"], "MANIFEST_DECLARED")
        self.assertIs(ready["local_receipt_is_organization_observation"], False)
        self.assertIs(ready["master_records_gating"], False)

    def test_gateway_refusal_carries_the_six_fields(self):
        with self.assertRaises(HTTPException) as refused:
            chat(ChatRequest(message="hello", source_policy="ANY_SOURCE"))
        self.assertEqual(refused.exception.status_code, 503)
        detail = refused.exception.detail
        self.assertEqual(detail["disposition"], "FAIL_CLOSED")
        self.assertEqual(detail["failure_code"], "source_policy_not_admitted")
        for key in SIX:
            self.assertTrue(detail[key], key)

    def test_gateway_returns_sdk_fail_closed(self):
        with self.assertRaises(HTTPException) as refused:
            chat(ChatRequest(message="How do I get a VA home loan?"))
        self.assertEqual(refused.exception.status_code, 503)
        self.assertEqual(refused.exception.detail["failure_code"],
                         "CANONICAL_ORGANIZATION_INGRESS_ENDPOINT_NOT_RESOLVED")

    def test_fails_closed_for_unadmitted_source_policy(self):
        with self.assertRaisesRegex(RuntimeError, "source_policy_not_admitted"):
            execute_chat(ChatRequest(message="hello", source_policy="ANY_SOURCE"))

    def test_fails_closed_for_private_document_or_filing_request(self):
        with self.assertRaisesRegex(RuntimeError, "private_document_or_filing_route_not_active"):
            execute_chat(ChatRequest(message="submit this", filing_requested=True))


if __name__ == "__main__":
    unittest.main()
