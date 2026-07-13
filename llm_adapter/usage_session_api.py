"""Usage-session storage and same-origin retrieval contract for Ecosystem Chat.

The browser retrieval route uses a same-origin session cookie or matching
X-SteGVerse-Session header. Machine submission is separately authenticated.
Retrieval grants no authority, admissibility, or Master-Records custody.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from fastapi import APIRouter, Cookie, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter()
DB_PATH = os.getenv("STEGVERSE_USAGE_SESSION_DB", "/tmp/stegverse-usage-sessions.db")
SUBMIT_TOKEN = os.getenv("STEGVERSE_USAGE_SUBMIT_TOKEN", "")
SESSION_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
EVIDENCE_CLASSES = {"MEASURED", "CONFIGURED", "DERIVED", "UNAVAILABLE"}
PRODUCER_IDENTITY = "StegVerse-org/LLM-adapter:usage_session_api"
POLICY_REFERENCE = "policy:stegverse-site-usage-retrieval-v1"
_LOCK = RLock()


class UsageSessionSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = Field(pattern=r"^1\.0\.0$")
    submission_type: str = Field(pattern=r"^usage_session_event_batch$")
    session_id: str = Field(min_length=1, max_length=160)
    events: list[dict[str, Any]] = Field(min_length=1, max_length=500)


def _connect() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def _initialize() -> None:
    with _LOCK, _connect() as connection:
        connection.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS usage_events (
                metric_owner TEXT NOT NULL,
                measurement_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                transition_id TEXT NOT NULL,
                event_sha256 TEXT NOT NULL,
                event_json TEXT NOT NULL,
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(metric_owner, measurement_id)
            );
            CREATE INDEX IF NOT EXISTS idx_usage_events_session
                ON usage_events(session_id, recorded_at, metric_owner, measurement_id);
            """
        )


def _canonical_hash(value: dict[str, Any]) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _validate_session_id(session_id: str) -> None:
    if not SESSION_PATTERN.fullmatch(session_id):
        raise HTTPException(status_code=400, detail={"reason": "invalid_session_identity"})


def _validate_event(event: dict[str, Any], session_id: str) -> dict[str, Any]:
    required = {
        "measurement_id", "session_id", "transition_id", "origin_entry_point",
        "entry_point", "entry_point_role", "interaction_type", "metric_owner",
        "measurement_source", "metrics", "timestamp", "receipt_refs",
    }
    if not required.issubset(event):
        raise HTTPException(status_code=422, detail={"reason": "usage_event_incomplete"})
    if event["session_id"] != session_id:
        raise HTTPException(status_code=409, detail={"reason": "session_identity_mismatch"})
    for field in (
        "measurement_id", "transition_id", "origin_entry_point", "entry_point",
        "entry_point_role", "interaction_type", "metric_owner", "measurement_source",
    ):
        if not isinstance(event[field], str) or not event[field].strip():
            raise HTTPException(status_code=422, detail={"reason": f"invalid_{field}"})
    if not isinstance(event["metrics"], dict) or not event["metrics"]:
        raise HTTPException(status_code=422, detail={"reason": "metrics_required"})
    for metric in event["metrics"].values():
        if not isinstance(metric, dict) or metric.get("evidence_class") not in EVIDENCE_CLASSES:
            raise HTTPException(status_code=422, detail={"reason": "evidence_class_invalid"})
        if metric["evidence_class"] == "UNAVAILABLE" and metric.get("value") is not None:
            raise HTTPException(status_code=422, detail={"reason": "unavailable_value_invalid"})
    if not isinstance(event["receipt_refs"], list):
        raise HTTPException(status_code=422, detail={"reason": "receipt_refs_invalid"})
    canonical = dict(event)
    supplied_hash = canonical.pop("event_sha256", None)
    computed_hash = _canonical_hash(canonical)
    if supplied_hash is not None and supplied_hash != computed_hash:
        raise HTTPException(status_code=422, detail={"reason": "event_hash_mismatch"})
    canonical["event_sha256"] = computed_hash
    return canonical


