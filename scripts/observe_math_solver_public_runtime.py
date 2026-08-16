#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "receipts" / "math-solver-public-runtime.latest.json"
DEFAULT_ORIGIN = "http://127.0.0.1:8000"
SITE_ORIGINS = (
    "https://stegverse.org",
    "https://www.stegverse.org",
    "https://stegverse-labs.github.io",
)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def request_json(url: str, *, body: dict | None = None, origin: str | None = None) -> tuple[int, dict, dict[str, str]]:
    data = None
    headers = {"Accept": "application/json"}
    method = "GET"
    if body is not None:
        method = "POST"
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if origin:
        headers["Origin"] = origin
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read().decode("utf-8")
        return response.status, json.loads(raw), {k.lower(): v for k, v in response.headers.items()}


def observe(origin: str) -> dict:
    base = origin.rstrip("/")
    receipt = {
        "schema_version": "MATH-SOLVER-PUBLIC-RUNTIME-OBSERVATION-v2",
        "task_id": "MATH-SOLVER-STEGGATE-RUNTIME-001",
        "origin": base,
        "origin_authority": "STEGVERSE_RUNTIME_ONLY",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "observed_at": now(),
        "state": "BLOCKED",
        "readiness": None,
        "first": None,
        "replay": None,
        "checks": {},
        "blocker": None,
        "next_executable_action": "Start or bind an eligible StegVerse portable-node/service-gateway carrier, then retry this observation against that StegVerse origin.",
        "authority_effect": False,
    }
    try:
        status, readiness, _ = request_json(base + "/api/math-solver/v1/readiness")
        receipt["readiness"] = readiness
        receipt["checks"]["readiness_http_200"] = status == 200
        receipt["checks"]["canonical_steggate_bound"] = readiness.get("canonical_steggate_bound") is True
        receipt["checks"]["readiness_state_ready"] = readiness.get("state") == "READY"

        first_status, first, first_headers = request_json(
            base + "/api/math-solver/v1/solve",
            body={"expression": "6 * 7", "request_id": "MATH-PUBLIC-OBS-A"},
            origin=SITE_ORIGINS[0],
        )
        replay_status, replay, replay_headers = request_json(
            base + "/api/math-solver/v1/solve",
            body={"expression": "6 * 7", "request_id": "MATH-PUBLIC-OBS-B"},
            origin=SITE_ORIGINS[0],
        )
        receipt["first"] = first
        receipt["replay"] = replay
        receipt["checks"].update({
            "solve_http_200": first_status == 200 and replay_status == 200,
            "result_42": first.get("result") == 42 and replay.get("result") == 42,
            "steggate_allow": first.get("disposition") == "ALLOW" and replay.get("disposition") == "ALLOW",
            "executed": first.get("execution_state") == "EXECUTED" and replay.get("execution_state") == "EXECUTED",
            "executor_invoked": first.get("executor_invoked") is True and replay.get("executor_invoked") is True,
            "decision_hash_present": bool(first.get("decision_state_hash")) and bool(replay.get("decision_state_hash")),
            "request_hash_replay_match": first.get("request_hash") == replay.get("request_hash") and bool(first.get("request_hash")),
            "result_hash_replay_match": first.get("result_hash") == replay.get("result_hash") and bool(first.get("result_hash")),
            "cors_allows_site": (
                first_headers.get("access-control-allow-origin") in SITE_ORIGINS + ("*",)
                and replay_headers.get("access-control-allow-origin") in SITE_ORIGINS + ("*",)
            ),
        })
        if all(receipt["checks"].values()):
            receipt["state"] = "COMPLETE"
            receipt["blocker"] = None
            receipt["next_executable_action"] = "Consume this verified StegVerse runtime evidence in StegVerse-Labs/Site#240 and directly verify the public Site client."
        else:
            failed = [key for key, passed in receipt["checks"].items() if not passed]
            receipt["blocker"] = {"type": "STEGVERSE_RUNTIME_CHECK_FAILED", "failed_checks": failed}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        receipt["blocker"] = {
            "type": "STEGVERSE_RUNTIME_UNAVAILABLE",
            "reason": f"{type(exc).__name__}: {exc}",
        }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--origin",
        default=os.getenv("MATH_SOLVER_RUNTIME_ORIGIN", DEFAULT_ORIGIN),
        help="StegVerse-owned node/service-gateway origin. Default is the local portable node.",
    )
    parser.add_argument("--fail-on-blocked", action="store_true")
    args = parser.parse_args()
    receipt = observe(args.origin)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    if args.fail_on_blocked and receipt["state"] != "COMPLETE":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
