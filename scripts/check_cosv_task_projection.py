#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
idx=json.loads((ROOT/"data/cosv/task-vector-index.json").read_text())
assert idx["profile"]=="task.v1" and idx["width"]==14 and idx["authority_effect"]=="NONE"
for row in idx["tasks"]:
    task=json.loads((ROOT/row["task_ref"]).read_text())
    rec=json.loads((ROOT/row["vector_ref"]).read_text())
    assert task["task_id"]==row["task_id"]
    assert task["source_state_vector_ref"]==row["vector_ref"]
    assert task["machine_readable_state"]["cosv"]["vector"]==row["vector"]
    assert rec["vector"]==row["vector"]
    m=rec["exact_metrics"]
    assert m["lifecycle"]=="COMPLETE" and m["archive_ready"] is True and m["blocker_count"]==0
    assert m["evidence_complete"] is True and m["activated"] is False and m["propagated"] is False
    assert rec["authority_effect"]=="NONE"
assert idx["coverage"]["explicit_cosv_gap"]==0
assert idx["coverage"]["repository_vector_present_claimed"] is False
print("LLMA_COSV_TASK_PROJECTION_PASS tasks=1 repository_vector_present=false")
