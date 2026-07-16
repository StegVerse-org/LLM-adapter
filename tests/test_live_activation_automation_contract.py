from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_live_activation_verifier_preserves_required_boundaries() -> None:
    source = (ROOT / "scripts/verify_live_ecosystem_chat_activation.py").read_text()
    for required in (
        "governed_provider_enabled",
        "master_records_submission_enabled",
        "provider_usage_custody_not_recorded",
        "provider_usage_reconstructability_not_pass",
        "transition_custody_not_recorded",
        '"authority_granted": False',
        '"repository_mutation_authorized": False',
    ):
        assert required in source
    assert "STEGVERSE_PROVIDER_TOKEN" not in source
    assert "STEGVERSE_MASTER_RECORDS_TOKEN" not in source


def test_live_activation_workflow_is_scheduled_and_retains_only_verified_receipt() -> None:
    workflow_path = ROOT / ".github/workflows/ecosystem-chat-live-activation.yml"
    workflow = yaml.safe_load(workflow_path.read_text())
    trigger = workflow.get("on") or workflow.get(True)
    assert "schedule" in trigger
    assert "workflow_run" in trigger
    source = workflow_path.read_text()
    assert "Preserve first verified activation receipt" in source
    assert 'if [ "$state" != "VERIFIED" ]' in source
    assert "actions/upload-artifact@v4" in source
    assert "contents: write" in source
    assert "secrets." not in source


def test_production_blueprint_enables_durable_usage_and_provider_path() -> None:
    blueprint = yaml.safe_load((ROOT / "render-production.yaml").read_text())
    service = blueprint["services"][0]
    assert service["autoDeploy"] is True
    assert service["disk"]["mountPath"] == "/var/data"
    env = {item["key"]: item.get("value") for item in service["envVars"]}
    assert env["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"
    assert env["STEGVERSE_PROVIDER_ENABLED"] == "true"
    assert env["STEGVERSE_USAGE_SESSION_DB"].startswith("/var/data/")
    assert env["STEGVERSE_EXTERNAL_MUTATION_ENABLED"] == "false"
