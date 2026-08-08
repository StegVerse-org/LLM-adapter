from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ecosystem-chat-live-activation.yml"
VALIDATE_WORKFLOW = ROOT / ".github/workflows/validate.yml"


def _persistence_block(source: str) -> str:
    start = source.index("      - name: Persist stable activation status")
    end = source.index("      - name: Retain first verified activation receipt", start)
    return source[start:end]


def test_mutable_observation_is_artifact_only_and_stable_status_is_force_added() -> None:
    block = _persistence_block(WORKFLOW.read_text(encoding="utf-8"))
    assert "git add -f reports/ecosystem-chat-live-activation-status.json" in block
    assert "git add receipts/ecosystem-chat-live-activation.latest.json" not in block
    assert "git add -f receipts/ecosystem-chat-live-activation.latest.json" not in block
    assert 'echo "Stable activation status unchanged."' in block
    assert 'git commit -m "chore: retain Ecosystem Chat live activation status [skip ci]"' in block


def test_status_persistence_remains_semantic_and_fail_closed() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "Write stable activation blocker status" in source
    assert "python scripts/write_live_activation_status.py" in source
    assert "Validate generated live observation" in source
    assert "reports/ecosystem-chat-live-activation-status.json" in source
    assert "Upload current activation evidence" in source
    assert "receipts/ecosystem-chat-live-activation.latest.json" in source


def test_validation_workflow_persists_only_stable_status_and_verified_receipt() -> None:
    source = VALIDATE_WORKFLOW.read_text(encoding="utf-8")
    start = source.index("      - name: Retain and persist current activation evidence")
    end = source.index("      - name: Test authenticated usage session endpoint", start)
    block = source[start:end]
    assert "git add -f reports/ecosystem-chat-live-activation-status.json" in block
    assert "git add receipts/ecosystem-chat-live-activation.latest.json" not in block
    assert "git add receipts/ecosystem-chat-live-activation.verified.json" in block
