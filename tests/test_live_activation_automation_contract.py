from __future__ import annotations

import json
from pathlib import Path

from llm_adapter.node_bootstrap import bootstrap
from llm_adapter.node_service import _runtime_environment


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
        "scripts/verify_authorized_provider_activation.py",
        "tests/test_authorized_provider_activation_verifier.py",
        "render-production.yaml",
        "Preserve first verified activation receipt",
        "Evaluate authorized provider configuration",
        "Start authorized provider and custody runtime",
        "Execute authorized provider, usage, custody, and reconstruction path",
        "Upload authorized provider activation evidence",
        "Persist authorized provider activation evidence",
        "Verify deployed request, provider, custody, and reconstruction path",
        "Validate generated live observation",
        "Write stable activation blocker status",
        "Upload current activation evidence",
        "Persist stable activation status",
        "Retain first verified activation receipt",
        "reports/ecosystem-chat-live-activation-status.json",
        "receipts/ecosystem-chat-live-activation.latest.json",
        "receipts/ecosystem-chat-live-activation.verified.json",
        "receipts/ecosystem-chat-authorized-provider-activation.latest.json",
        "git add -f reports/ecosystem-chat-live-activation-status.json",
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
        "git add receipts/ecosystem-chat-live-activation.latest.json",
        "write_live_activation_monitor_status.py",
        "Write live activation monitor heartbeat",
        "Validate live activation monitor heartbeat",
        "Persist semantic status and monitor heartbeat",
        "ecosystem-chat-live-activation-monitor.json",
        "monitor_sha256",
        "echo ${{ secrets.",
        "print(os.getenv(\"PROVIDER_TOKEN\"",
        "print(os.getenv(\"MASTER_RECORDS_TOKEN\"",
    ):
        assert prohibited not in source

    secret_references = {
        token.split(" }}")[0] + " }}"
        for token in source.split("${{ secrets.")[1:]
    }
    assert secret_references == {
        "STEGVERSE_PROVIDER_TOKEN }}",
        "STEGVERSE_MASTER_RECORDS_TOKEN }}",
    }
    executable_source = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    )
    assert "heartbeat" not in executable_source.lower()


def test_validate_workflow_retains_live_probe_without_secondary_workflow_dependency() -> None:
    source = (ROOT / ".github/workflows/validate.yml").read_text()
    for required in (
        "Probe deployed Ecosystem Chat vertical slice",
        "Write stable activation status from validation probe",
        "Retain and persist current activation evidence",
        "scripts/write_live_activation_status.py",
        "receipts/ecosystem-chat-live-activation.latest.json",
        "reports/ecosystem-chat-live-activation-status.json",
        "receipts/ecosystem-chat-live-activation.verified.json",
        "git add -f reports/ecosystem-chat-live-activation-status.json",
        "git add -f reports/ecosystem-chat-destination-activation-state.json",
        "github.ref == 'refs/heads/main'",
        "github.event_name != 'pull_request'",
        "[skip ci]",
    ):
        assert required in source
    assert "git add receipts/ecosystem-chat-live-activation.latest.json" not in source
    assert "secrets." not in source


def test_portable_node_manifest_supports_authorized_binding_and_fails_closed(tmp_path: Path) -> None:
    receipt = bootstrap(tmp_path)
    manifest = json.loads(Path(receipt["capability_manifest"]).read_text(encoding="utf-8"))

    assert manifest["version"] == "1.3.0"
    assert manifest["entrypoint"][-4:] == ["--host", "${HOST}", "--port", "${PORT}"]
    assert manifest["environment_defaults"]["HOST"] == "127.0.0.1"
    assert manifest["environment_defaults"]["STEGVERSE_PROVIDER_ENABLED"] == "false"
    assert manifest["environment_defaults"]["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"
    assert manifest["portability"]["authorized_host_binding_supported"] is True
    assert receipt["manual_action_required"] is False


def test_portable_node_runtime_preserves_authorized_environment(monkeypatch, tmp_path: Path) -> None:
    receipt = bootstrap(tmp_path)
    manifest = json.loads(Path(receipt["capability_manifest"]).read_text(encoding="utf-8"))

    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9010")
    monkeypatch.setenv("STEGVERSE_PROVIDER_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_PROVIDER_ENDPOINT", "https://provider.example/v1/chat")
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_ENDPOINT", "https://records.example/v1")

    env = _runtime_environment(tmp_path, manifest)

    assert env["HOST"] == "0.0.0.0"
    assert env["PORT"] == "9010"
    assert env["STEGVERSE_PROVIDER_ENABLED"] == "true"
    assert env["STEGVERSE_PROVIDER_ENDPOINT"] == "https://provider.example/v1/chat"
    assert env["STEGVERSE_MASTER_RECORDS_ENDPOINT"] == "https://records.example/v1"
    assert env["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"
    assert env["STEGVERSE_NODE_ROOT"] == str(tmp_path)


def test_portable_node_image_is_repository_owned_multi_arch_and_fail_closed() -> None:
    dockerfile = (ROOT / "Dockerfile.portable-node").read_text()
    workflow = (ROOT / ".github/workflows/publish-portable-node-image.yml").read_text()

    for required in (
        "FROM python:3.12-slim",
        "STEGVERSE_BIND_HOST=0.0.0.0",
        "STEGVERSE_NODE_ROOT=/var/lib/stegverse/portable-node",
        "USER stegverse",
        'VOLUME ["/var/lib/stegverse/portable-node"]',
        'ENTRYPOINT ["python", "-m", "llm_adapter.node_service", "daemon"]',
        "HEALTHCHECK",
    ):
        assert required in dockerfile

    for prohibited in (
        "STEGVERSE_PROVIDER_TOKEN=",
        "STEGVERSE_MASTER_RECORDS_TOKEN=",
        "STEGVERSE_PROVIDER_ENABLED=true",
    ):
        assert prohibited not in dockerfile

    for required in (
        "packages: write",
        "ghcr.io/${{ github.repository_owner }}/stegverse-ecosystem-chat-node",
        "Dockerfile.portable-node",
        "linux/amd64,linux/arm64",
        "provenance: mode=max",
        "sbom: true",
        "docker/build-push-action@v6",
    ):
        assert required in workflow

    assert "secrets." not in workflow


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
