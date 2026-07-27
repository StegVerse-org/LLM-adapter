from __future__ import annotations

import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict

from .service_gateway import canonical_json, utc_now

TERMINAL_DELIVERY_STATES = {"DELIVERED", "PARTIAL_EXPIRED", "DELIVERY_EXPIRED"}


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name.lower()}_missing")
    return value


def _max_attempts() -> int:
    value = int(os.getenv("STEGVERSE_NOTIFICATION_MAX_ATTEMPTS", "5"))
    if value < 1 or value > 20:
        raise RuntimeError("stegverse_notification_max_attempts_invalid")
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


def _result_key(value: Dict[str, Any]) -> tuple[str, str]:
    return str(value.get("role") or ""), str(value.get("recipient_id") or "")


def _aggregate_state(results: list[Dict[str, Any]], expected_count: int) -> str:
    delivered = sum(item.get("state") == "DELIVERED" for item in results)
    expired = sum(item.get("state") == "DELIVERY_EXPIRED" for item in results)
    if expected_count > 0 and delivered == expected_count:
        return "DELIVERED"
    if delivered and delivered + expired == expected_count:
        return "PARTIAL_EXPIRED"
    if expired == expected_count:
        return "DELIVERY_EXPIRED"
    if delivered:
        return "PARTIAL"
    return "DELIVERY_FAILED"


def _purge_address(recipient: Dict[str, Any], state: str) -> None:
    recipient.pop("address", None)
    recipient["address_retention_state"] = state
    recipient.setdefault("address_redacted_at", utc_now())


def deliver_envelope(envelope_path: Path) -> Dict[str, Any]:
    envelope = _load_json(envelope_path)
    if envelope.get("delivery_state") in TERMINAL_DELIVERY_STATES:
        return envelope

    notification_path = Path(envelope["notification_path"])
    notification = _load_json(notification_path)
    max_attempts = int(envelope.get("max_delivery_attempts") or _max_attempts())
    envelope["max_delivery_attempts"] = max_attempts

    results_by_key = {
        _result_key(result): result for result in envelope.get("delivery_results", [])
    }
    pending: list[Dict[str, Any]] = []
    for recipient in envelope["recipients"]:
        key = _result_key(recipient)
        result = results_by_key.get(key, {})
        if result.get("state") in {"DELIVERED", "DELIVERY_EXPIRED"}:
            continue
        if int(result.get("attempt_count") or 0) >= max_attempts:
            results_by_key[key] = {
                "role": recipient.get("role"),
                "recipient_id": recipient.get("recipient_id"),
                "state": "DELIVERY_EXPIRED",
                "attempt_count": int(result.get("attempt_count") or 0),
                "expired_at": utc_now(),
                "reason_code": "MAX_DELIVERY_ATTEMPTS_REACHED",
            }
            _purge_address(recipient, "REDACTED_AFTER_RETRY_EXPIRY")
            continue
        pending.append(recipient)

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
                key = _result_key(recipient)
                previous = results_by_key.get(key, {})
                attempt_count = int(previous.get("attempt_count") or 0) + 1
                base = {
                    "role": recipient.get("role"),
                    "recipient_id": recipient.get("recipient_id"),
                    "attempt_count": attempt_count,
                }
                try:
                    client.send_message(_message(notification, recipient))
                    results_by_key[key] = {
                        **base,
                        "state": "DELIVERED",
                        "delivered_at": utc_now(),
                    }
                    _purge_address(recipient, "REDACTED_AFTER_DELIVERY")
                except Exception as exc:
                    if attempt_count >= max_attempts:
                        results_by_key[key] = {
                            **base,
                            "state": "DELIVERY_EXPIRED",
                            "expired_at": utc_now(),
                            "reason_code": "MAX_DELIVERY_ATTEMPTS_REACHED",
                            "last_failure_class": type(exc).__name__,
                        }
                        _purge_address(recipient, "REDACTED_AFTER_RETRY_EXPIRY")
                    else:
                        results_by_key[key] = {
                            **base,
                            "state": "DELIVERY_FAILED",
                            "failed_at": utc_now(),
                            "reason_code": type(exc).__name__,
                        }

    results = list(results_by_key.values())
    delivery_state = _aggregate_state(results, len(envelope["recipients"]))
    envelope["delivery_state"] = delivery_state
    envelope["delivery_results"] = results
    envelope["last_delivery_attempt_at"] = utc_now()
    envelope["unresolved_recipient_count"] = sum(
        result.get("state") not in {"DELIVERED", "DELIVERY_EXPIRED"}
        for result in results
    ) + max(0, len(envelope["recipients"]) - len(results))
    envelope["retained_recipient_address_count"] = sum(
        bool(str(recipient.get("address") or "").strip())
        for recipient in envelope["recipients"]
    )
    envelope["completed_recipient_addresses_retained"] = False
    envelope["retry_authority_state"] = (
        "TERMINATED" if delivery_state in TERMINAL_DELIVERY_STATES else "ACTIVE"
    )
    _write_json(envelope_path, envelope)

    notification["notification_delivery_state"] = delivery_state
    notification["recipient_address_retention_state"] = (
        "NONE_RETAINED" if envelope["retained_recipient_address_count"] == 0
        else "UNRESOLVED_ONLY"
    )
    notification["notification_retry_authority_state"] = envelope["retry_authority_state"]
    _write_json(notification_path, notification)
    return envelope


def process_outbox(root: Path) -> Dict[str, int]:
    outbox = root / "notification-outbox"
    counts = {
        "examined": 0,
        "delivered": 0,
        "partial": 0,
        "failed": 0,
        "expired": 0,
    }
    for path in sorted(outbox.glob("*.json")):
        envelope = _load_json(path)
        if envelope.get("delivery_state") in TERMINAL_DELIVERY_STATES:
            continue
        counts["examined"] += 1
        state = deliver_envelope(path)["delivery_state"]
        if state == "DELIVERED":
            counts["delivered"] += 1
        elif state == "PARTIAL":
            counts["partial"] += 1
        elif state in {"PARTIAL_EXPIRED", "DELIVERY_EXPIRED"}:
            counts["expired"] += 1
        else:
            counts["failed"] += 1
    return counts


def main() -> None:
    root = Path(_required("STEGVERSE_HIL_STORAGE_ROOT")).expanduser().resolve()
    print(json.dumps(process_outbox(root), sort_keys=True))


if __name__ == "__main__":
    main()