def _authorize_submit(authorization: str | None) -> None:
    if not SUBMIT_TOKEN:
        raise HTTPException(status_code=503, detail={"reason": "usage_submission_not_configured"})
    expected = f"Bearer {SUBMIT_TOKEN}"
    if authorization is None or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail={"reason": "unauthorized"})


def _authorize_session(session_id: str, header_session: str | None, cookie_session: str | None) -> None:
    presented = header_session or cookie_session
    if presented is None or not hmac.compare_digest(presented, session_id):
        raise HTTPException(status_code=401, detail={"reason": "same_origin_session_required"})


_initialize()


@router.post("/api/usage/sessions")
def submit_usage_session(
    payload: UsageSessionSubmission,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _authorize_submit(authorization)
    _validate_session_id(payload.session_id)
    events = [_validate_event(event, payload.session_id) for event in payload.events]
    inserted = 0
    with _LOCK, _connect() as connection:
        for event in events:
            event_json = json.dumps(event, sort_keys=True, separators=(",", ":"))
            existing = connection.execute(
                "SELECT session_id, event_sha256 FROM usage_events WHERE metric_owner=? AND measurement_id=?",
                (event["metric_owner"], event["measurement_id"]),
            ).fetchone()
            if existing:
                if existing["session_id"] != payload.session_id or existing["event_sha256"] != event["event_sha256"]:
                    raise HTTPException(status_code=409, detail={"reason": "measurement_identity_conflict"})
                continue
            connection.execute(
                """
                INSERT INTO usage_events(metric_owner, measurement_id, session_id, transition_id, event_sha256, event_json)
                VALUES(?,?,?,?,?,?)
                """,
                (
                    event["metric_owner"], event["measurement_id"], payload.session_id,
                    event["transition_id"], event["event_sha256"], event_json,
                ),
            )
            inserted += 1
    return {
        "schema": "stegverse.usage.submission.v1",
        "session_id": payload.session_id,
        "accepted_events": len(events),
        "inserted_events": inserted,
        "authority_granted": False,
        "custody_recorded": False,
    }


@router.get("/api/usage/sessions/{session_id}")
def retrieve_usage_session(
    session_id: str,
    x_stegverse_session: str | None = Header(default=None, alias="X-SteGVerse-Session"),
    stegverse_session_id: str | None = Cookie(default=None),
) -> dict[str, Any]:
    _validate_session_id(session_id)
    _authorize_session(session_id, x_stegverse_session, stegverse_session_id)
    with _LOCK, _connect() as connection:
        rows = connection.execute(
            "SELECT event_json FROM usage_events WHERE session_id=? ORDER BY recorded_at, metric_owner, measurement_id",
            (session_id,),
        ).fetchall()
    events = [json.loads(row["event_json"]) for row in rows]
    if not events:
        raise HTTPException(status_code=404, detail={"reason": "usage_session_not_found"})
    retrieved_at = datetime.now(timezone.utc).isoformat()
    receipt_material = {
        "session_id": session_id,
        "event_hashes": [event["event_sha256"] for event in events],
        "retrieved_at": retrieved_at,
        "producer_identity": PRODUCER_IDENTITY,
        "policy_reference": POLICY_REFERENCE,
        "authority_granted": False,
        "custody_recorded": False,
    }
    return {
        "schema": "stegverse.usage.session.v1",
        "session_id": session_id,
        "source_class": "LIVE_USAGE_API",
        "events": events,
        "retrieval_receipt": {
            "session_id": session_id,
            "receipt_id": "usage-retrieval:sha256:" + _canonical_hash(receipt_material),
            "retrieved_at": retrieved_at,
            "producer_identity": PRODUCER_IDENTITY,
            "policy_reference": POLICY_REFERENCE,
            "event_count": len(events),
            "authority_granted": False,
            "custody_recorded": False,
        },
    }
