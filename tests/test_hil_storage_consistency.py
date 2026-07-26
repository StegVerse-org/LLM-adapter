from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_hil_storage_consistency.py"
SPEC = importlib.util.spec_from_file_location("hil_storage_consistency", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def canonical_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_store(root: Path) -> tuple[Path, Path, Path]:
    originals = root / "originals"
    provenance = root / "provenance"
    originals.mkdir(parents=True)
    provenance.mkdir(parents=True)

    submission_id = "HIL-INTAKE-TEST-0001"
    pdf = b"%PDF-1.7\n%%EOF\n"
    pdf_hash = hashlib.sha256(pdf).hexdigest()
    manifest = {"schema_version": "HIL-RESPONSE-PROVENANCE-v1.1", "response_sha256": pdf_hash}
    pdf_path = originals / f"{submission_id}.pdf"
    manifest_path = provenance / f"{submission_id}.json"
    pdf_path.write_bytes(pdf)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    database = root / "hil-intake.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """CREATE TABLE submissions (
            submission_id TEXT PRIMARY KEY,
            submitted_file_sha256 TEXT NOT NULL,
            provenance_manifest_sha256 TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            manifest_path TEXT NOT NULL
            )"""
        )
        connection.execute(
            "INSERT INTO submissions VALUES (?, ?, ?, ?, ?)",
            (submission_id, pdf_hash, canonical_hash(manifest), str(pdf_path), str(manifest_path)),
        )
    return database, pdf_path, manifest_path


def test_consistent_store_passes(tmp_path: Path) -> None:
    build_store(tmp_path)
    report = MODULE.audit(tmp_path)
    assert report["state"] == "PASS"
    assert report["submissions_checked"] == 1
    assert report["orphan_files"] == []


def test_pdf_hash_drift_fails(tmp_path: Path) -> None:
    _, pdf_path, _ = build_store(tmp_path)
    pdf_path.write_bytes(b"%PDF-1.7\nchanged\n%%EOF\n")
    report = MODULE.audit(tmp_path)
    assert report["state"] == "FAIL"
    assert "HIL-INTAKE-TEST-0001:pdf_hash_mismatch" in report["failures"]


def test_orphan_artifact_fails(tmp_path: Path) -> None:
    build_store(tmp_path)
    orphan = tmp_path / "originals" / "HIL-INTAKE-ORPHAN.pdf"
    orphan.write_bytes(b"%PDF-1.7\n%%EOF\n")
    report = MODULE.audit(tmp_path)
    assert report["state"] == "FAIL"
    assert "unreferenced_artifacts_detected" in report["failures"]
    assert str(orphan.resolve()) in report["orphan_files"]


def test_missing_database_fails_closed(tmp_path: Path) -> None:
    report = MODULE.audit(tmp_path)
    assert report["state"] == "FAIL"
    assert report["failures"] == ["hil_intake_database_missing"]
