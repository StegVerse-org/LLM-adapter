from __future__ import annotations

import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict

from .service_gateway import canonical_json, utc_now


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name.lower()}_missing")
    return value


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Dict[str, Any]) -> None:
    path.write_bytes(canonical_json(value) + b"\n")


def _message(notification: Dict[str, Any], recipient: Dict[str, Any]) -> EmailMessage:
    address = str(recipient.get("address") or "").strip()
    if not address:
        raise RuntimeError("recipient_address_missing")
    message = EmailMessage()
    message["From"] = _required("STEGVERSE_NOTIFICATION_FROM")
    message["To"] = address
    message["Subject"] = f"StegVerse HIL submission attempt {notification['attempt_id']}"
    message.set_content(
        "\n".join(
            [
                "StegVerse HIL response-submission notification",
                "",
                f"Attempt: {notification['attempt_id']}",
                f"Terminal state: {notification['terminal_state']}",
                f"Last completed transition: {notification['last_completed_transition']}",
                f"Submission: {notification.get('submission_id') or 'not assigned'}",
                f"Receipt: {notification.get('receipt_id') or 'not assigned'}",
                f"Chain validation: {notification['chain_validation_state']}",
                f"Custody: {notification['custody_state']}",
                f"Reason: {notification.get('reason_code') or 'none'}",
                f"Retry/reconciliation: {notification['retry_or_reconciliation_state']}",
                "",
                "This privacy-minimized notice does not contain the response PDF or response prose.",
                "Notification delivery does not determine the submission outcome.",
            ]
        )
    )
    return message


def _result_key(result: Dict[str, Any]) -> tuple[str, str]:
    return str(result.get("role") or ""), str(result.get("recipient_id") or "")


def _recipient_key(recipient: Dict[str, Any]) -> tuple[str, str]:
    return str(recipient.get("role") or ""), str(recipient.get("recipient_id") or "")


def _aggregate_state(results: list[Dict[str, Any]], expected_count: int) -> str:
    delivered = sum(item.get("state") == "DELIVERED" for item in results)
    if expected_count > 0 and delivered == expected_count:
        return "DELIVERED"
    if delivered:
        return "PARTIAL"
    return "DELIVERY_FAILED"


def _redact_delivered_addresses(
    recipients: list[Dict[str, Any]], delivered_keys: set[tuple[str, str]]
) -> None:
    redacted_at = utc_now()
    for recipient in recipients:
        if _recipient_key(recipient) not in delivered_keys:
            continue
        recipient.pop("address", None)
        recipient["address_retention_state"] = "REDACTED_AFTER_DELIVERY"
        recipient.setdefault("address_redacted_at", redacted_at)


def deliver_envelope(envelope_path: Path) -> Dict[str, Any]:
    envelope = _load_json(envelope_path)
    notification_path = Path(envelope["notification_path"])
    notification = _load_json(notification_path)

    existing = {
        _result_key(result): result
        for result in envelope.get("delivery_results", [])
        if result.get("state") == "DELIVERED"
    }
    pending = [
        recipient
        for recipient in envelope["recipients"]
        if _recipient_key(recipient) not in existing
    ]

    attempt_results: list[Dict[str, Any]] = []
    if pending:
        host = _required("STEGVERSE_SMTP_HOST")
        port = int(os.getenv("STEGVERSE_SMTP_PORT", "587"))
        username = _required("STEGVERSE_SMTP_USERNAME")
        password = _required("STEGVERSE_SMTP_PASSWORD")
        use_starttls = os.getenv("STEGVERSE_SMTP_STARTTLS", "true").strip().lower() != "false"

        with smtplib.SMTP(host, port, timeout=30) as client:
            if use_starttls:
                client.starttls(context=ssl.create_default_context())
            client.login(username, password)
            for recipient in pending:
                base = {
                    "role": recipient["role"],
                    "recipient_id": recipient.get("recipient_id"),
                }
                try:
                    client.send_message(_message(notification, recipient))
                    attempt_results.append({**base, "state": "DELIVERED", "delivered_at": utc_now()})
                except Exception as exc:  # delivery failure is recorded, never hidden
                    attempt_results.append({
                        **base,
                        "state": "DELIVERY_FAILED",
                        "failed_at": utc_now(),
                        "reason_code": type(exc).__name__,
                    })

    merged = dict(existing)
    for result in attempt_results:
        merged[_result_key(result)] = result
    results = list(merged.values())
    delivered_keys = {
        _result_key(result)
        for result in results
        if result.get("state") == "DELIVERED"
    }
    _redact_delivered_addresses(envelope["recipients"], delivered_keys)

    delivery_state = _aggregate_state(results, len(envelope["recipients"]))
    envelope["delivery_state"] = delivery_state
    envelope["delivery_results"] = results
    envelope["last_delivery_attempt_at"] = utc_now()
    envelope["unresolved_recipient_count"] = sum(
        result.get("state") != "DELIVERED" for result in results
    ) + max(0, len(envelope["recipients"]) - len(results))
    envelope["retained_recipient_address_count"] = sum(
        bool(str(recipient.get("address") or "").strip())
        for recipient in envelope["recipients"]
    )
    envelope["completed_recipient_addresses_retained"] = False
    _write_json(envelope_path, envelope)

    notification["notification_delivery_state"] = delivery_state
    notification["recipient_address_retention_state"] = (
        "NONE_RETAINED" if envelope["retained_recipient_address_count"] == 0
        else "UNRESOLVED_ONLY"
    )
    _write_json(notification_path, notification)
    return envelope


def process_outbox(root: Path) -> Dict[str, int]:
    outbox = root / "notification-outbox"
    counts = {"examined": 0, "delivered": 0, "partial": 0, "failed": 0}
    for path in sorted(outbox.glob("*.json")):
        envelope = _load_json(path)
        if envelope.get("delivery_state") == "DELIVERED":
            continue
        counts["examined"] += 1
        result = deliver_envelope(path)
        state = result["delivery_state"]
        if state == "DELIVERED":
            counts["delivered"] += 1
        elif state == "PARTIAL":
            counts["partial"] += 1
        else:
            counts["failed"] += 1
    return counts


def main() -> None:
    root = Path(_required("STEGVERSE_HIL_STORAGE_ROOT")).expanduser().resolve()
    print(json.dumps(process_outbox(root), sort_keys=True))


if __name__ == "__main__":
    main()
