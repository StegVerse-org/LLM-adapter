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
    '"schema": "stegdeploy.image-publication.v2"',
    '"stage_outcomes": outcomes',
    '"blockers": blockers',
    '"consumer_pull_verified": outcomes["verification_pull"] == "success"',
    '"repository_retained": True',
    '"package_visibility_asserted": False',
    "Refresh publication readiness status",
    "python scripts/check_stegdeploy_image_publication_readiness.py",
    "receipts/stegdeploy-image-publication.json",
    "receipts/stegdeploy-image-verification-pull.log",
    "status/stegdeploy-image-publication-readiness.json",
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
    schema = payload["schema"]
    if schema not in {"stegdeploy.image-publication.v1", "stegdeploy.image-publication.v2"}:
        return fail("unexpected receipt schema")
    if schema == "stegdeploy.image-publication.v2":
        v2_required = {"state", "stage_outcomes", "blockers", "consumer_pull_verified", "verification_pull_output"}
        v2_missing = sorted(v2_required - payload.keys())
        if v2_missing:
            return fail(f"v2 retained receipt missing fields: {', '.join(v2_missing)}")
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

    receipt_index = workflow.find("Write publication or blocker receipt")
    readiness_index = workflow.find("Refresh publication readiness status")
    retain_index = workflow.find("Retain publication evidence on main")
    upload_index = workflow.find("Upload publication evidence")
    enforce_index = workflow.find("Enforce successful publication after retaining evidence")
    if min(receipt_index, readiness_index, retain_index, upload_index, enforce_index) < 0:
        return fail("publication evidence lifecycle step missing")
    if not (receipt_index < readiness_index < retain_index < upload_index < enforce_index):
        return fail("publication evidence lifecycle is not ordered fail-closed")

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
