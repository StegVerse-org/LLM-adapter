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


def _message(notification: Dict[str, Any], recipient: Dict[str, str]) -> EmailMessage:
    message = EmailMessage()
    message["From"] = _required("STEGVERSE_NOTIFICATION_FROM")
    message["To"] = recipient["address"]
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


def deliver_envelope(envelope_path: Path) -> Dict[str, Any]:
    envelope = _load_json(envelope_path)
    notification_path = Path(envelope["notification_path"])
    notification = _load_json(notification_path)

    host = _required("STEGVERSE_SMTP_HOST")
    port = int(os.getenv("STEGVERSE_SMTP_PORT", "587"))
    username = _required("STEGVERSE_SMTP_USERNAME")
    password = _required("STEGVERSE_SMTP_PASSWORD")
    use_starttls = os.getenv("STEGVERSE_SMTP_STARTTLS", "true").strip().lower() != "false"

    results = []
    with smtplib.SMTP(host, port, timeout=30) as client:
        if use_starttls:
            client.starttls(context=ssl.create_default_context())
        client.login(username, password)
        for recipient in envelope["recipients"]:
            try:
                client.send_message(_message(notification, recipient))
                results.append({"role": recipient["role"], "state": "DELIVERED", "delivered_at": utc_now()})
            except Exception as exc:  # delivery failure is recorded, never hidden
                results.append({
                    "role": recipient["role"],
                    "state": "DELIVERY_FAILED",
                    "failed_at": utc_now(),
                    "reason_code": type(exc).__name__,
                })

    delivered = sum(item["state"] == "DELIVERED" for item in results)
    if delivered == len(results):
        delivery_state = "DELIVERED"
    elif delivered:
        delivery_state = "PARTIAL"
    else:
        delivery_state = "DELIVERY_FAILED"

    envelope["delivery_state"] = delivery_state
    envelope["delivery_results"] = results
    envelope["last_delivery_attempt_at"] = utc_now()
    _write_json(envelope_path, envelope)

    notification["notification_delivery_state"] = delivery_state
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
