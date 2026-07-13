#!/usr/bin/env python3
"""Verify the External Chat publication/mutation staging boundary.

Default mode validates the repository-local mutation health contract without
network access or mutation. Live health verification is explicit. A real
staging mutation requires live mode, every required environment value, and
STEGVERSE_STAGING_MUTATION_EXECUTE=true.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from llm_adapter.external_publication_mutation import mutation_health


def request_json(method: str, url: str, payload: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "StegVerse-External-Chat-Staging-Verify",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {"detail": raw}
        return exc.code, body
    except urllib.error.URLError as exc:
        return 0, {"detail": str(exc), "reason": "gateway_transport_error"}


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"missing required environment value: {name}")
    return value


def verify_health(health: dict) -> None:
    expected = {
        "status": "ok",
        "service": "stegverse-external-publication-mutation",
        "allowed_repository": "StegVerse-Labs/admissibility-wiki",
        "allowed_path_prefix": "docs/external-frameworks/",
        "commit_time_revalidation_required": True,
        "publication_transition_is_mutation_authority": False,
    }
    for key, value in expected.items():
        if health.get(key) != value:
            raise RuntimeError(f"health mismatch {key}={health.get(key)!r}")


def main() -> int:
    execute = os.getenv("STEGVERSE_STAGING_MUTATION_EXECUTE", "false").lower() == "true"
    live_verify = os.getenv("STEGVERSE_STAGING_VERIFY_LIVE", "false").lower() == "true"

    if execute and not live_verify:
        raise RuntimeError("staging mutation execution requires STEGVERSE_STAGING_VERIFY_LIVE=true")

    gateway = os.getenv(
        "STEGVERSE_GATEWAY_BASE_URL",
        "https://stegverse-ecosystem-chat-gateway.onrender.com",
    ).rstrip("/")

    if live_verify:
        status, health = request_json("GET", f"{gateway}/api/external-review/repository-mutation/health")
        if status != 200:
            print(f"STAGING MUTATION VERIFY: FAIL - mutation health HTTP {status}: {health}")
            return 1
    else:
        health = mutation_health()

    verify_health(health)

    if not execute:
        if health.get("mutation_enabled") is not False:
            print("STAGING MUTATION VERIFY: FAIL - non-mutating verification requires mutation disabled")
            return 1
        mode = "live" if live_verify else "repository-local"
        print(f"STAGING MUTATION VERIFY: PASS ({mode} health contract verified; mutation disabled; no write attempted)")
        return 0

    target_path = required("STEGVERSE_STAGING_TARGET_PATH")
    if not target_path.startswith("docs/external-frameworks/staging/"):
        raise RuntimeError("staging mutation target must be under docs/external-frameworks/staging/")
    payload = {
        "schema_version": "1.0.0",
        "request_type": "external_framework_repository_mutation_request",
        "publication_transition_id": required("STEGVERSE_STAGING_PUBLICATION_TRANSITION_ID"),
        "actor_ref": required("STEGVERSE_STAGING_MUTATOR_REF"),
        "repository_full_name": "StegVerse-Labs/admissibility-wiki",
        "target_path": target_path,
        "content": required("STEGVERSE_STAGING_CONTENT"),
        "expected_repository_head_sha": required("STEGVERSE_STAGING_EXPECTED_HEAD_SHA"),
        "expected_target_blob_sha": os.getenv("STEGVERSE_STAGING_EXPECTED_BLOB_SHA") or None,
        "commit_message": os.getenv("STEGVERSE_STAGING_COMMIT_MESSAGE", "Verify External Chat staging mutation"),
        "authority_ref": required("STEGVERSE_STAGING_AUTHORITY_REF"),
        "delegation_ref": required("STEGVERSE_STAGING_DELEGATION_REF"),
        "policy_ref": required("STEGVERSE_STAGING_POLICY_REF"),
        "freshness_valid_until": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        "branch": "main",
    }
    status, result = request_json(
        "POST",
        f"{gateway}/api/external-review/repository-mutations",
        payload,
        required("STEGVERSE_STAGING_MUTATOR_TOKEN"),
    )
    if status != 200:
        print(f"STAGING MUTATION VERIFY: FAIL - mutation HTTP {status}: {result}")
        return 1
    for key in ("mutation_receipt_id", "commit_sha", "new_blob_sha", "content_sha256"):
        if not result.get(key):
            print(f"STAGING MUTATION VERIFY: FAIL - response missing {key}")
            return 1
    if result.get("certification_created") is not False or result.get("standing_created") is not False:
        print("STAGING MUTATION VERIFY: FAIL - mutation receipt authority boundary mismatch")
        return 1
    print(json.dumps(result, indent=2))
    print("STAGING MUTATION VERIFY: PASS (authorized disposable-path mutation confirmed)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"STAGING MUTATION VERIFY: FAIL - {exc}")
        raise SystemExit(1)
