"""Same-origin HTTP adapter for the canonical StegWallet SIWE owner package.

This module intentionally owns no nonce, signature, replay, session, or revocation
logic. It exposes the canonical ``stegwallet.siwe_auth`` implementation through the
existing FastAPI gateway and fails closed when that owner package or durable runtime
configuration is unavailable.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/api/stegwallet/siwe", tags=["stegwallet-siwe"])
_OWNER: Any | None = None


class ChallengeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema: str
    wallet_address: str
    chain_id: int
    origin: str
    transaction_authority: bool = False
    execution_authority: bool = False


class VerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema: str
    challenge: dict[str, Any]
    signature: str
    transaction_authority: bool = False
    execution_authority: bool = False


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema: str
    receipt: dict[str, Any]


class RevocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema: str
    session_id: str = Field(min_length=1, max_length=200)


def _enabled() -> bool:
    return os.getenv("STEGVERSE_SIWE_ENABLED", "false").strip().lower() == "true"


def _canonical_origin() -> str:
    return os.getenv("STEGVERSE_SIWE_CANONICAL_ORIGIN", "https://stegverse.org").strip()


def _db_path() -> Path:
    configured = os.getenv("STEGVERSE_SIWE_DB", "").strip()
    if configured:
        return Path(configured)
    data_dir = Path(os.getenv("STEGVERSE_DATA_DIR", "/tmp"))
    return data_dir / "stegwallet-siwe.db"


def _load_owner() -> Any:
    global _OWNER
    if _OWNER is not None:
        return _OWNER
    try:
        from stegwallet import SiwePolicy, SiweStore, recover_with_eth_account
    except ImportError as exc:
        raise RuntimeError("stegwallet_siwe_owner_package_missing") from exc
    _OWNER = type(
        "StegWalletSiweOwner",
        (),
        {
            "SiwePolicy": SiwePolicy,
            "SiweStore": SiweStore,
            "recover_with_eth_account": staticmethod(recover_with_eth_account),
        },
    )
    return _OWNER


def _runtime() -> tuple[Any, Any, Any]:
    if not _enabled():
        raise RuntimeError("stegwallet_siwe_disabled")
    owner = _load_owner()
    path = _db_path()
    if not path.is_absolute():
        raise RuntimeError("stegwallet_siwe_db_must_be_absolute")
    path.parent.mkdir(parents=True, exist_ok=True)
    policy = owner.SiwePolicy(
        canonical_origin=_canonical_origin(),
        chain_id=8453,
        nonce_ttl_seconds=int(os.getenv("STEGVERSE_SIWE_NONCE_TTL_SECONDS", "300")),
        session_ttl_seconds=int(os.getenv("STEGVERSE_SIWE_SESSION_TTL_SECONDS", "1800")),
    )
    return owner, policy, owner.SiweStore(path)


def readiness() -> dict[str, Any]:
    blockers: list[str] = []
    owner_available = True
    if not _enabled():
        blockers.append("stegwallet_siwe_disabled")
    try:
        _load_owner()
    except RuntimeError:
        owner_available = False
        blockers.append("stegwallet_siwe_owner_package_missing")
    origin = _canonical_origin()
    if not origin.startswith("https://"):
        blockers.append("stegwallet_siwe_https_origin_required")
    path = _db_path()
    if not path.is_absolute():
        blockers.append("stegwallet_siwe_db_must_be_absolute")
    durable_requested = os.getenv(
        "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "false"
    ).strip().lower() == "true"
    if not durable_requested:
        blockers.append("stegwallet_siwe_durable_storage_not_declared")
    payload = {
        "schema": "stegwallet.siwe_gateway_readiness.v1",
        "state": "READY" if not blockers else "CONFIGURATION_REQUIRED",
        "blockers": blockers,
        "canonical_origin": origin,
        "chain_id": 8453,
        "owner_package_available": owner_available,
        "database_path_configured": path.is_absolute(),
        "durable_storage_declared": durable_requested,
        "challenge_endpoint": "/api/stegwallet/siwe/challenge",
        "verify_endpoint": "/api/stegwallet/siwe/verify",
        "session_endpoint": "/api/stegwallet/siwe/session",
        "revoke_endpoint": "/api/stegwallet/siwe/revoke",
        "wallet_authentication_enabled": not blockers,
        "transaction_authority": False,
        "execution_authority": False,
        "delegation_authority": False,
        "custody_recorded": False,
    }
    return payload


def _require_origin(request: Request, supplied: str) -> None:
    expected = _canonical_origin()
    request_origin = request.headers.get("origin")
    if supplied != expected or request_origin != expected:
        raise HTTPException(status_code=403, detail="siwe_origin_mismatch")


def _map_error(exc: Exception) -> HTTPException:
    message = str(exc) or type(exc).__name__
    if message in {
        "stegwallet_siwe_disabled",
        "stegwallet_siwe_owner_package_missing",
        "stegwallet_siwe_db_must_be_absolute",
    }:
        return HTTPException(status_code=503, detail=message)
    if "replayed" in message:
        return HTTPException(status_code=409, detail=message)
    if "expired" in message or "unknown" in message or "revoked" in message:
        return HTTPException(status_code=401, detail=message)
    return HTTPException(status_code=400, detail=message)


@router.get("/readiness")
def get_readiness() -> dict[str, Any]:
    return readiness()


@router.post("/challenge")
def issue_challenge(payload: ChallengeRequest, request: Request) -> dict[str, Any]:
    if payload.schema != "stegwallet.siwe_challenge_request.v1":
        raise HTTPException(status_code=400, detail="unsupported_siwe_challenge_request")
    if payload.chain_id != 8453:
        raise HTTPException(status_code=400, detail="unsupported_siwe_chain")
    if payload.transaction_authority is not False or payload.execution_authority is not False:
        raise HTTPException(status_code=400, detail="siwe_request_claims_authority")
    _require_origin(request, payload.origin)
    try:
        _owner, policy, store = _runtime()
        return store.issue(policy=policy, address=payload.wallet_address)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/verify")
def verify_signature(
    payload: VerificationRequest,
    request: Request,
    response: Response,
) -> dict[str, Any]:
    if payload.schema != "stegwallet.siwe_verification_request.v1":
        raise HTTPException(status_code=400, detail="unsupported_siwe_verification_request")
    if payload.transaction_authority is not False or payload.execution_authority is not False:
        raise HTTPException(status_code=400, detail="siwe_request_claims_authority")
    _require_origin(request, str(payload.challenge.get("uri", "")))
    try:
        owner, policy, store = _runtime()
        receipt = store.authenticate(
            policy=policy,
            challenge=payload.challenge,
            signature=payload.signature,
            recover_address=owner.recover_with_eth_account,
        )
    except Exception as exc:
        raise _map_error(exc) from exc
    response.set_cookie(
        key=os.getenv("STEGVERSE_SIWE_COOKIE_NAME", "stegwallet_siwe_session"),
        value=receipt["session_id"],
        max_age=int(os.getenv("STEGVERSE_SIWE_SESSION_TTL_SECONDS", "1800")),
        secure=True,
        httponly=True,
        samesite="strict",
        path="/api/stegwallet/siwe",
    )
    return receipt


@router.post("/session")
def verify_session(payload: SessionRequest, request: Request) -> dict[str, Any]:
    if payload.schema != "stegwallet.siwe_session_verification_request.v1":
        raise HTTPException(status_code=400, detail="unsupported_siwe_session_request")
    _require_origin(request, str(payload.receipt.get("uri", "")))
    try:
        _owner, _policy, store = _runtime()
        return store.verify_session(payload.receipt)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/revoke")
def revoke_session(
    payload: RevocationRequest,
    request: Request,
    response: Response,
) -> dict[str, Any]:
    if payload.schema != "stegwallet.siwe_revocation_request.v1":
        raise HTTPException(status_code=400, detail="unsupported_siwe_revocation_request")
    request_origin = request.headers.get("origin")
    if request_origin != _canonical_origin():
        raise HTTPException(status_code=403, detail="siwe_origin_mismatch")
    cookie_name = os.getenv("STEGVERSE_SIWE_COOKIE_NAME", "stegwallet_siwe_session")
    if request.cookies.get(cookie_name) != payload.session_id:
        raise HTTPException(status_code=403, detail="siwe_session_cookie_mismatch")
    try:
        _owner, _policy, store = _runtime()
        receipt = store.revoke(payload.session_id)
    except Exception as exc:
        raise _map_error(exc) from exc
    response.delete_cookie(cookie_name, path="/api/stegwallet/siwe")
    return receipt
