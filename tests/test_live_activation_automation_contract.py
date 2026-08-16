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


def test_validate_workflow_is_validation_only_and_secret_free() -> None:
    source = (ROOT / ".github/workflows/validate.yml").read_text()
    for required in (
        "Probe deployed Ecosystem Chat vertical slice",
        "Write stable activation status from validation probe",
        "scripts/write_live_activation_status.py",
        "reports/ecosystem-chat-live-activation-status.json",
        "github.event_name != 'pull_request'",
    ):
        assert required in source
    assert "secrets." not in source


def test_portable_node_manifest_supports_stegverse_binding_and_fails_closed(tmp_path: Path) -> None:
    receipt = bootstrap(tmp_path)
    manifest = json.loads(Path(receipt["capability_manifest"]).read_text(encoding="utf-8"))

    assert manifest["version"] == "1.4.0"
    assert manifest["entrypoint"][3] == "llm_adapter.deployed_gateway:app"
    assert manifest["entrypoint"][-4:] == ["--host", "${HOST}", "--port", "${PORT}"]
    assert manifest["routes"]["math_solver_readiness"] == "/api/math-solver/v1/readiness"
    assert manifest["routes"]["math_solver_solve"] == "/api/math-solver/v1/solve"
    assert manifest["environment_defaults"]["HOST"] == "127.0.0.1"
    assert manifest["environment_defaults"]["STEGVERSE_PROVIDER_ENABLED"] == "false"
    assert manifest["environment_defaults"]["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"
    assert manifest["portability"]["authorized_host_binding_supported"] is True
    assert manifest["credential_boundary"]["credential_authority"] == "TV/TVC"
    assert manifest["credential_boundary"]["github_token_runtime_authority"] == "NONE"
    assert manifest["credential_boundary"]["provider_credentials_in_manifest"] is False
    assert receipt["manual_action_required"] is False


def test_portable_node_runtime_preserves_tvc_authorized_environment(monkeypatch, tmp_path: Path) -> None:
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


def test_live_activation_status_writer_is_stable_fail_closed_and_non_authorizing() -> None:
    source = (ROOT / "scripts/write_live_activation_status.py").read_text()
    for required in (
        "live_activation_status.v1",
        "live_activation_observation_file_missing",
        "live_activation_observation_unreadable",
        "live_activation_observation_not_object",
        "verified_live_activation_contains_blockers",
        '"manual_user_action_required": False',
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
