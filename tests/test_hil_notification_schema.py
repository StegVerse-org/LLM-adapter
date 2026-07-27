from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "schemas" / "hil-attempt-notification-v1.schema.json").read_text(encoding="utf-8")
)


def base_notification() -> dict:
    return {
        "schema_version": "HIL-ATTEMPT-NOTIFICATION-v1",
        "attempt_id": "HIL-ATTEMPT-0123456789ABCDEFGHIJ",
        "submission_id": "HIL-SUBMISSION-0123456789ABCDEF",
        "receipt_id": "HIL-RECEIPT-0123456789ABCDEF",
        "attempted_at": "2026-07-27T20:00:00Z",
        "terminal_state": "SUBMISSION_ACCEPTED",
        "last_completed_transition": "RECEIPT_EMITTED",
        "submitted_file_sha256": "a" * 64,
        "provenance_manifest_sha256": "b" * 64,
        "chain_validation_state": "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED",
        "custody_state": "DURABLE_COMMITTED",
        "reason_code": None,
        "retry_or_reconciliation_state": "NONE",
        "notification_delivery_state": "PENDING",
        "required_recipient_role": "STEGVERSE_STUDY_AUTHORITY",
        "participant_copy_requested": True,
        "participant_address_retained_in_public_record": False,
        "content_included": False,
    }


class HILNotificationSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = Draft202012Validator(SCHEMA)

    def assertValid(self, value: dict) -> None:
        errors = sorted(self.validator.iter_errors(value), key=lambda error: list(error.path))
        self.assertEqual([], [error.message for error in errors])

    def test_pending_notification_is_valid(self) -> None:
        self.assertValid(base_notification())

    def test_terminal_delivery_requires_address_purge_and_authority_termination(self) -> None:
        value = base_notification()
        value.update({
            "notification_delivery_state": "DELIVERY_EXPIRED",
            "recipient_address_retention_state": "NONE_RETAINED",
            "notification_retry_authority_state": "TERMINATED",
        })
        self.assertValid(value)

        value["recipient_address_retention_state"] = "UNRESOLVED_ONLY"
        errors = list(self.validator.iter_errors(value))
        self.assertTrue(errors)

    def test_public_notification_rejects_contact_or_response_content(self) -> None:
        for field, content in (
            ("participant_notification_email", "private@example.com"),
            ("recipient_address", "private@example.com"),
            ("response_contents", "private response"),
        ):
            with self.subTest(field=field):
                value = base_notification()
                value[field] = content
                errors = list(self.validator.iter_errors(value))
                self.assertTrue(errors)

    def test_duplicate_restoration_runtime_state_is_valid(self) -> None:
        value = base_notification()
        value["terminal_state"] = "DUPLICATE_RECEIPT_RESTORED"
        self.assertValid(value)


if __name__ == "__main__":
    unittest.main()
