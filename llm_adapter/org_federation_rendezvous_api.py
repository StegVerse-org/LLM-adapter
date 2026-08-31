"""Non-authorizing organization-federation rendezvous for exact HB/InTr carrier frames."""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

FRAME_SCHEMA = "stegverse.org-resident-kernel.carrier/v1"
ACK_SCHEMA = "stegverse.org-federation-rendezvous.ack/v1"
CANONICAL_ORGS = {
    "AaCT-E",
    "Admissible-Existence",
    "AdmittedCode",
    "Data-Continuation",
    "ECAT-ICAT-Formal",
    "formalism-tests",
    "GCAT-BCAT-Engine",
    "Infrastructure-Continuity-Ventures",
    "master-records",
    "StegGhost",
    "StegVerse-002",
    "StegVerse-Labs",
    "StegVerse-org",
    "Triad-Test",
}


class OrgFederationRendezvousError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_uri_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sha256_uri(value: Any) -> str:
    return sha256_uri_bytes(canonical_json(value).encode("utf-8"))


def rendezvous_root() -> Path:
    raw = os.getenv("STEGVERSE_ORG_FEDERATION_RENDEZVOUS_ROOT", "").strip()
    if not raw:
        raise OrgFederationRendezvousError("durable organization federation rendezvous root not configured")
    return Path(raw).expanduser().resolve()


def rendezvous_enabled() -> bool:
    return os.getenv("STEGVERSE_ORG_FEDERATION_RENDEZVOUS_ENABLED", "false").lower() == "true"


def _require_enabled() -> None:
    if not rendezvous_enabled():
        raise HTTPException(status_code=503, detail="organization federation rendezvous not enabled")
    try:
        rendezvous_root()
    except OrgFederationRendezvousError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _safe_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _org_dir_name(org: str) -> str:
    return _safe_id(org)


