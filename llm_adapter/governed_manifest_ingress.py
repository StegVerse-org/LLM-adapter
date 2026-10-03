"""Governed machine-manifest ingress/egress for external LLM frameworks.

The adapter validates transport framing and delegates governance to an injected
canonical handler. It does not implement or replace StegGate authority.

The manifest may request how transition evidence is projected back to the
external caller. That projection never suppresses canonical Master Records
custody or alters the governed transition history.
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
RETURN_PROJECTION_MODES = {"ALL", "SELECTED", "NONE"}


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _normalize_return_projection(value: Mapping[str, Any] | None) -> dict[str, Any]:
    projection = dict(value or {})
    mode = str(projection.get("mode") or "ALL").strip().upper()
    if mode not in RETURN_PROJECTION_MODES:
        raise ValueError("manifest_return_projection_mode_invalid")
    selected = projection.get("transition_classes") or []
    if not isinstance(selected, list) or not all(isinstance(item, str) and item.strip() for item in selected):
        raise ValueError("manifest_return_projection_classes_invalid")
    selected = list(dict.fromkeys(item.strip() for item in selected))
    if mode == "SELECTED" and not selected:
        raise ValueError("manifest_return_projection_selected_requires_classes")
    if mode != "SELECTED" and selected:
        raise ValueError("manifest_return_projection_classes_only_for_selected")
    return {
        "mode": mode,
        "transition_classes": selected,
        "controls_user_return_only": True,
        "suppresses_master_records_custody": False,
        "erases_ecosystem_transitions": False,
        "grants_authority": False,
    }


def validate_ingress_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    required = (
        "manifest_profile", "manifest_profile_version", "source_framework",
        "source_output_id", "created_at", "candidate", "declared_intent",
        "requested_consequence", "hashes", "processing", "node_endpoint", "predecessor",
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
    processing = manifest.get("processing")
    if not isinstance(processing, Mapping):
        raise ValueError("manifest_processing_invalid")
    capability = str(processing.get("capability") or "").strip()
    route_id = str(processing.get("route_id") or "").strip()
    if not capability or not route_id:
        raise ValueError("manifest_processing_capability_route_required")
    node_endpoint = manifest.get("node_endpoint")
    if not isinstance(node_endpoint, Mapping) or not str(node_endpoint.get("node_id") or "").strip():
        raise ValueError("recognized_node_endpoint_required")
    if node_endpoint.get("recognized") is not True:
        raise ValueError("recognized_node_endpoint_required")
    predecessor = manifest["predecessor"]
    generation = manifest.get("generation")
    if predecessor is None:
        if generation != 1:
            raise ValueError("genesis_requires_generation_one")
        standing_mode = "ESTABLISH_GENESIS"
    else:
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 2:
            raise ValueError("existing_node_requires_generation_beyond_one")
        if not isinstance(predecessor, Mapping):
            raise ValueError("existing_node_predecessor_invalid")
        required_predecessor = ("generation", "manifest_sha256", "result_sha256", "heartbeat_epoch")
        if set(predecessor) != set(required_predecessor):
            raise ValueError("existing_node_predecessor_fields_invalid")
        if predecessor.get("generation") != generation - 1:
            raise ValueError("existing_node_predecessor_generation_mismatch")
        for key in ("manifest_sha256", "result_sha256"):
            value = predecessor.get(key)
            if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError(f"existing_node_predecessor_{key}_invalid")
        epoch = predecessor.get("heartbeat_epoch")
        if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 1:
            raise ValueError("existing_node_predecessor_heartbeat_epoch_invalid")
        standing_mode = "VERIFY_EXISTING"
    normalized = dict(manifest)
    normalized["return_projection"] = _normalize_return_projection(manifest.get("return_projection"))
    normalized["node_standing_mode"] = standing_mode
    normalized["external_manifest_valid"] = True
    normalized["external_manifest_grants_authority"] = False
    normalized["master_records_transition_custody_independent_of_return_projection"] = True
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


def _project_transition_evidence(governed: Mapping[str, Any], projection: Mapping[str, Any]) -> tuple[list[Any], list[str], list[str]]:
    mode = projection["mode"]
    evidence = list(governed.get("transition_evidence") or [])
    verification_refs = list(governed.get("verification_refs") or [])
    receipt_refs = list(governed.get("receipt_refs") or [])
    if mode == "NONE":
        return [], [], []
    if mode == "ALL":
        return evidence, verification_refs, receipt_refs
    selected = set(projection["transition_classes"])
    filtered: list[Any] = []
    for item in evidence:
        if isinstance(item, Mapping) and str(item.get("transition_class") or "") in selected:
            filtered.append(dict(item))
    return filtered, verification_refs, receipt_refs


def build_sdk_manifest_intr_transfer(canonical_manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Build the existing-boundary transfer into the distributed SDK manifest endpoint.

    This envelope is transport/framing only. The manifest's processing declaration,
    not source/provider identity and not this adapter, selects processing downstream.
    """
    processing = canonical_manifest["processing"]
    node = canonical_manifest["node_endpoint"]
    body = {
        "schema": "stegverse.sdk-manifest.intr-transfer/v1",
        "protocol": "InTr",
        "interlock_required": True,
        "source_node_id": node["node_id"],
        "source_node_recognized": True,
        "destination": "DISTRIBUTED_SDK_MANIFEST_ENDPOINT",
        "manifest": dict(canonical_manifest),
        "manifest_sha256": _hash(canonical_manifest),
        "canonical_node_standing": {
            "mode": canonical_manifest["node_standing_mode"],
            "generation": canonical_manifest["generation"],
            "predecessor": canonical_manifest["predecessor"],
        },
        "requested_processing": {
            "capability": processing["capability"],
            "route_id": processing["route_id"],
        },
        "adapter_selects_processing": False,
        "source_identity_selects_processing": False,
        "transport_grants_execution_authority": False,
        "authority_effect": "NONE",
    }
    body["transfer_sha256"] = _hash(body)
    return body


