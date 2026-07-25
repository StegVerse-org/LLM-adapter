"""Bounded intake API for Humans as the Interoperability Layer response PDFs."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile

router = APIRouter(prefix="/api/hil", tags=["hil-intake"])
PRIMARY_SHA256 = "52102cccb9ba9016c76434a64e22031b6a8c3edd3b8806e7b664e609216b2946"
PRIMARY_VERSION = "v0.5"
PROTOCOL_VERSION = "HIL-PROTOCOL-v1.0"
PROMPT_VERSION = "HIL-PROMPT-v1.0"
PROMPT_SHA256 = "0ebe215318b4eeeb8ed6422e0954372c314fadc8fac9254e452bc7670a1b9922"
MAX_BYTES = 10 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
ACTIVE_MARKERS = (b"/JavaScript", b"/JS", b"/Launch", b"/EmbeddedFile", b"/OpenAction")
HEX64 = re.compile(r"^[a-f0-9]{64}$")
REVIEW_DECISIONS = {"ACCEPT_PRIVATE", "QUARANTINE", "REJECT"}


def _enabled() -> bool:
    return os.getenv("STEGVERSE_HIL_INTAKE_ENABLED", "false").strip().lower() == "true"


def _data_dir() -> Path:
    return Path(os.getenv("STEGVERSE_HIL_DATA_DIR", "/tmp/stegverse-hil")).resolve()


def _canonical_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _connect() -> sqlite3.Connection:
    root = _data_dir()
    root.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(root / "hil-intake.db")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE IF NOT EXISTS submissions (
        submission_id TEXT PRIMARY KEY,
        received_at TEXT NOT NULL,
        participant_identifier TEXT NOT NULL,
        publication_consent TEXT NOT NULL,
        primary_sha256 TEXT NOT NULL,
        submitted_file_sha256 TEXT NOT NULL,
        provenance_manifest_sha256 TEXT NOT NULL,
        chain_validation_state TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        storage_path TEXT NOT NULL,
        manifest_path TEXT NOT NULL,
        validation_state TEXT NOT NULL,
        active_content_state TEXT NOT NULL,
        authority_json TEXT NOT NULL
        )"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS submission_reviews (
        review_id TEXT PRIMARY KEY,
        submission_id TEXT NOT NULL UNIQUE,
        reviewed_at TEXT NOT NULL,
        reviewer TEXT NOT NULL,
        decision TEXT NOT NULL,
        notes TEXT NOT NULL,
        review_receipt_sha256 TEXT NOT NULL,
        authority_json TEXT NOT NULL,
        FOREIGN KEY(submission_id) REFERENCES submissions(submission_id)
        )"""
    )
    return connection


def _review_token_required(token: str | None) -> None:
    expected = os.getenv("STEGVERSE_HIL_REVIEW_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="hil_review_not_configured")
    if not token or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="hil_review_forbidden")


def readiness() -> dict:
    blockers: list[str] = []
    if not _enabled():
        blockers.append("hil_intake_disabled")
    root = _data_dir()
    if not root.is_absolute():
        blockers.append("hil_data_dir_must_be_absolute")
    durable = os.getenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "false").lower() == "true"
    if not durable:
        blockers.append("durable_storage_not_declared")
    return {
        "schema": "stegverse.hil_intake_readiness.v2",
        "state": "READY" if not blockers else "CONFIGURATION_REQUIRED",
        "blockers": blockers,
        "maximum_size_bytes": MAX_BYTES,
        "accepted_media_type": "application/pdf",
        "provenance_manifest_required": True,
        "provenance_manifest_schema": "HIL-RESPONSE-PROVENANCE-v1",
        "primary_version": PRIMARY_VERSION,
        "primary_sha256": PRIMARY_SHA256,
        "protocol_version": PROTOCOL_VERSION,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": PROMPT_SHA256,
        "private_review_configured": bool(os.getenv("STEGVERSE_HIL_REVIEW_TOKEN", "")),
        "execution_authority": False,
        "publication_authority": False,
        "master_record_append_authority": False,
    }


@router.get("/readiness")
def get_readiness() -> dict:
    return readiness()


