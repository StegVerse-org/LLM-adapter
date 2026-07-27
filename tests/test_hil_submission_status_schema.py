from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "schemas" / "hil-submission-status-v1.schema.json").read_text(encoding="utf-8")
)
VALIDATOR = Draft202012Validator(SCHEMA)


class HILSubmissionStatusSchemaTests(unittest.TestCase):
    def base_status(self) -> dict:
        return {
            "schema_version": "HIL-SUBMISSION-STATUS-v1",
            "submission_id": "HIL-SUBMISSION-0123456789ABCDEF",
            "receipt_id": "HIL-RECEIPT-0123456789ABCDEF",
            "submission_state": "ACCEPTED",
            "chain_validation_state": "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED",
            "review_state": "PENDING",
            "publication_state": "NOT_PUBLISHED",
            "notification_delivery_state": "PARTIAL",
            "notification_retry_authority_state": "ACTIVE",
            "recipient_address_retention_state": "UNRESOLVED_ONLY",
            "required_recipient_delivery_state": "DELIVERED",
            "participant_copy_requested": True,
            "participant_copy_delivery_state": "DELIVERY_FAILED",
            "recipient_addresses_exposed": False,
            "notification_delivery_changes_submission_outcome": False,
        }

    def assert_valid(self, value: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(value), key=lambda error: list(error.path))
        self.assertEqual([], errors, "\n".join(error.message for error in errors))

    def assert_invalid(self, value: dict) -> None:
        self.assertTrue(list(VALIDATOR.iter_errors(value)))

    def test_partial_status_is_valid(self) -> None:
        self.assert_valid(self.base_status())

    def test_terminal_expiry_requires_purge_and_authority_termination(self) -> None:
        status = self.base_status()
        status.update({
            "notification_delivery_state": "PARTIAL_EXPIRED",
            "notification_retry_authority_state": "TERMINATED",
            "recipient_address_retention_state": "NONE_RETAINED",
            "participant_copy_delivery_state": "DELIVERY_EXPIRED",
        })
        self.assert_valid(status)

        retained = copy.deepcopy(status)
        retained["recipient_address_retention_state"] = "UNRESOLVED_ONLY"
        self.assert_invalid(retained)

    def test_no_copy_requires_not_requested_projection(self) -> None:
        status = self.base_status()
        status.update({
            "participant_copy_requested": False,
            "participant_copy_delivery_state": "NOT_REQUESTED",
        })
        self.assert_valid(status)

        incorrect = copy.deepcopy(status)
        incorrect["participant_copy_delivery_state"] = "PENDING"
        self.assert_invalid(incorrect)

    def test_address_or_content_fields_are_rejected(self) -> None:
        for field, value in (
            ("participant_notification_email", "private@example.com"),
            ("recipient_address", "Rigel@stegverse.org"),
            ("response_contents", "private response"),
            ("attempt_id", "HIL-ATTEMPT-PRIVATE"),
        ):
            status = self.base_status()
            status[field] = value
            self.assert_invalid(status)

    def test_delivery_cannot_change_submission_outcome(self) -> None:
        status = self.base_status()
        status["notification_delivery_changes_submission_outcome"] = True
        self.assert_invalid(status)


if __name__ == "__main__":
    unittest.main()
