#!/usr/bin/env python3
"""Validate retained historical StegDeploy publication evidence after hosted retirement."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "receipts" / "stegdeploy-image-publication.json"
HANDOFF = ROOT / "docs" / "STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md"
RETIRED_WORKFLOWS = (
    ROOT / ".github/workflows/stegdeploy-image.yml",
    ROOT / ".github/workflows/publish-portable-node-image.yml",
)


def fail(message: str) -> int:
    print(f"STEGDEPLOY_IMAGE_RECEIPT_RETENTION_FAIL: {message}")
    return 1


def validate_receipt(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema",
        "repository",
        "source_commit",
        "image",
        "digest",
        "published_by_workflow",
        "publication_run_id",
        "publication_run_attempt",
        "repository_retained",
        "package_visibility_asserted",
        "manual_credentials_required",
        "authority_effect",
        "receipt_sha256",
    }
    missing = sorted(required - payload.keys())
    if missing:
        return fail(f"retained receipt missing fields: {', '.join(missing)}")
    if payload["schema"] not in {"stegdeploy.image-publication.v1", "stegdeploy.image-publication.v2"}:
        return fail("unexpected receipt schema")
    if payload["repository_retained"] is not True:
        return fail("receipt does not assert repository retention")
    if payload["package_visibility_asserted"] is not False:
        return fail("receipt improperly asserts package visibility")
    if payload["manual_credentials_required"] is not False:
        return fail("historical receipt unexpectedly requires manual credentials")
    if payload["authority_effect"] != "IMAGE_PUBLICATION_ONLY":
        return fail("historical receipt authority effect exceeds image publication")
    if not str(payload["digest"]).startswith("sha256:"):
        return fail("receipt digest is not sha256-addressed")
    claimed = payload.pop("receipt_sha256")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    if claimed != hashlib.sha256(canonical).hexdigest():
        return fail("retained receipt hash mismatch")
    return 0


def main() -> int:
    for workflow in RETIRED_WORKFLOWS:
        if workflow.exists():
            return fail(f"retired GitHub publication workflow still present: {workflow.name}")
    if not RECEIPT.is_file():
        return fail("historical publication receipt missing")
    result = validate_receipt(RECEIPT)
    if result:
        return result
    handoff = HANDOFF.read_text(encoding="utf-8")
    required = (
        "github_actions_publication_authority: NONE",
        "historical_ghcr_receipt_retained: true",
        "credential_authority: TV/TVC",
        "StegVerse-Labs/StegVerse-Healer/docs/HEALER_MIRROR_HANDOFF.md",
    )
    missing = [marker for marker in required if marker not in handoff]
    if missing:
        return fail("publication handoff missing retirement markers: " + ",".join(missing))
    print("STEGDEPLOY_IMAGE_RECEIPT_RETENTION_PASS: historical receipt retained; hosted publication authority retired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
