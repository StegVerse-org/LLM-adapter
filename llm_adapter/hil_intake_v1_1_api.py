"""Governed HIL v1.1 intake with optional participant metadata."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response

from llm_adapter.hil_intr_interlock import (
    HILInTrError,
    build_egress_envelope,
    build_hop_receipt,
    build_receipt_chain,
    validate_ingress_envelope,
)

router = APIRouter(prefix="/api/hil", tags=["hil-intake-v1.1"])
PRIMARY_SHA256 = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PRIMARY_VERSION = "v1.1"
PROTOCOL_VERSION = "HIL-PROTOCOL-v1.1"
PROMPT_VERSION = "HIL-PROMPT-v1.1"
PROMPT_SHA256 = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"
PROVENANCE_VERSION = "HIL-RESPONSE-PROVENANCE-v1.1"
MAX_BYTES = 10 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
MAX_INTR_ENVELOPE_BYTES = 32 * 1024
ACTIVE_MARKERS = (b"/JavaScript", b"/JS", b"/Launch", b"/EmbeddedFile", b"/OpenAction")
REVIEW_DECISIONS = {"ACCEPT_PRIVATE", "QUARANTINE", "REJECT"}
PUBLICATION_CONSENTS = {"public", "anonymous", "private", "not_provided"}


def _enabled() -> bool:
    return os.getenv("STEGVERSE_HIL_INTAKE_ENABLED", "false").strip().lower() == "true"


def _data_dir() -> Path:
    return Path(os.getenv("STEGVERSE_HIL_DATA_DIR", "/tmp/stegverse-hil")).resolve()


def _canonical_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _connect() -> sqlite3.Connection:
    root = _data_dir()
    root.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(root / "hil-intake.db")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(
        """CREATE TABLE IF NOT EXISTS submissions (
        submission_id TEXT PRIMARY KEY, received_at TEXT NOT NULL,
        participant_identifier TEXT NOT NULL, publication_consent TEXT NOT NULL,
        primary_sha256 TEXT NOT NULL, submitted_file_sha256 TEXT NOT NULL,
        provenance_manifest_sha256 TEXT NOT NULL, chain_validation_state TEXT NOT NULL,
        size_bytes INTEGER NOT NULL, storage_path TEXT NOT NULL, manifest_path TEXT NOT NULL,
        validation_state TEXT NOT NULL, active_content_state TEXT NOT NULL,
        authority_json TEXT NOT NULL)"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS submission_reviews (
        review_id TEXT PRIMARY KEY, submission_id TEXT NOT NULL UNIQUE,
        reviewed_at TEXT NOT NULL, reviewer TEXT NOT NULL, decision TEXT NOT NULL,
        notes TEXT NOT NULL, review_receipt_sha256 TEXT NOT NULL,
        authority_json TEXT NOT NULL,
        FOREIGN KEY(submission_id) REFERENCES submissions(submission_id))"""
    )
    return connection


def _review_token_required(token: str | None) -> None:
    expected = os.getenv("STEGVERSE_HIL_REVIEW_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="hil_review_not_configured")
    if not token or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="hil_review_forbidden")


def _submission_row(submission_id: str) -> sqlite3.Row:
    with _connect() as connection:
        submission = connection.execute(
            "SELECT submission_id, received_at, participant_identifier, publication_consent, primary_sha256, submitted_file_sha256, provenance_manifest_sha256, chain_validation_state, size_bytes, storage_path, manifest_path, validation_state, active_content_state, authority_json FROM submissions WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
    if submission is None:
        raise HTTPException(status_code=404, detail="hil_submission_not_found")
    return submission


def readiness() -> dict:
    blockers: list[str] = []
    if not _enabled():
        blockers.append("hil_intake_disabled")
    if not _data_dir().is_absolute():
        blockers.append("hil_data_dir_must_be_absolute")
    if os.getenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "false").lower() != "true":
        blockers.append("durable_storage_not_declared")
    return {
        "schema": "stegverse.hil_intake_readiness.v3",
        "state": "READY" if not blockers else "CONFIGURATION_REQUIRED",
        "blockers": blockers,
        "maximum_size_bytes": MAX_BYTES,
        "accepted_media_type": "application/pdf",
        "provenance_manifest_required": True,
        "provenance_manifest_schema": PROVENANCE_VERSION,
        "participant_metadata_required": False,
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
    expected = {
        "schema_version": PROVENANCE_VERSION,
        "primary_version": PRIMARY_VERSION,
        "primary_sha256": PRIMARY_SHA256,
        "protocol_version": PROTOCOL_VERSION,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": PROMPT_SHA256,
        "response_sha256": response_sha256,
    }
    for field, value in expected.items():
        if manifest.get(field) != value:
            raise HTTPException(status_code=400, detail=f"provenance_{field}_mismatch")
    signature = manifest.get("producer_signature") or {
        "state": "UNAVAILABLE", "scheme": None, "value": None, "key_id": None
    }
    if not isinstance(signature, dict) or signature.get("state") not in {"UNAVAILABLE", "DECLARED", "VERIFIED"}:
        raise HTTPException(status_code=400, detail="producer_signature_invalid")
    normalized = dict(manifest)
    normalized["model"] = manifest.get("model") or None
    normalized["provider"] = manifest.get("provider") or None
    normalized["conversation_reference"] = manifest.get("conversation_reference") or None
    normalized["producer_signature"] = signature
    return normalized


@router.post("/submissions")
async def submit_response(
    response_pdf: UploadFile = File(...),
    provenance_manifest: UploadFile = File(...),
    intr_ingress_envelope: UploadFile = File(...),
    participant_identifier: str = Form("not_provided"),
    publication_consent: str = Form("not_provided"),
    primary_sha256: str = Form(...),
    prompt_sha256: str | None = Form(None),
    model_response_declared_unedited: bool = Form(False),
    participant_consent_authority_acknowledged: bool = Form(False),
) -> dict:
    if not _enabled():
        raise HTTPException(status_code=503, detail="hil_intake_disabled")
    if publication_consent not in PUBLICATION_CONSENTS:
        raise HTTPException(status_code=400, detail="invalid_publication_consent")
    if primary_sha256 != PRIMARY_SHA256:
        raise HTTPException(status_code=400, detail="primary_sha256_mismatch")
    if prompt_sha256 is not None and prompt_sha256 != PROMPT_SHA256:
        raise HTTPException(status_code=400, detail="prompt_sha256_mismatch")

    data = await response_pdf.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="response_pdf_size_invalid")
    if not data.startswith(b"%PDF-"):
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

    ingress_bytes = await intr_ingress_envelope.read(MAX_INTR_ENVELOPE_BYTES + 1)
    if not ingress_bytes or len(ingress_bytes) > MAX_INTR_ENVELOPE_BYTES:
        raise HTTPException(status_code=413, detail="hil_intr_ingress_envelope_size_invalid")
    try:
        ingress_envelope = json.loads(ingress_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="hil_intr_ingress_envelope_json_invalid") from exc
    if not isinstance(ingress_envelope, dict):
        raise HTTPException(status_code=400, detail="hil_intr_ingress_envelope_shape_invalid")
    try:
        ingress_envelope = validate_ingress_envelope(
            ingress_envelope,
            response_sha256=digest,
            provenance_sha256=manifest_sha256,
        )
    except HILInTrError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    signature_state = manifest["producer_signature"]["state"]
    chain_state = "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED"
    if signature_state == "VERIFIED":
        chain_state = "PRIMARY_PROMPT_RESPONSE_SIGNATURE_CHAIN_VERIFIED"

    received_at = datetime.now(timezone.utc).isoformat()
    submission_id = f"HIL-INTAKE-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:12].upper()}"
    root = _data_dir()
    originals, manifests = root / "originals", root / "provenance"
    originals.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    path, manifest_path = originals / f"{submission_id}.pdf", manifests / f"{submission_id}.json"
    path.write_bytes(data)
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    authority = {"execution": False, "acceptance": False, "publication": False, "master_record_append": False}
    participant_identifier = participant_identifier.strip() or "not_provided"
    with _connect() as connection:
        connection.execute(
            "INSERT INTO submissions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (submission_id, received_at, participant_identifier, publication_consent,
             primary_sha256, digest, manifest_sha256, chain_state, len(data), str(path),
             str(manifest_path), "RECEIVED_PENDING_REVIEW", "ABSENT", json.dumps(authority, sort_keys=True)),
        )

    # Do not advertise durable custody or registry admission until the persisted row
    # can be independently re-read after the transaction has committed.
    persisted_submission = _submission_row(submission_id)
    if persisted_submission["submitted_file_sha256"] != digest:
        raise HTTPException(status_code=500, detail="hil_submission_registry_hash_mismatch")
    if Path(persisted_submission["storage_path"]).resolve() != path.resolve() or not path.is_file():
        raise HTTPException(status_code=500, detail="hil_submission_persistence_verification_failed")

    device_ingress_receipt = build_hop_receipt(
        ingress_envelope=ingress_envelope,
        hop_index=1,
        from_role="DEVICE",
        to_role="HIL_INGRESS",
        boundary_identity_ref=f"stegverse://hil/ingress/{submission_id}",
        prior_receipt_hash=None,
        recorded_at=received_at,
    )
    custody_receipt = build_hop_receipt(
        ingress_envelope=ingress_envelope,
        hop_index=2,
        from_role="HIL_INGRESS",
        to_role="HIL_CUSTODY",
        boundary_identity_ref=f"stegverse://hil/custody/{submission_id}",
        prior_receipt_hash=device_ingress_receipt["receipt_hash"],
        recorded_at=datetime.now(timezone.utc).isoformat(),
    )
    tvc_egress_envelope = build_egress_envelope(
        ingress_envelope=ingress_envelope,
        submission_id=submission_id,
        custody_receipt_hash=custody_receipt["receipt_hash"],
    )
    intr_chain = build_receipt_chain(
        ingress_envelope=ingress_envelope,
        ingress_receipt=device_ingress_receipt,
        custody_receipt=custody_receipt,
        egress_envelope=tvc_egress_envelope,
    )
    intr_root = root / "intr-receipts"
    intr_root.mkdir(parents=True, exist_ok=True)
    intr_path = intr_root / f"{submission_id}.json"
    intr_path.write_text(json.dumps(intr_chain, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    persisted_intr_chain = json.loads(intr_path.read_text(encoding="utf-8"))
    if persisted_intr_chain.get("chain_hash") != intr_chain["chain_hash"]:
        raise HTTPException(status_code=500, detail="hil_intr_receipt_chain_persistence_failed")

    receipt = {
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
        "custody_state": "EXACT_BYTES_PERSISTED",
        "registry_state": "RECORDED",
        "publication_state": "NOT_AUTHORIZED",
        "participant_metadata_state": "PROVIDED" if participant_identifier != "not_provided" else "NOT_PROVIDED",
        "participant_declarations": {
            "model_response_declared_unedited": model_response_declared_unedited,
            "participant_consent_authority_acknowledged": participant_consent_authority_acknowledged,
        },
        "response_id": None,
        "master_record_release": None,
        "previous_receipt_sha256": None,
        "intr_receipt_chain": intr_chain,
        "next_required_transition": "HIL_CUSTODY_TVC_INTERLOCK_ADMISSION",
        "authority": authority,
        "notes": [
            "Submit initiated a governed InTr ingress Interlock; the receiver issued the DEVICE->HIL_INGRESS receipt only after validating the transported packet.",
            "HIL custody is a second chained Interlock receipt whose prior hash binds the ingress receipt.",
            "A TVC-bound egress Interlock envelope is persisted automatically; TVC admission is not claimed until TVC returns its own chained receipt.",
            "Exact uploaded PDF bytes and provenance manifest persisted before receipt issuance.",
            "Submission registry row re-read successfully before RECORDED was asserted.",
            "Participant metadata and publication permission are optional at intake.",
            "Missing optional metadata does not imply consent, attribution, or publication authority.",
            "Review, acceptance, publication, and Master Record append remain pending.",
        ],
    }
    receipt["receipt_sha256"] = _canonical_hash(receipt)
    return receipt


@router.get("/submissions/{submission_id}/status")
def get_submission_status(submission_id: str) -> dict:
    """Expose stable, non-sensitive post-submit evidence without private metadata."""
    if not _enabled():
        raise HTTPException(status_code=503, detail="hil_intake_disabled")
    submission = _submission_row(submission_id)
    intr_path = _data_dir() / "intr-receipts" / f"{submission_id}.json"
    intr_chain = None
    if intr_path.is_file():
        try:
            intr_chain = json.loads(intr_path.read_text(encoding="utf-8"))
        except Exception:
            intr_chain = None
    return {
        "schema_version": "HIL-SUBMISSION-STATUS-v1",
        "submission_id": submission["submission_id"],
        "received_at": submission["received_at"],
        "primary_version": PRIMARY_VERSION,
        "primary_sha256": submission["primary_sha256"],
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": PROMPT_SHA256,
        "submitted_file_sha256": submission["submitted_file_sha256"],
        "provenance_manifest_sha256": submission["provenance_manifest_sha256"],
        "chain_validation_state": submission["chain_validation_state"],
        "size_bytes": submission["size_bytes"],
        "validation_state": submission["validation_state"],
        "active_content_state": submission["active_content_state"],
        "custody_state": "EXACT_BYTES_PERSISTED",
        "registry_state": "RECORDED",
        "intr_chain_state": "PERSISTED" if isinstance(intr_chain, dict) else "MISSING_FAIL_CLOSED",
        "intr_chain_hash": intr_chain.get("chain_hash") if isinstance(intr_chain, dict) else None,
        "next_required_transition": intr_chain.get("next_required_transition") if isinstance(intr_chain, dict) else None,
        "artifact_bytes_exposed": False,
        "participant_metadata_exposed": False,
        "storage_paths_exposed": False,
        "authority": {
            "execution": False,
            "acceptance": False,
            "publication": False,
            "master_record_append": False,
        },
    }


@router.get("/submissions/{submission_id}/exact-bytes")
def get_submission_exact_bytes(
    submission_id: str,
    x_stegverse_hil_review_token: str | None = Header(default=None),
) -> Response:
    """Reconstruct and verify the exact submitted PDF under existing TV/TVC review auth."""
    if not _enabled():
        raise HTTPException(status_code=503, detail="hil_intake_disabled")
    _review_token_required(x_stegverse_hil_review_token)
    submission = _submission_row(submission_id)

    originals_root = (_data_dir() / "originals").resolve()
    storage_path = Path(submission["storage_path"]).resolve()
    if not storage_path.is_relative_to(originals_root):
        raise HTTPException(status_code=409, detail="hil_exact_bytes_storage_boundary_mismatch")
    if not storage_path.is_file():
        raise HTTPException(status_code=409, detail="hil_exact_bytes_missing")

    data = storage_path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != submission["submitted_file_sha256"]:
        raise HTTPException(status_code=409, detail="hil_exact_bytes_hash_mismatch")
    if len(data) != submission["size_bytes"]:
        raise HTTPException(status_code=409, detail="hil_exact_bytes_size_mismatch")

    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "X-SteGVerse-HIL-Submission-ID": submission_id,
            "X-SteGVerse-HIL-Submitted-SHA256": digest,
            "X-SteGVerse-HIL-Reconstruction-State": "EXACT_BYTES_HASH_VERIFIED",
            "Cache-Control": "no-store",
        },
    )


@router.get("/submissions/{submission_id}/review-state")
def get_review_state(submission_id: str, x_stegverse_hil_review_token: str | None = Header(default=None)) -> dict:
    _review_token_required(x_stegverse_hil_review_token)
    with _connect() as connection:
        submission = connection.execute(
            "SELECT submission_id, received_at, participant_identifier, publication_consent, primary_sha256, submitted_file_sha256, provenance_manifest_sha256, chain_validation_state, size_bytes, validation_state, active_content_state FROM submissions WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
        if submission is None:
            raise HTTPException(status_code=404, detail="hil_submission_not_found")
        review = connection.execute(
            "SELECT review_id, reviewed_at, reviewer, decision, notes, review_receipt_sha256 FROM submission_reviews WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
    return {
        "schema_version": "HIL-PRIVATE-REVIEW-STATE-v1",
        "submission": dict(submission),
        "review": dict(review) if review else None,
        "artifact_bytes_exposed": False,
        "storage_paths_exposed": False,
        "authority": {"execution": False, "publication": False, "master_record_append": False},
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
    authority = {"execution": False, "public_acceptance": False, "publication": False, "master_record_append": False}
    receipt = {
        "schema_version": "HIL-PRIVATE-REVIEW-RECEIPT-v1",
        "review_id": review_id,
        "submission_id": submission_id,
        "reviewed_at": reviewed_at,
        "reviewer": reviewer,
        "decision": decision,
        "notes": notes.strip(),
        "authority": authority,
    }
    receipt["review_receipt_sha256"] = _canonical_hash(receipt)
    with _connect() as connection:
        if connection.execute("SELECT 1 FROM submissions WHERE submission_id = ?", (submission_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="hil_submission_not_found")
        if connection.execute("SELECT 1 FROM submission_reviews WHERE submission_id = ?", (submission_id,)).fetchone() is not None:
            raise HTTPException(status_code=409, detail="hil_review_already_recorded")
        connection.execute(
            "INSERT INTO submission_reviews VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (review_id, submission_id, reviewed_at, reviewer, decision, notes.strip(), receipt["review_receipt_sha256"], json.dumps(authority, sort_keys=True)),
        )
        connection.execute("UPDATE submissions SET validation_state = ? WHERE submission_id = ?", (decision, submission_id))
    return receipt
