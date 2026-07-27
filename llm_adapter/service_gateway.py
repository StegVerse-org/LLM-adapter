from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

SCHEMA = "HIL-RECEIVER-RECEIPT-v2"
SERVICE_ID = "stegverse-service-gateway"
INTAKE_ROLE = "service_gateway_intake"
INTAKE_KEYS = {
    "service-gateway/hil-intake/storage-root",
    "service-gateway/hil-intake/receipt-key",
}
PRIMARY_VERSION = "v1.1"
PRIMARY_SHA256 = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROTOCOL_VERSION = "HIL-PROTOCOL-v1.1"
PROMPT_VERSION = "HIL-PROMPT-v1.1"
PROMPT_SHA256 = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"
PROVENANCE_SCHEMA = "HIL-RESPONSE-PROVENANCE-v1.1"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_tag(value: bytes) -> str:
    return "sha256:" + sha256_hex(value)


def _load_tvc_receipt() -> Dict[str, Any]:
    raw = os.getenv("STEGVERSE_TVC_DECISION_RECEIPT", "").strip()
    receipt_path = os.getenv("STEGVERSE_TVC_DECISION_RECEIPT_FILE", "").strip()
    if not raw and receipt_path:
        raw = Path(receipt_path).read_text(encoding="utf-8")
    if not raw:
        raise RuntimeError("tvc_decision_receipt_missing")
    receipt = json.loads(raw)
    if receipt.get("role") != INTAKE_ROLE:
        raise RuntimeError("tvc_role_mismatch")
    if receipt.get("admissible") is not True or receipt.get("binding_matched") is not True:
        raise RuntimeError("tvc_intake_not_admissible")
    allowed = set(receipt.get("allowed_keys") or [])
    denied = set(receipt.get("denied_keys") or [])
    if allowed != INTAKE_KEYS or denied:
        raise RuntimeError("tvc_intake_scope_invalid")
    return receipt


def _runtime() -> Dict[str, Any]:
    tvc = _load_tvc_receipt()
    root = Path(os.environ["STEGVERSE_HIL_STORAGE_ROOT"]).expanduser().resolve()
    key = os.environ["STEGVERSE_HIL_RECEIPT_KEY"].encode("utf-8")
    if len(key) < 32:
        raise RuntimeError("receipt_key_too_short")
    root.mkdir(parents=True, exist_ok=True)
    (root / "packets").mkdir(exist_ok=True)
    (root / "receipts").mkdir(exist_ok=True)
    return {"root": root, "key": key, "tvc": tvc}


def _sign_receipt(receipt: Dict[str, Any], key: bytes) -> Dict[str, Any]:
    receipt["receipt_sha256"] = sha256_hex(canonical_json(receipt))
    receipt["receiver_signature"] = "hmac-sha256:" + hmac.new(
        key, canonical_json(receipt), hashlib.sha256
    ).hexdigest()
    return receipt


app = FastAPI(title="StegVerse Service Gateway", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://stegverse-labs.github.io",
        "https://stegverse.org",
        "https://www.stegverse.org",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service_id": SERVICE_ID, "time": utc_now()}


@app.get("/ready")
def ready() -> Dict[str, Any]:
    try:
        runtime = _runtime()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "status": "ready",
        "service_id": SERVICE_ID,
        "protocol": SCHEMA,
        "adapter": "hil-intake",
        "durable_storage": True,
        "tvc_decision_id": runtime["tvc"].get("decision_id"),
        "accepted_media_types": ["application/pdf"],
    }


@app.get("/api/hil/readiness")
def hil_readiness() -> Dict[str, Any]:
    try:
        runtime = _runtime()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "state": "READY",
        "service_id": SERVICE_ID,
        "primary_version": PRIMARY_VERSION,
        "primary_sha256": PRIMARY_SHA256,
        "protocol_version": PROTOCOL_VERSION,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": PROMPT_SHA256,
        "provenance_manifest_required": True,
        "provenance_manifest_schema": PROVENANCE_SCHEMA,
        "participant_metadata_required": False,
        "durable_storage": True,
        "tvc_decision_id": runtime["tvc"].get("decision_id"),
    }


async def _persist_packet(
    *, runtime: Dict[str, Any], packet_id: str, upload: UploadFile, metadata: Dict[str, Any]
) -> tuple[str, int, Path]:
    packet_dir = runtime["root"] / "packets" / packet_id
    receipt_path = runtime["root"] / "receipts" / f"{packet_id}.json"
    if packet_dir.exists():
        if receipt_path.exists():
            return "duplicate", 0, receipt_path
        raise HTTPException(status_code=409, detail="packet_exists_without_receipt")
    packet_dir.mkdir(parents=False)
    tmp_path = Path(tempfile.mkstemp(prefix="upload-", suffix=".pdf", dir=packet_dir)[1])
    digest = hashlib.sha256()
    size = 0
    try:
        with tmp_path.open("wb") as output:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > 100 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="document_too_large")
                digest.update(chunk)
                output.write(chunk)
        with tmp_path.open("rb") as source:
            if source.read(5) != b"%PDF-":
                raise HTTPException(status_code=422, detail="invalid_pdf_signature")
        document_hash = digest.hexdigest()
        declared_hash = metadata.get("response_sha256") or metadata.get("document_hash") or metadata.get("content_hash")
        if declared_hash:
            declared_hash = str(declared_hash).removeprefix("sha256:")
            if declared_hash != document_hash:
                raise HTTPException(status_code=422, detail="document_hash_mismatch")
        tmp_path.replace(packet_dir / "document.pdf")
        (packet_dir / "metadata.json").write_bytes(canonical_json(metadata) + b"\n")
        return document_hash, size, receipt_path
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        if packet_dir.exists() and not any(packet_dir.iterdir()):
            packet_dir.rmdir()
        raise


