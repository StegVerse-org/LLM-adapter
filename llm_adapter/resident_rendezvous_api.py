"""Non-authorizing Service Gateway rendezvous for sovereign resident requests."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

REQUEST_SCHEMA = "stegverse.resident-rendezvous.request/v1"
ACK_SCHEMA = "stegverse.resident-rendezvous.acknowledgement/v1"
ADVERTISEMENT_SCHEMA = "stegverse.resident-rendezvous.advertisement/v1"
DISCOVERY_SCHEMA = "stegverse.resident-rendezvous.discovery/v1"
RESIDENT_SCHEMA = "stegverse.resident-execution-request/v1"
ALLOWED_CONSUMER = "stegos_kv_intr_chain"
ALLOWED_TASK = "SHWP-STEGOS-KV-INTR-CHAIN-001"
ALLOWED_MODE = "STEGOS_KV_INTR_CHAIN"
ALLOWED_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
CURRENT_ALLOWED_STEPS = [
    "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
    "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001",
    "SHWP-DEVICE-KV-INTR-OBSERVATION-001",
]
LEGACY_ALLOWED_STEPS = [
    *CURRENT_ALLOWED_STEPS,
    "SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001",
]
ALLOWED_STEP_SETS = (CURRENT_ALLOWED_STEPS, LEGACY_ALLOWED_STEPS)
CURRENT_REQUEST_ID = "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003"
LEGACY_REQUEST_IDS = {
    "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-001",
    "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-002",
}
MAX_ADVERTISEMENT_LEASE_SECONDS = 300
FORBIDDEN_FIELD_NAMES = {
    "password", "secret", "credential", "credential_value", "private_key",
    "private_key_material", "token", "access_token", "refresh_token", "cookie",
    "mnemonic", "seed", "raw_biometric", "shell", "command", "argv",
}


class ResidentRendezvousError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_uri(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ResidentRendezvousError("timestamp required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ResidentRendezvousError("invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise ResidentRendezvousError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _forbidden_key(name: str) -> bool:
    return name.lower() in FORBIDDEN_FIELD_NAMES


def _reject_secret_or_command_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ResidentRendezvousError(f"non-string field at {path}")
            if _forbidden_key(key):
                raise ResidentRendezvousError(f"forbidden field at {path}.{key}")
            _reject_secret_or_command_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_or_command_fields(child, f"{path}[{index}]")


def validate_resident_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ResidentRendezvousError("resident_request must be an object")
    _reject_secret_or_command_fields(value)
    expected = {
        "schema": RESIDENT_SCHEMA,
        "state": "REQUESTED",
        "task_id": ALLOWED_TASK,
        "mode": ALLOWED_MODE,
        "entrypoint": ALLOWED_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "network_source_fetch_allowed": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise ResidentRendezvousError(f"resident_request {key} mismatch")
    request_id = value.get("request_id")
    if request_id not in LEGACY_REQUEST_IDS | {CURRENT_REQUEST_ID}:
        raise ResidentRendezvousError("resident_request request_id not admitted")
    steps = value.get("steps")
    if request_id == "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-001":
        if steps not in ALLOWED_STEP_SETS:
            raise ResidentRendezvousError("resident_request steps mismatch")
    elif steps != CURRENT_ALLOWED_STEPS:
        raise ResidentRendezvousError("resident_request steps mismatch")
    allowed = set(expected) | {"request_id", "note"}
    if set(value) - allowed:
        raise ResidentRendezvousError("resident_request contains unsupported fields")
    if "note" in value and (not isinstance(value["note"], str) or len(value["note"]) > 1000):
        raise ResidentRendezvousError("resident_request note invalid")
    return dict(value)


def validate_rendezvous_request(value: Any, *, now: datetime | None = None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ResidentRendezvousError("request must be an object")
    _reject_secret_or_command_fields(value)
    required = {
        "schema", "request_id", "target_node_ref", "consumer", "resident_request",
        "resident_request_sha256", "submitted_at", "expires_at",
        "submitter_authorization_ref", "authority_effect",
    }
    if set(value) != required:
        raise ResidentRendezvousError("rendezvous request fields invalid")
    if value["schema"] != REQUEST_SCHEMA:
        raise ResidentRendezvousError("rendezvous request schema mismatch")
    if value["consumer"] != ALLOWED_CONSUMER:
        raise ResidentRendezvousError("consumer not admitted")
    for field in ("request_id", "target_node_ref", "submitter_authorization_ref"):
        if not isinstance(value[field], str) or not value[field] or len(value[field]) > 256:
            raise ResidentRendezvousError(f"{field} invalid")
    if value["authority_effect"] != "NONE_REQUEST_ONLY":
        raise ResidentRendezvousError("authority_effect mismatch")
    resident_request = validate_resident_request(value["resident_request"])
    if value["resident_request_sha256"] != sha256_uri(resident_request):
        raise ResidentRendezvousError("resident request digest mismatch")
    submitted = _parse_time(value["submitted_at"])
    expires = _parse_time(value["expires_at"])
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if expires <= submitted:
        raise ResidentRendezvousError("expiry must follow submission")
    if expires <= current:
        raise ResidentRendezvousError("request expired")
    if (expires - submitted).total_seconds() > 3600:
        raise ResidentRendezvousError("request lease exceeds one hour")
    return dict(value)


def validate_acknowledgement(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ResidentRendezvousError("acknowledgement must be an object")
    _reject_secret_or_command_fields(value)
    required = {
        "schema", "request_id", "target_node_ref", "resident_request_sha256",
        "resident_consumption_state", "local_receipt_refs", "terminal_chain_observed",
        "credential_authority", "gateway_execution_authority",
        "authority_effect", "acknowledged_at",
    }
    if set(value) != required:
        raise ResidentRendezvousError("acknowledgement fields invalid")
    if value["schema"] != ACK_SCHEMA:
        raise ResidentRendezvousError("acknowledgement schema mismatch")
    for field in ("request_id", "target_node_ref"):
        if not isinstance(value[field], str) or not value[field]:
            raise ResidentRendezvousError(f"{field} required")
    digest = value["resident_request_sha256"]
    if not isinstance(digest, str) or len(digest) != 71 or not digest.startswith("sha256:"):
        raise ResidentRendezvousError("resident request digest invalid")
    if value["resident_consumption_state"] not in {
        "ATTEMPT_RECORDED", "COMPLETED", "BLOCKED", "NO_REQUEST"
    }:
        raise ResidentRendezvousError("resident consumption state invalid")
    refs = value["local_receipt_refs"]
    if not isinstance(refs, list) or len(refs) > 16 or any(not isinstance(x, str) or not x for x in refs):
        raise ResidentRendezvousError("local receipt refs invalid")
    if not isinstance(value["terminal_chain_observed"], bool):
        raise ResidentRendezvousError("terminal_chain_observed invalid")
    if value["credential_authority"] != "TV/TVC":
        raise ResidentRendezvousError("credential authority mismatch")
    if value["gateway_execution_authority"] != "NONE":
        raise ResidentRendezvousError("gateway execution authority must be NONE")
    if value["authority_effect"] != "NONE_OBSERVATION_ONLY":
        raise ResidentRendezvousError("acknowledgement authority_effect mismatch")
    _parse_time(value["acknowledged_at"])
    return dict(value)


def validate_advertisement(value: Any, *, now: datetime | None = None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ResidentRendezvousError("advertisement must be an object")
    _reject_secret_or_command_fields(value)
    required = {
        "schema", "target_node_ref", "consumer", "current_resident_request_id",
        "advertised_at", "expires_at", "credential_authority",
        "gateway_execution_authority", "advertisement_grants_authority", "authority_effect",
    }
    if set(value) != required:
        raise ResidentRendezvousError("advertisement fields invalid")
    expected = {
        "schema": ADVERTISEMENT_SCHEMA,
        "consumer": ALLOWED_CONSUMER,
        "current_resident_request_id": CURRENT_REQUEST_ID,
        "credential_authority": "TV/TVC",
        "gateway_execution_authority": "NONE",
        "advertisement_grants_authority": False,
        "authority_effect": "NONE_DISCOVERY_ONLY",
    }
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            raise ResidentRendezvousError(f"advertisement {field} mismatch")
    node_ref = value.get("target_node_ref")
    if not isinstance(node_ref, str) or not node_ref or len(node_ref) > 256:
        raise ResidentRendezvousError("advertisement target_node_ref invalid")
    advertised = _parse_time(value.get("advertised_at"))
    expires = _parse_time(value.get("expires_at"))
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if expires <= advertised:
        raise ResidentRendezvousError("advertisement expiry must follow advertised_at")
    if (expires - advertised).total_seconds() > MAX_ADVERTISEMENT_LEASE_SECONDS:
        raise ResidentRendezvousError("advertisement lease exceeds five minutes")
    if expires <= current:
        raise ResidentRendezvousError("advertisement expired")
    return dict(value)


def store_advertisement(
    value: Mapping[str, Any],
    *,
    root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    advertisement = validate_advertisement(value, now=now)
    base = root or rendezvous_root()
    directory = base / "advertisements"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (_safe_id(advertisement["target_node_ref"]) + ".json")
    raw = (json.dumps(advertisement, indent=2, sort_keys=True) + "\n").encode("utf-8")
    tmp = path.with_name("." + path.name + ".tmp")
    fd = os.open(tmp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    try:
        os.write(fd, raw)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    return {
        "schema": "stegverse.resident-rendezvous.advertisement-store-result/v1",
        "state": "ADVERTISED",
        "target_node_ref": advertisement["target_node_ref"],
        "expires_at": advertisement["expires_at"],
        "gateway_execution_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_DISCOVERY_ONLY",
    }


def discover_resident(
    *,
    root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    base = root or rendezvous_root()
    directory = base / "advertisements"
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    matches: list[dict[str, Any]] = []
    if directory.is_dir():
        for path in sorted(directory.glob("*.json")):
            try:
                value = validate_advertisement(
                    json.loads(path.read_text(encoding="utf-8")),
                    now=current,
                )
            except Exception:
                continue
            matches.append(value)
    common = {
        "schema": DISCOVERY_SCHEMA,
        "consumer": ALLOWED_CONSUMER,
        "current_resident_request_id": CURRENT_REQUEST_ID,
        "gateway_execution_authority": "NONE",
        "credential_authority": "TV/TVC",
        "discovery_grants_authority": False,
        "authority_effect": "NONE_DISCOVERY_ONLY",
    }
    if not matches:
        return {**common, "state": "UNAVAILABLE", "target_node_ref": None, "expires_at": None}
    if len(matches) != 1:
        return {**common, "state": "AMBIGUOUS", "target_node_ref": None, "expires_at": None}
    match = matches[0]
    return {
        **common,
        "state": "AVAILABLE",
        "target_node_ref": match["target_node_ref"],
        "expires_at": match["expires_at"],
    }


def rendezvous_root() -> Path:
    raw = os.getenv("STEGVERSE_RESIDENT_RENDEZVOUS_ROOT", "").strip()
    if not raw:
        raise ResidentRendezvousError("durable rendezvous root not configured")
    return Path(raw).expanduser().resolve()


def rendezvous_enabled() -> bool:
    return os.getenv("STEGVERSE_RESIDENT_RENDEZVOUS_ENABLED", "false").lower() == "true"


def _paths(root: Path) -> tuple[Path, Path]:
    pending = root / "pending"
    acknowledged = root / "acknowledged"
    pending.mkdir(parents=True, exist_ok=True)
    acknowledged.mkdir(parents=True, exist_ok=True)
    return pending, acknowledged


def _safe_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _atomic_create(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(dict(value), indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        existing = json.loads(path.read_text(encoding="utf-8"))
        if canonical_json(existing) != canonical_json(value):
            raise ResidentRendezvousError("request id collision with different bytes")
        return
    try:
        os.write(fd, raw)
    finally:
        os.close(fd)


def store_request(value: Mapping[str, Any], *, root: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    request = validate_rendezvous_request(value, now=now)
    base = root or rendezvous_root()
    pending, acknowledged = _paths(base)
    name = _safe_id(request["request_id"]) + ".json"
    if (acknowledged / name).exists():
        raise ResidentRendezvousError("request already acknowledged")
    _atomic_create(pending / name, request)
    return {
        "schema": "stegverse.resident-rendezvous.store-result/v1",
        "state": "PENDING",
        "request_id": request["request_id"],
        "resident_request_sha256": request["resident_request_sha256"],
        "gateway_execution_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_REQUEST_ONLY",
    }


def next_request(target_node_ref: str, *, root: Path | None = None, now: datetime | None = None) -> dict[str, Any] | None:
    base = root or rendezvous_root()
    pending, acknowledged = _paths(base)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    for path in sorted(pending.glob("*.json"), key=lambda p: p.stat().st_mtime):
        if (acknowledged / path.name).exists():
            continue
        try:
            value = validate_rendezvous_request(
                json.loads(path.read_text(encoding="utf-8")), now=current
            )
        except Exception:
            continue
        if value["target_node_ref"] == target_node_ref:
            return value
    return None


def store_acknowledgement(value: Mapping[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    ack = validate_acknowledgement(value)
    base = root or rendezvous_root()
    pending, acknowledged = _paths(base)
    name = _safe_id(ack["request_id"]) + ".json"
    pending_path = pending / name
    if not pending_path.is_file():
        raise ResidentRendezvousError("pending request not found")
    request = json.loads(pending_path.read_text(encoding="utf-8"))
    if request.get("target_node_ref") != ack["target_node_ref"]:
        raise ResidentRendezvousError("ack target node mismatch")
    if request.get("resident_request_sha256") != ack["resident_request_sha256"]:
        raise ResidentRendezvousError("ack request digest mismatch")
    record = {
        "request": request,
        "acknowledgement": ack,
        "gateway_recorded_at": datetime.now(timezone.utc).isoformat(),
        "canonical_runtime_evidence_verified": False,
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    _atomic_create(acknowledged / name, record)
    return {
        "schema": "stegverse.resident-rendezvous.ack-store-result/v1",
        "state": "ACKNOWLEDGED",
        "request_id": ack["request_id"],
        "canonical_runtime_evidence_verified": False,
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }


def _require_enabled() -> None:
    if not rendezvous_enabled():
        raise HTTPException(status_code=503, detail="resident rendezvous not enabled")
    try:
        rendezvous_root()
    except ResidentRendezvousError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/api/resident-rendezvous/v1/advertisements")
async def advertise_resident(request: Request) -> dict[str, Any]:
    _require_enabled()
    payload = await request.json()
    node_header = request.headers.get("X-StegVerse-Node-Ref", "")
    if not node_header or node_header != payload.get("target_node_ref"):
        raise HTTPException(status_code=403, detail="node reference binding required")
    try:
        return store_advertisement(payload)
    except ResidentRendezvousError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/resident-rendezvous/v1/discovery")
def discover_resident_endpoint() -> dict[str, Any]:
    _require_enabled()
    return discover_resident()


@router.post("/api/resident-rendezvous/v1/requests")
async def submit_resident_request(request: Request) -> dict[str, Any]:
    _require_enabled()
    payload = await request.json()
    auth_header = request.headers.get("X-StegVerse-Authorization-Id", "")
    if not auth_header or auth_header != payload.get("submitter_authorization_ref"):
        raise HTTPException(status_code=403, detail="authorization reference binding required")
    try:
        return store_request(payload)
    except ResidentRendezvousError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/resident-rendezvous/v1/requests")
def fetch_resident_request(target_node_ref: str, request: Request) -> dict[str, Any]:
    _require_enabled()
    node_header = request.headers.get("X-StegVerse-Node-Ref", "")
    if not node_header or node_header != target_node_ref:
        raise HTTPException(status_code=403, detail="node reference binding required")
    value = next_request(target_node_ref)
    if value is None:
        return {
            "schema": "stegverse.resident-rendezvous.fetch-result/v1",
            "state": "NO_REQUEST",
            "gateway_execution_authority": "NONE",
            "authority_effect": "NONE",
        }
    return {
        "schema": "stegverse.resident-rendezvous.fetch-result/v1",
        "state": "REQUEST_AVAILABLE",
        "request": value,
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_REQUEST_ONLY",
    }


@router.post("/api/resident-rendezvous/v1/acknowledgements")
async def acknowledge_resident_request(request: Request) -> dict[str, Any]:
    _require_enabled()
    payload = await request.json()
    node_header = request.headers.get("X-StegVerse-Node-Ref", "")
    if not node_header or node_header != payload.get("target_node_ref"):
        raise HTTPException(status_code=403, detail="node reference binding required")
    try:
        return store_acknowledgement(payload)
    except ResidentRendezvousError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
