from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str, *needles: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"{path} missing required runtime contract entries: {missing}")


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
        "exec uvicorn llm_adapter.combined_gateway:app",
    )
    require(
        "compose.stegdeploy.yaml",
        "restart: unless-stopped",
        "init: true",
        'STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS: "true"',
        "stegverse_gateway_data:/var/lib/stegverse",
        "STEGVERSE_PROVIDER_ENABLED: ${STEGVERSE_PROVIDER_ENABLED:-false}",
        "STEGVERSE_EXTERNAL_MUTATION_ENABLED: ${STEGVERSE_EXTERNAL_MUTATION_ENABLED:-false}",
        "healthcheck:",
    )
    require(
        "scripts/stegdeploy_bootstrap.py",
        "deployment-receipt.json",
        "hashlib.sha256",
        '_run("docker", "compose"',
        "/health",
        '"render_dependency": False',
        '"authority_effect": "RUNTIME_DEPLOYMENT_ONLY"',
    )
    print("StegDeploy runtime contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