def _validate_manifest(manifest: dict, response_sha256: str) -> dict:
    if manifest.get("schema_version") != "HIL-RESPONSE-PROVENANCE-v1":
        raise HTTPException(status_code=400, detail="provenance_schema_version_invalid")
    if manifest.get("primary_version") != PRIMARY_VERSION:
        raise HTTPException(status_code=400, detail="provenance_primary_version_mismatch")
    if manifest.get("primary_sha256") != PRIMARY_SHA256:
        raise HTTPException(status_code=400, detail="provenance_primary_sha256_mismatch")
    if manifest.get("protocol_version") != PROTOCOL_VERSION:
        raise HTTPException(status_code=400, detail="provenance_protocol_version_mismatch")
    if manifest.get("prompt_version") != PROMPT_VERSION:
        raise HTTPException(status_code=400, detail="provenance_prompt_version_mismatch")
    if manifest.get("prompt_sha256") != PROMPT_SHA256:
        raise HTTPException(status_code=400, detail="provenance_prompt_sha256_mismatch")
    if manifest.get("response_sha256") != response_sha256:
        raise HTTPException(status_code=400, detail="provenance_response_sha256_mismatch")
    if not manifest.get("model") or not manifest.get("provider"):
        raise HTTPException(status_code=400, detail="provenance_model_provider_required")
    signature = manifest.get("producer_signature")
    if signature is not None:
        if not isinstance(signature, dict):
            raise HTTPException(status_code=400, detail="producer_signature_invalid")
        if signature.get("state") not in {"UNAVAILABLE", "DECLARED", "VERIFIED"}:
            raise HTTPException(status_code=400, detail="producer_signature_state_invalid")
    else:
        signature = {"state": "UNAVAILABLE", "scheme": None, "value": None, "key_id": None}
    normalized = dict(manifest)
    normalized["producer_signature"] = signature
    return normalized


@router.post("/submissions")
async def submit_response(
    response_pdf: UploadFile = File(...),
    provenance_manifest: UploadFile = File(...),
    participant_identifier: str = Form(...),
    publication_consent: str = Form(...),
    primary_sha256: str = Form(...),
    model_response_declared_unedited: bool = Form(...),
    participant_consent_authority_acknowledged: bool = Form(...),
) -> dict:
    if not _enabled():
        raise HTTPException(status_code=503, detail="hil_intake_disabled")
    if publication_consent not in {"public", "anonymous", "private"}:
        raise HTTPException(status_code=400, detail="invalid_publication_consent")
    if primary_sha256 != PRIMARY_SHA256:
        raise HTTPException(status_code=400, detail="primary_sha256_mismatch")
    if not model_response_declared_unedited:
        raise HTTPException(status_code=400, detail="unedited_confirmation_required")
    if not participant_consent_authority_acknowledged:
        raise HTTPException(status_code=400, detail="participant_authority_acknowledgement_required")

    data = await response_pdf.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="response_pdf_size_invalid")
    if response_pdf.content_type != "application/pdf" or not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="response_pdf_signature_invalid")

    active = [marker.decode("ascii") for marker in ACTIVE_MARKERS if marker in data]
    if active:
        raise HTTPException(status_code=400, detail={"active_pdf_content_detected": active})

    manifest_bytes = await provenance_manifest.read(MAX_MANIFEST_BYTES + 1)
    if not manifest_bytes or len(manifest_bytes) > MAX_MANIFEST_BYTES:
        raise HTTPException(status_code=413, detail="provenance_manifest_size_invalid")
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="provenance_manifest_json_invalid") from exc
    if not isinstance(manifest, dict):
        raise HTTPException(status_code=400, detail="provenance_manifest_shape_invalid")

    digest = hashlib.sha256(data).hexdigest()
    manifest = _validate_manifest(manifest, digest)
    manifest_sha256 = _canonical_hash(manifest)
    signature_state = manifest["producer_signature"]["state"]
    chain_state = "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED"
    if signature_state == "VERIFIED":
        chain_state = "PRIMARY_PROMPT_RESPONSE_SIGNATURE_CHAIN_VERIFIED"

    received_at = datetime.now(timezone.utc).isoformat()
    submission_id = f"HIL-INTAKE-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:12].upper()}"
    root = _data_dir()
    originals = root / "originals"
    manifests = root / "provenance"
    originals.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    path = originals / f"{submission_id}.pdf"
    manifest_path = manifests / f"{submission_id}.json"
    path.write_bytes(data)
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    authority = {
        "execution": False,
        "acceptance": False,
        "publication": False,
        "master_record_append": False,
    }
    with _connect() as connection:
        connection.execute(
            "INSERT INTO submissions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                submission_id,
                received_at,
                participant_identifier.strip() or "anonymous",
                publication_consent,
                primary_sha256,
                digest,
                manifest_sha256,
                chain_state,
                len(data),
                str(path),
                str(manifest_path),
                "RECEIVED_PENDING_REVIEW",
                "ABSENT",
                json.dumps(authority, sort_keys=True),
            ),
        )

    receipt_core = {
        "schema_version": "HIL-RECEIVER-RECEIPT-v2",
        "receipt_id": f"HIL-RECEIPT-{uuid4().hex[:16].upper()}",
        "submission_id": submission_id,
        "issued_at": received_at,
        "receiver": "StegVerse-org/LLM-adapter",
        "primary_version": PRIMARY_VERSION,
        "primary_sha256": PRIMARY_SHA256,
        "protocol_version": PROTOCOL_VERSION,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": PROMPT_SHA256,
        "submitted_file_sha256": digest,
        "provenance_manifest_sha256": manifest_sha256,
        "producer_signature_state": signature_state,
        "chain_validation_state": chain_state,
        "validation_state": "PENDING_REVIEW",
        "custody_state": "GATEWAY_EXACT_BYTES_PRESERVED",
        "publication_state": "NOT_AUTHORIZED",
        "response_id": None,
        "master_record_release": None,
        "previous_receipt_sha256": None,
        "authority": authority,
        "notes": [
            "Exact uploaded PDF bytes and provenance manifest preserved.",
            "Primary, protocol, prompt, and response hash chain verified.",
            "Producer signature is optional and its state is reported separately.",
            "Malware scanning, substantive review, acceptance, publication, and Master Record append remain pending.",
        ],
    }
    receipt_core["receipt_sha256"] = _canonical_hash(receipt_core)
    return receipt_core


