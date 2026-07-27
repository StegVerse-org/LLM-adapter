from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from llm_adapter import service_gateway_site


class HILReadinessContractTests(unittest.TestCase):
    def test_readiness_advertises_status_retry_and_privacy_contract(self) -> None:
        with patch.object(
            service_gateway_site.gateway,
            "_runtime",
            return_value={"tvc": {"decision_id": "TVC-TEST"}},
        ), patch.dict(os.environ, {"STEGVERSE_NOTIFICATION_MAX_ATTEMPTS": "7"}, clear=False):
            readiness = service_gateway_site.site_hil_readiness()

        self.assertEqual(readiness["state"], "READY")
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

    def test_retry_bound_is_clamped_and_invalid_values_fail_safe(self) -> None:
        cases = (("0", 1), ("21", 20), ("invalid", 5))
        for configured, expected in cases:
            with self.subTest(configured=configured), patch.object(
                service_gateway_site.gateway,
                "_runtime",
                return_value={"tvc": {"decision_id": "TVC-TEST"}},
            ), patch.dict(
                os.environ,
                {"STEGVERSE_NOTIFICATION_MAX_ATTEMPTS": configured},
                clear=False,
            ):
                readiness = service_gateway_site.site_hil_readiness()
                self.assertEqual(readiness["notification_max_attempts"], expected)


if __name__ == "__main__":
    unittest.main()
