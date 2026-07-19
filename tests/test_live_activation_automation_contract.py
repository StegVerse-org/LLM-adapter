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
        "STEGVERSE_LIVE_ACTIVATION_ATTEMPTS",
        "STEGVERSE_LIVE_ACTIVATION_RETRY_DELAY_SECONDS",
        "transport_retry_exhausted",
        "RETRYABLE_HTTP",
        '"verification_policy"',
    ):
        assert required in source
    assert "STEGVERSE_PROVIDER_TOKEN" not in source
    assert "STEGVERSE_MASTER_RECORDS_TOKEN" not in source


def test_live_activation_workflow_is_self_starting_scheduled_and_durable() -> None:
    source = (ROOT / ".github/workflows/ecosystem-chat-live-activation.yml").read_text()
    for required in (
        "push:",
        "paths:",
        "workflow_run:",
        "schedule:",
        'cron: "*/15 * * * *"',
        "scripts/verify_live_ecosystem_chat_activation.py",
        "render-production.yaml",
        "Preserve first verified activation receipt",
        "Verify deployed request, provider, custody, and reconstruction path",
        "Validate generated live observation",
        "Write stable activation blocker status",
        "Upload current activation evidence",
        "Persist semantic activation status",
        "Retain first verified activation receipt",
        "reports/ecosystem-chat-live-activation-status.json",
        "receipts/ecosystem-chat-live-activation.latest.json",
        "receipts/ecosystem-chat-live-activation.verified.json",
        'if [ "$state" != "VERIFIED" ]',
        "actions/upload-artifact@v4",
        "contents: write",
        'STEGVERSE_LIVE_ACTIVATION_ATTEMPTS: "5"',
        "result_sha256",
        "retention-days: 30",
        "[skip ci]",
    ):
        assert required in source

    for prohibited in (
        "write_live_activation_monitor_status.py",
        "Write live activation monitor heartbeat",
        "Validate live activation monitor heartbeat",
        "Persist semantic status and monitor heartbeat",
        "ecosystem-chat-live-activation-monitor.json",
        "monitor_sha256",
    ):
        assert prohibited not in source

    assert "secrets." not in source
    assert "heartbeat" not in source.lower()


def test_live_activation_status_writer_is_stable_fail_closed_and_non_authorizing() -> None:
    source = (ROOT / "scripts/write_live_activation_status.py").read_text()
    for required in (
        "live_activation_status.v1",
        "live_activation_observation_file_missing",
        "live_activation_observation_unreadable",
        "live_activation_observation_not_object",
        "verified_live_activation_contains_blockers",
        '"manual_user_action_required": False',
        '"continuation_mode": "scheduled_workflow_managed"',
        '"status_is_activation_authority": False',
        '"status_is_deployment_authority": False',
        '"status_is_custody": False',
        '"status_is_release_authority": False',
        "sorted(set(blockers))",
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