@router.get("/submissions/{submission_id}/review-state")
def get_review_state(
    submission_id: str,
    x_stegverse_hil_review_token: str | None = Header(default=None),
) -> dict:
    _review_token_required(x_stegverse_hil_review_token)
    with _connect() as connection:
        submission = connection.execute(
            "SELECT submission_id, received_at, participant_identifier, publication_consent, "
            "primary_sha256, submitted_file_sha256, provenance_manifest_sha256, "
            "chain_validation_state, size_bytes, validation_state, active_content_state "
            "FROM submissions WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
        if submission is None:
            raise HTTPException(status_code=404, detail="hil_submission_not_found")
        review = connection.execute(
            "SELECT review_id, reviewed_at, reviewer, decision, notes, review_receipt_sha256 "
            "FROM submission_reviews WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
    return {
        "schema_version": "HIL-PRIVATE-REVIEW-STATE-v1",
        "submission": dict(submission),
        "review": dict(review) if review else None,
        "artifact_bytes_exposed": False,
        "storage_paths_exposed": False,
        "authority": {
            "execution": False,
            "publication": False,
            "master_record_append": False,
        },
    }


@router.post("/submissions/{submission_id}/review-decisions")
def record_review_decision(
    submission_id: str,
    decision: str = Form(...),
    reviewer: str = Form(...),
    notes: str = Form(""),
    x_stegverse_hil_review_token: str | None = Header(default=None),
) -> dict:
    _review_token_required(x_stegverse_hil_review_token)
    if decision not in REVIEW_DECISIONS:
        raise HTTPException(status_code=400, detail="hil_review_decision_invalid")
    reviewer = reviewer.strip()
    if not reviewer:
        raise HTTPException(status_code=400, detail="hil_reviewer_required")
    reviewed_at = datetime.now(timezone.utc).isoformat()
    review_id = f"HIL-REVIEW-{uuid4().hex[:16].upper()}"
    authority = {
        "execution": False,
        "public_acceptance": False,
        "publication": False,
        "master_record_append": False,
    }
    receipt_core = {
        "schema_version": "HIL-PRIVATE-REVIEW-RECEIPT-v1",
        "review_id": review_id,
        "submission_id": submission_id,
        "reviewed_at": reviewed_at,
        "reviewer": reviewer,
        "decision": decision,
        "notes": notes.strip(),
        "authority": authority,
    }
    receipt_core["review_receipt_sha256"] = _canonical_hash(receipt_core)
    with _connect() as connection:
        exists = connection.execute(
            "SELECT 1 FROM submissions WHERE submission_id = ?", (submission_id,)
        ).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="hil_submission_not_found")
        prior = connection.execute(
            "SELECT 1 FROM submission_reviews WHERE submission_id = ?", (submission_id,)
        ).fetchone()
        if prior is not None:
            raise HTTPException(status_code=409, detail="hil_review_already_recorded")
        connection.execute(
            "INSERT INTO submission_reviews VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                review_id,
                submission_id,
                reviewed_at,
                reviewer,
                decision,
                notes.strip(),
                receipt_core["review_receipt_sha256"],
                json.dumps(authority, sort_keys=True),
            ),
        )
        connection.execute(
            "UPDATE submissions SET validation_state = ? WHERE submission_id = ?",
            (decision, submission_id),
        )
    return receipt_core
