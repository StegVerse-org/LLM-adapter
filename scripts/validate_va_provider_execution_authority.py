#!/usr/bin/env python3
"""Validate an explicit bounded GitHub Models authority receipt for one VA route.

The validator grants no authority. It proves only that a separately supplied
approval receipt matches the exact route, caller commit, cost, time, and false-
authority contract required by a future permission-bearing execution workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA = "stegverse.va_claim_assistant.provider_execution_authority.github_models.v1"
PROVIDER = "github-models"
PROTOCOL = "openai-chat-completions-v1"
ENDPOINT = "https://models.github.ai/inference/chat/completions"
ALLOWED_HOST = "models.github.ai"
ROUTE = "service_connection"
SCOPE = "VA_CLAIM_ASSISTANT_SERVICE_CONNECTION_SINGLE_GOVERNED_EXECUTION"
PURPOSE = "SOURCE_GROUNDED_VA_CLAIM_GUIDANCE"
CALLER = "StegVerse-org/LLM-adapter"
MAX_COST_USD = 0.10
MAX_WINDOW = timedelta(hours=24)
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")

FALSE_FIELDS = (
    "provider_output_is_authority",
    "external_mutation_authorized",
    "publication_authorized",
    "deployment_authorized",
    "release_authorized",
    "filing_authorized",
    "submission_authorized",
    "representation_authorized",
    "adjudication_authorized",
    "rating_authorized",
    "medical_opinion_authorized",
    "site_activation_authorized",
)


def canonical_hash(payload: dict[str, Any]) -> str:
    material = dict(payload)
    material.pop("authority_sha256", None)
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def validate(payload: Any, *, now: datetime | None = None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("authority_receipt_not_object")

    exact = {
        "schema": SCHEMA,
        "state": "APPROVED",
        "provider": PROVIDER,
        "protocol": PROTOCOL,
        "endpoint": ENDPOINT,
        "allowed_host": ALLOWED_HOST,
        "route": ROUTE,
        "scope": SCOPE,
        "purpose": PURPOSE,
        "caller_repository": CALLER,
        "single_execution": True,
        "maximum_provider_requests": 1,
        "master_records_configuration_required": True,
        "tvc_execution_time_admission_required": True,
    }
    for field, expected in exact.items():
        if payload.get(field) != expected:
            raise ValueError(f"authority_field_invalid:{field}")

    for field in FALSE_FIELDS:
        if payload.get(field) is not False:
            raise ValueError(f"authority_boundary_invalid:{field}")

    approved_by = payload.get("approved_by")
    if not isinstance(approved_by, str) or not approved_by.strip():
        raise ValueError("approved_by_missing")

    model = payload.get("model")
    if not isinstance(model, str) or not MODEL_PATTERN.fullmatch(model):
        raise ValueError("model_invalid")

    caller_commit = payload.get("caller_commit")
    if not isinstance(caller_commit, str) or not HEX40.fullmatch(caller_commit):
        raise ValueError("caller_commit_invalid")

    maximum_request_cost = payload.get("maximum_request_cost_usd")
    if not isinstance(maximum_request_cost, (int, float)):
        raise ValueError("maximum_request_cost_usd_missing")
    if maximum_request_cost <= 0 or float(maximum_request_cost) > MAX_COST_USD:
        raise ValueError("maximum_request_cost_usd_exceeds_ceiling")

    issued_at = parse_time(payload.get("issued_at"), "issued_at")
    expires_at = parse_time(payload.get("expires_at"), "expires_at")
    if expires_at <= issued_at:
        raise ValueError("authority_expiry_not_after_issue")
    if expires_at - issued_at > MAX_WINDOW:
        raise ValueError("authority_window_exceeds_24_hours")

    observed = now or datetime.now(timezone.utc)
    if observed < issued_at:
        raise ValueError("authority_not_yet_valid")
    if observed >= expires_at:
        raise ValueError("authority_expired")

    expected_hash = payload.get("authority_sha256")
    actual_hash = canonical_hash(payload)
    if expected_hash != actual_hash:
        raise ValueError("authority_sha256_mismatch")

    return {
        "approved_by": approved_by.strip(),
        "model": model,
        "caller_commit": caller_commit,
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "maximum_request_cost_usd": float(maximum_request_cost),
        "authority_sha256": actual_hash,
        "state": "VALID",
    }


def write_outputs(values: dict[str, Any]) -> None:
    output_path = os.getenv("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--receipt",
        default="receipts/va-claim-assistant-provider-execution-authority.github-models.v1.json",
    )
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt_path = Path(args.receipt)
    if not receipt_path.exists():
        raise SystemExit("VA_PROVIDER_AUTHORITY_MISSING")
    try:
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
        result = validate(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"VA_PROVIDER_AUTHORITY_INVALID:{exc}") from exc

    if args.output:
        Path(args.output).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    write_outputs(result)
    print(
        "VA_PROVIDER_AUTHORITY_PASS:"
        f"{result['caller_commit']}:{result['authority_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
