#!/usr/bin/env python3
"""Smoke test the complete governed LLM adapter boundary chain."""

from __future__ import annotations

import json
from pathlib import Path

from llm_adapter.cli import run_session_fixture


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "governed_response_fixture.json"


def main() -> int:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = run_session_fixture(fixture)

    expected = {
        "adapter_decision": "QUARANTINE",
        "commitment_status": "requires_downstream_commit_time_standing",
        "authority_decision": "FAIL_CLOSED",
        "execution_status": "not_executable",
    }

    actual = {
        "adapter_decision": result["adapter_result"]["decision"],
        "commitment_status": result["commitment_request"]["status"],
        "authority_decision": result["authority_decision"]["decision"],
        "execution_status": result["execution_handoff"]["status"],
    }

    if actual != expected:
        print(json.dumps({"status": "FAIL", "expected": expected, "actual": actual}, indent=2, sort_keys=True))
        return 1

    print(json.dumps({"status": "PASS", "actual": actual}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
