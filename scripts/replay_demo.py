#!/usr/bin/env python3
"""Replay a governed LLM demo session report without side effects."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


PROVIDER_RESPONSES = {
    "What is the capital of France?": "Informational answer: the capital of France is Paris.",
    "Please draft a commit message updating the README file.": "Candidate commit message: update README with governed LLM demo notes.",
}


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-report", required=True)
    args = parser.parse_args()
    path = Path(args.session_report)
    if not path.is_absolute():
        path = REPO_ROOT / path
    report = json.loads(path.read_text(encoding="utf-8"))
    packet = report.get("session_packet", report)
    query = packet["query"]
    request_envelope = {"query": query, "fixture_mode": True, "live_provider_required": False}
    expected_hash = sha256_text(canonical_json(request_envelope))
    expected_response = PROVIDER_RESPONSES.get(query, f"Fixture response for: {query}")
    ok = packet.get("request_hash") == expected_hash and packet.get("provider_response") == expected_response
    result = {
        "replay_result": "PASS" if ok else "FAIL",
        "request_hash_matches": packet.get("request_hash") == expected_hash,
        "provider_response_matches": packet.get("provider_response") == expected_response,
        "side_effects_executed": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
