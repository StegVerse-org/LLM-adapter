#!/usr/bin/env python3
"""Check that the COSV task-vector index states only what its records support.

A terminal task (lifecycle COMPLETE) must be archive-ready, evidence-complete and
unblocked. A non-terminal task must not claim either archive readiness or complete
evidence. Activation or propagation is never claimed without complete evidence. The
index's repository-vector claim must equal whether a repository vector is actually
referenced and present. Every failure is reported; none is hidden behind the first.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = Path("data/cosv/task-vector-index.json")
TERMINAL_LIFECYCLES = {"COMPLETE"}


def check(root: Path = ROOT) -> tuple[list[str], dict]:
    errors: list[str] = []
    idx = json.loads((root / INDEX).read_text())
    if idx.get("profile") != "task.v1" or idx.get("width") != 14 or idx.get("authority_effect") != "NONE":
        errors.append("index_profile_width_or_authority_invalid")
    tasks = idx.get("tasks") or []
    terminal = 0
    for row in tasks:
        tid = row.get("task_id")
        task = json.loads((root / row["task_ref"]).read_text())
        rec = json.loads((root / row["vector_ref"]).read_text())
        if task.get("task_id") != tid:
            errors.append(f"{tid}:task_id_mismatch")
        if task.get("source_state_vector_ref") != row["vector_ref"]:
            errors.append(f"{tid}:vector_ref_mismatch")
        if (task.get("machine_readable_state") or {}).get("cosv", {}).get("vector") != row["vector"]:
            errors.append(f"{tid}:task_vector_mismatch")
        if rec.get("vector") != row["vector"]:
            errors.append(f"{tid}:record_vector_mismatch")
        if rec.get("authority_effect") != "NONE":
            errors.append(f"{tid}:record_authority_effect_not_none")
        m = rec.get("exact_metrics") or {}
        if m.get("lifecycle") in TERMINAL_LIFECYCLES:
            terminal += 1
            if m.get("archive_ready") is not True:
                errors.append(f"{tid}:terminal_task_not_archive_ready")
            if m.get("evidence_complete") is not True:
                errors.append(f"{tid}:terminal_task_evidence_incomplete")
            if m.get("blocker_count") != 0:
                errors.append(f"{tid}:terminal_task_has_blockers")
        else:
            if m.get("archive_ready") is not False:
                errors.append(f"{tid}:non_terminal_task_claims_archive_ready")
            if m.get("evidence_complete") is not False:
                errors.append(f"{tid}:non_terminal_task_claims_evidence_complete")
        for claim in ("activated", "propagated"):
            if m.get(claim) is True and m.get("evidence_complete") is not True:
                errors.append(f"{tid}:{claim}_claimed_without_complete_evidence")
    coverage = idx.get("coverage") or {}
    if coverage.get("explicit_cosv_gap") != 0:
        errors.append("explicit_cosv_gap_nonzero")
    if coverage.get("explicit_cosv_tasks_vectorized") != len(tasks):
        errors.append("explicit_cosv_tasks_vectorized_does_not_match_index")
    ref = idx.get("repository_vector_ref")
    present = bool(ref) and (root / str(ref)).is_file()
    if coverage.get("repository_vector_present_claimed") is not present:
        errors.append("repository_vector_present_claimed_does_not_match_index")
    return errors, {"tasks": len(tasks), "terminal": terminal, "repository_vector_present": present}


def main() -> int:
    errors, summary = check()
    if errors:
        for error in errors:
            print("FAIL: " + error, file=sys.stderr)
        return 1
    print("LLMA_COSV_TASK_PROJECTION_PASS tasks={tasks} terminal={terminal} "
          "repository_vector_present={present}".format(
              present=str(summary["repository_vector_present"]).lower(), **summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
