from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from llm_adapter import service_gateway_site


class HILSubmissionStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        for name in ("receipts", "notifications", "notification-outbox"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.submission_id = "HIL-SUBMISSION-0123456789ABCDEF"
        self.receipt_id = "HIL-RECEIPT-0123456789ABCDEF"
        self.attempt_id = "HIL-ATTEMPT-0123456789ABCDEFGHIJ"
        (self.root / "receipts" / f"{self.submission_id}.json").write_text(json.dumps({
            "receipt_id": self.receipt_id,
            "submission_id": self.submission_id,
            "chain_validation_state": "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED",
            "review_state": "PENDING",
            "publication_state": "NOT_PUBLISHED",
        }), encoding="utf-8")
        (self.root / "notifications" / f"{self.attempt_id}.json").write_text(json.dumps({
            "attempt_id": self.attempt_id,
            "submission_id": self.submission_id,
            "attempted_at": "2026-07-27T20:00:00Z",
            "notification_delivery_state": "PARTIAL",
            "participant_copy_requested": True,
        }), encoding="utf-8")
        (self.root / "notification-outbox" / f"{self.attempt_id}.json").write_text(json.dumps({
            "attempt_id": self.attempt_id,
            "recipients": [
                {"role": "STEGVERSE_STUDY_AUTHORITY", "address": "Rigel@stegverse.org"},
                {"role": "PARTICIPANT_ATTEMPT_COPY", "address": "private@example.com"},
            ],
            "delivery_results": [
                {"role": "STEGVERSE_STUDY_AUTHORITY", "state": "DELIVERED"},
                {"role": "PARTICIPANT_ATTEMPT_COPY", "state": "DELIVERY_FAILED"},
            ],
        }), encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_projection_exposes_states_not_addresses(self) -> None:
        with patch.object(service_gateway_site.gateway, "_runtime", return_value={"root": self.root}):
            status = service_gateway_site.site_hil_submission_status(
                self.submission_id, self.receipt_id
            )
        encoded = json.dumps(status)
        self.assertEqual(status["submission_state"], "ACCEPTED")
        self.assertEqual(status["notification_delivery_state"], "PARTIAL")
        self.assertEqual(status["required_recipient_delivery_state"], "DELIVERED")
        self.assertEqual(status["participant_copy_delivery_state"], "DELIVERY_FAILED")
        self.assertFalse(status["recipient_addresses_exposed"])
        self.assertFalse(status["notification_delivery_changes_submission_outcome"])
        self.assertNotIn("Rigel@stegverse.org", encoded)
        self.assertNotIn("private@example.com", encoded)

    def test_wrong_receipt_capability_does_not_reveal_submission(self) -> None:
        with patch.object(service_gateway_site.gateway, "_runtime", return_value={"root": self.root}):
            with self.assertRaises(HTTPException) as raised:
                service_gateway_site.site_hil_submission_status(
                    self.submission_id, "HIL-RECEIPT-WRONGCAPABILITY"
                )
        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.detail, "submission_status_not_found")

    def test_no_participant_copy_is_explicit(self) -> None:
        notification_path = self.root / "notifications" / f"{self.attempt_id}.json"
        notification = json.loads(notification_path.read_text(encoding="utf-8"))
        notification["participant_copy_requested"] = False
        notification_path.write_text(json.dumps(notification), encoding="utf-8")
        with patch.object(service_gateway_site.gateway, "_runtime", return_value={"root": self.root}):
            status = service_gateway_site.site_hil_submission_status(
                self.submission_id, self.receipt_id
            )
        self.assertEqual(status["participant_copy_delivery_state"], "NOT_REQUESTED")


if __name__ == "__main__":
    unittest.main()
