from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOSTED_WORKFLOW = ROOT / ".github/workflows/ecosystem-chat-live-activation.yml"
VALIDATE_WORKFLOW = ROOT / ".github/workflows/validate.yml"
STATUS_WRITER = ROOT / "scripts/write_live_activation_status.py"
HANDOFF = ROOT / "docs/WORKFLOW_CONSOLIDATION_MIRROR_HANDOFF.md"


def test_hosted_activation_persistence_workflow_is_retired() -> None:
    assert not HOSTED_WORKFLOW.exists()
    source = HANDOFF.read_text(encoding="utf-8")
    assert "ecosystem-chat-live-activation.yml" in source
    assert "resident StegVerse carrier + TV/TVC" in source


def test_status_writer_remains_semantic_fail_closed_and_non_authorizing() -> None:
    source = STATUS_WRITER.read_text(encoding="utf-8")
    for required in (
        "live_activation_status.v1",
        "live_activation_observation_file_missing",
        "live_activation_observation_unreadable",
        "live_activation_observation_not_object",
        "verified_live_activation_contains_blockers",
        '"status_is_activation_authority": False',
        '"status_is_deployment_authority": False',
        '"status_is_custody": False',
        '"status_is_release_authority": False',
        "status_sha256",
    ):
        assert required in source
    assert "observed_at" not in source
    assert "generated_at" not in source


def test_validation_workflow_persists_only_stable_status_and_verified_receipt() -> None:
    source = VALIDATE_WORKFLOW.read_text(encoding="utf-8")
    start = source.index("      - name: Retain and persist current activation evidence")
    end = source.index("      - name: Test authenticated usage session endpoint", start)
    block = source[start:end]
    assert "git add -f reports/ecosystem-chat-live-activation-status.json" in block
    assert "git add receipts/ecosystem-chat-live-activation.latest.json" not in block
    assert "git add receipts/ecosystem-chat-live-activation.verified.json" in block
