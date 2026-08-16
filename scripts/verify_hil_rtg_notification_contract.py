from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "llm_adapter" / "service_gateway.py"
SITE_GATEWAY = ROOT / "llm_adapter" / "service_gateway_site.py"
DELIVERY = ROOT / "llm_adapter" / "notification_delivery.py"
NOTIFICATION_SCHEMA = ROOT / "schemas" / "hil-attempt-notification-v1.schema.json"
STATUS_SCHEMA = ROOT / "schemas" / "hil-submission-status-v1.schema.json"
READINESS_SCHEMA = ROOT / "schemas" / "hil-readiness-v1.schema.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def source(path: Path) -> str:
    require(path.exists(), f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    ast.parse(text, filename=str(path))
    return text


def load_schema(path: Path) -> dict:
    require(path.exists(), f"missing {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    gateway = source(GATEWAY)
    site_gateway = source(SITE_GATEWAY)
    delivery = source(DELIVERY)

    schema = load_schema(NOTIFICATION_SCHEMA)
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    forbidden = {
        "participant_notification_email",
        "recipient_email",
        "recipient_address",
        "notification_recipient",
        "response_pdf",
        "response_contents",
        "participant_prose",
    }
    require(not (forbidden & set(properties)), "public notification schema exposes restricted data")

    for field in (
        "participant_notification_requested",
        "participant_notification_email",
        "participant_notification_scope",
    ):
        require(field in gateway, f"gateway does not accept {field}")
        require(field in site_gateway, f"Site wrapper does not forward {field}")

    require("Rigel@stegverse.org" in gateway, "required Rigel notification destination missing")
    require("ATTEMPT_NOTIFICATION_ONLY" in gateway, "participant notification scope not enforced")
    require("notification-outbox" in gateway, "restricted delivery outbox missing")
    require("participant_notification_email" not in required, "email cannot be required")

    delivery_states = set(properties.get("notification_delivery_state", {}).get("enum", []))
    require(
        {"PENDING", "DELIVERED", "PARTIAL", "DELIVERY_FAILED", "PARTIAL_EXPIRED", "DELIVERY_EXPIRED"}
        <= delivery_states,
        "notification schema omits runtime delivery states",
    )
    terminal_states = set(properties.get("terminal_state", {}).get("enum", []))
    require("DUPLICATE_RECEIPT_RESTORED" in terminal_states, "duplicate restoration state missing")

    for field in (
        "required_recipient_role",
        "participant_copy_requested",
        "participant_address_retained_in_public_record",
        "content_included",
    ):
        require(field in required, f"public notification schema does not require {field}")

    require(
        properties.get("participant_address_retained_in_public_record", {}).get("const") is False,
        "public notification schema permits participant-address retention",
    )
    require(
        properties.get("content_included", {}).get("const") is False,
        "public notification schema permits response content",
    )

    for token in (
        "STEGVERSE_NOTIFICATION_MAX_ATTEMPTS",
        "DELIVERY_EXPIRED",
        "PARTIAL_EXPIRED",
        "REDACTED_AFTER_DELIVERY",
        "REDACTED_AFTER_RETRY_EXPIRY",
        "notification_retry_authority_state",
        "recipient_address_retention_state",
    ):
        require(token in delivery, f"delivery runtime missing {token}")

    require("smtplib" in delivery, "replaceable SMTP transport missing")
    require("address" in delivery and ".pop(" in delivery, "recipient address purge missing")
    require("notification_retry_authority_state" in site_gateway, "status projection omits retry authority")
    require(
        "receipt_id" in site_gateway and "submission_status_not_found" in site_gateway,
        "status projection lacks receipt-bound capability check",
    )

    status_schema = load_schema(STATUS_SCHEMA)
    status_properties = status_schema.get("properties", {})
    status_required = set(status_schema.get("required", []))
    status_forbidden = forbidden | {"attempt_id", "notification_path", "delivery_results", "recipients"}
    require(not (status_forbidden & set(status_properties)), "participant status schema exposes internal data")

    for field in (
        "submission_id",
        "receipt_id",
        "submission_state",
        "notification_delivery_state",
        "notification_retry_authority_state",
        "recipient_address_retention_state",
        "required_recipient_delivery_state",
        "participant_copy_requested",
        "participant_copy_delivery_state",
        "recipient_addresses_exposed",
        "notification_delivery_changes_submission_outcome",
    ):
        require(field in status_required, f"participant status schema does not require {field}")
        require(f'"{field}"' in site_gateway, f"status runtime does not project {field}")

    require(
        status_properties.get("recipient_addresses_exposed", {}).get("const") is False,
        "participant status schema permits recipient-address exposure",
    )
    require(
        status_properties.get("notification_delivery_changes_submission_outcome", {}).get("const") is False,
        "participant status schema permits delivery to mutate submission outcome",
    )
    status_delivery_states = set(status_properties.get("notification_delivery_state", {}).get("enum", []))
    require(
        delivery_states | {"UNKNOWN"} <= status_delivery_states,
        "participant status schema omits notification delivery states",
    )

    readiness_schema = load_schema(READINESS_SCHEMA)
    readiness_properties = readiness_schema.get("properties", {})
    readiness_required = set(readiness_schema.get("required", []))
    for field in (
        "readiness_schema_sha256",
        "attempt_notification_schema_sha256",
        "submission_status_schema_sha256",
        "runtime_contract_version",
        "tvc_authority_role",
        "tvc_decision_id",
        "tvc_policy_hash",
        "tvc_decision_receipt_sha256",
        "tvc_admissible",
        "tvc_binding_matched",
    ):
        require(field in readiness_required, f"readiness schema does not require {field}")
        require(f'"{field}"' in site_gateway, f"readiness runtime does not advertise {field}")

    require(
        readiness_properties.get("tvc_authority_role", {}).get("const") == "service_gateway_intake",
        "readiness schema does not bind the intake authority role",
    )
    require(
        readiness_properties.get("tvc_admissible", {}).get("const") is True,
        "readiness schema permits inadmissible TVC authority",
    )
    require(
        readiness_properties.get("tvc_binding_matched", {}).get("const") is True,
        "readiness schema permits unmatched TVC binding",
    )

    for discovery_token in (
        "attempt_notification_schema",
        "submission_status_supported",
        "submission_status_schema",
        "submission_status_authorization",
        "SUBMISSION_ID_PLUS_RECEIPT_ID",
        "notification_max_attempts",
        "terminal_notification_delivery_states",
        "completed_recipient_addresses_retained",
        "expired_recipient_addresses_retained",
        "notification_delivery_changes_submission_outcome",
        "application/schema+json",
        "_schema_response",
        "_schema_sha256",
        "_authority_evidence",
        "authority_evidence_schema",
        "authority_evidence_path",
        "canonical_json",
        "ETag",
        "nosniff",
    ):
        require(discovery_token in site_gateway, f"readiness discovery omits {discovery_token}")
    require("min(20, max(1" in site_gateway, "readiness retry advertisement is not bounded")

    receipt_block = gateway.split("receipt: Dict[str, Any] =", 1)[-1].split("_sign_receipt", 1)[0]
    require(
        "participant_notification_email" not in receipt_block,
        "participant email appears in receipt construction",
    )

    print(
        "PASS: HIL RTG notification, retry, participant-status, schema-digest, TVC-authority, and privacy contract verified"
    )


if __name__ == "__main__":
    main()
