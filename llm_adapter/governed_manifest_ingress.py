"""Governed machine-manifest ingress/egress for external LLM frameworks.

The adapter validates transport framing and delegates governance to an injected
canonical handler. It does not implement or replace StegGate authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Callable, Mapping

INGRESS_SCHEMA = "stegverse.ingress-manifest.v1"
RESULT_SCHEMA = "stegverse.llm-adapter.governed-result.v1"
ALLOWED_STATES = {"ALLOW", "DENY", "REVIEW", "FAIL_CLOSED"}
ALLOWED_MODES = {"TEST", "LIVE_STREAM"}


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_ingress_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    required = (
        "manifest_profile", "manifest_profile_version", "source_framework",
        "source_output_id", "created_at", "candidate", "declared_intent",
        "requested_consequence", "hashes",
    )
    missing = [key for key in required if key not in manifest]
    if missing:
        raise ValueError("manifest_missing_required_fields:" + ",".join(missing))
    if manifest.get("manifest_profile") != INGRESS_SCHEMA:
        raise ValueError("manifest_profile_not_supported")
    if str(manifest.get("manifest_profile_version")) != "1":
        raise ValueError("manifest_profile_version_not_supported")
    if not isinstance(manifest.get("candidate"), Mapping):
        raise ValueError("manifest_candidate_invalid")
    hashes = manifest.get("hashes")
    if not isinstance(hashes, Mapping):
        raise ValueError("manifest_hashes_invalid")
    candidate_hash = _hash(manifest["candidate"])
    if hashes.get("candidate_sha256") != candidate_hash:
        raise ValueError("manifest_candidate_hash_mismatch")
    has_payload = "payload" in manifest and manifest.get("payload") is not None
    has_commitment = isinstance(manifest.get("payload_commitment"), str) and bool(str(manifest.get("payload_commitment")).strip())
    if has_payload == has_commitment:
        raise ValueError("manifest_requires_exactly_one_payload_or_commitment")
    if has_payload and hashes.get("payload_sha256") != _hash(manifest["payload"]):
        raise ValueError("manifest_payload_hash_mismatch")
    normalized = dict(manifest)
    normalized["external_manifest_valid"] = True
    normalized["external_manifest_grants_authority"] = False
    normalized["adapter_ingress_hash"] = _hash(normalized)
    return normalized


def _fail_closed(*, mode: str, reason: str, manifest: Mapping[str, Any] | None = None, stream_id: str | None = None, sequence: int | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "mode": mode,
        "governance_state": "FAIL_CLOSED",
        "governed_result": None,
        "manifest_receipt_id": None,
        "consequence_executed": False,
        "reason": reason,
        "stream_id": stream_id,
        "sequence": sequence,
        "adapter_is_governance_authority": False,
    }
    if manifest is not None:
        body["source_output_id"] = manifest.get("source_output_id")
    body["result_hash"] = _hash(body)
    return body


def process_manifest(
    manifest: Mapping[str, Any],
    *,
    mode: str,
    governance_handler: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    stream_id: str | None = None,
    sequence: int | None = None,
) -> dict[str, Any]:
    """Validate one machine manifest, delegate canonical governance, return a model-facing envelope."""
    mode = mode.upper()
    if mode not in ALLOWED_MODES:
        return _fail_closed(mode=mode, reason="unsupported_ingress_mode", manifest=manifest, stream_id=stream_id, sequence=sequence)
    try:
        canonical_manifest = validate_ingress_manifest(manifest)
    except ValueError as exc:
        return _fail_closed(mode=mode, reason=str(exc), manifest=manifest, stream_id=stream_id, sequence=sequence)
    try:
        governed = governance_handler(canonical_manifest)
    except Exception as exc:  # boundary converts unavailable dependencies into explicit governed failure
        return _fail_closed(mode=mode, reason=f"governance_dependency_failed:{type(exc).__name__}", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)
    state = str(governed.get("governance_state") or governed.get("disposition") or "")
    receipt_id = governed.get("manifest_receipt_id")
    if state not in ALLOWED_STATES:
        return _fail_closed(mode=mode, reason="governance_result_state_invalid", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)
    if not isinstance(receipt_id, str) or not receipt_id.startswith("MR-"):
        return _fail_closed(mode=mode, reason="governance_result_receipt_id_missing", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)
    consequence_executed = bool(governed.get("consequence_executed", False))
    if state != "ALLOW" and consequence_executed:
        return _fail_closed(mode=mode, reason="non_allow_result_claimed_consequence", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)
    body = {
        "schema": RESULT_SCHEMA,
        "mode": mode,
        "source_framework": canonical_manifest.get("source_framework"),
        "source_output_id": canonical_manifest.get("source_output_id"),
        "adapter_ingress_hash": canonical_manifest["adapter_ingress_hash"],
        "governance_state": state,
        "governed_result": governed.get("governed_result", governed.get("result")),
        "manifest_receipt_id": receipt_id,
        "verification_refs": list(governed.get("verification_refs") or []),
        "receipt_refs": list(governed.get("receipt_refs") or []),
        "consequence_executed": consequence_executed,
        "stream_id": stream_id,
        "sequence": sequence,
        "adapter_is_governance_authority": False,
        "provider_output_grants_consequence_authority": False,
    }
    body["result_hash"] = _hash(body)
    return body


@dataclass
class GovernedStreamSession:
    """Ordered per-unit governance wrapper for a live stream.

    Every unit keeps its own manifest and receipt identity. The stream provides
    continuity only; it never substitutes for per-unit governance.
    """

    stream_id: str
    governance_handler: Callable[[Mapping[str, Any]], Mapping[str, Any]]
    _next_sequence: int = 0
    _seen: dict[str, dict[str, Any]] = field(default_factory=dict)

    def process(self, manifest: Mapping[str, Any], *, sequence: int, idempotency_key: str) -> dict[str, Any]:
        if not idempotency_key:
            return _fail_closed(mode="LIVE_STREAM", reason="idempotency_key_required", manifest=manifest, stream_id=self.stream_id, sequence=sequence)
        if idempotency_key in self._seen:
            previous = self._seen[idempotency_key]
            if previous.get("source_output_id") != manifest.get("source_output_id"):
                return _fail_closed(mode="LIVE_STREAM", reason="idempotency_key_reused_for_different_input", manifest=manifest, stream_id=self.stream_id, sequence=sequence)
            return dict(previous)
        if sequence != self._next_sequence:
            return _fail_closed(mode="LIVE_STREAM", reason=f"stream_sequence_expected:{self._next_sequence}", manifest=manifest, stream_id=self.stream_id, sequence=sequence)
        result = process_manifest(
            manifest,
            mode="LIVE_STREAM",
            governance_handler=self.governance_handler,
            stream_id=self.stream_id,
            sequence=sequence,
        )
        if result["governance_state"] != "FAIL_CLOSED" or result.get("manifest_receipt_id") is not None:
            self._seen[idempotency_key] = dict(result)
            self._next_sequence += 1
        return result
