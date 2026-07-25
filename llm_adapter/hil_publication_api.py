"""Separately authorized append-only publication transition for HIL submissions."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from fastapi import APIRouter, Form, Header, HTTPException

router = APIRouter(prefix="/api/hil", tags=["hil-publication"])
RESPONSE_ID = re.compile(r"^HIL-RESP-[A-Z0-9-]+$")


def _data_dir() -> Path:
    return Path(os.getenv("STEGVERSE_HIL_DATA_DIR", "/tmp/stegverse-hil")).resolve()


def _connect() -> sqlite3.Connection:
    root = _data_dir()
    root.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(root / "hil-intake.db")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(
        """CREATE TABLE IF NOT EXISTS publications (
        publication_id TEXT PRIMARY KEY,
        response_id TEXT NOT NULL UNIQUE,
        submission_id TEXT NOT NULL UNIQUE,
        published_at TEXT NOT NULL,
        publisher TEXT NOT NULL,
        participant_display_name TEXT,
        artifact_public_path TEXT NOT NULL,
        publication_record_json TEXT NOT NULL,
        publication_record_sha256 TEXT NOT NULL,
        previous_publication_sha256 TEXT,
        authority_json TEXT NOT NULL,
        FOREIGN KEY(submission_id) REFERENCES submissions(submission_id)
        )"""
    )
    return connection


def _canonical_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _publication_token_required(token: str | None) -> None:
    expected = os.getenv("STEGVERSE_HIL_PUBLICATION_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="hil_publication_not_configured")
    if not token or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="hil_publication_forbidden")


def _validate_artifact_path(value: str) -> str:
    candidate = value.strip()
    path = PurePosixPath(candidate)
    if (
        not candidate.endswith(".pdf")
        or candidate.startswith(("http://", "https://", "/"))
        or ".." in path.parts
        or path.parts[:2] != ("data", "hil-responses")
    ):
        raise HTTPException(status_code=400, detail="hil_artifact_public_path_invalid")
    return candidate


def publication_readiness() -> dict:
    blockers: list[str] = []
    if not os.getenv("STEGVERSE_HIL_PUBLICATION_TOKEN", ""):
        blockers.append("hil_publication_token_not_configured")
    if os.getenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "false").lower() != "true":
        blockers.append("durable_storage_not_declared")
    return {
        "schema_version": "HIL-PUBLICATION-READINESS-v1",
        "state": "READY" if not blockers else "CONFIGURATION_REQUIRED",
        "blockers": blockers,
        "append_only": True,
        "requires_private_review_decision": "ACCEPT_PRIVATE",
        "requires_publication_consent": ["public", "anonymous"],
        "artifact_path_prefix": "data/hil-responses/",
        "execution_authority": False,
        "master_record_append_authority": False,
    }


@router.get("/publication-readiness")
def get_publication_readiness() -> dict:
    return publication_readiness()


@router.get("/publications/{response_id}")
def get_publication(response_id: str) -> dict:
    if not RESPONSE_ID.fullmatch(response_id):
        raise HTTPException(status_code=400, detail="hil_response_id_invalid")
    with _connect() as connection:
        row = connection.execute(
            "SELECT publication_record_json FROM publications WHERE response_id = ?",
            (response_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="hil_publication_not_found")
    return json.loads(row["publication_record_json"])


@router.post("/submissions/{submission_id}/publication-decisions")
def publish_submission(
    submission_id: str,
    response_id: str = Form(...),
    publisher: str = Form(...),
    participant_display_name: str = Form(""),
    artifact_public_path: str = Form(...),
    x_stegverse_hil_publication_token: str | None = Header(default=None),
) -> dict:
    _publication_token_required(x_stegverse_hil_publication_token)
    if not RESPONSE_ID.fullmatch(response_id):
        raise HTTPException(status_code=400, detail="hil_response_id_invalid")
    publisher = publisher.strip()
    if not publisher:
        raise HTTPException(status_code=400, detail="hil_publisher_required")
    artifact_public_path = _validate_artifact_path(artifact_public_path)

    with _connect() as connection:
        submission = connection.execute(
            "SELECT submission_id, participant_identifier, publication_consent, primary_sha256, "
            "submitted_file_sha256, provenance_manifest_sha256, chain_validation_state, validation_state "
            "FROM submissions WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
        if submission is None:
            raise HTTPException(status_code=404, detail="hil_submission_not_found")
        review = connection.execute(
            "SELECT review_id, decision, review_receipt_sha256 FROM submission_reviews WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
        if review is None or review["decision"] != "ACCEPT_PRIVATE":
            raise HTTPException(status_code=409, detail="hil_private_acceptance_required")
        if submission["publication_consent"] not in {"public", "anonymous"}:
            raise HTTPException(status_code=409, detail="hil_publication_consent_required")
        if connection.execute(
            "SELECT 1 FROM publications WHERE submission_id = ? OR response_id = ?",
            (submission_id, response_id),
        ).fetchone() is not None:
            raise HTTPException(status_code=409, detail="hil_publication_already_recorded_or_id_reused")
        previous = connection.execute(
            "SELECT publication_record_sha256 FROM publications ORDER BY rowid DESC LIMIT 1"
        ).fetchone()

        published_at = datetime.now(timezone.utc).isoformat()
        publication_id = f"HIL-PUBLICATION-{response_id.removeprefix('HIL-RESP-')}"
        display_name = None
        if submission["publication_consent"] == "public":
            display_name = participant_display_name.strip() or submission["participant_identifier"]
        record = {
            "schema_version": "HIL-PUBLICATION-RECORD-v1",
            "publication_id": publication_id,
            "response_id": response_id,
            "submission_id": submission_id,
            "published_at": published_at,
            "publisher": publisher,
            "participant_display_name": display_name,
            "publication_consent": submission["publication_consent"],
            "artifact_path": artifact_public_path,
            "primary_sha256": submission["primary_sha256"],
            "response_sha256": submission["submitted_file_sha256"],
            "provenance_manifest_sha256": submission["provenance_manifest_sha256"],
            "chain_validation_state": submission["chain_validation_state"],
            "private_review_id": review["review_id"],
            "private_review_receipt_sha256": review["review_receipt_sha256"],
            "previous_publication_sha256": previous["publication_record_sha256"] if previous else None,
            "master_record_release": None,
            "authority": {
                "public_projection_authorized": True,
                "execution": False,
                "endorsement": False,
                "master_record_append": False,
            },
        }
        record_sha256 = _canonical_hash(record)
        record["publication_record_sha256"] = record_sha256
        try:
            connection.execute(
                "INSERT INTO publications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    publication_id,
                    response_id,
                    submission_id,
                    published_at,
                    publisher,
                    display_name,
                    artifact_public_path,
                    json.dumps(record, sort_keys=True),
                    record_sha256,
                    record["previous_publication_sha256"],
                    json.dumps(record["authority"], sort_keys=True),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(
                status_code=409,
                detail="hil_publication_already_recorded_or_id_reused",
            ) from exc
    return record
