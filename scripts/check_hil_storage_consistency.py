#!/usr/bin/env python3
"""Fail-closed audit for HIL intake storage and SQLite custody records."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit(data_dir: Path) -> dict:
    root = data_dir.resolve()
    database = root / "hil-intake.db"
    failures: list[str] = []
    observations: list[dict] = []

    if not database.is_file():
        return {
            "schema_version": "HIL-STORAGE-CONSISTENCY-REPORT-v1",
            "state": "FAIL",
            "data_dir": str(root),
            "failures": ["hil_intake_database_missing"],
            "submissions_checked": 0,
            "orphan_files": [],
            "observations": [],
            "authority_effect": "NONE",
        }

    referenced: set[Path] = set()
    try:
        with sqlite3.connect(database) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT submission_id, submitted_file_sha256, provenance_manifest_sha256, "
                "storage_path, manifest_path FROM submissions ORDER BY submission_id"
            ).fetchall()
    except (sqlite3.DatabaseError, sqlite3.OperationalError) as exc:
        return {
            "schema_version": "HIL-STORAGE-CONSISTENCY-REPORT-v1",
            "state": "FAIL",
            "data_dir": str(root),
            "failures": [f"hil_intake_database_unreadable:{type(exc).__name__}"],
            "submissions_checked": 0,
            "orphan_files": [],
            "observations": [],
            "authority_effect": "NONE",
        }

    for row in rows:
        submission_id = row["submission_id"]
        pdf_path = Path(row["storage_path"]).resolve()
        manifest_path = Path(row["manifest_path"]).resolve()
        referenced.update({pdf_path, manifest_path})
        item = {"submission_id": submission_id, "pdf": str(pdf_path), "manifest": str(manifest_path)}

        for path, label in ((pdf_path, "pdf"), (manifest_path, "manifest")):
            try:
                path.relative_to(root)
            except ValueError:
                failures.append(f"{submission_id}:{label}_path_outside_data_dir")

        if not pdf_path.is_file():
            failures.append(f"{submission_id}:pdf_missing")
        elif sha256_file(pdf_path) != row["submitted_file_sha256"]:
            failures.append(f"{submission_id}:pdf_hash_mismatch")

        if not manifest_path.is_file():
            failures.append(f"{submission_id}:manifest_missing")
        else:
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                failures.append(f"{submission_id}:manifest_invalid_json")
            else:
                if not isinstance(manifest, dict):
                    failures.append(f"{submission_id}:manifest_not_object")
                else:
                    if canonical_hash(manifest) != row["provenance_manifest_sha256"]:
                        failures.append(f"{submission_id}:manifest_hash_mismatch")
                    if manifest.get("response_sha256") != row["submitted_file_sha256"]:
                        failures.append(f"{submission_id}:manifest_response_hash_mismatch")
        observations.append(item)

    candidates: set[Path] = set()
    for directory, suffix in ((root / "originals", "*.pdf"), (root / "provenance", "*.json")):
        if directory.is_dir():
            candidates.update(path.resolve() for path in directory.glob(suffix) if path.is_file())
    orphan_files = sorted(str(path) for path in candidates - referenced)
    if orphan_files:
        failures.append("unreferenced_artifacts_detected")

    return {
        "schema_version": "HIL-STORAGE-CONSISTENCY-REPORT-v1",
        "state": "PASS" if not failures else "FAIL",
        "data_dir": str(root),
        "failures": failures,
        "submissions_checked": len(rows),
        "orphan_files": orphan_files,
        "observations": observations,
        "authority_effect": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path, help="HIL data directory containing hil-intake.db")
    parser.add_argument("--report", type=Path, help="Optional JSON report output path")
    args = parser.parse_args()

    report = audit(args.data_dir)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if report["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
