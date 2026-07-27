#!/usr/bin/env python3
"""Verify that a HIL full-cycle evidence bundle is pure, bounded, and hash-consistent."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

RECEIPT_NAME = "hil-automated-full-cycle-receipt-v1.json"
ALLOWED_NAMES = {
    RECEIPT_NAME,
    "gateway-first.log",
    "gateway-restart.log",
}
REQUIRED_TRUE = {
    "actual_process_restart",
    "exact_response_bytes_persisted",
    "provenance_manifest_persisted",
    "accept_private_completed",
    "append_only_publication_completed",
    "stable_public_lookup_completed",
}
REQUIRED_FALSE = {
    "external_production_deployment_claimed",
    "master_record_release_claimed",
    "orchestration_authority_granted",
}


def canonical_hash(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_bundle(path: Path) -> dict[str, bytes]:
    if path.is_dir():
        files: dict[str, bytes] = {}
        for candidate in path.rglob("*"):
            if candidate.is_file():
                files[candidate.relative_to(path).as_posix()] = candidate.read_bytes()
        return files
    require(path.is_file(), f"bundle does not exist: {path}")
    require(zipfile.is_zipfile(path), "bundle must be a directory or ZIP archive")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(all(not name.endswith("/") for name in names), "bundle must not contain directories")
        require(len(names) == len(set(names)), "bundle contains duplicate filenames")
        return {name: archive.read(name) for name in names}


def verify(path: Path) -> dict:
    files = read_bundle(path)
    names = set(files)
    unexpected = sorted(names - ALLOWED_NAMES)
    missing = sorted(ALLOWED_NAMES - names)
    require(not unexpected, f"unexpected evidence files: {unexpected}")
    require(not missing, f"missing evidence files: {missing}")

    try:
        receipt = json.loads(files[RECEIPT_NAME].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("receipt is not valid UTF-8 JSON") from exc
    require(isinstance(receipt, dict), "receipt must be a JSON object")
    require(receipt.get("schema_version") == "HIL-AUTOMATED-FULL-CYCLE-RECEIPT-v1", "receipt schema mismatch")
    require(receipt.get("observation_scope") == "GITHUB_HOSTED_EPHEMERAL_FULL_CYCLE_PROOF", "receipt scope mismatch")
    require(receipt.get("authority_effect") == "NONE", "receipt authority effect must be NONE")
    require(receipt.get("readiness_before_restart") == "READY", "pre-restart readiness mismatch")
    require(receipt.get("readiness_after_restart") == "READY", "post-restart readiness mismatch")

    for field in REQUIRED_TRUE:
        require(receipt.get(field) is True, f"receipt field must be true: {field}")
    for field in REQUIRED_FALSE:
        require(receipt.get(field) is False, f"receipt field must be false: {field}")
    require(receipt.get("durable_counts") == {"submissions": 1, "reviews": 1, "publications": 1}, "durable counts mismatch")

    claimed = receipt.get("receipt_sha256")
    require(isinstance(claimed, str) and len(claimed) == 64, "receipt_sha256 is invalid")
    unhashed = dict(receipt)
    unhashed.pop("receipt_sha256", None)
    require(canonical_hash(unhashed) == claimed, "receipt_sha256 mismatch")

    return {
        "schema_version": "HIL-FULL-CYCLE-ARTIFACT-VERIFICATION-v1",
        "bundle": str(path),
        "files": sorted(names),
        "receipt_sha256": claimed,
        "artifact_purity_state": "PURE_BOUNDED_HIL_EVIDENCE",
        "provider_specific_files_present": False,
        "authority_effect": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.bundle)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"HIL_FULL_CYCLE_ARTIFACT_VERIFICATION=FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
