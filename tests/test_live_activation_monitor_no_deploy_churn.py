from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ecosystem-chat-live-activation-monitor.yml"


def test_monitor_retains_each_heartbeat_as_artifact_without_repository_push() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    for required in (
        'cron: "7,22,37,52 * * * *"',
        "scripts/write_live_activation_monitor_status.py",
        "Validate monitor heartbeat",
        "actions/upload-artifact@v4",
        "reports/ecosystem-chat-live-activation-monitor.json",
        "retention-days: 30",
        "contents: read",
        "persist-credentials: false",
    ):
        assert required in source

    for prohibited in (
        "Persist monitor heartbeat",
        "git commit",
        "git push",
        "git add -f reports/ecosystem-chat-live-activation-monitor.json",
        "contents: write",
    ):
        assert prohibited not in source


def test_monitor_workflow_documents_non_authorizing_artifact_retention() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "artifact only" in source.lower()
    assert "semantic state is retained separately" in source.lower()
    assert "Authority granted: false" in source
