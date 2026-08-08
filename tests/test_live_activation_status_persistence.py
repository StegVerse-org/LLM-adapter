from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ecosystem-chat-live-activation.yml"


def _persistence_block(source: str) -> str:
    start = source.index("      - name: Persist current activation evidence")
    end = source.index("      - name: Retain first verified activation receipt", start)
    return source[start:end]


def test_ignored_stable_status_is_force_added_without_forcing_receipt() -> None:
    block = _persistence_block(WORKFLOW.read_text(encoding="utf-8"))

    assert "git add receipts/ecosystem-chat-live-activation.latest.json" in block
    assert "git add -f reports/ecosystem-chat-live-activation-status.json" in block
    assert "git add -f receipts/ecosystem-chat-live-activation.latest.json" not in block
    assert 'echo "Current activation evidence unchanged."' in block
    assert 'git commit -m "chore: retain Ecosystem Chat live activation evidence [skip ci]"' in block


def test_status_persistence_remains_semantic_and_fail_closed() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "Write stable activation blocker status" in source
    assert "python scripts/write_live_activation_status.py" in source
    assert "Validate generated live observation" in source
    assert "reports/ecosystem-chat-live-activation-status.json" in source
