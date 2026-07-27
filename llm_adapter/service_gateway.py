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

SCHEMA = "HIL-RECEIVER-RECEIPT-v2"
SERVICE_ID = "stegverse-service-gateway"
INTAKE_ROLE = "service_gateway_intake"
INTAKE_KEYS = {
    "service-gateway/hil-intake/storage-root",
    "service-gateway/hil-intake/receipt-key",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


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
    if not INTAKE_KEYS.issubset(allowed) or denied:
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


app = FastAPI(title="StegVerse Service Gateway", version="0.1.0")


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


@app.post("/v1/hil/intake")
async def hil_intake(
    document: UploadFile = File(...),
    metadata: str = Form(...),
) -> Dict[str, Any]:
    try:
        runtime = _runtime()
        meta = json.loads(metadata)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if document.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="pdf_required")

    packet_id = str(meta.get("packet_id") or uuid.uuid4())
    packet_dir = runtime["root"] / "packets" / packet_id
    if packet_dir.exists():
        receipt_path = runtime["root"] / "receipts" / f"{packet_id}.json"
        if receipt_path.exists():
            return json.loads(receipt_path.read_text(encoding="utf-8"))
        raise HTTPException(status_code=409, detail="packet_exists_without_receipt")

    packet_dir.mkdir(parents=False)
    tmp_path = Path(tempfile.mkstemp(prefix="upload-", suffix=".pdf", dir=packet_dir)[1])
    digest = hashlib.sha256()
    size = 0
    try:
        with tmp_path.open("wb") as output:
            while chunk := await document.read(1024 * 1024):
                size += len(chunk)
                if size > 100 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="document_too_large")
                digest.update(chunk)
                output.write(chunk)
        with tmp_path.open("rb") as source:
            if source.read(5) != b"%PDF-":
                raise HTTPException(status_code=422, detail="invalid_pdf_signature")

        document_hash = "sha256:" + digest.hexdigest()
        declared_hash = meta.get("document_hash") or meta.get("content_hash")
        if declared_hash and declared_hash != document_hash:
            raise HTTPException(status_code=422, detail="document_hash_mismatch")

        metadata_hash = sha256_bytes(canonical_json(meta))
        final_path = packet_dir / "document.pdf"
        tmp_path.replace(final_path)
        (packet_dir / "metadata.json").write_bytes(canonical_json(meta) + b"\n")

        receipt: Dict[str, Any] = {
            "schema": SCHEMA,
            "service_id": SERVICE_ID,
            "status": "SUBMISSION_ACCEPTED",
            "packet_id": packet_id,
            "received_at": utc_now(),
            "document_hash": document_hash,
            "metadata_hash": metadata_hash,
            "document_size_bytes": size,
            "storage_class": "durable-local",
            "tvc_decision_id": runtime["tvc"].get("decision_id"),
            "tvc_policy_hash": runtime["tvc"].get("policy_hash"),
            "provider_processing": "not_required_for_acceptance",
            "master_records_custody": "queued_separately",
        }
        receipt["receipt_hash"] = sha256_bytes(canonical_json(receipt))
        receipt["signature"] = "hmac-sha256:" + hmac.new(
            runtime["key"], canonical_json(receipt), hashlib.sha256
        ).hexdigest()
        receipt_path = runtime["root"] / "receipts" / f"{packet_id}.json"
        receipt_path.write_bytes(canonical_json(receipt) + b"\n")
        return receipt
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        if packet_dir.exists() and not any(packet_dir.iterdir()):
            packet_dir.rmdir()
        raise


def main() -> None:
    import uvicorn

    uvicorn.run(
        "llm_adapter.service_gateway:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )


if __name__ == "__main__":
    main()
