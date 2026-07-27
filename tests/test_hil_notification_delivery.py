from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from llm_adapter import notification_delivery as delivery


class FakeSMTP:
    sent_to: list[str] = []
    fail_participant = True

    def __init__(self, host: str, port: int, timeout: int = 30) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def starttls(self, context=None) -> None:
        return None

    def login(self, username: str, password: str) -> None:
        return None

    def send_message(self, message) -> None:
        address = str(message["To"])
        self.sent_to.append(address)
        if self.fail_participant and address == "participant@example.com":
            raise RuntimeError("simulated participant delivery failure")


class NotificationDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeSMTP.sent_to = []
        FakeSMTP.fail_participant = True
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "notifications").mkdir()
        (self.root / "notification-outbox").mkdir()
        self.notification_path = self.root / "notifications" / "attempt.json"
        self.envelope_path = self.root / "notification-outbox" / "attempt.json"

        notification = {
            "attempt_id": "HIL-ATTEMPT-TEST",
            "terminal_state": "SUBMISSION_ACCEPTED",
            "last_completed_transition": "RECEIPT_EMITTED",
            "submission_id": "HIL-SUBMISSION-TEST",
            "receipt_id": "HIL-RECEIPT-TEST",
            "chain_validation_state": "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED",
            "custody_state": "DURABLE_CUSTODY_COMMITTED",
            "reason_code": None,
            "retry_or_reconciliation_state": "NONE",
            "notification_delivery_state": "PENDING",
        }
        envelope = {
            "attempt_id": "HIL-ATTEMPT-TEST",
            "notification_path": str(self.notification_path),
            "recipients": [
                {"role": "STEGVERSE_STUDY_AUTHORITY", "address": "Rigel@stegverse.org"},
                {"role": "PARTICIPANT_ATTEMPT_COPY", "address": "participant@example.com"},
            ],
            "delivery_state": "PENDING",
        }
        self.notification_path.write_text(json.dumps(notification), encoding="utf-8")
        self.envelope_path.write_text(json.dumps(envelope), encoding="utf-8")

        self.env = patch.dict(
            os.environ,
            {
                "STEGVERSE_NOTIFICATION_FROM": "notices@stegverse.org",
                "STEGVERSE_SMTP_HOST": "smtp.example.test",
                "STEGVERSE_SMTP_PORT": "587",
                "STEGVERSE_SMTP_USERNAME": "test-user",
                "STEGVERSE_SMTP_PASSWORD": "test-password",
                "STEGVERSE_SMTP_STARTTLS": "false",
                "STEGVERSE_NOTIFICATION_MAX_ATTEMPTS": "5",
            },
            clear=False,
        )
        self.smtp = patch("llm_adapter.notification_delivery.smtplib.SMTP", FakeSMTP)
        self.env.start()
        self.smtp.start()

    def tearDown(self) -> None:
        self.smtp.stop()
        self.env.stop()
        self.temp.cleanup()

    def test_partial_delivery_redacts_success_and_retries_only_unresolved(self) -> None:
        first = delivery.deliver_envelope(self.envelope_path)
        self.assertEqual(first["delivery_state"], "PARTIAL")
        self.assertEqual(first["unresolved_recipient_count"], 1)
        self.assertEqual(first["retained_recipient_address_count"], 1)
        self.assertEqual(first["retry_authority_state"], "ACTIVE")
        self.assertEqual(FakeSMTP.sent_to, ["Rigel@stegverse.org", "participant@example.com"])

        by_role = {item["role"]: item for item in first["recipients"]}
        self.assertNotIn("address", by_role["STEGVERSE_STUDY_AUTHORITY"])
        self.assertEqual(
            by_role["STEGVERSE_STUDY_AUTHORITY"]["address_retention_state"],
            "REDACTED_AFTER_DELIVERY",
        )
        self.assertEqual(by_role["PARTICIPANT_ATTEMPT_COPY"]["address"], "participant@example.com")

        FakeSMTP.fail_participant = False
        second = delivery.deliver_envelope(self.envelope_path)
        self.assertEqual(second["delivery_state"], "DELIVERED")
        self.assertEqual(second["unresolved_recipient_count"], 0)
        self.assertEqual(second["retained_recipient_address_count"], 0)
        self.assertEqual(second["retry_authority_state"], "TERMINATED")
        self.assertEqual(
            FakeSMTP.sent_to,
            ["Rigel@stegverse.org", "participant@example.com", "participant@example.com"],
        )
        self.assertTrue(all("address" not in item for item in second["recipients"]))

        persisted = self.envelope_path.read_text(encoding="utf-8")
        self.assertNotIn("Rigel@stegverse.org", persisted)
        self.assertNotIn("participant@example.com", persisted)

        notification = json.loads(self.notification_path.read_text(encoding="utf-8"))
        self.assertEqual(notification["notification_delivery_state"], "DELIVERED")
        self.assertEqual(notification["recipient_address_retention_state"], "NONE_RETAINED")
        self.assertEqual(notification["notification_retry_authority_state"], "TERMINATED")
        self.assertEqual(notification["terminal_state"], "SUBMISSION_ACCEPTED")

    def test_failed_participant_address_expires_and_is_purged(self) -> None:
        with patch.dict(os.environ, {"STEGVERSE_NOTIFICATION_MAX_ATTEMPTS": "2"}, clear=False):
            first = delivery.deliver_envelope(self.envelope_path)
            self.assertEqual(first["delivery_state"], "PARTIAL")
            second = delivery.deliver_envelope(self.envelope_path)

        self.assertEqual(second["delivery_state"], "PARTIAL_EXPIRED")
        self.assertEqual(second["retry_authority_state"], "TERMINATED")
        self.assertEqual(second["unresolved_recipient_count"], 0)
        self.assertEqual(second["retained_recipient_address_count"], 0)
        self.assertEqual(
            FakeSMTP.sent_to,
            ["Rigel@stegverse.org", "participant@example.com", "participant@example.com"],
        )
        by_role = {item["role"]: item for item in second["recipients"]}
        self.assertEqual(
            by_role["PARTICIPANT_ATTEMPT_COPY"]["address_retention_state"],
            "REDACTED_AFTER_RETRY_EXPIRY",
        )
        result_by_role = {item["role"]: item for item in second["delivery_results"]}
        self.assertEqual(result_by_role["PARTICIPANT_ATTEMPT_COPY"]["state"], "DELIVERY_EXPIRED")
        self.assertEqual(result_by_role["PARTICIPANT_ATTEMPT_COPY"]["attempt_count"], 2)
        self.assertNotIn("participant@example.com", self.envelope_path.read_text(encoding="utf-8"))

        third = delivery.deliver_envelope(self.envelope_path)
        self.assertEqual(third["delivery_state"], "PARTIAL_EXPIRED")
        self.assertEqual(len(FakeSMTP.sent_to), 3)

    def test_terminal_envelope_is_skipped_by_outbox_processor(self) -> None:
        envelope = json.loads(self.envelope_path.read_text(encoding="utf-8"))
        envelope["delivery_state"] = "DELIVERY_EXPIRED"
        self.envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
        counts = delivery.process_outbox(self.root)
        self.assertEqual(
            counts,
            {"examined": 0, "delivered": 0, "partial": 0, "failed": 0, "expired": 0},
        )
        self.assertEqual(FakeSMTP.sent_to, [])


if __name__ == "__main__":
    unittest.main()