def _atomic_create(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(dict(value), indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        existing = json.loads(path.read_text(encoding="utf-8"))
        if canonical_json(existing) != canonical_json(value):
            raise OrgFederationRendezvousError("write-once collision with different bytes")
        return
    try:
        os.write(fd, raw)
    finally:
        os.close(fd)


def validate_frame(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise OrgFederationRendezvousError("frame must be object")
    required = {
        "schema", "packet_id", "packet_sha256", "packet_base64",
        "heartbeat_reference", "channel", "origin_org", "destination_org",
        "intr_profile", "authority_effect", "frame_sha256",
    }
    if set(value) != required:
        raise OrgFederationRendezvousError("frame fields invalid")
    if value["schema"] != FRAME_SCHEMA:
        raise OrgFederationRendezvousError("frame schema mismatch")
    if value["origin_org"] not in CANONICAL_ORGS or value["destination_org"] not in CANONICAL_ORGS:
        raise OrgFederationRendezvousError("organization not admitted")
    if value["authority_effect"] != "NONE_CARRIER_ONLY":
        raise OrgFederationRendezvousError("carrier authority effect mismatch")
    if value["intr_profile"] != "stegverse.intr.org-boundary.v1":
        raise OrgFederationRendezvousError("InTr profile mismatch")
    try:
        raw = base64.b64decode(str(value["packet_base64"]).encode("ascii"), validate=True)
    except Exception as exc:
        raise OrgFederationRendezvousError("packet_base64 invalid") from exc
    if sha256_uri_bytes(raw) != value["packet_sha256"]:
        raise OrgFederationRendezvousError("packet hash mismatch")
    try:
        packet = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise OrgFederationRendezvousError("packet JSON invalid") from exc
    if packet.get("packet_id") != value["packet_id"]:
        raise OrgFederationRendezvousError("packet id mismatch")
    if (packet.get("origin") or {}).get("org") != value["origin_org"]:
        raise OrgFederationRendezvousError("origin organization mismatch")
    if (packet.get("destination") or {}).get("org") != value["destination_org"]:
        raise OrgFederationRendezvousError("destination organization mismatch")
    if packet.get("intr_profile") != value["intr_profile"]:
        raise OrgFederationRendezvousError("packet InTr profile mismatch")
    body = dict(value)
    claimed = body.pop("frame_sha256")
    if sha256_uri(body) != claimed:
        raise OrgFederationRendezvousError("frame hash mismatch")
    return dict(value)


def _paths(root: Path, org: str) -> tuple[Path, Path]:
    pending = root / "pending" / _org_dir_name(org)
    acknowledged = root / "acknowledged" / _org_dir_name(org)
    pending.mkdir(parents=True, exist_ok=True)
    acknowledged.mkdir(parents=True, exist_ok=True)
    return pending, acknowledged


def store_frame(value: Mapping[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    frame = validate_frame(value)
    base = root or rendezvous_root()
    pending, acknowledged = _paths(base, frame["destination_org"])
    frame_id = _safe_id(frame["packet_id"] + "|" + frame["frame_sha256"])
    path = pending / (frame_id + ".json")
    if (acknowledged / path.name).exists():
        raise OrgFederationRendezvousError("frame already acknowledged")
    _atomic_create(path, frame)
    return {
        "schema": "stegverse.org-federation-rendezvous.store-result/v1",
        "state": "PENDING",
        "packet_id": frame["packet_id"],
        "frame_sha256": frame["frame_sha256"],
        "destination_org": frame["destination_org"],
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_CARRIER_ONLY",
    }


def next_frame(organization: str, *, root: Path | None = None) -> dict[str, Any] | None:
    if organization not in CANONICAL_ORGS:
        raise OrgFederationRendezvousError("organization not admitted")
    base = root or rendezvous_root()
    pending, acknowledged = _paths(base, organization)
    for path in sorted(pending.glob("*.json"), key=lambda p: p.stat().st_mtime):
        if (acknowledged / path.name).exists():
            continue
        try:
            frame = validate_frame(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
        if frame["destination_org"] == organization:
            return frame
    return None


def validate_ack(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise OrgFederationRendezvousError("ack must be object")
    required = {
        "schema", "organization", "packet_id", "frame_sha256",
        "state", "observed_at", "gateway_execution_authority", "authority_effect",
    }
    if set(value) != required:
        raise OrgFederationRendezvousError("ack fields invalid")
    if value["schema"] != ACK_SCHEMA:
        raise OrgFederationRendezvousError("ack schema mismatch")
    if value["organization"] not in CANONICAL_ORGS:
        raise OrgFederationRendezvousError("organization not admitted")
    if value["state"] not in {"RECEIVED", "CONSUMED", "BLOCKED"}:
        raise OrgFederationRendezvousError("ack state invalid")
    if value["gateway_execution_authority"] != "NONE":
        raise OrgFederationRendezvousError("gateway execution authority must be NONE")
    if value["authority_effect"] != "NONE_OBSERVATION_ONLY":
        raise OrgFederationRendezvousError("ack authority effect mismatch")
    try:
        dt = datetime.fromisoformat(str(value["observed_at"]).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError
    except Exception as exc:
        raise OrgFederationRendezvousError("observed_at invalid") from exc
    return dict(value)


def store_ack(value: Mapping[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    ack = validate_ack(value)
    base = root or rendezvous_root()
    pending, acknowledged = _paths(base, ack["organization"])
    match = None
    for path in pending.glob("*.json"):
        try:
            frame = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if frame.get("packet_id") == ack["packet_id"] and frame.get("frame_sha256") == ack["frame_sha256"]:
            match = (path, frame)
            break
    if match is None:
        raise OrgFederationRendezvousError("pending frame not found")
    path, frame = match
    record = {
        "frame": frame,
        "acknowledgement": ack,
        "gateway_recorded_at": datetime.now(timezone.utc).isoformat(),
        "canonical_runtime_evidence_verified": False,
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    _atomic_create(acknowledged / path.name, record)
    return {
        "schema": "stegverse.org-federation-rendezvous.ack-store-result/v1",
        "state": "ACKNOWLEDGED",
        "packet_id": ack["packet_id"],
        "organization": ack["organization"],
        "canonical_runtime_evidence_verified": False,
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }


@router.post("/api/org-federation/v1/frames")
async def submit_org_federation_frame(request: Request) -> dict[str, Any]:
    _require_enabled()
    payload = await request.json()
    origin_header = request.headers.get("X-StegVerse-Origin-Organization", "")
    if origin_header != payload.get("origin_org"):
        raise HTTPException(status_code=403, detail="origin organization binding required")
    try:
        return store_frame(payload)
    except OrgFederationRendezvousError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/org-federation/v1/frames")
def fetch_org_federation_frame(organization: str, request: Request) -> dict[str, Any]:
    _require_enabled()
    bound = request.headers.get("X-StegVerse-Organization", "")
    if bound != organization:
        raise HTTPException(status_code=403, detail="organization binding required")
    try:
        frame = next_frame(organization)
    except OrgFederationRendezvousError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if frame is None:
        return {
            "schema": "stegverse.org-federation-rendezvous.fetch-result/v1",
            "state": "NO_FRAME",
            "gateway_execution_authority": "NONE",
            "authority_effect": "NONE",
        }
    return {
        "schema": "stegverse.org-federation-rendezvous.fetch-result/v1",
        "state": "FRAME_AVAILABLE",
        "frame": frame,
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_CARRIER_ONLY",
    }


@router.post("/api/org-federation/v1/acknowledgements")
async def acknowledge_org_federation_frame(request: Request) -> dict[str, Any]:
    _require_enabled()
    payload = await request.json()
    bound = request.headers.get("X-StegVerse-Organization", "")
    if bound != payload.get("organization"):
        raise HTTPException(status_code=403, detail="organization binding required")
    try:
        return store_ack(payload)
    except OrgFederationRendezvousError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
