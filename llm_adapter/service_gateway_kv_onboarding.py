from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException, Request

from llm_adapter.service_gateway import app

REQUEST_SCHEMA = "stegverse.site.kv_onboarding_request/v1"
STAGE_RECEIPT_SCHEMA = "stegverse.service_gateway.kv_onboarding_stage_receipt/v1"
TRANSPORT_PROTOCOL = "InTr"
DECISION = "STAGED_FOR_CANONICAL_KV_AUTHORITY"
NEXT_TRANSITION = "CANONICAL_KV_OWNERSHIP_ADMISSION"
ALLOWED_ORIGINS = {"https://stegverse.org", "https://www.stegverse.org"}
ALLOWED_OPERATIONS = {"CREATE_KV", "ATTACH_KV", "REGISTER_DEVICE", "INSTALL_KV"}
MAX_BODY_BYTES = 32 * 1024
FORBIDDEN_KEYS = {
    "password",
    "secret",
    "private_key",
    "api_key",
    "api_key_name",
    "authorization",
    "access_token",
    "refresh_token",
    "credential",
    "credential_material",
    "skap_material",
}


class KvOnboardingStageError(ValueError):
    pass


@dataclass(frozen=True)
class KvOnboardingStageRuntime:
    root: Path


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _valid_digest(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and len(value) == 71


def _safe_id(value: Any) -> bool:
    if not isinstance(value, str) or not value or len(value) > 160:
        return False
    return all(ch.isalnum() or ch in "._-" for ch in value)


def _find_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in FORBIDDEN_KEYS:
                findings.append(f"{path}.{key}")
            findings.extend(_find_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_find_forbidden_keys(child, f"{path}[{index}]"))
    return findings


def validate_request(packet: Dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if packet.get("schema") != REQUEST_SCHEMA:
        findings.append("schema_invalid")
    if not _safe_id(packet.get("request_id")):
        findings.append("request_id_invalid")
    operation = packet.get("operation")
    if operation not in ALLOWED_OPERATIONS:
        findings.append("operation_invalid")
    if packet.get("transport_protocol") != TRANSPORT_PROTOCOL:
        findings.append("transport_protocol_invalid")
    if not _valid_digest(packet.get("account_ref_sha256")):
        findings.append("account_ref_sha256_invalid")
    if not _valid_digest(packet.get("identity_assertion_hash")):
        findings.append("identity_assertion_hash_invalid")
    assertion_id = packet.get("identity_assertion_id")
    if not isinstance(assertion_id, str) or not assertion_id or len(assertion_id) > 256:
        findings.append("identity_assertion_id_invalid")
    prior = packet.get("prior_transition_receipt_hash")
    if prior is not None and not _valid_digest(prior):
        findings.append("prior_transition_receipt_hash_invalid")
    if packet.get("secret_plaintext_present") is not False:
        findings.append("secret_plaintext_present_forbidden")
    if packet.get("credential_material_recorded") is not False:
        findings.append("credential_material_recorded_forbidden")
    if packet.get("authority_effect") != "REQUEST_ONLY":
        findings.append("authority_effect_invalid")

    kv_ref = packet.get("kv_ref")
    device_ref = packet.get("device_ref")
    if operation == "CREATE_KV":
        if kv_ref is not None:
            findings.append("create_kv_ref_must_be_unassigned")
        if device_ref is not None:
            findings.append("create_device_ref_forbidden")
    elif operation == "ATTACH_KV":
        if not isinstance(kv_ref, str) or not kv_ref.startswith("kv://") or len(kv_ref) > 256:
            findings.append("attach_kv_ref_invalid")
        if device_ref is not None:
            findings.append("attach_device_ref_forbidden")
    elif operation in {"REGISTER_DEVICE", "INSTALL_KV"}:
        if not isinstance(kv_ref, str) or not kv_ref.startswith("kv://") or len(kv_ref) > 256:
            findings.append("operation_kv_ref_invalid")
        if not isinstance(device_ref, str) or not device_ref.startswith("device://") or len(device_ref) > 256:
            findings.append("device_ref_invalid")
        if operation == "INSTALL_KV" and not _valid_digest(prior):
            findings.append("install_prior_receipt_required")

    forbidden = _find_forbidden_keys(packet)
    if forbidden:
        findings.append("forbidden_field:" + ",".join(forbidden))
    return findings


def load_runtime() -> KvOnboardingStageRuntime:
    root_value = (
        os.getenv("STEGVERSE_KV_ONBOARDING_STORAGE_ROOT", "").strip()
        or os.getenv("STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT", "").strip()
    )
    if not root_value:
        raise KvOnboardingStageError("kv_onboarding_storage_root_missing")
    root = Path(root_value).expanduser().resolve()
    (root / "kv-onboarding-staging").mkdir(parents=True, exist_ok=True)
    (root / "kv-onboarding-stage-receipts").mkdir(parents=True, exist_ok=True)
    return KvOnboardingStageRuntime(root=root)


def _exclusive_write(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def stage_request(packet: Dict[str, Any], runtime: KvOnboardingStageRuntime) -> Dict[str, Any]:
    findings = validate_request(packet)
    if findings:
        raise KvOnboardingStageError("kv_onboarding_request_denied:" + ",".join(findings))

    request_id = str(packet["request_id"])
    request_digest = digest(packet)
    staging_dir = runtime.root / "kv-onboarding-staging"
    receipt_dir = runtime.root / "kv-onboarding-stage-receipts"
    packet_path = staging_dir / f"{request_id}.json"
    receipt_path = receipt_dir / f"{request_id}.json"

    if packet_path.exists() or receipt_path.exists():
        raise KvOnboardingStageError("kv_onboarding_replay_denied")

    payload = canonical_bytes(packet) + b"\n"
    try:
        _exclusive_write(packet_path, payload)
    except FileExistsError as exc:
        raise KvOnboardingStageError("kv_onboarding_replay_denied") from exc

    if packet_path.read_bytes() != payload:
        packet_path.unlink(missing_ok=True)
        raise KvOnboardingStageError("kv_onboarding_stage_readback_mismatch")

    body = {
        "schema": STAGE_RECEIPT_SCHEMA,
        "decision": DECISION,
        "request_id": request_id,
        "operation": packet["operation"],
        "account_ref_sha256": packet["account_ref_sha256"],
        "identity_assertion_id": packet["identity_assertion_id"],
        "identity_assertion_hash": packet["identity_assertion_hash"],
        "request_digest": request_digest,
        "transport_protocol": TRANSPORT_PROTOCOL,
        "completed_boundary": "DEVICE_TO_KV_STAGING",
        "staged_request_ref": f"kv-onboarding-stage://{request_id}",
        "kv_ownership_established": False,
        "owner_binding_established": False,
        "device_registration_established": False,
        "installation_admitted": False,
        "kv_active": False,
        "skap_unlocked": False,
        "gateway_identity_authority": False,
        "gateway_kv_authority": False,
        "gateway_device_authority": False,
        "gateway_execution_authority": "NONE",
        "authority_transfer": False,
        "secret_plaintext_present": False,
        "credential_material_recorded": False,
        "next_required_transition": NEXT_TRANSITION,
        "blind_retry_allowed": False,
    }
    receipt = {**body, "receipt_hash": digest(body)}
    try:
        _exclusive_write(receipt_path, canonical_bytes(receipt) + b"\n")
    except FileExistsError as exc:
        packet_path.unlink(missing_ok=True)
        raise KvOnboardingStageError("kv_onboarding_replay_denied") from exc
    return receipt


@app.get("/api/kv/onboarding/readiness")
def kv_onboarding_readiness() -> Dict[str, Any]:
    try:
        load_runtime()
    except KvOnboardingStageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "state": "READY_FOR_STAGING",
        "service_id": "stegverse-service-gateway",
        "adapter": "knowledgevault-onboarding-staging",
        "request_schema": REQUEST_SCHEMA,
        "receipt_schema": STAGE_RECEIPT_SCHEMA,
        "transport_protocol": TRANSPORT_PROTOCOL,
        "durable_storage": True,
        "decision": DECISION,
        "gateway_identity_authority": False,
        "gateway_kv_authority": False,
        "gateway_device_authority": False,
        "gateway_execution_authority": "NONE",
        "canonical_ownership_admission_required": True,
        "next_required_transition": NEXT_TRANSITION,
    }


@app.post("/api/kv/onboarding/transitions", status_code=202)
async def kv_onboarding_transition(request: Request) -> Dict[str, Any]:
    origin = str(request.headers.get("origin") or "")
    if origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="origin_not_admitted")
    if request.headers.get("authorization"):
        raise HTTPException(status_code=400, detail="authorization_header_forbidden")
    if request.headers.get("cookie"):
        raise HTTPException(status_code=400, detail="cookie_header_forbidden")
    content_type = str(request.headers.get("content-type") or "").lower()
    if not content_type.startswith("application/json"):
        raise HTTPException(status_code=415, detail="content_type_not_admitted")
    declared = request.headers.get("content-length")
    if declared:
        try:
            if int(declared) > MAX_BODY_BYTES:
                raise HTTPException(status_code=413, detail="body_too_large")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="content_length_invalid") from exc

    raw_body = await request.body()
    if not raw_body or len(raw_body) > MAX_BODY_BYTES:
        raise HTTPException(
            status_code=413 if len(raw_body) > MAX_BODY_BYTES else 400,
            detail="body_size_invalid",
        )
    try:
        packet = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="json_body_invalid") from exc
    if not isinstance(packet, dict):
        raise HTTPException(status_code=422, detail="packet_not_object")

    try:
        runtime = load_runtime()
        return stage_request(packet, runtime)
    except KvOnboardingStageError as exc:
        reason = str(exc)
        if reason == "kv_onboarding_replay_denied":
            raise HTTPException(status_code=409, detail=reason) from exc
        raise HTTPException(status_code=422, detail=reason) from exc
