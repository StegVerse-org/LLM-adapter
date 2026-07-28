from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response

from . import service_gateway as gateway
app = gateway.app

READINESS_SCHEMA = "HIL-READINESS-v1"
READINESS_SCHEMA_PATH = "/schemas/hil-readiness-v1.schema.json"
STATUS_SCHEMA = "HIL-SUBMISSION-STATUS-v1"
STATUS_SCHEMA_PATH = "/schemas/hil-submission-status-v1.schema.json"
NOTIFICATION_SCHEMA_PATH = "/schemas/hil-attempt-notification-v1.schema.json"
AUTHORITY_EVIDENCE_SCHEMA = "HIL-TVC-AUTHORITY-EVIDENCE-v1"
AUTHORITY_EVIDENCE_PATH = "/api/hil/authority-evidence"
RUNTIME_CONTRACT_VERSION = "HIL-RTG-RUNTIME-v1"
TERMINAL_NOTIFICATION_STATES = ["DELIVERED", "PARTIAL_EXPIRED", "DELIVERY_EXPIRED"]
SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "schemas"
SCHEMA_FILES = {
    READINESS_SCHEMA_PATH: "hil-readiness-v1.schema.json",
    NOTIFICATION_SCHEMA_PATH: "hil-attempt-notification-v1.schema.json",
    STATUS_SCHEMA_PATH: "hil-submission-status-v1.schema.json",
}

app.router.routes[:] = [
    route for route in app.router.routes
    if getattr(route, "path", None) not in {
        "/api/hil/submissions",
        "/api/hil/readiness",
        AUTHORITY_EVIDENCE_PATH,
        *SCHEMA_FILES.keys(),
    }
]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_bytes(schema_path: str) -> bytes:
    filename = SCHEMA_FILES.get(schema_path)
    if not filename:
        raise HTTPException(status_code=404, detail="schema_not_found")
    path = SCHEMA_ROOT / filename
    if not path.is_file():
        raise HTTPException(status_code=503, detail="governed_schema_unavailable")
    return path.read_bytes()


def _schema_sha256(schema_path: str) -> str:
    return hashlib.sha256(_schema_bytes(schema_path)).hexdigest()


