#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/provider_usage_event.json"
SCHEMA = "stegverse.provider_usage_event.v1"
FALSE_KEYS = (
    "adapter_is_execution_authority",
    "provider_response_is_admissibility",
    "model_output_is_publication_authority",
    "reasoning_provenance_is_full_chain_of_thought",
    "usage_measurement_is_value_claim",
    "provider_identity_is_actor_authority",
)


def canonical_hash(event: dict) -> str:
    material = dict(event)
    material.pop("event_sha256", None)
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate(event: dict | None = None) -> list[str]:
    failures: list[str] = []
    if event is None:
        if not FIXTURE.exists():
            return ["fixture missing"]
        event = json.loads(FIXTURE.read_text(encoding="utf-8"))

    if event.get("schema") != SCHEMA:
        failures.append("schema mismatch")
    if event.get("event_type") not in {"PROVIDER_RESPONSE", "PROVIDER_REFUSAL", "PROVIDER_ERROR"}:
        failures.append("event type invalid")

    provider = event.get("provider", {})
    for key in ("name", "model", "model_version"):
        if not isinstance(provider.get(key), str) or not provider[key]:
            failures.append(f"provider identity missing: {key}")

    request = event.get("request", {})
    response = event.get("response", {})
    for label, value in (
        ("request hash", request.get("request_sha256")),
        ("response hash", response.get("response_sha256")),
    ):
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            failures.append(f"{label} malformed")

    measurements = event.get("measurements", {})
    for key in ("input_tokens", "output_tokens", "total_tokens", "latency_ms"):
        value = measurements.get(key)
        if not isinstance(value, int) or value < 0:
            failures.append(f"measurement invalid: {key}")
    if measurements.get("total_tokens") != measurements.get("input_tokens", 0) + measurements.get("output_tokens", 0):
        failures.append("token total mismatch")

    provenance = event.get("reasoning_provenance", {})
    if provenance.get("mode") != "bounded_reference":
        failures.append("reasoning provenance mode invalid")
    if provenance.get("full_chain_of_thought_included") is not False:
        failures.append("full chain of thought boundary violated")

    boundary = event.get("authority_boundary", {})
    for key in FALSE_KEYS:
        if boundary.get(key) is not False:
            failures.append(f"authority escalation: {key}")

    return_path = event.get("return_to_origin", {})
    if not return_path.get("origin_event_id"):
        failures.append("origin event id missing")
    if return_path.get("receipt_required") is not True:
        failures.append("return receipt must be required")
    if event.get("manual_user_action_required") is not False:
        failures.append("manual action boundary invalid")

    digest = canonical_hash(event)
    if event.get("event_sha256") != digest:
        failures.append("event hash mismatch")
    return failures


def main() -> int:
    failures = validate()
    print("PROVIDER USAGE EVENT:", "FAIL" if failures else "PASS")
    for failure in failures:
        print(f"- {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
