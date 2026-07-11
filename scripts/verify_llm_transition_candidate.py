#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "examples/llm_transition_candidate.json")
    if not path.exists():
        print(f"LLM TRANSITION CANDIDATE: FAIL - missing {path}")
        return 1
    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if data.get("record_type") != "governed_transition_relationship": errors.append("record_type")
    if data.get("lifecycle_state") != "DECLARED": errors.append("lifecycle_state")
    if data.get("origin", {}).get("origin_class") != "LLM_ADAPTER_INPUT": errors.append("origin_class")
    if data.get("governance", {}).get("admissibility_result") != "PENDING": errors.append("admissibility_result")
    if data.get("execution", {}).get("action_ref") is not None: errors.append("action_ref")
    if data.get("continuity", {}).get("final_receipt_id") is not None: errors.append("final_receipt_id")
    if data.get("continuity", {}).get("master_record_status") != "NOT_YET_SUBMITTED": errors.append("master_record_status")
    if errors:
        print("LLM TRANSITION CANDIDATE: FAIL - " + ", ".join(errors))
        return 1
    print("LLM TRANSITION CANDIDATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
