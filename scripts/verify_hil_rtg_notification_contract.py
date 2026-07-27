from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "llm_adapter" / "service_gateway.py"
SITE_GATEWAY = ROOT / "llm_adapter" / "service_gateway_site.py"
DELIVERY = ROOT / "llm_adapter" / "notification_delivery.py"
SCHEMA = ROOT / "schemas" / "hil-attempt-notification-v1.schema.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def source(path: Path) -> str:
    require(path.exists(), f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    ast.parse(text, filename=str(path))
    return text


def main() -> None:
    gateway = source(GATEWAY)
    site_gateway = source(SITE_GATEWAY)
    delivery = source(DELIVERY)

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
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
        "REDACTED_AFTER_EXPIRY",
        "notification_retry_authority_state",
        "recipient_address_retention_state",
    ):
        require(token in delivery, f"delivery runtime missing {token}")

    require("smtplib" in delivery, "replaceable SMTP transport missing")
    require("address" in delivery and ".pop(" in delivery, "recipient address purge missing")
    require("notification_retry_authority_state" in site_gateway, "status projection omits retry authority")
    require("receipt_id" in site_gateway and "submission_status_not_found" in site_gateway,
            "status projection lacks receipt-bound capability check")

    # Receipt/public artifacts must describe notification state without disclosing an address.
    receipt_block = gateway.split("receipt: Dict[str, Any] =", 1)[-1].split("_sign_receipt", 1)[0]
    require("participant_notification_email" not in receipt_block,
            "participant email appears in receipt construction")

    print("PASS: HIL RTG notification, retry, and privacy contract verified")


if __name__ == "__main__":
    main()
