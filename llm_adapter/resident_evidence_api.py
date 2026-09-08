"""Non-authorizing resident evidence rendezvous for governed SV001 custody proof."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from fastapi import APIRouter, HTTPException, Request

from llm_adapter.resident_rendezvous_api import rendezvous_enabled, rendezvous_root

router = APIRouter()

EVIDENCE_SCHEMA = "stegverse.resident-rendezvous.site-custody-evidence/v1"
STORE_SCHEMA = "stegverse.resident-rendezvous.site-custody-evidence-store/v1"
FETCH_SCHEMA = "stegverse.resident-rendezvous.site-custody-evidence-fetch/v1"
PROOF_SCHEMA = "stegos.master-records.portable-sv001-custody-proof/v1"
CANONICAL_G23 = "sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35"


class ResidentEvidenceError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_uri(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _node_ref(value: Any) -> str:
    text = str(value or "")
    if not text.startswith("SV-NODE-") or len(text) != 32:
        raise ResidentEvidenceError("canonical sovereign node ref required")
    suffix = text[8:]
    if len(suffix) != 24 or any(ch not in "0123456789abcdef" for ch in suffix):
        raise ResidentEvidenceError("canonical sovereign node ref required")
    return text


def _parse_time(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ResidentEvidenceError("submitted_at required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ResidentEvidenceError("submitted_at invalid") from exc
    if parsed.tzinfo is None:
        raise ResidentEvidenceError("submitted_at must be timezone-aware")
    return parsed.astimezone(timezone.utc).isoformat()


def validate_site_custody_proof(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ResidentEvidenceError("proof must be object")
    required = {
        "schema": PROOF_SCHEMA,
        "state": "PASS",
        "execution_surface": "CURRENT_USER_IPHONE",
        "source_receipt_sha256": CANONICAL_G23,
        "intr_governance_admission_observed": True,
        "reconstruction_state": "PASS",
        "canonical_owner": "master-records/orchestration",
        "site_custody_authority": False,
        "site_execution_authority": False,
        "heartbeat_granted_authority": False,
        "human_approval_checkpoint_inserted": False,
        "prior_receipt_authorizes_transition": False,
        "historical_state_retroactively_authorized": False,
    }
    for key, expected in required.items():
        if value.get(key) != expected:
            raise ResidentEvidenceError(f"proof {key} mismatch")
    for key in (
        "intr_admission_receipt_sha256",
        "intr_admission_journal_entry_sha256",
        "custody_hash",
        "reconstruction_hash",
        "custody_journal_entry_sha256",
        "reconstruction_journal_entry_sha256",
        "final_replay_tail_sha256",
    ):
        raw = value.get(key)
        if not isinstance(raw, str) or not raw:
            raise ResidentEvidenceError(f"proof {key} required")
    return dict(value)


def validate_envelope(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ResidentEvidenceError("evidence envelope must be object")
    required = {
        "schema", "target_node_ref", "proof", "proof_sha256", "submitted_at",
        "gateway_execution_authority", "evidence_grants_authority", "authority_effect",
    }
    if set(value) != required:
        raise ResidentEvidenceError("evidence envelope fields invalid")
    if value.get("schema") != EVIDENCE_SCHEMA:
        raise ResidentEvidenceError("evidence envelope schema mismatch")
    node_ref = _node_ref(value.get("target_node_ref"))
    proof = validate_site_custody_proof(value.get("proof"))
    if value.get("proof_sha256") != sha256_uri(proof):
        raise ResidentEvidenceError("proof digest mismatch")
    submitted_at = _parse_time(value.get("submitted_at"))
    if value.get("gateway_execution_authority") != "NONE":
        raise ResidentEvidenceError("gateway execution authority must be NONE")
    if value.get("evidence_grants_authority") is not False:
        raise ResidentEvidenceError("evidence may not grant authority")
    if value.get("authority_effect") != "NONE_EVIDENCE_ONLY":
        raise ResidentEvidenceError("authority effect mismatch")
    return {
        "schema": EVIDENCE_SCHEMA,
        "target_node_ref": node_ref,
        "proof": proof,
        "proof_sha256": value["proof_sha256"],
        "submitted_at": submitted_at,
        "gateway_execution_authority": "NONE",
        "evidence_grants_authority": False,
        "authority_effect": "NONE_EVIDENCE_ONLY",
    }


def _path(node_ref: str, *, root: Path | None = None) -> Path:
    base = root or rendezvous_root()
    directory = base / "evidence" / "site-governed-custody"
    directory.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(node_ref.encode("utf-8")).hexdigest()
    return directory / f"{digest}.json"


def store_evidence(value: Mapping[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    envelope = validate_envelope(value)
    path = _path(envelope["target_node_ref"], root=root)
    if path.is_file():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("proof_sha256") != envelope["proof_sha256"]:
            raise ResidentEvidenceError("conflicting custody proof already retained for node")
        envelope = existing
    else:
        raw = json.dumps(envelope, indent=2, sort_keys=True) + "\n"
        tmp = path.with_name("." + path.name + ".tmp")
        fd = os.open(tmp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
        try:
            os.write(fd, raw.encode("utf-8"))
        finally:
            os.close(fd)
        os.replace(tmp, path)
    return {
        "schema": STORE_SCHEMA,
        "state": "RETAINED",
        "target_node_ref": envelope["target_node_ref"],
        "proof_sha256": envelope["proof_sha256"],
        "gateway_execution_authority": "NONE",
        "evidence_grants_authority": False,
        "authority_effect": "NONE_EVIDENCE_ONLY",
    }


def fetch_evidence(node_ref: str, *, root: Path | None = None) -> dict[str, Any]:
    node = _node_ref(node_ref)
    path = _path(node, root=root)
    common = {
        "schema": FETCH_SCHEMA,
        "target_node_ref": node,
        "gateway_execution_authority": "NONE",
        "evidence_grants_authority": False,
        "authority_effect": "NONE_EVIDENCE_ONLY",
    }
    if not path.is_file():
        return {**common, "state": "NO_EVIDENCE", "evidence": None}
    evidence = validate_envelope(json.loads(path.read_text(encoding="utf-8")))
    return {**common, "state": "EVIDENCE_AVAILABLE", "evidence": evidence}


@router.post("/api/resident-rendezvous/v1/evidence/site-governed-custody")
async def store_site_custody_evidence(request: Request) -> dict[str, Any]:
    if not rendezvous_enabled():
        raise HTTPException(status_code=503, detail="resident rendezvous disabled")
    try:
        payload = await request.json()
        return store_evidence(payload)
    except ResidentEvidenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/resident-rendezvous/v1/evidence/site-governed-custody")
def fetch_site_custody_evidence(target_node_ref: str) -> dict[str, Any]:
    if not rendezvous_enabled():
        raise HTTPException(status_code=503, detail="resident rendezvous disabled")
    try:
        return fetch_evidence(target_node_ref)
    except ResidentEvidenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
