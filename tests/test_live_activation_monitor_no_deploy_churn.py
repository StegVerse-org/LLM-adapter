from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ecosystem-chat-live-activation-monitor.yml"
SCRIPT = ROOT / "scripts/write_live_activation_monitor_status.py"
HANDOFF = ROOT / "docs/WORKFLOW_CONSOLIDATION_MIRROR_HANDOFF.md"


def test_hosted_activation_monitor_is_retired() -> None:
    assert not WORKFLOW.exists()
    assert not SCRIPT.exists()


def test_resident_stegverse_carrier_owns_continuity_after_retirement() -> None:
    source = HANDOFF.read_text(encoding="utf-8")
    assert "ecosystem-chat-live-activation-monitor.yml" in source
    assert "resident carrier owns continuity" in source
    assert "GitHub token as runtime/control-plane authority: prohibited" in source
    assert "credential_authority: TV/TVC" in source
