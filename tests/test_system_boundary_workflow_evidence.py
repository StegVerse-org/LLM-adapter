import json
from copy import deepcopy
from pathlib import Path

from llm_adapter.system_boundary_workflow_evidence import validate_workflow_evidence


ROOT = Path(__file__).resolve().parents[1]
PENDING = ROOT / "evidence/system-boundary-workflow-evidence.pending.v0.1.json"


def pending_record():
    return json.loads(PENDING.read_text(encoding="utf-8"))


def test_pending_record_is_accepted_but_not_verified():
    result = validate_workflow_evidence(pending_record())
    assert result.accepted is True
    assert result.verified is False
    assert result.result == "PENDING"


def test_missing_status_cannot_become_pass():
    record = pending_record()
    record["result"] = "PASS"
    result = validate_workflow_evidence(record)
    assert result.accepted is False
    assert result.verified is False


def test_pass_requires_exact_required_commit_and_run_identity():
    record = pending_record()
    record.update(
        {
            "observed_commit": record["required_commit"],
            "run_id": "workflow-run-001",
            "run_url": "https://github.com/StegVerse-org/LLM-adapter/actions/runs/1",
            "result": "PASS",
        }
    )
    result = validate_workflow_evidence(record)
    assert result.accepted is True
    assert result.verified is True


def test_pass_rejects_commit_drift():
    record = pending_record()
    record.update(
        {
            "observed_commit": "different-commit",
            "run_id": "workflow-run-001",
            "run_url": "https://github.com/StegVerse-org/LLM-adapter/actions/runs/1",
            "result": "PASS",
        }
    )
    result = validate_workflow_evidence(record)
    assert result.accepted is False
    assert "PASS must be bound to the required commit" in result.errors


def test_authority_escalation_fails_closed():
    record = deepcopy(pending_record())
    record["release_authorized"] = True
    result = validate_workflow_evidence(record)
    assert result.accepted is False
    assert "release_authorized must remain false" in result.errors
