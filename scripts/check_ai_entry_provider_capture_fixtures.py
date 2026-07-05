#!/usr/bin/env python3
"""Verify provider capture fixtures remain preview-only and disabled."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "fixtures" / "ai-entry-provider-capture-request.example.json"
RESPONSE = ROOT / "fixtures" / "ai-entry-provider-capture-response.example.json"
REQUEST_FALSE = (
    "perform_provider_call",
    "capture_provider_output",
    "persist_capture",
    "treat_provider_output_as_authority",
)
RESPONSE_FALSE = (
    "provider_call_performed",
    "provider_output_captured",
    "provider_authority",
    "persisted",
    "live_calls_allowed",
)


def fail(message: str) -> None:
    raise SystemExit(f"ADAPTER_PROVIDER_CAPTURE_FIXTURES_FAIL: {message}")


def main() -> int:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    response = json.loads(RESPONSE.read_text(encoding="utf-8"))
    if request.get("schema_version") != "stegverse.adapter.ai_entry.provider_capture_request.v0.1":
        fail("bad request schema version")
    if response.get("schema_version") != "stegverse.adapter.ai_entry.provider_capture_response.v0.1":
        fail("bad response schema version")
    if request.get("request_id") != response.get("request_id"):
        fail("request/response id mismatch")
    if request.get("activation_request_id") != response.get("activation_request_id"):
        fail("activation request id mismatch")
    if request.get("mode") != "preview_only":
        fail("request mode must be preview_only")
    requested = request.get("requested_capture", {})
    for key in REQUEST_FALSE:
        if requested.get(key) is not False:
            fail(f"request {key} must be false")
    if response.get("status") != "NOT_CAPTURED":
        fail("response status must be NOT_CAPTURED")
    preview = response.get("capture_preview", {})
    for key in RESPONSE_FALSE:
        if preview.get(key) is not False:
            fail(f"response {key} must be false")
    if not response.get("missing_preconditions"):
        fail("missing preconditions required")
    print("ADAPTER_PROVIDER_CAPTURE_FIXTURES_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
