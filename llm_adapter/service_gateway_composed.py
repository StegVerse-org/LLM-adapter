from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import HTTPException, Request

from llm_adapter.service_gateway import app
from llm_adapter.service_gateway_coinbase_skap import (
    ALLOWED_ORIGINS,
    CoinbaseSkapStageError,
    MAX_BODY_BYTES,
    STAGE_RECEIPT_SCHEMA,
    load_runtime,
    stage_packet,
)


@app.get("/api/coinbase/skap/readiness")
def coinbase_skap_readiness() -> Dict[str, Any]:
    try:
        runtime = load_runtime()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "state": "READY",
        "service_id": "stegverse-service-gateway",
        "adapter": "coinbase-skap-ciphertext-staging",
        "receipt_schema": STAGE_RECEIPT_SCHEMA,
        "durable_storage": True,
        "transport_protocol": "InTr",
        "completed_boundary": "DEVICE_TO_KV",
        "credential_custody_target": "KV_HOSTED_SKAP_VAULT",
        "credential_authority": "TV/TVC",
        "gateway_credential_value_access": False,
        "gateway_decryption_authority": False,
        "gateway_execution_authority": "NONE",
        "tvc_admission_completed": False,
        "skap_vault_admission_completed": False,
        "next_required_transition": "KV_SKAP_VAULT_INTERLOCK_ADMISSION",
        "tvc_decision_id": runtime.tvc_decision_id,
    }


@app.post("/api/coinbase/skap/ingress", status_code=202)
async def coinbase_skap_ingress(request: Request) -> Dict[str, Any]:
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
        raise HTTPException(status_code=413 if len(raw_body) > MAX_BODY_BYTES else 400, detail="body_size_invalid")
    try:
        packet = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="json_body_invalid") from exc
    if not isinstance(packet, dict):
        raise HTTPException(status_code=422, detail="packet_not_object")

    try:
        runtime = load_runtime()
        return stage_packet(raw_body=raw_body, packet=packet, runtime=runtime)
    except CoinbaseSkapStageError as exc:
        reason = str(exc)
        if reason == "ingress_replay_denied":
            raise HTTPException(status_code=409, detail=reason) from exc
        raise HTTPException(status_code=422, detail=reason) from exc
