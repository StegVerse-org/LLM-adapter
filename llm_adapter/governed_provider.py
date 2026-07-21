"""Governed, vendor-neutral provider broker for bounded chat responses.

The provider is optional and disabled by default. It may generate text only after
endpoint, credential, explicit hostname allowlist, quota, input-size,
output-size, and estimated-cost checks pass. Provider output is evidence for a
bounded response; it is never authority.
"""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict, dataclass
from datetime import date
from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Any
from urllib.parse import urlparse

import requests

_LOCK = RLock()


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default).lower()).lower() == "true"


def _allowed_hosts() -> set[str]:
    return {
        item.strip().lower()
        for item in os.getenv("STEGVERSE_PROVIDER_ALLOWED_HOSTS", "").split(",")
        if item.strip()
    }


def _db_path() -> Path:
    return Path(os.getenv("STEGVERSE_TRANSITION_DB", "/tmp/stegverse-ecosystem-chat.db"))


@dataclass(frozen=True)
class ProviderReadiness:
    ready: bool
    state: str
    blockers: tuple[str, ...]
    provider_enabled_requested: bool
    endpoint_configured: bool
    endpoint_scheme_https: bool
    endpoint_hostname: str | None
    explicit_allowlist_configured: bool
    endpoint_hostname_allowlisted: bool
    credential_configured: bool
    model_configured: bool
    authority_granted: bool = False
    execution_authority: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        return payload


def readiness() -> ProviderReadiness:
    """Return secret-free provider configuration readiness.

    Readiness is configuration posture only. It does not test the provider,
    authorize cost, grant execution authority, or prove that a credential is
    valid. An empty hostname allowlist is always fail-closed.
    """
    endpoint = os.getenv("STEGVERSE_PROVIDER_ENDPOINT", "").strip()
    parsed = urlparse(endpoint)
    hostname = parsed.hostname.lower() if parsed.hostname else None
    hosts = _allowed_hosts()
    requested = _bool("STEGVERSE_PROVIDER_ENABLED")
    endpoint_configured = bool(endpoint)
    scheme_https = parsed.scheme == "https"
    allowlist_configured = bool(hosts)
    hostname_allowlisted = bool(hostname and hostname in hosts)
    credential_configured = bool(os.getenv("STEGVERSE_PROVIDER_TOKEN"))
    model_configured = bool(os.getenv("STEGVERSE_PROVIDER_MODEL"))

    blockers: list[str] = []
    if not requested:
        blockers.append("provider_not_enabled")
    if not endpoint_configured:
        blockers.append("provider_endpoint_missing")
    elif not scheme_https:
        blockers.append("provider_endpoint_not_https")
    elif not hostname:
        blockers.append("provider_endpoint_hostname_missing")
    if not allowlist_configured:
        blockers.append("provider_allowed_hosts_missing")
    elif not hostname_allowlisted:
        blockers.append("provider_endpoint_hostname_not_allowlisted")
    if not credential_configured:
        blockers.append("provider_credential_missing")
    if not model_configured:
        blockers.append("provider_model_missing")

    ready = not blockers
    return ProviderReadiness(
        ready=ready,
        state="READY" if ready else "BLOCKED",
        blockers=tuple(blockers),
        provider_enabled_requested=requested,
        endpoint_configured=endpoint_configured,
        endpoint_scheme_https=scheme_https,
        endpoint_hostname=hostname,
        explicit_allowlist_configured=allowlist_configured,
        endpoint_hostname_allowlisted=hostname_allowlisted,
        credential_configured=credential_configured,
        model_configured=model_configured,
    )