def _schema_response(schema_path: str) -> Response:
    content = _schema_bytes(schema_path)
    digest = hashlib.sha256(content).hexdigest()
    return Response(
        content=content,
        media_type="application/schema+json",
        headers={
            "Cache-Control": "public, max-age=300, must-revalidate",
            "ETag": f'"sha256:{digest}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


def _notification_max_attempts() -> int:
    try:
        value = int(os.getenv("STEGVERSE_NOTIFICATION_MAX_ATTEMPTS", "5"))
    except ValueError:
        value = 5
    return min(20, max(1, value))


def _authority_evidence(tvc: Dict[str, Any]) -> Dict[str, Any]:
    allowed_keys = sorted(str(value) for value in (tvc.get("allowed_keys") or []))
    denied_keys = sorted(str(value) for value in (tvc.get("denied_keys") or []))
    return {
        "schema_version": AUTHORITY_EVIDENCE_SCHEMA,
        "runtime_contract_version": RUNTIME_CONTRACT_VERSION,
        "authority_role": str(tvc.get("role") or ""),
        "decision_id": str(tvc.get("decision_id") or ""),
        "policy_hash": str(tvc.get("policy_hash") or ""),
        "admissible": tvc.get("admissible") is True,
        "binding_matched": tvc.get("binding_matched") is True,
        "allowed_keys_sha256": hashlib.sha256(gateway.canonical_json(allowed_keys)).hexdigest(),
        "denied_keys_sha256": hashlib.sha256(gateway.canonical_json(denied_keys)).hexdigest(),
        "allowed_key_count": len(allowed_keys),
        "denied_key_count": len(denied_keys),
        "restricted_fields_exposed": False,
    }


def _authority_evidence_bytes(tvc: Dict[str, Any]) -> bytes:
    return gateway.canonical_json(_authority_evidence(tvc))


def _authority_evidence_sha256(tvc: Dict[str, Any]) -> str:
    return hashlib.sha256(_authority_evidence_bytes(tvc)).hexdigest()


def _latest_submission_notification(root: Path, submission_id: str) -> Optional[Dict[str, Any]]:
    matches = []
    for path in (root / "notifications").glob("*.json"):
        try:
            notification = _load_json(path)
        except (OSError, ValueError):
            continue
        if notification.get("submission_id") == submission_id:
            matches.append((notification.get("attempted_at") or "", notification))
    if not matches:
        return None
    matches.sort(key=lambda item: item[0], reverse=True)
    return matches[0][1]


def _recipient_states(root: Path, attempt_id: str) -> Dict[str, str]:
    path = root / "notification-outbox" / f"{attempt_id}.json"
    if not path.exists():
        return {}
    envelope = _load_json(path)
    return {
        str(result.get("role")): str(result.get("state"))
        for result in envelope.get("delivery_results") or []
        if result.get("role") and result.get("state")
    }


@app.get(READINESS_SCHEMA_PATH)
def hil_readiness_schema() -> Response:
    return _schema_response(READINESS_SCHEMA_PATH)


@app.get(NOTIFICATION_SCHEMA_PATH)
def hil_attempt_notification_schema() -> Response:
    return _schema_response(NOTIFICATION_SCHEMA_PATH)


@app.get(STATUS_SCHEMA_PATH)
def hil_submission_status_schema() -> Response:
    return _schema_response(STATUS_SCHEMA_PATH)


@app.get(AUTHORITY_EVIDENCE_PATH)
def hil_authority_evidence() -> Response:
    try:
        runtime = gateway._runtime()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    content = _authority_evidence_bytes(runtime["tvc"])
    digest = hashlib.sha256(content).hexdigest()
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Cache-Control": "no-store",
            "ETag": f'"sha256:{digest}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/api/hil/readiness")
def site_hil_readiness() -> Dict[str, Any]:
    try:
        runtime = gateway._runtime()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    tvc = runtime["tvc"]
    return {
        "schema_version": READINESS_SCHEMA,
        "readiness_schema_path": READINESS_SCHEMA_PATH,
        "readiness_schema_sha256": _schema_sha256(READINESS_SCHEMA_PATH),
        "state": "READY",
        "service_id": gateway.SERVICE_ID,
        "primary_version": gateway.PRIMARY_VERSION,
        "primary_sha256": gateway.PRIMARY_SHA256,
        "protocol_version": gateway.PROTOCOL_VERSION,
        "prompt_version": gateway.PROMPT_VERSION,
        "prompt_sha256": gateway.PROMPT_SHA256,
        "provenance_manifest_required": True,
        "provenance_manifest_schema": gateway.PROVENANCE_SCHEMA,
        "participant_metadata_required": False,
        "participant_notification_supported": True,
        "participant_notification_scope": "ATTEMPT_NOTIFICATION_ONLY",
        "attempt_notification_schema": gateway.NOTIFICATION_SCHEMA,
        "attempt_notification_schema_path": NOTIFICATION_SCHEMA_PATH,
        "attempt_notification_schema_sha256": _schema_sha256(NOTIFICATION_SCHEMA_PATH),
        "submission_status_supported": True,
        "submission_status_schema": STATUS_SCHEMA,
        "submission_status_schema_path": STATUS_SCHEMA_PATH,
        "submission_status_schema_sha256": _schema_sha256(STATUS_SCHEMA_PATH),
        "submission_status_authorization": "SUBMISSION_ID_PLUS_RECEIPT_ID",
        "notification_max_attempts": _notification_max_attempts(),
        "terminal_notification_delivery_states": TERMINAL_NOTIFICATION_STATES,
        "completed_recipient_addresses_retained": False,
        "expired_recipient_addresses_retained": False,
        "notification_delivery_changes_submission_outcome": False,
        "durable_storage": True,
        "runtime_contract_version": RUNTIME_CONTRACT_VERSION,
        "tvc_authority_role": tvc.get("role"),
        "tvc_decision_id": tvc.get("decision_id"),
        "tvc_policy_hash": tvc.get("policy_hash"),
        "tvc_decision_receipt_sha256": hashlib.sha256(gateway.canonical_json(tvc)).hexdigest(),
        "tvc_admissible": tvc.get("admissible") is True,
        "tvc_binding_matched": tvc.get("binding_matched") is True,
        "authority_evidence_schema": AUTHORITY_EVIDENCE_SCHEMA,
        "authority_evidence_path": AUTHORITY_EVIDENCE_PATH,
        "authority_evidence_sha256": _authority_evidence_sha256(tvc),
    }


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
    participant_notification_requested: str = Form("false"),
    participant_notification_email: str = Form("not_provided"),
    participant_notification_scope: str = Form("NONE"),
) -> Dict[str, Any]:
    receipt = await gateway.site_hil_submission(
        response_pdf=response_pdf,
        provenance_manifest=provenance_manifest,
        participant_identifier=participant_identifier,
        publication_consent=publication_consent,
        primary_sha256=primary_sha256,
        prompt_sha256=prompt_sha256,
        model_response_declared_unedited=model_response_declared_unedited,
        participant_consent_authority_acknowledged=participant_consent_authority_acknowledged,
        participant_notification_requested=participant_notification_requested,
        participant_notification_email=participant_notification_email,
        participant_notification_scope=participant_notification_scope,
    )
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = gateway.sha256_hex(gateway.canonical_json(unsigned))

    runtime = gateway._runtime()
    receipt_path = runtime["root"] / "receipts" / f"{receipt['submission_id']}.json"
    receipt_path.write_bytes(gateway.canonical_json(receipt) + b"\n")
    return receipt


@app.get("/api/hil/submissions/{submission_id}/status")
def site_hil_submission_status(
    submission_id: str,
    receipt_id: str = Query(..., min_length=16, max_length=64),
) -> Dict[str, Any]:
    if not submission_id.startswith("HIL-SUBMISSION-") or len(submission_id) > 64:
        raise HTTPException(status_code=404, detail="submission_status_not_found")
    runtime = gateway._runtime()
    receipt_path = runtime["root"] / "receipts" / f"{submission_id}.json"
    if not receipt_path.exists():
        raise HTTPException(status_code=404, detail="submission_status_not_found")

    receipt = _load_json(receipt_path)
    if receipt.get("receipt_id") != receipt_id:
        raise HTTPException(status_code=404, detail="submission_status_not_found")

    notification = _latest_submission_notification(runtime["root"], submission_id)
    recipient_states = _recipient_states(
        runtime["root"], str(notification.get("attempt_id"))
    ) if notification else {}

    return {
        "schema_version": STATUS_SCHEMA,
        "submission_id": submission_id,
        "receipt_id": receipt.get("receipt_id"),
        "submission_state": "ACCEPTED",
        "chain_validation_state": receipt.get("chain_validation_state"),
        "review_state": receipt.get("review_state"),
        "publication_state": receipt.get("publication_state"),
        "notification_delivery_state": (
            notification.get("notification_delivery_state") if notification else "UNKNOWN"
        ),
        "notification_retry_authority_state": (
            notification.get("notification_retry_authority_state") if notification else "UNKNOWN"
        ),
        "recipient_address_retention_state": (
            notification.get("recipient_address_retention_state")
            if notification else "UNKNOWN"
        ),
        "required_recipient_delivery_state": recipient_states.get(
            "STEGVERSE_STUDY_AUTHORITY", "PENDING"
        ),
        "participant_copy_requested": bool(
            notification and notification.get("participant_copy_requested")
        ),
        "participant_copy_delivery_state": (
            recipient_states.get("PARTICIPANT_ATTEMPT_COPY", "PENDING")
            if notification and notification.get("participant_copy_requested")
            else "NOT_REQUESTED"
        ),
        "recipient_addresses_exposed": False,
        "notification_delivery_changes_submission_outcome": False,
    }


def main() -> None:
    import uvicorn

    uvicorn.run(
        "llm_adapter.service_gateway_site:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )


if __name__ == "__main__":
    main()
