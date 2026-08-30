"""Governed HIL v1.1 intake with optional participant metadata."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from llm_adapter.generated_intr import hil_submission_connector as canonical_intr
from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response

router = APIRouter(prefix="/api/hil", tags=["hil-intake-v1.1"])
PRIMARY_SHA256 = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PRIMARY_VERSION = "v1.1"
PROTOCOL_VERSION = "HIL-PROTOCOL-v1.1"
PROMPT_VERSION = "HIL-PROMPT-v1.1"
PROMPT_SHA256 = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"
PROVENANCE_VERSION = "HIL-RESPONSE-PROVENANCE-v1.1"
MAX_BYTES = 10 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
ACTIVE_MARKERS = (b"/JavaScript", b"/JS", b"/Launch", b"/EmbeddedFile", b"/OpenAction")
REVIEW_DECISIONS = {"ACCEPT_PRIVATE", "QUARANTINE", "REJECT"}
PUBLICATION_CONSENTS = {"public", "anonymous", "private", "not_provided"}

HIL_INTR_CHAIN_SCHEMA = "stegverse.hil.intr_receipt_chain/v2"
HIL_TVC_QUEUE_SCHEMA = "stegverse.hil.tvc_interlock_queue/v1"


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _digest_uri(value: Any) -> str:
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
    else:
        raw = _canonical_json_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _build_profile_intent(
    profile_id: str,
    payload_binding: Mapping[str, Any],
    *,
    operation: str,
    operation_id: str,
    prior_receipt_hash: str | None,
) -> dict[str, Any]:
    return canonical_intr.build_intent(
        profile_id,
        _canonical_json_bytes(dict(payload_binding)),
        operation=operation,
        operation_id=operation_id,
        prior_receipt_hash=prior_receipt_hash,
    )


def _validate_ingress_transport_intent(
    intent: Mapping[str, Any],
    *,
    expected_payload_binding: Mapping[str, Any],
) -> None:
    operation_id = intent.get("operation_id")
    if not isinstance(operation_id, str) or not operation_id:
        raise HTTPException(status_code=400, detail="intr_transport_operation_id_invalid")
    expected = _build_profile_intent(
        "hil-submission",
        expected_payload_binding,
        operation="SUBMIT",
        operation_id=operation_id,
        prior_receipt_hash=None,
    )
    comparisons = (
        ("schema", "intr_transport_intent_schema_invalid"),
        ("protocol", "intr_transport_intent_schema_invalid"),
        ("payload_hash", "intr_transport_payload_hash_mismatch"),
        ("prior_transport_receipt_hash", "intr_transport_prior_receipt_mismatch"),
        ("source", "intr_transport_source_invalid"),
        ("destination", "intr_transport_destination_invalid"),
        ("boundary_path", "intr_transport_boundary_path_invalid"),
        ("interlock_required", "intr_interlock_required"),
        ("transport_semantics", "intr_transport_semantics_invalid"),
        ("authority", "intr_transport_authority_invalid"),
        ("receipt_chain", "intr_transport_receipt_policy_invalid"),
        ("packet_id", "intr_transport_packet_id_invalid"),
    )
    for field, detail in comparisons:
        if intent.get(field) != expected[field]:
            raise HTTPException(status_code=400, detail=detail)


def _hil_payload_binding(response_sha256: str, provenance_sha256_uri: str) -> dict[str, Any]:
    return {
        "schema": "stegverse.hil.intr_payload_binding/v1",
        "protocol": PROTOCOL_VERSION,
        "response_sha256": "sha256:" + response_sha256,
        "provenance_sha256": provenance_sha256_uri,
        "primary_sha256": "sha256:" + PRIMARY_SHA256,
        "prompt_sha256": "sha256:" + PROMPT_SHA256,
    }


def _persist_interlock_lineage(
    *,
    submission_id: str,
    root: Path,
    ingress_intent: Mapping[str, Any],
    payload_binding: Mapping[str, Any],
    payload_hash: str,
    recorded_at: str,
    storage_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    binding_bytes = _canonical_json_bytes(dict(payload_binding))
    ingress_receipt = canonical_intr.build_receipt(
        ingress_intent,
        hop_index=1,
        receipt_id=f"HIL-INTR-INGRESS-{uuid4().hex[:16].upper()}",
        boundary_identity_ref="stegverse://StegOS/HIL/Ingress",
        recorded_at=recorded_at,
        prior_receipt_hash=ingress_intent.get("prior_transport_receipt_hash"),
        transition_state="RECEIVED",
    )
    canonical_intr.validate_complete(ingress_intent, [ingress_receipt])
    custody_intent = canonical_intr.build_intent(
        "hil-ingress-custody",
        binding_bytes,
        operation="ACCEPT_CUSTODY",
        operation_id=f"{ingress_intent['operation_id']}:HIL_CUSTODY",
        prior_receipt_hash=ingress_receipt["receipt_hash"],
    )
    custody_receipt = canonical_intr.build_receipt(
        custody_intent,
        hop_index=1,
        receipt_id=f"HIL-INTR-CUSTODY-{uuid4().hex[:16].upper()}",
        boundary_identity_ref="stegverse://StegOS/HIL/Custody",
        recorded_at=recorded_at,
        prior_receipt_hash=ingress_receipt["receipt_hash"],
        transition_state="RECEIVED",
    )
    canonical_intr.validate_complete(custody_intent, [custody_receipt])
    next_intent = canonical_intr.build_intent(
        "hil-tvc-lifecycle",
        binding_bytes,
        operation="ADMIT_LIFECYCLE",
        operation_id=f"{ingress_intent['operation_id']}:TVC_HIL_LIFECYCLE",
        prior_receipt_hash=custody_receipt["receipt_hash"],
    )
    chain_body = {
        "schema": HIL_INTR_CHAIN_SCHEMA,
        "submission_id": submission_id,
        "payload_hash": payload_hash,
        "ingress_transport_intent": dict(ingress_intent),
        "device_stegos_ingress_receipt": ingress_receipt,
        "hil_custody_transport_intent": custody_intent,
        "hil_custody_interlock_receipt": custody_receipt,
        "next_interlock_intent": next_intent,
        "next_required_transition": "HIL_CUSTODY_TVC_INTERLOCK_ADMISSION",
        "authority_transfer": False,
    }
    chain = {**chain_body, "chain_hash": _digest_uri(chain_body)}

    interlock_dir = root / "interlock"
    queue_dir = root / "intr-outbox" / "tvc-hil-lifecycle"
    interlock_dir.mkdir(parents=True, exist_ok=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    chain_path = interlock_dir / f"{submission_id}.json"
    queue_path = queue_dir / f"{submission_id}.json"
    chain_path.write_bytes(_canonical_json_bytes(chain) + b"\n")

    receiver_receipt_path = root / "receiver-receipts" / f"{submission_id}.json"
    queue_body = {
        "schema": HIL_TVC_QUEUE_SCHEMA,
        "state": "READY_FOR_INTERLOCK_ADMISSION",
        "submission_id": submission_id,
        "payload_hash": payload_hash,
        "prior_receipt_hash": custody_receipt["receipt_hash"],
        "transport_intent": next_intent,
        "response_artifact_ref": str(storage_path),
        "provenance_artifact_ref": str(manifest_path),
        "receiver_receipt_ref": str(receiver_receipt_path),
        "transport_protocol": "InTr",
        "interlock_required": True,
        "authority_transfer": False,
        "tvc_admission_completed": False,
        "blind_consequence_retry_allowed": False,
    }
    queue = {**queue_body, "queue_hash": _digest_uri(queue_body)}
    queue_path.write_bytes(_canonical_json_bytes(queue) + b"\n")

    if json.loads(chain_path.read_text(encoding="utf-8")) != chain:
        raise HTTPException(status_code=500, detail="hil_intr_chain_persistence_verification_failed")
    if json.loads(queue_path.read_text(encoding="utf-8")) != queue:
        raise HTTPException(status_code=500, detail="hil_tvc_interlock_queue_persistence_verification_failed")
    return {
        "chain": chain,
        "queue_hash": queue["queue_hash"],
        "receiver_receipt_path": receiver_receipt_path,
    }




def _persist_receiver_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    """Persist the exact receiver-issued receipt write-once before HTTP success."""
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = _canonical_json_bytes(dict(receipt)) + b"\n"
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=500, detail="hil_receiver_receipt_existing_unreadable") from exc
        if existing != dict(receipt):
            raise HTTPException(status_code=409, detail="hil_receiver_receipt_write_once_collision")
        return
    path.write_bytes(serialized)
    try:
        reread = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="hil_receiver_receipt_persistence_verification_failed") from exc
    if reread != dict(receipt):
        raise HTTPException(status_code=500, detail="hil_receiver_receipt_persistence_verification_failed")



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
    intr_transport_intent: UploadFile = File(...),
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
    provenance_sha256_uri = _digest_uri(manifest)
    payload_binding = _hil_payload_binding(digest, provenance_sha256_uri)
    payload_hash = _digest_uri(payload_binding)

    intent_bytes = await intr_transport_intent.read(MAX_MANIFEST_BYTES + 1)
    if not intent_bytes or len(intent_bytes) > MAX_MANIFEST_BYTES:
        raise HTTPException(status_code=413, detail="intr_transport_intent_size_invalid")
    try:
        ingress_intent = json.loads(intent_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="intr_transport_intent_json_invalid") from exc
    if not isinstance(ingress_intent, dict):
        raise HTTPException(status_code=400, detail="intr_transport_intent_shape_invalid")
    _validate_ingress_transport_intent(
        ingress_intent,
        expected_payload_binding=payload_binding,
    )

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

    intr_lineage = _persist_interlock_lineage(
        submission_id=submission_id,
        root=root,
        ingress_intent=ingress_intent,
        payload_binding=payload_binding,
        payload_hash=payload_hash,
        recorded_at=received_at,
        storage_path=path,
        manifest_path=manifest_path,
    )

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
        "intr_receipt_chain": intr_lineage["chain"],
        "intr_tvc_queue_hash": intr_lineage["queue_hash"],
        "next_required_transition": "HIL_CUSTODY_TVC_INTERLOCK_ADMISSION",
        "transport_initiated_by_submission": True,
        "always_on_application_receiver_required": False,
        "second_user_device_required": False,
        "authority": authority,
        "notes": [
            "Exact uploaded PDF bytes and provenance manifest persisted before receipt issuance.",
            "Submission registry row re-read successfully before RECORDED was asserted.",
            "Participant metadata and publication permission are optional at intake.",
            "Missing optional metadata does not imply consent, attribution, or publication authority.",
            "Review, acceptance, publication, and Master Record append remain pending.",
            "Submit initiated the canonical DEVICE_SYSTEM -> STEGOS_ECOSYSTEM Interlock/InTr transport.",
            "The receiver persisted a chained HIL custody Interlock receipt and queued the next TVC lifecycle Interlock intent.",
        ],
    }
    receipt["receipt_sha256"] = _canonical_hash(receipt)
    _persist_receiver_receipt(intr_lineage["receiver_receipt_path"], receipt)
    return receipt


@router.get("/submissions/{submission_id}/status")
def get_submission_status(submission_id: str) -> dict:
    """Expose stable, non-sensitive post-submit evidence without private metadata."""
    if not _enabled():
        raise HTTPException(status_code=503, detail="hil_intake_disabled")
    submission = _submission_row(submission_id)
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
