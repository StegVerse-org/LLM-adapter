from __future__ import annotations

from pathlib import Path


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


def test_live_activation_workflow_is_scheduled_and_retains_durable_semantic_state() -> None:
    source = (ROOT / ".github/workflows/ecosystem-chat-live-activation.yml").read_text()
    for required in (
        "workflow_run:",
        "schedule:",
        'cron: "17 * * * *"',
        "Preserve first verified activation receipt",
        "Write stable activation blocker status",
        "Persist semantic activation status",
        "reports/ecosystem-chat-live-activation-status.json",
        "receipts/ecosystem-chat-live-activation.verified.json",
        'if [ "$state" != "VERIFIED" ]',
        "actions/upload-artifact@v4",
        "contents: write",
    ):
        assert required in source
    assert "secrets." not in source


def test_live_activation_status_writer_is_stable_and_non_authorizing() -> None:
    source = (ROOT / "scripts/write_live_activation_status.py").read_text()
    for required in (
        "live_activation_status.v1",
        '"manual_user_action_required": False',
        '"continuation_mode": "scheduled_workflow_managed"',
        '"status_is_activation_authority": False',
        '"status_is_deployment_authority": False',
        '"status_is_custody": False',
        '"status_is_release_authority": False',
        "sorted({str(item)",
        "status_sha256",
    ):
        assert required in source
    assert "observed_at" not in source
    assert "generated_at" not in source


def test_production_blueprint_automates_durable_private_custody_and_provider_path() -> None:
    source = (ROOT / "render-production.yaml").read_text()
    for required in (
        "type: pserv",
        "name: stegverse-master-records-custody",
        "repo: https://github.com/master-records/orchestration",
        "autoDeployTrigger: checksPass",
        "MASTER_RECORDS_AUTH_TOKEN",
        "generateValue: true",
        "STEGVERSE_MASTER_RECORDS_HOSTPORT",
        "property: hostport",
        "envVarKey: MASTER_RECORDS_AUTH_TOKEN",
        "STEGVERSE_ALLOW_PRIVATE_MASTER_RECORDS_HTTP",
        "mountPath: /var/data",
        "STEGVERSE_USAGE_SESSION_DB",
        "value: /var/data/stegverse-usage-sessions.db",
        "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS",
        'value: "true"',
        "STEGVERSE_PROVIDER_ENABLED",
        "STEGVERSE_EXTERNAL_MUTATION_ENABLED",
        'value: "false"',
    ):
        assert required in source
    assert "MASTER_RECORDS_RECEIPT_KEY\n        sync: false" not in source
