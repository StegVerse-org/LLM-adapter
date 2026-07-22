#!/usr/bin/env python3
"""Validate a hash-bound, expiring GitHub Models execution authority receipt.

The validator grants no authority. It only proves that a committed receipt matches
the exact bounded contract required by the permission-bearing execution workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "stegverse.provider_execution_authority.github_models.v1"
PROVIDER = "github-models"
PROTOCOL = "openai-chat-completions-v1"
ENDPOINT = "https://models.github.ai/inference/chat/completions"
ALLOWED_HOST = "models.github.ai"
SCOPE = "ecosystem-chat-single-governed-execution"
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")


def canonical_sha256(payload: dict[str, Any]) -> str:
    material = dict(payload)
    material.pop("authority_sha256", None)
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_missing")
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def validate(payload: Any, *, now: datetime | None = None) -> dict[str, str]:
    if not isinstance(payload, dict):
        raise ValueError("authority_receipt_not_object")

    required_exact = {
        "schema": SCHEMA,
        "state": "APPROVED",
        "provider": PROVIDER,
        "protocol": PROTOCOL,
        "endpoint": ENDPOINT,
        "allowed_host": ALLOWED_HOST,
        "scope": SCOPE,
        "provider_output_is_authority": False,
        "external_mutation_authorized": False,
        "publication_authorized": False,
        "deployment_authorized": False,
        "release_authorized": False,
        "cost_expansion_authorized": False,
        "single_execution": True,
    }
    for field, expected in required_exact.items():
        if payload.get(field) != expected:
            raise ValueError(f"authority_field_invalid:{field}")

    approved_by = payload.get("approved_by")
    if not isinstance(approved_by, str) or not approved_by.strip():
        raise ValueError("approved_by_missing")

    model = payload.get("model")
    if not isinstance(model, str) or not MODEL_PATTERN.fullmatch(model):
        raise ValueError("model_invalid")

    issued_at = parse_time(payload.get("issued_at"), "issued_at")
    expires_at = parse_time(payload.get("expires_at"), "expires_at")
    if expires_at <= issued_at:
        raise ValueError("authority_expiry_not_after_issue")
    if expires_at - issued_at > __import__("datetime").timedelta(hours=24):
        raise ValueError("authority_window_exceeds_24_hours")

    observed = now or datetime.now(timezone.utc)
    if observed < issued_at:
        raise ValueError("authority_not_yet_valid")
    if observed >= expires_at:
        raise ValueError("authority_expired")

    expected_hash = payload.get("authority_sha256")
    actual_hash = canonical_sha256(payload)
    if expected_hash != actual_hash:
        raise ValueError("authority_sha256_mismatch")

    return {
        "model": model,
        "provider": PROVIDER,
        "protocol": PROTOCOL,
        "endpoint": ENDPOINT,
        "allowed_host": ALLOWED_HOST,
        "scope": SCOPE,
        "approved_by": approved_by.strip(),
        "authority_sha256": actual_hash,
        "expires_at": expires_at.isoformat(),
    }


def write_outputs(values: dict[str, str]) -> None:
    output_path = os.getenv("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")
        handle.write("valid=true\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receipt",
        nargs="?",
        default="receipts/provider-execution-authority.github-models.v1.json",
    )
    args = parser.parse_args()
    path = Path(args.receipt)
    if not path.is_file():
        raise SystemExit("authority_receipt_missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = validate(payload)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc
    write_outputs(values)
    print(json.dumps({"valid": True, **values}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