def process_manifest(
    manifest: Mapping[str, Any],
    *,
    mode: str,
    sdk_manifest_endpoint: Callable[[Mapping[str, Any]], Mapping[str, Any]],
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
        governed = sdk_manifest_endpoint(build_sdk_manifest_intr_transfer(canonical_manifest))
    except Exception as exc:
        return _fail_closed(mode=mode, reason=f"sdk_manifest_endpoint_failed:{type(exc).__name__}", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)
    state = str(governed.get("governance_state") or governed.get("disposition") or "")
    receipt_id = governed.get("manifest_receipt_id")
    if state not in ALLOWED_STATES:
        return _fail_closed(mode=mode, reason="governance_result_state_invalid", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)
    if not isinstance(receipt_id, str) or not receipt_id.startswith("MR-"):
        return _fail_closed(mode=mode, reason="governance_result_receipt_id_missing", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)
    consequence_executed = bool(governed.get("consequence_executed", False))
    if state != "ALLOW" and consequence_executed:
        return _fail_closed(mode=mode, reason="non_allow_result_claimed_consequence", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)

    projection = canonical_manifest["return_projection"]
    transition_evidence, verification_refs, receipt_refs = _project_transition_evidence(governed, projection)
    body = {
        "schema": RESULT_SCHEMA,
        "mode": mode,
        "source_framework": canonical_manifest.get("source_framework"),
        "source_output_id": canonical_manifest.get("source_output_id"),
        "adapter_ingress_hash": canonical_manifest["adapter_ingress_hash"],
        "governance_state": state,
        "governed_result": governed.get("governed_result", governed.get("result")),
        "manifest_receipt_id": receipt_id,
        "return_projection": projection,
        "transition_evidence": transition_evidence,
        "verification_refs": verification_refs,
        "receipt_refs": receipt_refs,
        "consequence_executed": consequence_executed,
        "master_records_transition_custody_independent_of_return_projection": True,
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
    sdk_manifest_endpoint: Callable[[Mapping[str, Any]], Mapping[str, Any]]
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
            sdk_manifest_endpoint=self.sdk_manifest_endpoint,
            stream_id=self.stream_id,
            sequence=sequence,
        )
        if result["governance_state"] != "FAIL_CLOSED" or result.get("manifest_receipt_id") is not None:
            self._seen[idempotency_key] = dict(result)
            self._next_sequence += 1
        return result
