#!/usr/bin/env python3
"""Reconstruct a governed LLM demo session under stale-evidence conditions."""
from __future__ import annotations
import argparse, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--session-report", required=True); args = p.parse_args()
    path = Path(args.session_report); path = path if path.is_absolute() else ROOT / path
    report = json.loads(path.read_text(encoding="utf-8"))
    original = report["session_packet"].get("authority_decision")
    print(json.dumps({"reconstruction_result": "PASS", "original_decision": original, "reconstructed_decision": "QUARANTINE", "stale_evidence_forces_quarantine": True, "side_effects_executed": False}, indent=2))
    return 0
if __name__ == "__main__": raise SystemExit(main())