@app.post("/v1/hil/intake")
async def hil_intake(document: UploadFile = File(...), metadata: str = Form(...)) -> Dict[str, Any]:
    try:
        runtime = _runtime()
        meta = json.loads(metadata)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    packet_id = str(meta.get("packet_id") or uuid.uuid4())
    result, size, receipt_path = await _persist_packet(
        runtime=runtime, packet_id=packet_id, upload=document, metadata=meta
    )
    if result == "duplicate":
        return json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt: Dict[str, Any] = {
        "schema": SCHEMA,
        "service_id": SERVICE_ID,
        "status": "SUBMISSION_ACCEPTED",
        "packet_id": packet_id,
        "received_at": utc_now(),
        "document_hash": "sha256:" + result,
        "metadata_hash": sha256_tag(canonical_json(meta)),
        "document_size_bytes": size,
        "storage_class": "durable-local",
        "tvc_decision_id": runtime["tvc"].get("decision_id"),
        "tvc_policy_hash": runtime["tvc"].get("policy_hash"),
        "provider_processing": "not_required_for_acceptance",
        "master_records_custody": "queued_separately",
    }
    receipt["receipt_hash"] = sha256_tag(canonical_json(receipt))
    receipt["signature"] = "hmac-sha256:" + hmac.new(
        runtime["key"], canonical_json(receipt), hashlib.sha256
    ).hexdigest()
    receipt_path.write_bytes(canonical_json(receipt) + b"\n")
    return receipt


@app.post("/api/hil/submissions")
async def site_hil_submission(
    response_pdf: UploadFile = File(...),
    provenance_manifest: UploadFile = File(...),
    participant_identifier: str = Form("not_provided"),
    publication_consent: str = Form("not_provided"),
    primary_sha256: str = Form(...),
    prompt_sha256: str = Form(...),
    model_response_declared_unedited: str = Form("false"),
    participant_consent_authority_acknowledged: str = Form("false"),
) -> Dict[str, Any]:
    try:
        runtime = _runtime()
        manifest = json.loads((await provenance_manifest.read()).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if primary_sha256 != PRIMARY_SHA256 or prompt_sha256 != PROMPT_SHA256:
        raise HTTPException(status_code=422, detail="primary_or_prompt_hash_mismatch")
    if manifest.get("schema_version") != PROVENANCE_SCHEMA:
        raise HTTPException(status_code=422, detail="provenance_schema_mismatch")
    if manifest.get("primary_sha256") != PRIMARY_SHA256 or manifest.get("prompt_sha256") != PROMPT_SHA256:
        raise HTTPException(status_code=422, detail="provenance_chain_mismatch")
    response_hash = str(manifest.get("response_sha256") or "")
    if len(response_hash) != 64:
        raise HTTPException(status_code=422, detail="response_hash_missing")
    submission_id = f"HIL-SUBMISSION-{response_hash[:16].upper()}"
    result, size, receipt_path = await _persist_packet(
        runtime=runtime,
        packet_id=submission_id,
        upload=response_pdf,
        metadata={
            **manifest,
            "participant_identifier": participant_identifier,
            "publication_consent": publication_consent,
            "model_response_declared_unedited": model_response_declared_unedited,
            "participant_consent_authority_acknowledged": participant_consent_authority_acknowledged,
        },
    )
    if result == "duplicate":
        return json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "receipt_id": f"HIL-RECEIPT-{uuid.uuid4().hex[:16].upper()}",
        "submission_id": submission_id,
        "received_at": utc_now(),
        "primary_sha256": PRIMARY_SHA256,
        "prompt_sha256": PROMPT_SHA256,
        "submitted_file_sha256": result,
        "provenance_manifest_sha256": sha256_hex(canonical_json(manifest)),
        "submitted_file_size_bytes": size,
        "chain_validation_state": "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED",
        "review_state": "PENDING",
        "publication_state": "NOT_PUBLISHED",
        "tvc_decision_id": runtime["tvc"].get("decision_id"),
        "tvc_policy_hash": runtime["tvc"].get("policy_hash"),
    }
    _sign_receipt(receipt, runtime["key"])
    receipt_path.write_bytes(canonical_json(receipt) + b"\n")
    return receipt


def main() -> None:
    import uvicorn

    uvicorn.run(
        "llm_adapter.service_gateway:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )


if __name__ == "__main__":
    main()
