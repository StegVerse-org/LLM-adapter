import unittest

from llm_adapter.manifest_ingress import (
    INGRESS_SCHEMA,
    PROFILE_ID,
    canonical_sha256,
    execute_manifest_ingress,
    verify_manifest_ingress_result,
)


def make_request(**overrides):
    request = {
        "schema": INGRESS_SCHEMA,
        "profile_id": PROFILE_ID,
        "mode": "TEST",
        "request_id": "req-001",
        "unit_id": "unit-001",
        "idempotency_key": "idem-001",
        "manifest": {"kind": "test.vector", "value": 7},
        "provider_selection_authority": False,
        "credential_access_granted": False,
        "route_authority_granted": False,
        "governance_authority_granted": False,
        "repository_access_granted": False,
        "wallet_authority_granted": False,
        "publication_authority_granted": False,
        "release_authority_granted": False,
        "github_token_required": False,
    }
    request.update(overrides)
    candidate = dict(request)
    candidate.pop("request_hash", None)
    request["request_hash"] = canonical_sha256(candidate)
    return request


class ManifestIngressTests(unittest.TestCase):
    def test_test_mode_returns_governed_result(self):
        request = make_request()

        def governed_ingest(manifest, context):
            self.assertEqual(manifest["value"], 7)
            self.assertEqual(context["mode"], "TEST")
            return {
                "decision": "ALLOW",
                "manifest_receipt_id": "mr:test:001",
                "governed_result": {"accepted": True},
                "verification_refs": ["receipt://mr:test:001"],
                "consequence_executed": True,
                "idempotent_replay": False,
            }

        result = execute_manifest_ingress(request=request, governed_ingest=governed_ingest)
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(result["manifest_receipt_id"], "mr:test:001")
        self.assertTrue(result["consequence_executed"])
        self.assertFalse(result["github_token_required"])
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertTrue(verify_manifest_ingress_result(result))

    def test_authority_escalation_fails_closed_without_calling_governance(self):
        request = make_request(provider_selection_authority=True)
        called = False

        def governed_ingest(_manifest, _context):
            nonlocal called
            called = True
            raise AssertionError("must not execute")

        result = execute_manifest_ingress(request=request, governed_ingest=governed_ingest)
        self.assertFalse(called)
        self.assertEqual(result["decision"], "FAIL_CLOSED")
        self.assertFalse(result["consequence_executed"])
        self.assertIn("authority_escalation", result["reason"])
        self.assertTrue(verify_manifest_ingress_result(result))

    def test_live_stream_requires_predecessor_after_first_unit(self):
        request = make_request(mode="LIVE_STREAM", stream_id="stream-1", sequence=2)

        result = execute_manifest_ingress(
            request=request,
            governed_ingest=lambda *_args: self.fail("must not execute"),
        )
        self.assertEqual(result["decision"], "FAIL_CLOSED")
        self.assertEqual(result["reason"], "predecessor_receipt_required")
        self.assertTrue(verify_manifest_ingress_result(result))

    def test_non_allow_cannot_report_consequence_execution(self):
        request = make_request()

        result = execute_manifest_ingress(
            request=request,
            governed_ingest=lambda _manifest, _context: {
                "decision": "DENY",
                "manifest_receipt_id": "mr:test:deny",
                "governed_result": {"accepted": False},
                "verification_refs": ["receipt://mr:test:deny"],
                "consequence_executed": True,
            },
        )
        self.assertEqual(result["decision"], "FAIL_CLOSED")
        self.assertEqual(result["reason"], "non_allow_consequence_execution_forbidden")
        self.assertFalse(result["consequence_executed"])
        self.assertTrue(verify_manifest_ingress_result(result))

    def test_callback_exception_fails_closed_without_secret_detail(self):
        request = make_request()

        def governed_ingest(_manifest, _context):
            raise RuntimeError("secret detail must not escape")

        result = execute_manifest_ingress(request=request, governed_ingest=governed_ingest)
        self.assertEqual(result["decision"], "FAIL_CLOSED")
        self.assertEqual(result["reason"], "governed_ingest_error:RuntimeError")
        self.assertNotIn("secret detail", str(result))
        self.assertTrue(verify_manifest_ingress_result(result))


if __name__ == "__main__":
    unittest.main()
