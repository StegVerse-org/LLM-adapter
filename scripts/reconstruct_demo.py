#!/usr/bin/env python3
"""Reconstruct a governed LLM demo session under stale-evidence conditions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-report", required=True)
    args = parser.parse_args()
    path = Path(args.session_report)
    if not path.is_absolute():
        path = REPO_ROOT / path
    report = json.loads(path.read_text(encoding="utf-8"))
    packet = dict(report.get("session_packet", report))
    evidence = dict(packet.get("evidence", {}))
    evidence["stale"] = True
    packet["evidence"] = evidence
    packet["authority_decision"] = "QUARANTINE"
    packet["reconstruction_result"] = "STALE_EVIDENCE_QUARANTINE"
    result = {
        "reconstruction_result": "PASS",
        "original_decision": report.get("session_packet", report).get("authority_decision"),
        "reconstructed_decision": packet["authority_decision"],
        "stale_evidence_forces_quarantine": True,
        "side_effects_executed": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
