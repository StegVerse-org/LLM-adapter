#!/usr/bin/env python3
"""Validate canonical StegDeploy image publication receipt retention."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "stegdeploy-image.yml"
RECEIPT = ROOT / "receipts" / "stegdeploy-image-publication.json"

REQUIRED_WORKFLOW_SNIPPETS = (
    "contents: write",
    "repository_retained\": True",
    "package_visibility_asserted\": False",
    "git add receipts/stegdeploy-image-publication.json",
    "chore: retain canonical StegDeploy image publication evidence [skip ci]",
    "git pull --rebase",
    "git push",
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
    if payload["schema"] != "stegdeploy.image-publication.v2":
        return fail("unexpected receipt schema")
    if payload["repository_retained"] is not True:
        return fail("receipt does not assert repository retention")
    if payload["package_visibility_asserted"] is not False:
        return fail("receipt improperly asserts package visibility")
    if payload["manual_credentials_required"] is not False:
        return fail("publication receipt requires manual credentials")
    if payload["authority_effect"] != "IMAGE_PUBLICATION_ONLY":
        return fail("receipt authority effect exceeds image publication")
    if not str(payload["digest"]).startswith("sha256:"):
        return fail("receipt digest is not sha256-addressed")

    claimed = payload.pop("receipt_sha256")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    actual = hashlib.sha256(canonical).hexdigest()
    if claimed != actual:
        return fail("retained receipt hash mismatch")
    return 0


def main() -> int:
    if not WORKFLOW.is_file():
        return fail("missing canonical image workflow")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for snippet in REQUIRED_WORKFLOW_SNIPPETS:
        if snippet not in workflow:
            return fail(f"workflow missing retention invariant: {snippet}")

    if RECEIPT.exists():
        result = validate_receipt(RECEIPT)
        if result:
            return result
        print("STEGDEPLOY_IMAGE_RECEIPT_RETENTION_PASS: retained receipt validated")
    else:
        print("STEGDEPLOY_IMAGE_RECEIPT_RETENTION_PASS: workflow contract valid; first retained receipt pending publication run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
