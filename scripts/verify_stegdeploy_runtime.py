from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str, *needles: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"{path} missing required runtime contract entries: {missing}")


def reject(path: str, *needles: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    present = [needle for needle in needles if needle in text]
    if present:
        raise SystemExit(f"{path} retains prohibited runtime entries: {present}")


def main() -> int:
    require(
        "Dockerfile",
        "FROM python:3.12-slim",
        "USER stegverse",
        'VOLUME ["/var/lib/stegverse"]',
        'ENTRYPOINT ["/usr/local/bin/stegverse-entrypoint"]',
        "HEALTHCHECK",
    )
    require(
        "scripts/container-entrypoint.sh",
        "set -eu",
        "STEGVERSE_TRANSITION_DB",
        "STEGVERSE_EXTERNAL_REVIEW_DB",
        "python -m llm_adapter.custody_worker",
        "exec uvicorn llm_adapter.deployed_gateway:app",
    )
    require(
        "compose.stegdeploy.yaml",
        "stegverse/llm-adapter:local",
        "build:",
        "dockerfile: Dockerfile",
        "pull_policy: never",
        "restart: unless-stopped",
        "init: true",
        'STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS: "true"',
        "stegverse_gateway_data:/var/lib/stegverse",
        "STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT: /var/lib/stegverse",
        "STEGVERSE_COINBASE_SKAP_TVC_DECISION_RECEIPT: ${STEGVERSE_COINBASE_SKAP_TVC_DECISION_RECEIPT:-}",
        "STEGVERSE_PROVIDER_ENABLED: ${STEGVERSE_PROVIDER_ENABLED:-false}",
        "STEGVERSE_EXTERNAL_MUTATION_ENABLED: ${STEGVERSE_EXTERNAL_MUTATION_ENABLED:-false}",
        "healthcheck:",
    )
    reject("compose.stegdeploy.yaml", "ghcr.io/stegverse-org/llm-adapter:main", "pull_policy: always")
    require(
        "scripts/stegdeploy_bootstrap.py",
        "stegdeploy.deployment-receipt.v2",
        '"docker", "compose"',
        '_compose("build")',
        '"image_source": "LOCAL_BUILD"',
        '"registry_pull_required": False',
        '"credential_authority": "TV/TVC"',
        '"generated_credentials": False',
        '"manual_build_required": False',
        '"manual_credentials_required": False',
        '"render_dependency": False',
        "/health",
    )
    reject(
        "scripts/stegdeploy_bootstrap.py",
        "secrets.token_urlsafe",
        '_compose("pull")',
        '"STEGVERSE_MASTER_RECORDS_TOKEN": existing.get',
        '"STEGVERSE_PROVIDER_TOKEN": existing.get',
    )
    for workflow in (
        ROOT / ".github/workflows/publish-portable-node-image.yml",
        ROOT / ".github/workflows/stegdeploy-image.yml",
    ):
        if workflow.exists():
            raise SystemExit(f"hosted publication workflow must be retired: {workflow.relative_to(ROOT)}")
    require(
        "docs/STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md",
        "github_actions_publication_authority: NONE",
        "credential_authority: TV/TVC",
        "resident sovereign heartbeat + healer-sovereign-scheduler-worker",
        "historical_ghcr_receipt_retained: true",
    )
    print("StegDeploy sovereign local runtime contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