@dataclass(frozen=True)
class ProviderResult:
    used: bool
    status: str
    text: str | None
    provider_name: str | None
    model: str | None
    provider_request_id: str | None
    provider_receipt_id: str | None
    estimated_cost_usd: float
    input_units: int
    output_units: int
    fallback_required: bool
    reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProviderUsageLedger:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_usage (
                    usage_date TEXT NOT NULL,
                    provider_name TEXT NOT NULL,
                    request_count INTEGER NOT NULL DEFAULT 0,
                    estimated_cost_usd REAL NOT NULL DEFAULT 0,
                    PRIMARY KEY (usage_date, provider_name)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10)

    def current(self, provider_name: str) -> tuple[int, float]:
        with _LOCK, self._connect() as connection:
            row = connection.execute(
                "SELECT request_count, estimated_cost_usd FROM provider_usage WHERE usage_date=? AND provider_name=?",
                (date.today().isoformat(), provider_name),
            ).fetchone()
        return (int(row[0]), float(row[1])) if row else (0, 0.0)

    def record(self, provider_name: str, cost: float) -> None:
        with _LOCK, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO provider_usage(usage_date, provider_name, request_count, estimated_cost_usd)
                VALUES(?,?,1,?)
                ON CONFLICT(usage_date, provider_name) DO UPDATE SET
                    request_count=request_count+1,
                    estimated_cost_usd=estimated_cost_usd+excluded.estimated_cost_usd
                """,
                (date.today().isoformat(), provider_name, cost),
            )
            connection.commit()


def enabled() -> bool:
    return readiness().ready


def _fallback(status: str, reason: str) -> ProviderResult:
    return ProviderResult(
        used=False,
        status=status,
        text=None,
        provider_name=os.getenv("STEGVERSE_PROVIDER_NAME") or None,
        model=os.getenv("STEGVERSE_PROVIDER_MODEL") or None,
        provider_request_id=None,
        provider_receipt_id=None,
        estimated_cost_usd=0.0,
        input_units=0,
        output_units=0,
        fallback_required=True,
        reason=reason,
    )


def generate(*, message: str, transition_id: str, run_id: str) -> ProviderResult:
    provider_readiness = readiness()
    if not provider_readiness.ready:
        reason = "provider boundary blocked: " + ",".join(provider_readiness.blockers)
        return _fallback("DISABLED", reason)

    provider_name = os.getenv("STEGVERSE_PROVIDER_NAME", "governed-provider")
    model = os.environ["STEGVERSE_PROVIDER_MODEL"]
    max_input = int(os.getenv("STEGVERSE_PROVIDER_MAX_INPUT_CHARS", "12000"))
    max_output = int(os.getenv("STEGVERSE_PROVIDER_MAX_OUTPUT_CHARS", "6000"))
    daily_requests = int(os.getenv("STEGVERSE_PROVIDER_DAILY_REQUEST_LIMIT", "100"))
    daily_cost = float(os.getenv("STEGVERSE_PROVIDER_DAILY_COST_LIMIT_USD", "5.00"))
    request_cost = float(os.getenv("STEGVERSE_PROVIDER_MAX_REQUEST_COST_USD", "0.25"))
    input_rate = float(os.getenv("STEGVERSE_PROVIDER_INPUT_COST_PER_1K_CHARS_USD", "0.001"))
    output_rate = float(os.getenv("STEGVERSE_PROVIDER_OUTPUT_COST_PER_1K_CHARS_USD", "0.002"))

    if len(message) > max_input:
        return _fallback("POLICY_BLOCKED", "input exceeds governed provider character limit")

    estimated_ceiling = (len(message) / 1000 * input_rate) + (max_output / 1000 * output_rate)
    if estimated_ceiling > request_cost:
        return _fallback("COST_BLOCKED", "estimated request ceiling exceeds governed per-request cost limit")

    ledger = ProviderUsageLedger()
    count, spent = ledger.current(provider_name)
    if count >= daily_requests:
        return _fallback("QUOTA_BLOCKED", "daily provider request quota exhausted")
    if spent + estimated_ceiling > daily_cost:
        return _fallback("COST_BLOCKED", "daily provider cost ceiling would be exceeded")

    endpoint = os.environ["STEGVERSE_PROVIDER_ENDPOINT"]
    timeout = float(os.getenv("STEGVERSE_PROVIDER_TIMEOUT_SECONDS", "20"))
    request_body = {
        "schema_version": "1.0.0",
        "request_type": "governed_text_generation",
        "model": model,
        "input": message,
        "max_output_chars": max_output,
        "metadata": {
            "transition_id": transition_id,
            "run_id": run_id,
            "raw_shell_allowed": False,
            "provider_output_is_authority": False,
        },
    }
    try:
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {os.environ['STEGVERSE_PROVIDER_TOKEN']}",
                "Content-Type": "application/json",
            },
            data=json.dumps(request_body),
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError, TypeError) as exc:
        return _fallback("TRANSPORT_FAILED", type(exc).__name__)

    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        return _fallback("CONTRACT_FAILED", "provider response text missing")
    if len(text) > max_output:
        return _fallback("POLICY_BLOCKED", "provider output exceeds governed character limit")

    metadata = payload.get("metadata") or {}
    if metadata.get("transition_id") not in {None, transition_id} or metadata.get("run_id") not in {None, run_id}:
        return _fallback("IDENTITY_FAILED", "provider response identity mismatch")

    usage = payload.get("usage") or {}
    input_units = int(usage.get("input_chars", len(message)))
    output_units = int(usage.get("output_chars", len(text)))
    actual_cost = (input_units / 1000 * input_rate) + (output_units / 1000 * output_rate)
    if actual_cost > request_cost or spent + actual_cost > daily_cost:
        return _fallback("COST_BLOCKED", "reported provider usage exceeds governed cost boundary")

    request_id = str(payload.get("provider_request_id") or "unreported")
    receipt_material = "\n".join([
        provider_name,
        model,
        transition_id,
        run_id,
        request_id,
        sha256(message.encode("utf-8")).hexdigest(),
        sha256(text.encode("utf-8")).hexdigest(),
        f"{actual_cost:.8f}",
    ])
    provider_receipt = "provider-response-receipt:sha256:" + sha256(receipt_material.encode("utf-8")).hexdigest()
    ledger.record(provider_name, actual_cost)
    return ProviderResult(
        used=True,
        status="USED",
        text=text,
        provider_name=provider_name,
        model=model,
        provider_request_id=request_id,
        provider_receipt_id=provider_receipt,
        estimated_cost_usd=round(actual_cost, 8),
        input_units=input_units,
        output_units=output_units,
        fallback_required=False,
        reason=None,
    )
