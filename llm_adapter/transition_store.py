"""Durable SQLite storage for Ecosystem Chat transition relationships.

This store persists canonical transition records and Master-Records submission queue
entries. Local persistence is not Master-Records custody and never marks a record
RECORDED without an independently returned custody receipt.
"""
from __future__ import annotations

import json
import os
import sqlite3
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

DEFAULT_PATH = os.getenv("STEGVERSE_TRANSITION_DB", "/tmp/stegverse-ecosystem-chat.db")


class TransitionStore:
    def __init__(self, path: str | Path = DEFAULT_PATH) -> None:
        self.path = str(path)
        self._lock = RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS transitions (
                    transition_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    lifecycle_state TEXT NOT NULL,
                    record_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS custody_queue (
                    transition_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    final_receipt_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    custody_receipt_id TEXT,
                    master_record_ref TEXT,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (transition_id) REFERENCES transitions(transition_id)
                );
                """
            )

    def put(self, record: dict[str, Any]) -> dict[str, Any]:
        transition_id = str(record["transition_id"])
        run_id = str(record["run_id"])
        state = str(record["lifecycle_state"])
        now = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
        with self._lock, self._connect() as connection:
            existing = connection.execute(
                "SELECT run_id FROM transitions WHERE transition_id = ?", (transition_id,)
            ).fetchone()
            if existing and existing["run_id"] != run_id:
                raise ValueError("transition_id already exists with a different run_id")
            connection.execute(
                """
                INSERT INTO transitions(transition_id, run_id, lifecycle_state, record_json, updated_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(transition_id) DO UPDATE SET
                    run_id=excluded.run_id,
                    lifecycle_state=excluded.lifecycle_state,
                    record_json=excluded.record_json,
                    updated_at=excluded.updated_at
                """,
                (transition_id, run_id, state, payload, now),
            )
        return deepcopy(record)

    def get(self, transition_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM transitions WHERE transition_id = ?", (transition_id,)
            ).fetchone()
        return json.loads(row["record_json"]) if row else None

    def enqueue_custody(self, record: dict[str, Any]) -> None:
        continuity = record.get("continuity", {})
        final_receipt_id = continuity.get("final_receipt_id")
        if record.get("lifecycle_state") != "COMPLETED" or not final_receipt_id:
            raise ValueError("custody queue requires a COMPLETED record with final_receipt_id")
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO custody_queue(
                    transition_id, run_id, final_receipt_id, state, attempts, updated_at
                ) VALUES(?,?,?,?,0,?)
                ON CONFLICT(transition_id) DO UPDATE SET
                    run_id=excluded.run_id,
                    final_receipt_id=excluded.final_receipt_id,
                    state=CASE
                        WHEN custody_queue.state = 'RECORDED' THEN custody_queue.state
                        ELSE 'PENDING'
                    END,
                    updated_at=excluded.updated_at
                """,
                (record["transition_id"], record["run_id"], final_receipt_id, "PENDING", now),
            )

    def custody_status(self, transition_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM custody_queue WHERE transition_id = ?", (transition_id,)
            ).fetchone()
        return dict(row) if row else None

    def pending_custody(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT q.*, t.record_json
                FROM custody_queue q
                JOIN transitions t USING(transition_id)
                WHERE q.state IN ('PENDING','RETRY')
                ORDER BY q.updated_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [{**dict(row), "record": json.loads(row["record_json"])} for row in rows]

    def mark_attempt(self, transition_id: str, *, state: str, error: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE custody_queue
                SET state=?, attempts=attempts+1, last_error=?, updated_at=?
                WHERE transition_id=?
                """,
                (state, error, now, transition_id),
            )

    def mark_recorded(
        self,
        transition_id: str,
        *,
        custody_receipt_id: str,
        master_record_ref: str,
    ) -> dict[str, Any]:
        record = self.get(transition_id)
        if record is None:
            raise KeyError(transition_id)
        record["continuity"]["master_record_status"] = "RECORDED"
        record["continuity"]["master_record_ref"] = master_record_ref
        record["continuity"]["reconstruction_status"] = "PASS"
        record["governance"]["evidence_refs"] = list(dict.fromkeys([
            *record["governance"].get("evidence_refs", []),
            custody_receipt_id,
        ]))
        self.put(record)
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE custody_queue
                SET state='RECORDED', custody_receipt_id=?, master_record_ref=?,
                    last_error=NULL, updated_at=?
                WHERE transition_id=?
                """,
                (custody_receipt_id, master_record_ref, now, transition_id),
            )
        return record


store = TransitionStore()
