"""Transport-only Service Gateway adapter for StegVerse-002 public observation."""
from __future__ import annotations
import hashlib, json, os
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlsplit
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

router=APIRouter()
MAX_BODY=2*1024*1024
ALLOWED_ORIGINS={"https://stegverse.org","https://www.stegverse.org"}
FORBIDDEN_REQUEST_HEADERS=("authorization","cookie")
FORWARDED_HEADERS=("origin","content-type","x-stegverse-transport","x-stegverse-authorization-id","x-stegverse-payload-sha256")
ENABLED_ENV="STEGVERSE_SV002_OBSERVE_ENABLED"
UPSTREAM_ENV="STEGVERSE_SV002_OBSERVE_UPSTREAM"
LOOPBACK_UPSTREAM="http://127.0.0.1:8766/intr/sv002-observe"

def _enabled()->bool: return os.getenv(ENABLED_ENV,"false").strip().lower()=="true"
def _upstream()->str:
    raw=os.getenv(UPSTREAM_ENV,"").strip()
    if not raw: raise ValueError("SV002 observation upstream is not configured")
    parsed=urlsplit(raw)
    if parsed.scheme!="http" or parsed.hostname not in {"127.0.0.1","::1","localhost"}: raise ValueError("SV002 observation upstream must be same-host loopback http")
    if parsed.path!="/intr/sv002-observe" or parsed.query or parsed.fragment: raise ValueError("SV002 observation upstream path must be /intr/sv002-observe")
    return raw
def _hash_body(body:bytes)->str: return hashlib.sha256(body).hexdigest()
def _validate_browser_request(request:Request,body:bytes)->dict[str,str]:
    if request.headers.get("origin") not in ALLOWED_ORIGINS: raise HTTPException(status_code=403,detail="origin_not_admitted")
    if any(request.headers.get(name) for name in FORBIDDEN_REQUEST_HEADERS): raise HTTPException(status_code=400,detail="credential_header_rejected")
    if not body or len(body)>MAX_BODY: raise HTTPException(status_code=413,detail="request_size_invalid")
    if request.headers.get("content-type","").split(";")[0].strip().lower()!="application/json": raise HTTPException(status_code=415,detail="json_required")
    if request.headers.get("x-stegverse-transport")!="InTr": raise HTTPException(status_code=400,detail="transport_header_mismatch")
    authority=request.headers.get("x-stegverse-authorization-id","").strip()
    if not authority: raise HTTPException(status_code=400,detail="authorization_id_required")
    if request.headers.get("x-stegverse-payload-sha256","").strip()!=_hash_body(body): raise HTTPException(status_code=400,detail="request_payload_hash_mismatch")
    try: payload=json.loads(body)
    except Exception as exc: raise HTTPException(status_code=400,detail="invalid_json") from exc
    if not isinstance(payload,dict): raise HTTPException(status_code=400,detail="request_object_required")
    if payload.get("schema_version")!="stegverse.sv002.public_observation.interlock_request.v1": raise HTTPException(status_code=400,detail="request_schema_mismatch")
    if payload.get("request_class")!="SV002_PUBLIC_OBSERVE" or payload.get("operation")!="READ_OBSERVATION" or payload.get("transport")!="InTr": raise HTTPException(status_code=400,detail="request_class_transport_mismatch")
    if payload.get("authority_transfer") is not False: raise HTTPException(status_code=400,detail="authority_transfer_rejected")
    return {name:request.headers[name] for name in FORWARDED_HEADERS if name in request.headers}
def _forward(body:bytes,headers:dict[str,str])->tuple[int,bytes,str]:
    req=urlrequest.Request(_upstream(),data=body,method="POST")
    for name,value in headers.items(): req.add_header(name,value)
    try:
        with urlrequest.urlopen(req,timeout=15) as response:
            raw=response.read(MAX_BODY+1)
            if len(raw)>MAX_BODY: raise ValueError("SV002 observation runtime response too large")
            return response.status,raw,response.headers.get_content_type()
    except urlerror.HTTPError as exc:
        return exc.code,exc.read(MAX_BODY+1),exc.headers.get_content_type()
    except Exception as exc:
        raise HTTPException(status_code=503,detail=f"sv002_observation_runtime_unavailable:{type(exc).__name__}") from exc

@router.get("/intr/sv002-observe/readiness")
def readiness()->dict:
    configured=False; reason=None; upstream_state="NOT_PROBED"; upstream=None
    try:
        base=_upstream(); configured=True
        if _enabled():
            req=urlrequest.Request(base+"/readiness",method="GET")
            try:
                with urlrequest.urlopen(req,timeout=2) as response:
                    raw=response.read(MAX_BODY+1)
                    if len(raw)>MAX_BODY: raise ValueError("SV002 readiness response too large")
                    value=json.loads(raw.decode("utf-8"))
                    upstream=value if isinstance(value,dict) else None
                    upstream_state="READY" if response.status==200 and isinstance(value,dict) and value.get("state")=="READY" else "NOT_READY"
            except Exception as exc:
                upstream_state="UNREACHABLE"
                reason=f"upstream_unreachable:{type(exc).__name__}"
    except ValueError as exc:
        reason=str(exc)
    ready=bool(_enabled() and configured and upstream_state=="READY")
    return {
      "schema":"stegverse.service-gateway.sv002-observation-readiness/v2",
      "enabled":_enabled(),
      "loopback_upstream_configured":configured,
      "upstream_runtime_state":upstream_state,
      "upstream_runtime":upstream,
      "state":"READY" if ready else "NOT_READY",
      "reason":reason,
      "transport":"InTr",
      "credential_authority":"TV/TVC",
      "gateway_receipt_authority":False,
      "gateway_experiment_authority":False,
      "authority_effect":"NONE"
    }

@router.post("/intr/sv002-observe")
async def proxy(request:Request)->Response:
    if not _enabled(): raise HTTPException(status_code=503,detail="sv002_observation_disabled")
    body=await request.body(); headers=_validate_browser_request(request,body); status,raw,content_type=_forward(body,headers)
    return Response(content=raw,status_code=status,media_type=content_type or "application/json",headers={"Cache-Control":"no-store"})
