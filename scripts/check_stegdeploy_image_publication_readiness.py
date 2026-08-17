#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "receipts" / "stegdeploy-image-publication.json"
STATUS = ROOT / "status" / "stegdeploy-image-publication-readiness.json"
HANDOFF = ROOT / "docs" / "STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md"
RETIRED_WORKFLOWS = (
    ROOT / ".github/workflows/stegdeploy-image.yml",
    ROOT / ".github/workflows/publish-portable-node-image.yml",
)


def main() -> int:
    blockers: list[str] = []
    for workflow in RETIRED_WORKFLOWS:
        if workflow.exists():
            blockers.append(f"retired GitHub publication workflow still present: {workflow.name}")

    handoff = HANDOFF.read_text(encoding="utf-8") if HANDOFF.exists() else ""
    for marker in (
        "github_actions_publication_authority: NONE",
        "credential_authority: TV/TVC",
        "resident sovereign heartbeat + healer-sovereign-scheduler-worker",
        "historical_ghcr_receipt_retained: true",
    ):
        if marker not in handoff:
            blockers.append(f"publication handoff missing marker: {marker}")

    receipt = json.loads(RECEIPT.read_text(encoding="utf-8")) if RECEIPT.exists() else None
    historical_digest = receipt.get("digest") if receipt else None
    historical_receipt_valid_shape = bool(
        receipt
        and receipt.get("schema") == "stegdeploy.image-publication.v2"
        and receipt.get("state") == "PUBLISHED"
        and isinstance(historical_digest, str)
        and historical_digest.startswith("sha256:")
        and receipt.get("consumer_pull_verified") is True
    )
    if not historical_receipt_valid_shape:
        blockers.append("retained historical GHCR publication receipt is missing or invalid")

    local_contract_ready = not blockers
    status = {
        "schema": "stegdeploy.image-publication-readiness.v2",
        "repository": "StegVerse-org/LLM-adapter",
        "hosted_publication_authority": "NONE",
        "credential_authority": "TV/TVC",
        "historical_receipt": "receipts/stegdeploy-image-publication.json",
        "historical_digest": historical_digest,
        "historical_ghcr_receipt_retained": historical_receipt_valid_shape,
        "runtime_image_source": "LOCAL_BUILD",
        "registry_pull_required": False,
        "continuation_owner": "resident sovereign heartbeat + healer-sovereign-scheduler-worker",
        "state": "LOCAL_CONTINUATION_READY" if local_contract_ready else "BLOCKED",
        "blockers": blockers,
        "provider_execution_authorized": False,
        "persistent_deployment_authorized": False,
        "custody_authorized": False,
        "site_activation_authorized": False,
        "manual_user_action_required": False,
    }
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if blockers:
        print("STEGDEPLOY IMAGE PUBLICATION READINESS: BLOCKED")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1
    print("STEGDEPLOY IMAGE PUBLICATION READINESS: LOCAL_CONTINUATION_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
