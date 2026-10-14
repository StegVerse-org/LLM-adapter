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
    for retired in (
        "Dockerfile",
        "Dockerfile.portable-node",
        "Dockerfile.service-gateway",
        "compose.yaml",
        "compose.stegdeploy.yaml",
        "compose.stegdeploy.tls.yaml",
        "scripts/stegdeploy_bootstrap.py",
        "scripts/container-entrypoint.sh",
    ):
        if (ROOT / retired).exists():
            raise SystemExit(f"container runtime path must stay retired: {retired}")
    require(
        "llm_adapter/combined_gateway.py",
        "apply_sovereign_hil_receiver_profile",
        "hil_intake_router",
        'app.include_router(hil_intake_router)',
    )
    require(
        "llm_adapter/hil_sovereign_receiver_profile.py",
        'env["STEGVERSE_HIL_INTAKE_ENABLED"] = "true"',
        'env["STEGVERSE_HIL_DATA_DIR"] = str(hil_root)',
        'env["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] = "true"',
        '"state": "ACTIVE_SOVEREIGN_RECEIVER"',
        '"credential_authority": "TV/TVC"',
        '"third_party_runtime_required": False',
    )
    require(
        "scripts/stegdeploy_native_gateway.py",
        "HOST_NATIVE_PYTHON_UVICORN",
        "STEGVERSE_EVALUATOR_INTR_ENABLED",
        "http://127.0.0.1:8765/intr/evaluator",
        "LOCAL_NATIVE_GATEWAY_STARTED",
        '"destination_liveness_is_transition_predicate": False',
        '"docker_required": False',
        '"third_party_runtime_required": False',
        '"production_public_route_observed": False',
        '"public_certificate_hostname_verified": False',
        '"credential_authority": "TV/TVC"',
        '"github_token_runtime_authority": "NONE"',
        '"org_federation_rendezvous_enabled": True',
        '"org_federation_gateway_execution_authority": "NONE"',
        "custody_worker.main()",
        "gateway_forward_queue.main()",
        "access_log=False",
        '"STEGVERSE_TRANSITION_DB"',
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
