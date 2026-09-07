"""Canonical transport primitives for stegverse.intr.anthropic.transport.v1.

Optional, non-authoritative Anthropic Messages API interoperability.  The module
verifies externally supplied Interlock/InTr decisions and TV/TVC credential
materialization; it never grants those authorities itself.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, MutableMapping

PROTOCOL_VERSION = "stegverse.intr.anthropic.transport.v1"
PROVIDER = "anthropic"
ENDPOINT_PROFILE = "anthropic_messages"
ENDPOINT_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"
CREDENTIAL_AUTHORITY = "TV/TVC"
CREDENTIAL_CLASS = "TV_TVC_PROVIDER_SECRET"
AUTHORITY_EFFECT = "NONE"
NORMALIZATION_VERSION = "1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")

KNOWN_BLOCK_TYPES = {
    "text", "thinking", "redacted_thinking", "tool_use", "server_tool_use",
    "tool_result", "web_search_tool_result", "mcp_tool_use", "mcp_tool_result",
    "image", "document",
}
ADMITTED_PAYLOAD_KEYS = {
    "max_tokens", "messages", "service_tier", "stop_sequences", "system",
    "temperature", "thinking", "tool_choice", "tools", "top_k", "top_p",
}
ADMITTED_MODELS = {
    "claude-opus-5",
    "claude-sonnet-5",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
}

class FailClosed(RuntimeError):
    code = "FAIL_CLOSED"
    def __init__(self, message: str, detail: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.detail = dict(detail or {})

class CanonicalizationError(FailClosed): code = "CANONICALIZATION_ERROR"
class HashBindingMismatch(FailClosed): code = "HASH_BINDING_MISMATCH"
class AuthorityEscalation(FailClosed): code = "AUTHORITY_ESCALATION"
class EndpointRejected(FailClosed): code = "ENDPOINT_REJECTED"
class ModelRejected(FailClosed): code = "MODEL_REJECTED"
class PayloadRejected(FailClosed): code = "PAYLOAD_REJECTED"
class CredentialLeak(FailClosed): code = "CREDENTIAL_LEAK"
class EgressRejected(FailClosed): code = "EGRESS_REJECTED"
class CustodyRejected(FailClosed): code = "CUSTODY_REJECTED"

@dataclass(frozen=True)
class ProviderRequest:
    provider: str
    model: str
    endpoint_profile: str
    payload: Mapping[str, Any]
    request_hash: str
    transition_id: str
    session_id: str

@dataclass(frozen=True)
class IngressDecision:
    disposition: str
    request_hash: str
    transition_id: str
    ingress_receipt_hash: str
    carrier_ref: str
    authority: str = "Interlock/InTr"

@dataclass(frozen=True)
class EgressDecision:
    disposition: str
    response_hash: str
    egress_receipt_hash: str
    authority: str = "Interlock/InTr"

@dataclass(frozen=True)
class TransportConfig:
    endpoint_profile: str = ENDPOINT_PROFILE
    endpoint_url: str = ENDPOINT_URL
    anthropic_api_version: str = ANTHROPIC_API_VERSION
    allow_unknown_block_types: bool = False

@dataclass
class EphemeralCredential:
    _secret: str
    def headers(self, api_version: str) -> dict[str, str]:
        if not self._secret:
            raise FailClosed("empty TV/TVC credential")
        return {
            "x-api-key": self._secret,
            "anthropic-version": api_version,
            "content-type": "application/json",
        }
    def assert_absent_from(self, value: Any) -> None:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
        if self._secret and self._secret in encoded:
            raise CredentialLeak("credential material appeared in durable artifact")
    def clear(self) -> None:
        self._secret = ""


def _check_key(key: str) -> None:
    if not isinstance(key, str) or any(ord(c) > 0xFFFF for c in key):
        raise CanonicalizationError("object keys must be BMP strings")


def _canon(value: Any) -> str:
    if value is None: return "null"
    if value is True: return "true"
    if value is False: return "false"
    if isinstance(value, int) and not isinstance(value, bool): return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("non-finite float")
        if value == 0: return "0"
        if value.is_integer() and abs(value) < 1e17: return str(int(value))
        rendered = repr(value)
        if "e" in rendered.lower():
            raise CanonicalizationError("exponent-form float rejected")
        return rendered
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_canon(v) for v in value) + "]"
    if isinstance(value, Mapping):
        for k in value: _check_key(k)
        return "{" + ",".join(
            json.dumps(k, ensure_ascii=False) + ":" + _canon(value[k])
            for k in sorted(value)
        ) + "}"
    raise CanonicalizationError(f"unsupported type: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return _canon(value)


def digest(domain: str, value: Any) -> str:
    return hashlib.sha256((domain + "\n" + canonical_json(value)).encode("utf-8")).hexdigest()


def _require_hex(value: str, label: str) -> None:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise HashBindingMismatch(f"{label} must be lowercase sha256")


def compute_request_hash(request: ProviderRequest | Mapping[str, Any]) -> str:
    if isinstance(request, ProviderRequest):
        basis = {
            "provider": request.provider,
            "model": request.model,
            "endpoint_profile": request.endpoint_profile,
            "payload": dict(request.payload),
        }
    else:
        basis = dict(request)
    return digest(PROTOCOL_VERSION + "/request", basis)


def compute_transport_id(*, transition_id: str, request_hash: str, ingress_receipt_hash: str,
                         carrier_ref: str, endpoint_profile: str) -> str:
    basis = {
        "protocol_version": PROTOCOL_VERSION,
        "transition_id": transition_id,
        "request_hash": request_hash,
        "ingress_receipt_hash": ingress_receipt_hash,
        "carrier_ref": carrier_ref,
        "endpoint_profile": endpoint_profile,
    }
    return "svintr-anth-" + digest(PROTOCOL_VERSION + "/transport_id", basis)


def verify_ingress(decision: IngressDecision, request: ProviderRequest) -> None:
    if request.provider != PROVIDER:
        raise PayloadRejected("provider must be anthropic")
    if decision.disposition != "ALLOW" or decision.authority != "Interlock/InTr":
        raise FailClosed("external ingress ALLOW required")
    recomputed = compute_request_hash(request)
    if request.request_hash != recomputed or decision.request_hash != recomputed:
        raise HashBindingMismatch("request hash binding mismatch")
    if decision.transition_id != request.transition_id:
        raise HashBindingMismatch("transition id mismatch")
    _require_hex(decision.ingress_receipt_hash, "ingress_receipt_hash")
    if not decision.carrier_ref:
        raise FailClosed("carrier_ref required")


def verify_endpoint(config: TransportConfig, request: ProviderRequest) -> dict[str, str]:
    if request.endpoint_profile != ENDPOINT_PROFILE or config.endpoint_profile != ENDPOINT_PROFILE:
        raise EndpointRejected("endpoint profile substitution rejected")
    if config.endpoint_url != ENDPOINT_URL:
        raise EndpointRejected("endpoint URL substitution rejected")
    if config.anthropic_api_version != ANTHROPIC_API_VERSION:
        raise EndpointRejected("Anthropic API version not admitted")
    if request.model not in ADMITTED_MODELS:
        raise ModelRejected("model is not explicitly admitted")
    return {"method": "POST", "url": ENDPOINT_URL, "anthropic_api_version": ANTHROPIC_API_VERSION}


def build_transport_envelope(request: ProviderRequest, ingress: IngressDecision,
                             config: TransportConfig) -> dict[str, Any]:
    verify_ingress(ingress, request)
    verify_endpoint(config, request)
    tid = compute_transport_id(
        transition_id=request.transition_id,
        request_hash=request.request_hash,
        ingress_receipt_hash=ingress.ingress_receipt_hash,
        carrier_ref=ingress.carrier_ref,
        endpoint_profile=request.endpoint_profile,
    )
    return {
        "protocol_version": PROTOCOL_VERSION,
        "transport_id": tid,
        "transition_id": request.transition_id,
        "request_hash": request.request_hash,
        "provider": PROVIDER,
        "model": request.model,
        "endpoint_profile": request.endpoint_profile,
        "ingress_receipt_hash": ingress.ingress_receipt_hash,
        "credential_authority": CREDENTIAL_AUTHORITY,
        "credential_class": CREDENTIAL_CLASS,
        "carrier_ref": ingress.carrier_ref,
        "authority_effect": AUTHORITY_EFFECT,
        "egress_intr_required": True,
        "credential_material_present": False,
    }


def envelope_hash(envelope: Mapping[str, Any]) -> str:
    return digest(PROTOCOL_VERSION + "/envelope", dict(envelope))


def _validate_payload(payload: Mapping[str, Any], model: str) -> None:
    unknown = set(payload) - ADMITTED_PAYLOAD_KEYS
    if unknown:
        raise PayloadRejected("unadmitted payload keys", {"keys": sorted(unknown)})
    if not isinstance(payload.get("messages"), list) or not payload["messages"]:
        raise PayloadRejected("messages must be a non-empty array")
    if not isinstance(payload.get("max_tokens"), int) or payload["max_tokens"] <= 0:
        raise PayloadRejected("positive max_tokens required")
    if "stream" in payload:
        raise PayloadRejected("streaming unsupported in v1")
    if model in {"claude-opus-5", "claude-sonnet-5"}:
        thinking = payload.get("thinking")
        if thinking is not None:
            if not isinstance(thinking, Mapping) or thinking.get("type") not in {"adaptive", "disabled"}:
                raise PayloadRejected("Claude 5 admits only adaptive or disabled thinking")
    if model in {"claude-opus-5", "claude-sonnet-5"}:
        for msg in payload.get("messages", []):
            if isinstance(msg, Mapping) and msg.get("role") == "assistant":
                raise PayloadRejected("Claude 5 assistant-message prefill rejected")
    if model in {"claude-opus-5", "claude-sonnet-5"}:
        if "top_k" in payload:
            raise PayloadRejected("top_k rejected for admitted Claude 5 models")
        if "temperature" in payload and payload["temperature"] != 1:
            raise PayloadRejected("non-default temperature rejected for admitted Claude 5 models")
        if "top_p" in payload and payload["top_p"] != 1:
            raise PayloadRejected("non-default top_p rejected for admitted Claude 5 models")


def map_request_to_anthropic(request: ProviderRequest, config: TransportConfig) -> dict[str, Any]:
    verify_endpoint(config, request)
    _validate_payload(request.payload, request.model)
    wire = dict(request.payload)
    wire["model"] = request.model
    return wire


def normalize_content_blocks(content: Any, *, allow_unknown_block_types: bool = False) -> tuple[list[dict[str, Any]], str, bool]:
    if not isinstance(content, list):
        raise PayloadRejected("provider content must be an array")
    out: list[dict[str, Any]] = []
    text_parts: list[str] = []
    lossy = False
    for i, raw in enumerate(content):
        if not isinstance(raw, Mapping):
            raise PayloadRejected("content block must be an object")
        t = raw.get("type")
        if not isinstance(t, str) or not t:
            raise PayloadRejected("content block type required")
        if t not in KNOWN_BLOCK_TYPES and not allow_unknown_block_types:
            raise PayloadRejected("unknown content block type", {"type": t})
        block = dict(raw)
        row: dict[str, Any] = {"index": i, "type": t, "material": t != "text", "block": block}
        if t == "text":
            text = block.get("text")
            if not isinstance(text, str):
                raise PayloadRejected("text block requires string text")
            row["text"] = text
            text_parts.append(text)
        else:
            lossy = True
        if t in {"tool_use", "server_tool_use", "mcp_tool_use"}:
            if isinstance(block.get("name"), str): row["tool_name"] = block["name"]
            if isinstance(block.get("id"), str): row["tool_use_id"] = block["id"]
        out.append(row)
    return out, "\n".join(text_parts), lossy


def normalize_provider_response(raw: Any, envelope: Mapping[str, Any], endpoint: Mapping[str, Any],
                                config: TransportConfig) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise PayloadRejected("provider response must be an object")
    response_id = raw.get("id")
    runtime_model = raw.get("model")
    if not isinstance(response_id, str) or not response_id:
        raise PayloadRejected("provider response id required")
    if not isinstance(runtime_model, str) or not runtime_model:
        raise PayloadRejected("provider runtime model required")
    if runtime_model != envelope["model"]:
        raise PayloadRejected("runtime model differs from admitted model")
    blocks, output, lossy = normalize_content_blocks(raw.get("content"), allow_unknown_block_types=config.allow_unknown_block_types)
    usage = raw.get("usage") if isinstance(raw.get("usage"), Mapping) else {}
    metadata = {
        "provider_mode": "anthropic_messages_intr_transport",
        "response_id": response_id,
        "stop_reason": raw.get("stop_reason"),
        "stop_sequence": raw.get("stop_sequence"),
        "runtime_model": runtime_model,
        "runtime_model_matches_admitted": True,
        "usage": dict(usage),
        "transport_id": envelope["transport_id"],
        "ingress_receipt_hash": envelope["ingress_receipt_hash"],
        "anthropic_api_version": endpoint["anthropic_api_version"],
        "credential_authority": CREDENTIAL_AUTHORITY,
        "credential_material_present": False,
        "egress_intr_required": True,
        "authority_effect": AUTHORITY_EFFECT,
        "normalization_version": NORMALIZATION_VERSION,
        "unknown_block_types_admitted": bool(config.allow_unknown_block_types),
        "output_is_lossy_projection": lossy,
    }
    return {
        "provider": PROVIDER,
        "model": envelope["model"],
        "output": output,
        "normalized_blocks": blocks,
        "request_hash": envelope["request_hash"],
        "metadata": metadata,
        "authority_effect": AUTHORITY_EFFECT,
        "egress_intr_required": True,
    }


def compute_response_hash(response: Mapping[str, Any]) -> str:
    basis = {
        "provider": response["provider"],
        "model": response["model"],
        "normalized_output": response["output"],
        "normalized_blocks": response["normalized_blocks"],
        "request_hash": response["request_hash"],
        "normalized_metadata": response["metadata"],
    }
    return digest(PROTOCOL_VERSION + "/response", basis)


def build_transport_evidence(envelope: Mapping[str, Any], env_hash: str,
                             response: Mapping[str, Any]) -> dict[str, Any]:
    _require_hex(env_hash, "envelope_hash")
    response_hash = compute_response_hash(response)
    return {
        "protocol_version": PROTOCOL_VERSION,
        "transport_id": envelope["transport_id"],
        "transition_id": envelope["transition_id"],
        "request_hash": envelope["request_hash"],
        "envelope_hash": env_hash,
        "ingress_receipt_hash": envelope["ingress_receipt_hash"],
        "provider": PROVIDER,
        "model": envelope["model"],
        "response_hash": response_hash,
        "egress_intr_required": True,
        "authority_effect": AUTHORITY_EFFECT,
        "credential_authority": CREDENTIAL_AUTHORITY,
        "credential_material_present": False,
    }


def project_usage(response: Mapping[str, Any], envelope: Mapping[str, Any], evidence: Mapping[str, Any], session_id: str) -> dict[str, Any]:
    usage = dict(response["metadata"].get("usage", {}))
    i = usage.get("input_tokens") if isinstance(usage.get("input_tokens"), int) else None
    o = usage.get("output_tokens") if isinstance(usage.get("output_tokens"), int) else None
    total = i + o if i is not None and o is not None else None
    measurement_id = "meas-" + digest(PROTOCOL_VERSION + "/measurement", {
        "transport_id": envelope["transport_id"],
        "transition_id": envelope["transition_id"],
        "response_hash": evidence["response_hash"],
    })
    return {
        "protocol_version": PROTOCOL_VERSION,
        "measurement_id": measurement_id,
        "session_id": session_id,
        "transition_id": envelope["transition_id"],
        "provider": PROVIDER,
        "model": envelope["model"],
        "interaction_type": "governed_anthropic_inference",
        "origin_entry_point": "intr",
        "metrics": {"input_units": i, "output_units": o, "total_units": total, "metrics_complete": total is not None},
        "provider_native_usage": usage,
        "receipt_refs": {
            "ingress_receipt_hash": envelope["ingress_receipt_hash"],
            "envelope_hash": evidence["envelope_hash"],
            "response_hash": evidence["response_hash"],
        },
        "authority_effect": AUTHORITY_EFFECT,
        "credential_material_present": False,
    }


def build_master_records_handoff(envelope: Mapping[str, Any], evidence: Mapping[str, Any],
                                 response: Mapping[str, Any], usage: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "stegverse.master-records.provider-usage-handoff/v1",
        "provider": PROVIDER,
        "transport_id": envelope["transport_id"],
        "transition_id": envelope["transition_id"],
        "envelope_hash": evidence["envelope_hash"],
        "response_hash": evidence["response_hash"],
        "envelope": dict(envelope),
        "normalized_response": dict(response),
        "usage_event": dict(usage),
        "credential_material_present": False,
        "authority_effect": AUTHORITY_EFFECT,
        "custody_grants_authority": False,
    }


def verify_master_records_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise CustodyRejected("Master Records receipt object required")
    out = dict(receipt)
    if out.get("accepted") is not True:
        raise CustodyRejected("Master Records did not accept custody")
    if out.get("authority_effect", "NONE") != "NONE":
        raise AuthorityEscalation("custody receipt may not grant authority")
    return out


def resolve_credential(resolver: Callable[[Mapping[str, Any]], str], request: Mapping[str, Any]) -> EphemeralCredential:
    if request.get("credential_authority") != CREDENTIAL_AUTHORITY:
        raise AuthorityEscalation("credential authority must remain TV/TVC")
    secret = resolver(dict(request))
    if not isinstance(secret, str) or not secret:
        raise FailClosed("TV/TVC credential resolver returned no secret")
    return EphemeralCredential(secret)


def verify_egress(evidence: Mapping[str, Any], decision: EgressDecision) -> dict[str, Any]:
    if decision.disposition != "ALLOW" or decision.authority != "Interlock/InTr":
        raise EgressRejected("external egress ALLOW required")
    if decision.response_hash != evidence.get("response_hash"):
        raise HashBindingMismatch("egress response hash mismatch")
    _require_hex(decision.egress_receipt_hash, "egress_receipt_hash")
    return {
        "state": "EGRESS_ADMITTED",
        "transition_authority": "Interlock/InTr",
        "authority_effect": "NONE_LOCAL",
        "response_hash": evidence["response_hash"],
        "egress_receipt_hash": decision.egress_receipt_hash,
        "decision_origin": "external_interlock_intr",
        "locally_generated_allow": False,
    }


def assert_no_credential_material(value: Any, *, label: str = "artifact") -> None:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    prohibited = ("api_key", "apikey", "authorization", "bearer ", "x-api-key")
    if any(token in text for token in prohibited):
        raise CredentialLeak(f"credential-shaped material in {label}")
