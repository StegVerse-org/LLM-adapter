#!/usr/bin/env python3
"""Replay a governed LLM demo session report without side effects."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[1]
RESPONSES = {"What is the capital of France?": "Informational answer: the capital of France is Paris.", "Please draft a commit message updating the README file.": "Candidate commit message: update README with governed LLM demo notes."}
def cjson(v: Any) -> str: return json.dumps(v, sort_keys=True, separators=(",", ":"))
def sha(v: Any) -> str: return hashlib.sha256(cjson(v).encode("utf-8")).hexdigest()
def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--session-report", required=True); args = p.parse_args()
    path = Path(args.session_report); path = path if path.is_absolute() else ROOT / path
    packet = json.loads(path.read_text(encoding="utf-8"))["session_packet"]
    q = packet["query"]
    expected_hash = sha({"query": q, "fixture_mode": True, "live_provider_required": False})
    ok = packet.get("request_hash") == expected_hash and packet.get("provider_response") == RESPONSES.get(q, f"Fixture response for: {q}")
    print(json.dumps({"replay_result": "PASS" if ok else "FAIL", "request_hash_matches": packet.get("request_hash") == expected_hash, "side_effects_executed": False}, indent=2))
    return 0 if ok else 1
if __name__ == "__main__": raise SystemExit(main())
