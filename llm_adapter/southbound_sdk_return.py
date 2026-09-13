"""Generic final StegVerse-side transition for SDK-bound framework returns.

Consumes an exact SDK Publisher-return binding, preserves it byte-for-byte, and
prepares the existing Interlock/InTr egress handoff. This module does not admit
InTr egress or claim the far-side transition.
"""
from __future__ import annotations

import base64
import hashlib
import json
from typing import Any, Mapping

SDK_BINDING_SCHEMA = "stegverse.sdk.publisher-return-binding/v1"
TRANSITION_SCHEMA = "stegverse.llm-adapter.southbound-final-transition/v1"
HANDOFF_SCHEMA = "stegverse.llm-adapter.southbound-intr-egress-handoff/v1"

class SouthboundSDKReturnError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def prepare_sdk_return_for_intr(sdk_binding_bytes: bytes, *, transition_id: str) -> dict[str, Any]:
    if not isinstance(sdk_binding_bytes, bytes) or not sdk_binding_bytes:
        raise SouthboundSDKReturnError("exact SDK binding bytes required")
    try:
        binding = json.loads(sdk_binding_bytes.decode("utf-8"))
    except Exception as exc:
        raise SouthboundSDKReturnError("SDK binding JSON invalid") from exc
    if not isinstance(binding, Mapping) or _canonical(binding) != sdk_binding_bytes:
        raise SouthboundSDKReturnError("SDK binding bytes must be canonical JSON")
    if binding.get("schema") != SDK_BINDING_SCHEMA:
        raise SouthboundSDKReturnError("SDK binding schema invalid")
    if binding.get("communication_state") != "READY_FOR_FINAL_STEGVERSE_EGRESS_TRANSITION":
        raise SouthboundSDKReturnError("SDK binding not ready for final StegVerse egress transition")
    if binding.get("authority_effect") != "NONE" or binding.get("communication_complete") is not False:
        raise SouthboundSDKReturnError("SDK binding authority/completion boundary invalid")
    egress = binding.get("egress")
    if not isinstance(egress, Mapping):
        raise SouthboundSDKReturnError("SDK binding egress declaration missing")
    if egress.get("final_stegverse_transition_surface") != "LLM_ADAPTER":
        raise SouthboundSDKReturnError("SDK binding not addressed to LLM_ADAPTER")
    if egress.get("transport") != "INTERLOCK_INTR" or egress.get("far_side_transition_required") is not True:
        raise SouthboundSDKReturnError("SDK binding does not require canonical InTr/far-side transition")
    if not isinstance(transition_id, str) or not transition_id.strip():
        raise SouthboundSDKReturnError("transition_id required")

    binding_hash = _sha(sdk_binding_bytes)
    declared_binding_hash = binding.get("binding_sha256")
    if not isinstance(declared_binding_hash, str) or not declared_binding_hash.startswith("sha256:"):
        raise SouthboundSDKReturnError("SDK binding digest missing")

    handoff = {
        "schema": HANDOFF_SCHEMA,
        "protocol": "InTr",
        "transition_id": transition_id.strip(),
        "manifest_receipt_id": binding.get("manifest_receipt_id"),
        "sdk_binding_sha256": binding_hash,
        "sdk_declared_binding_sha256": declared_binding_hash,
        "payload_media_type": "application/json",
        "payload_base64": base64.b64encode(sdk_binding_bytes).decode("ascii"),
        "requested_disposition": "ALLOW",
        "egress_intr_required": True,
        "far_side_transition_required": True,
        "credential_material_present": False,
        "authority_effect": "NONE",
    }
    transition = {
        "schema": TRANSITION_SCHEMA,
        "direction": "SOUTH",
        "state": "FINAL_STEGVERSE_SIDE_TRANSITION_PREPARED",
        "transition_surface": "LLM_ADAPTER",
        "transition_id": transition_id.strip(),
        "manifest_receipt_id": binding.get("manifest_receipt_id"),
        "initiator": binding.get("initiator"),
        "sdk_binding_sha256": binding_hash,
        "intr_handoff": handoff,
        "final_stegverse_transition_surface_reached": True,
        "interlock_intr_egress_admitted": False,
        "far_side_transition_observed": False,
        "communication_complete": False,
        "authority_effect": "NONE",
    }
    transition["transition_sha256"] = _sha(_canonical(transition))
    return transition


def admit_intr_egress(transition: Mapping[str, Any], *, disposition: str, egress_receipt_hash: str, admitted_sdk_binding_sha256: str) -> dict[str, Any]:
    """Record authentic InTr admission only after Interlock/InTr supplies it."""
    if transition.get("schema") != TRANSITION_SCHEMA:
        raise SouthboundSDKReturnError("southbound transition schema invalid")
    handoff = transition.get("intr_handoff")
    if not isinstance(handoff, Mapping) or handoff.get("egress_intr_required") is not True:
        raise SouthboundSDKReturnError("southbound InTr handoff invalid")
    if disposition != "ALLOW":
        raise SouthboundSDKReturnError("southbound SDK return requires InTr ALLOW")
    if not isinstance(egress_receipt_hash, str) or len(egress_receipt_hash) != 64 or any(c not in "0123456789abcdef" for c in egress_receipt_hash):
        raise SouthboundSDKReturnError("egress_receipt_hash must be lowercase sha256")
    if admitted_sdk_binding_sha256 != handoff.get("sdk_binding_sha256"):
        raise SouthboundSDKReturnError("InTr admission does not bind exact SDK return")
    return {
        "schema": "stegverse.llm-adapter.southbound-intr-egress-admission/v1",
        "transition_id": transition.get("transition_id"),
        "manifest_receipt_id": transition.get("manifest_receipt_id"),
        "sdk_binding_sha256": admitted_sdk_binding_sha256,
        "egress_receipt_hash": egress_receipt_hash,
        "state": "EGRESS_ADMITTED",
        "transition_authority": "Interlock/InTr",
        "far_side_transition_observed": False,
        "communication_complete": False,
        "authority_effect": "NONE_LOCAL",
    }

__all__ = ["SouthboundSDKReturnError", "prepare_sdk_return_for_intr", "admit_intr_egress"]
