"""Append-only storage for External Chat cooperative review packages and receipts."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReviewConflict(ValueError):
    pass


class ExternalReviewStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or os.getenv("STEGVERSE_EXTERNAL_REVIEW_DB", "/tmp/stegverse-external-review.db")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS review_packages (
                    package_id TEXT PRIMARY KEY,
                    framework_id TEXT NOT NULL,
                    compatibility_receipt_id TEXT NOT NULL,
                    submission_sha256 TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    intake_receipt_id TEXT NOT NULL,
                    review_state TEXT NOT NULL,
                    received_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS review_package_identity
                ON review_packages(compatibility_receipt_id, submission_sha256);

                CREATE TABLE IF NOT EXISTS correction_receipts (
                    correction_receipt_id TEXT PRIMARY KEY,
                    package_id TEXT NOT NULL,
                    challenged_receipt_id TEXT NOT NULL,
                    reviewer_ref TEXT NOT NULL,
                    reviewer_delegation_ref TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    issued_at TEXT NOT NULL,
                    FOREIGN KEY(package_id) REFERENCES review_packages(package_id)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS correction_identity
                ON correction_receipts(package_id, challenged_receipt_id);
                """
            )

    def append_package(self, record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        with self._lock, self._connect() as db:
            existing = db.execute(
                "SELECT * FROM review_packages WHERE package_id = ?",
                (record["package_id"],),
            ).fetchone()
            if existing:
                row = dict(existing)
                if row["content_sha256"] != record["content_sha256"]:
                    raise ReviewConflict("package_id already exists with different content")
                return self._decode_package(row), False
            identity = db.execute(
                "SELECT * FROM review_packages WHERE compatibility_receipt_id = ? AND submission_sha256 = ?",
                (record["compatibility_receipt_id"], record["submission_sha256"]),
            ).fetchone()
            if identity:
                row = dict(identity)
                if row["content_sha256"] != record["content_sha256"]:
                    raise ReviewConflict("compatibility receipt and submission hash already bind different package content")
                return self._decode_package(row), False
            db.execute(
                """INSERT INTO review_packages
                (package_id, framework_id, compatibility_receipt_id, submission_sha256,
                 content_sha256, payload_json, intake_receipt_id, review_state, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record["package_id"], record["framework_id"], record["compatibility_receipt_id"],
                    record["submission_sha256"], record["content_sha256"],
                    json.dumps(record["payload"], sort_keys=True, separators=(",", ":")),
                    record["intake_receipt_id"], record["review_state"], record["received_at"],
                ),
            )
            db.commit()
            return record, True

    def get_package(self, package_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM review_packages WHERE package_id = ?", (package_id,)).fetchone()
            return self._decode_package(dict(row)) if row else None

    def append_correction(self, record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        with self._lock, self._connect() as db:
            package = db.execute("SELECT * FROM review_packages WHERE package_id = ?", (record["package_id"],)).fetchone()
            if not package:
                raise KeyError("review package not found")
            existing = db.execute(
                "SELECT * FROM correction_receipts WHERE package_id = ? AND challenged_receipt_id = ?",
                (record["package_id"], record["challenged_receipt_id"]),
            ).fetchone()
            if existing:
                row = dict(existing)
                if row["content_sha256"] != record["content_sha256"]:
                    raise ReviewConflict("a conflicting correction already exists for this challenged receipt")
                return self._decode_correction(row), False
            db.execute(
                """INSERT INTO correction_receipts
                (correction_receipt_id, package_id, challenged_receipt_id, reviewer_ref,
                 reviewer_delegation_ref, decision, content_sha256, payload_json, issued_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record["correction_receipt_id"], record["package_id"], record["challenged_receipt_id"],
                    record["reviewer_ref"], record["reviewer_delegation_ref"], record["decision"],
                    record["content_sha256"], json.dumps(record["payload"], sort_keys=True, separators=(",", ":")),
                    record["issued_at"],
                ),
            )
            state = "CORRECTION_RECORDED" if record["decision"] in {"CORRECT", "PARTIAL_CORRECTION"} else "REVIEW_RECORDED"
            db.execute("UPDATE review_packages SET review_state = ? WHERE package_id = ?", (state, record["package_id"]))
            db.commit()
            return record, True

    def list_corrections(self, package_id: str) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM correction_receipts WHERE package_id = ? ORDER BY issued_at",
                (package_id,),
            ).fetchall()
            return [self._decode_correction(dict(row)) for row in rows]

    @staticmethod
    def _decode_package(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "package_id": row["package_id"],
            "framework_id": row["framework_id"],
            "compatibility_receipt_id": row["compatibility_receipt_id"],
            "submission_sha256": row["submission_sha256"],
            "content_sha256": row["content_sha256"],
            "payload": json.loads(row["payload_json"]),
            "intake_receipt_id": row["intake_receipt_id"],
            "review_state": row["review_state"],
            "received_at": row["received_at"],
        }

    @staticmethod
    def _decode_correction(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "correction_receipt_id": row["correction_receipt_id"],
            "package_id": row["package_id"],
            "challenged_receipt_id": row["challenged_receipt_id"],
            "reviewer_ref": row["reviewer_ref"],
            "reviewer_delegation_ref": row["reviewer_delegation_ref"],
            "decision": row["decision"],
            "content_sha256": row["content_sha256"],
            "payload": json.loads(row["payload_json"]),
            "issued_at": row["issued_at"],
        }


store = ExternalReviewStore()
