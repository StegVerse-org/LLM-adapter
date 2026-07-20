#!/usr/bin/env python3
"""Verify the deployed Ecosystem Chat, provider usage, and custody path.

The verifier requires no browser credential and never mutates a repository. It writes
one machine-readable result suitable for workflow retention. A non-ready deployment
is reported as PENDING rather than hidden behind a transport exception. Transient
network and cold-start failures are retried within a bounded window.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib import error, request

BASE_URL = os.getenv(
    "STEGVERSE_GATEWAY_BASE_URL",
    "https://stegverse-ecosystem-chat-gateway.onrender.com",
).rstrip("/")
OUTPUT = Path(os.getenv("STEGVERSE_LIVE_ACTIVATION_OUTPUT", "receipts/ecosystem-chat-live-activation.latest.json"))
TIMEOUT = float(os.getenv("STEGVERSE_LIVE_ACTIVATION_TIMEOUT_SECONDS", "35"))
ATTEMPTS = max(1, int(os.getenv("STEGVERSE_LIVE_ACTIVATION_ATTEMPTS", "5")))
RETRY_DELAY = max(0.0, float(os.getenv("STEGVERSE_LIVE_ACTIVATION_RETRY_DELAY_SECONDS", "8")))
RETRYABLE_HTTP = {408, 425, 429, 500, 502, 503, 504}
RETAINED_RESPONSE_HEADERS = {
    "content-type",
    "date",
    "server",
    "via",
    "x-render-origin-server",
    "x-render-routing",
    "x-request-id",
}


def canonical_sha(payload: dict) -> str:
    material = dict(payload)
    material.pop("result_sha256", None)
    return sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def response_metadata(response: object) -> dict:
    raw_headers = getattr(response, "headers", None)
    headers: dict[str, str] = {}
    if raw_headers is not None:
        for key, value in raw_headers.items():
            normalized = str(key).lower()
            if normalized in RETAINED_RESPONSE_HEADERS:
                headers[normalized] = str(value)[:500]
    final_url = None
    geturl = getattr(response, "geturl", None)
    if callable(geturl):
        final_url = str(geturl())[:1000]
    return {"final_url": final_url, "headers": headers}


def fetch_json(
    url: str,
    *,
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict, int]:
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    last_error: Exception | None = None
    for attempt in range(1, ATTEMPTS + 1):
        outbound = request.Request(
            url,
            data=body,
            method="GET" if payload is None else "POST",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "StegVerse-Ecosystem-Chat-Live-Activation/2.0",
                **(headers or {}),
            },
        )
        try:
            with request.urlopen(outbound, timeout=TIMEOUT) as response:
                raw = response.read()
                status = int(getattr(response, "status", 200))
                metadata = response_metadata(response)
            parsed = json.loads(raw.decode("utf-8"))
            if not isinstance(parsed, dict):
                raise RuntimeError("live_endpoint_response_not_object")
            parsed.setdefault("_http_response", metadata)
            return status, parsed, attempt
        except error.HTTPError as exc:
            raw = exc.read()
            status = exc.code
            metadata = response_metadata(exc)
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except Exception:
                parsed = {"error": f"http_{status}", "body": raw.decode("utf-8", errors="replace")[:500]}
            if not isinstance(parsed, dict):
                parsed = {"error": "live_endpoint_response_not_object"}
            parsed.setdefault("_http_response", metadata)
            if status not in RETRYABLE_HTTP or attempt == ATTEMPTS:
                return status, parsed, attempt
            last_error = exc
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            last_error = exc
            if attempt == ATTEMPTS:
                raise RuntimeError(f"transport_retry_exhausted:{type(exc).__name__}") from exc
        if RETRY_DELAY:
            time.sleep(RETRY_DELAY)
    raise RuntimeError(f"transport_retry_exhausted:{type(last_error).__name__ if last_error else 'Unknown'}")


def result(state: str, blockers: list[str], evidence: dict) -> dict:
    payload = {
        "schema": "stegverse.ecosystem_chat.live_activation.v1",
        "state": state,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "gateway_base_url": BASE_URL,
        "verification_policy": {
            "attempts_per_request": ATTEMPTS,
            "retry_delay_seconds": RETRY_DELAY,
            "timeout_seconds": TIMEOUT,
        },
        "blockers": blockers,
        "evidence": evidence,
        "authority_granted": False,
        "publication_authorized": False,
        "repository_mutation_authorized": False,
    }
    payload["result_sha256"] = canonical_sha(payload)
    return payload


def main() -> int:
    blockers: list[str] = []
    evidence: dict = {}
    try:
        health_status, health, health_attempts = fetch_json(f"{BASE_URL}/health")
        evidence["health"] = health
        evidence["request_attempts"] = {"health": health_attempts}
        if health_status != 200 or health.get("status") != "ok":
            blockers.append("gateway_health_not_ok")
        if health.get("storage_durable_across_restarts") is not True:
            blockers.append("gateway_storage_not_durable")
        if health.get("governed_provider_enabled") is not True:
            blockers.append("governed_provider_not_enabled")
        if health.get("master_records_submission_enabled") is not True:
            blockers.append("master_records_transition_submission_not_enabled")

        nonce = uuid.uuid4().hex
        session_id = f"ecosystem-live-session-{nonce}"
        transition_id = f"ecosystem-live-transition-{nonce}"
        run_id = f"ecosystem-live-run-{nonce}"
        chat_request = {
            "message": "Return a concise governed confirmation that the Ecosystem Chat live activation path is operating.",
            "session_id": session_id,
            "requested_route": "Site",
            "transition_intent": "verify_live_activation",
            "transition_destination": "ecosystem-chat.html",
            "goal": "verify governed live request response provider usage and custody",
            "execution_model": "allowlisted_task_request_only",
            "raw_shell_allowed": False,
            "authority_required": True,
            "rate_limit_required": True,
            "receipt_required_for_execution": True,
            "interaction_profile": {},
            "interaction_bands": ["activation_verification"],
            "math_solver_supported": True,
            "transition_identity": {
                "transition_id": transition_id,
                "run_id": run_id,
                "event_id": f"ecosystem-live-event-{nonce}",
                "origin_manifest_id": f"ecosystem-live-origin-{nonce}",
                "parent_transition_id": None,
                "previous_receipt_id": None,
            },
        }
        chat_status, chat, chat_attempts = fetch_json(f"{BASE_URL}/api/ecosystem-chat", payload=chat_request)
        evidence["chat"] = chat
        evidence["request_attempts"]["chat"] = chat_attempts
        evidence["requested_identity"] = {
            "session_id": session_id,
            "transition_id": transition_id,
            "run_id": run_id,
        }
        if chat_status != 200:
            blockers.append(f"chat_http_status_{chat_status}")
        if chat.get("transition_id") != transition_id or chat.get("run_id") != run_id:
            blockers.append("chat_identity_mismatch")
        provider = chat.get("provider") or {}
        if provider.get("used") is not True:
            blockers.append("live_provider_not_used")
        local_usage = chat.get("provider_usage_submission") or {}
        if not local_usage or local_usage.get("custody_recorded") is not False:
            blockers.append("local_usage_submission_invalid")
        custody = chat.get("master_records_usage_submission") or {}
        if custody.get("custody_recorded") is not True:
            blockers.append("provider_usage_custody_not_recorded")
        if custody.get("reconstructability") != "PASS":
            blockers.append("provider_usage_reconstructability_not_pass")
        if custody.get("authority_granted") is not False:
            blockers.append("provider_usage_authority_escalation")
        authority = chat.get("authority") or {}
        if authority.get("provider_usage_grants_authority") is not False:
            blockers.append("chat_authority_boundary_invalid")

        transition_status, transition, transition_attempts = fetch_json(f"{BASE_URL}/api/transitions/{transition_id}")
        evidence["transition"] = transition
        evidence["request_attempts"]["transition"] = transition_attempts
        if transition_status != 200:
            blockers.append(f"transition_http_status_{transition_status}")
        if transition.get("transition_id") != transition_id or transition.get("run_id") != run_id:
            blockers.append("transition_identity_mismatch")
        if transition.get("master_record_status") != "RECORDED":
            blockers.append("transition_custody_not_recorded")
        if transition.get("reconstruction_status") != "PASS":
            blockers.append("transition_reconstructability_not_pass")

        state = "VERIFIED" if not blockers else "PENDING"
        payload = result(state, sorted(set(blockers)), evidence)
    except Exception as exc:
        payload = result(
            "PENDING",
            [f"verifier_exception:{type(exc).__name__}"],
            {"exception": str(exc)[:500]},
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": payload["state"], "blockers": payload["blockers"], "output": str(OUTPUT)}))
    return 0 if payload["state"] == "VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
