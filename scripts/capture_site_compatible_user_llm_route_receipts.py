#!/usr/bin/env python3
"""Exercise bounded test routes and emit Site-compatible execution receipts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROUTES: tuple[dict[str, Any], ...] = (
    {
        "route": "demo_test_suite",
        "action": "list",
        "required_scope": "demo:read",
        "payload": {},
    },
    {
        "route": "entity_sandbox_runner",
        "action": "submit",
        "required_scope": "sandbox:submit",
        "payload": {"task": "bounded-site-import-test"},
    },
    {
        "route": "hil_response_packet",
        "action": "submit_pdf_metadata",
        "required_scope": "hil:submit",
        "payload": {
            "title": "Bounded Site Import Test",
            "sha256": "0" * 64,
            "media_type": "application/pdf",
        },
    },
)

FALSE_CLAIMS = {
    "production_execution": False,
    "publication": False,
    "continuity": False,
    "custody": False,
    "master_record_release": False,
    "site_activation": False,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        url,
        data=canonical_bytes(payload),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:  # noqa: S310 - local CI endpoint
        if response.status != 200:
            raise RuntimeError(f"unexpected HTTP status {response.status}")
        return json.loads(response.read().decode("utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    port = os.environ.get("PORT", "18080")
    base_url = os.environ.get("STEGVERSE_USER_LLM_BASE_URL", f"http://127.0.0.1:{port}/user-llm")
    source_commit = os.environ.get("SOURCE_COMMIT", os.environ.get("GITHUB_SHA", ""))
    require(
        len(source_commit) == 40 and all(c in "0123456789abcdef" for c in source_commit),
        "SOURCE_COMMIT must be a durable 40-character lowercase commit SHA",
    )

    evidence_root = Path("artifacts/receipts/user-llm-bounded-execution")
    import_root = Path("artifacts/site-imports/user-llm-bounded-execution-receipts")
    evidence_root.mkdir(parents=True, exist_ok=True)
    import_root.mkdir(parents=True, exist_ok=True)

    for case in ROUTES:
        request_payload = {
            "identity": {
                "user_id": "site-import-test-user",
                "llm_id": "site-import-test-llm",
                "provider": "repository-owned-test-transport",
                "model": "deterministic-fixture",
                "scopes": [case["required_scope"]],
            },
            "route": case["route"],
            "action": case["action"],
            "payload": case["payload"],
        }
        response = post_json(f"{base_url.rstrip('/')}/v1/user-llm/requests", request_payload)
        result = response.get("result") or {}

        require(response.get("status") == "RETURNED", f"{case['route']}: response did not return")
        require(response.get("authority_attached") is False, f"{case['route']}: authority attached")
        require(response.get("test_mode") is True, f"{case['route']}: test mode not explicit")
        require(response.get("downstream_execution_verified") is False, f"{case['route']}: downstream execution overclaim")
        require(result.get("status") == "TEST_RETURNED", f"{case['route']}: fixture result missing")
        require(result.get("route") == case["route"], f"{case['route']}: result route mismatch")
        require(result.get("authority_attached") is False, f"{case['route']}: result authority attached")

        request_hash = response.get("request_hash") or result.get("request_hash")
        result_hash = result.get("fixture_result_hash") or sha256_hex(result)
        require(isinstance(request_hash, str) and len(request_hash) == 64, f"{case['route']}: invalid request hash")
        require(isinstance(result_hash, str) and len(result_hash) == 64, f"{case['route']}: invalid result hash")

        evidence_name = f"{case['route']}-{case['action']}.json"
        evidence_path = evidence_root / evidence_name
        evidence_document = {
            "request": request_payload,
            "response": response,
            "source_commit": source_commit,
        }
        evidence_path.write_text(json.dumps(evidence_document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        evidence_hash = hashlib.sha256(evidence_path.read_bytes()).hexdigest()

        site_import = {
            "schema_version": "USER-LLM-BOUNDED-EXECUTION-RECEIPT-IMPORT-v1",
            "source_repository": "StegVerse-org/LLM-adapter",
            "source_commit": source_commit,
            "source_evidence_path": f"receipts/user-llm-bounded-execution/{evidence_name}",
            "source_evidence_sha256": evidence_hash,
            "route": case["route"],
            "action": case["action"],
            "required_scope": case["required_scope"],
            "request_hash": request_hash,
            "result_hash": result_hash,
            "status": "RETURNED",
            "transport_configured": True,
            "execution_observed": True,
            "authority_attached": False,
            "claims": FALSE_CLAIMS,
        }
        (import_root / evidence_name).write_text(
            json.dumps(site_import, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print(f"SITE_COMPATIBLE_ROUTE_RECEIPTS=PASS imports={len(ROUTES)} source_commit={source_commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
