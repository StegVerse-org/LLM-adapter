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
    forbidden = {
        "participant_notification_email",
        "recipient_email",
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
    require("notification_outbox" in gateway or "outbox" in gateway, "restricted delivery outbox missing")
    require("participant_notification_email" not in schema.get("required", []), "email cannot be required")

    require("smtplib" in delivery, "replaceable SMTP transport missing")
    require("PARTIAL" in delivery or "partial" in delivery.lower(), "partial delivery state not represented")
    require("submission" in delivery.lower(), "delivery worker lacks submission-context handling")

    # Receipt/public artifacts must describe notification state without disclosing an address.
    require("participant_notification_email" not in gateway.split("receipt: Dict[str, Any] =", 1)[-1].split("_sign_receipt", 1)[0],
            "participant email appears in receipt construction")

    print("PASS: HIL RTG notification contract verified")


if __name__ == "__main__":
    main()
