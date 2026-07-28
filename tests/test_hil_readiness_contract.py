from __future__ import annotations

import hashlib
import os
import unittest
from unittest.mock import patch

from llm_adapter import service_gateway_site


class HILReadinessContractTests(unittest.TestCase):
    def _readiness(self, configured_attempts: str = "7"):
        with patch.object(
            service_gateway_site.gateway,
            "_runtime",
            return_value={"tvc": {"decision_id": "TVC-TEST"}},
        ), patch.dict(
            os.environ,
            {"STEGVERSE_NOTIFICATION_MAX_ATTEMPTS": configured_attempts},
            clear=False,
        ):
            return service_gateway_site.site_hil_readiness()

    def test_readiness_advertises_status_retry_privacy_and_schema_digests(self) -> None:
        readiness = self._readiness()

        self.assertEqual(readiness["state"], "READY")
        self.assertEqual(readiness["schema_version"], "HIL-READINESS-v1")
        self.assertEqual(readiness["attempt_notification_schema"], "HIL-ATTEMPT-NOTIFICATION-v1")
        self.assertEqual(readiness["submission_status_schema"], "HIL-SUBMISSION-STATUS-v1")
        self.assertEqual(
            readiness["submission_status_authorization"],
            "SUBMISSION_ID_PLUS_RECEIPT_ID",
        )
        self.assertEqual(readiness["notification_max_attempts"], 7)
        self.assertEqual(
            set(readiness["terminal_notification_delivery_states"]),
            {"DELIVERED", "PARTIAL_EXPIRED", "DELIVERY_EXPIRED"},
        )
        self.assertFalse(readiness["completed_recipient_addresses_retained"])
        self.assertFalse(readiness["expired_recipient_addresses_retained"])
        self.assertFalse(readiness["notification_delivery_changes_submission_outcome"])

        bindings = (
            ("readiness_schema_path", "readiness_schema_sha256"),
            ("attempt_notification_schema_path", "attempt_notification_schema_sha256"),
            ("submission_status_schema_path", "submission_status_schema_sha256"),
        )
        for path_field, digest_field in bindings:
            path = readiness[path_field]
            expected = hashlib.sha256(service_gateway_site._schema_bytes(path)).hexdigest()
            self.assertEqual(readiness[digest_field], expected)
            self.assertRegex(readiness[digest_field], r"^[a-f0-9]{64}$")

    def test_schema_endpoints_serve_exact_advertised_bytes(self) -> None:
        readiness = self._readiness()
        endpoints = (
            service_gateway_site.hil_readiness_schema,
            service_gateway_site.hil_attempt_notification_schema,
            service_gateway_site.hil_submission_status_schema,
        )
        digest_fields = (
            "readiness_schema_sha256",
            "attempt_notification_schema_sha256",
            "submission_status_schema_sha256",
        )
        for endpoint, digest_field in zip(endpoints, digest_fields):
            response = endpoint()
            self.assertEqual(response.media_type, "application/schema+json")
            self.assertEqual(hashlib.sha256(response.body).hexdigest(), readiness[digest_field])
            self.assertEqual(response.headers["x-content-type-options"], "nosniff")
            self.assertIn(readiness[digest_field], response.headers["etag"])

    def test_retry_bound_is_clamped_and_invalid_values_fail_safe(self) -> None:
        cases = (("0", 1), ("21", 20), ("invalid", 5))
        for configured, expected in cases:
            with self.subTest(configured=configured):
                readiness = self._readiness(configured)
                self.assertEqual(readiness["notification_max_attempts"], expected)


if __name__ == "__main__":
    unittest.main()
