from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

UNIVERSAL_INTR_SCHEMA = "stegverse.universal-intr-transport/v1"
HOP_RECEIPT_SCHEMA = "stegverse.intr.hop_receipt/v1"
PAYLOAD_BINDING_SCHEMA = "stegverse.hil.intr_payload_binding/v1"
CHAIN_SCHEMA = "stegverse.hil.intr_receipt_chain/v2"

PRIMARY_SHA256 = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT_SHA256 = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"
PROTOCOL_VERSION = "HIL-PROTOCOL-v1.1"

UNIVERSAL_FIELDS = {
    "schema", "protocol", "operation_id", "packet_id", "payload_hash",
    "prior_transport_receipt_hash", "source", "destination", "boundary_path",
    "interlock_required", "transport_semantics", "authority", "receipt_chain",
}
HOP_FIELDS = {
    "schema", "receipt_id", "packet_id", "hop_index", "direction", "from_role",
    "to_role", "operation_hash", "payload_hash", "prior_receipt_hash",
    "boundary_identity_ref", "boundary_verification", "transition_state",
    "secret_plaintext_present", "authority_transfer", "recorded_at", "receipt_hash",
}

TRANSPORT_SEMANTICS = {
    "event_triggered": True,
    "always_on_receiver_required": False,
    "second_user_device_required": False,
    "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
    "exact_packet_transport_retry_allowed": True,
    "blind_consequence_retry_allowed": False,
}
AUTHORITY = {
    "authority_transfer": False,
    "transport_grants_execution_authority": False,
    "credential_authority": "TV/TVC",
}
RECEIPT_POLICY = {
    "required": True,
    "receipt_schema": HOP_RECEIPT_SCHEMA,
    "payload_plaintext_in_receipts": False,
    "prior_hash_required_after_first_hop": True,
}


class HILInTrError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def is_digest_uri(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    tail = value[7:]
    return len(tail) == 64 and all(ch in "0123456789abcdef" for ch in tail)


def payload_binding(*, response_sha256: str, provenance_sha256: str) -> dict[str, Any]:
    return {
        "schema": PAYLOAD_BINDING_SCHEMA,
        "protocol": PROTOCOL_VERSION,
        "response_sha256": f"sha256:{response_sha256}",
        "provenance_sha256": f"sha256:{provenance_sha256}",
        "primary_sha256": f"sha256:{PRIMARY_SHA256}",
        "prompt_sha256": f"sha256:{PROMPT_SHA256}",
    }


def operation_hash(intent: Mapping[str, Any]) -> str:
    return digest_uri({
        "operation_id": intent.get("operation_id"),
        "packet_id": intent.get("packet_id"),
        "payload_hash": intent.get("payload_hash"),
    })


def transport_intent_hash(intent: Mapping[str, Any]) -> str:
    return digest_uri(dict(intent))


def _validate_endpoint(value: Any, *, boundary: str, subsystem: str, label: str) -> None:
    if not isinstance(value, Mapping):
        raise HILInTrError(f"{label}_endpoint_required")
    if set(value) != {"boundary", "subsystem"}:
        raise HILInTrError(f"{label}_endpoint_shape_invalid")
    if value.get("boundary") != boundary or value.get("subsystem") != subsystem:
        raise HILInTrError(f"{label}_endpoint_binding_invalid")


def _validate_universal_common(intent: Mapping[str, Any]) -> None:
    if set(intent) != UNIVERSAL_FIELDS:
        raise HILInTrError("universal_intr_field_set_invalid")
    if intent.get("schema") != UNIVERSAL_INTR_SCHEMA or intent.get("protocol") != "InTr":
        raise HILInTrError("universal_intr_protocol_invalid")
    for field in ("operation_id", "packet_id"):
        if not isinstance(intent.get(field), str) or not intent[field]:
            raise HILInTrError(f"universal_intr_{field}_required")
    if not is_digest_uri(intent.get("payload_hash")):
        raise HILInTrError("universal_intr_payload_hash_invalid")
    prior = intent.get("prior_transport_receipt_hash")
    if prior is not None and not is_digest_uri(prior):
        raise HILInTrError("universal_intr_prior_receipt_hash_invalid")
    if not isinstance(intent.get("boundary_path"), list) or not intent["boundary_path"]:
        raise HILInTrError("universal_intr_boundary_path_invalid")
    if intent.get("interlock_required") is not True:
        raise HILInTrError("universal_intr_interlock_required")
    if intent.get("transport_semantics") != TRANSPORT_SEMANTICS:
        raise HILInTrError("universal_intr_transport_semantics_invalid")
    if intent.get("authority") != AUTHORITY:
        raise HILInTrError("universal_intr_authority_invalid")
    if intent.get("receipt_chain") != RECEIPT_POLICY:
        raise HILInTrError("universal_intr_receipt_policy_invalid")


def validate_ingress_intent(
    intent: Mapping[str, Any],
    *,
    response_sha256: str,
    provenance_sha256: str,
) -> dict[str, Any]:
    _validate_universal_common(intent)
    _validate_endpoint(
        intent.get("source"),
        boundary="DEVICE_SYSTEM",
        subsystem="Site:HIL",
        label="universal_intr_source",
    )
    _validate_endpoint(
        intent.get("destination"),
        boundary="STEGOS_ECOSYSTEM",
        subsystem="HIL:Ingress",
        label="universal_intr_destination",
    )
    if intent.get("boundary_path") != ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"]:
        raise HILInTrError("universal_intr_ingress_boundary_path_invalid")
    if intent.get("prior_transport_receipt_hash") is not None:
        raise HILInTrError("universal_intr_ingress_must_begin_chain")
    expected_payload = digest_uri(payload_binding(
        response_sha256=response_sha256,
        provenance_sha256=provenance_sha256,
    ))
    if intent.get("payload_hash") != expected_payload:
        raise HILInTrError("universal_intr_ingress_payload_hash_mismatch")
    return dict(intent)


def build_universal_intent(
    *,
    ingress_intent: Mapping[str, Any],
    operation_suffix: str,
    source_subsystem: str,
    destination_subsystem: str,
    prior_receipt_hash: str,
) -> dict[str, Any]:
    if not is_digest_uri(prior_receipt_hash):
        raise HILInTrError("universal_intr_prior_receipt_hash_invalid")
    operation_id = f"{ingress_intent['operation_id']}:{operation_suffix}"
    packet_basis = {
        "operation_id": operation_id,
        "payload_hash": ingress_intent["payload_hash"],
        "prior_transport_receipt_hash": prior_receipt_hash,
        "source_subsystem": source_subsystem,
        "destination_subsystem": destination_subsystem,
    }
    packet_id = "INTR-" + digest_uri(packet_basis)[7:31]
    return {
        "schema": UNIVERSAL_INTR_SCHEMA,
        "protocol": "InTr",
        "operation_id": operation_id,
        "packet_id": packet_id,
        "payload_hash": ingress_intent["payload_hash"],
        "prior_transport_receipt_hash": prior_receipt_hash,
        "source": {
            "boundary": "STEGOS_ECOSYSTEM",
            "subsystem": source_subsystem,
        },
        "destination": {
            "boundary": "STEGOS_ECOSYSTEM",
            "subsystem": destination_subsystem,
        },
        "boundary_path": ["STEGOS_ECOSYSTEM"],
        "interlock_required": True,
        "transport_semantics": dict(TRANSPORT_SEMANTICS),
        "authority": dict(AUTHORITY),
        "receipt_chain": dict(RECEIPT_POLICY),
    }


def build_hop_receipt(
    *,
    intent: Mapping[str, Any],
    hop_index: int,
    from_role: str,
    to_role: str,
    boundary_identity_ref: str,
    prior_receipt_hash: str | None,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    _validate_universal_common(intent)
    if hop_index < 1:
        raise HILInTrError("hil_intr_hop_index_invalid")
    if prior_receipt_hash is not None and not is_digest_uri(prior_receipt_hash):
        raise HILInTrError("hil_intr_prior_receipt_hash_invalid")
    body = {
        "schema": HOP_RECEIPT_SCHEMA,
        "receipt_id": f"HIL-INTR-RCPT-{uuid4().hex[:16].upper()}",
        "packet_id": str(intent["packet_id"]),
        "hop_index": hop_index,
        "direction": "FORWARD",
        "from_role": from_role,
        "to_role": to_role,
        "operation_hash": operation_hash(intent),
        "payload_hash": str(intent["payload_hash"]),
        "prior_receipt_hash": prior_receipt_hash,
        "boundary_identity_ref": boundary_identity_ref,
        "boundary_verification": "VERIFIED",
        "transition_state": "RECEIVED",
        "secret_plaintext_present": False,
        "authority_transfer": False,
        "recorded_at": recorded_at or datetime.now(timezone.utc).isoformat(),
    }
    return {**body, "receipt_hash": digest_uri(body)}


def validate_hop_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if set(receipt) != HOP_FIELDS:
        raise HILInTrError("hil_intr_hop_receipt_field_set_invalid")
    if receipt.get("schema") != HOP_RECEIPT_SCHEMA:
        raise HILInTrError("hil_intr_hop_receipt_schema_invalid")
    if receipt.get("direction") != "FORWARD":
        raise HILInTrError("hil_intr_hop_direction_invalid")
    if receipt.get("boundary_verification") != "VERIFIED":
        raise HILInTrError("hil_intr_hop_boundary_not_verified")
    if receipt.get("transition_state") != "RECEIVED":
        raise HILInTrError("hil_intr_hop_transition_not_received")
    if receipt.get("secret_plaintext_present") is not False:
        raise HILInTrError("hil_intr_hop_secret_plaintext_forbidden")
    if receipt.get("authority_transfer") is not False:
        raise HILInTrError("hil_intr_hop_authority_transfer_forbidden")
    for field in ("operation_hash", "payload_hash", "receipt_hash"):
        if not is_digest_uri(receipt.get(field)):
            raise HILInTrError(f"hil_intr_hop_{field}_invalid")
    prior = receipt.get("prior_receipt_hash")
    if prior is not None and not is_digest_uri(prior):
        raise HILInTrError("hil_intr_hop_prior_receipt_hash_invalid")
    body = dict(receipt)
    claimed = body.pop("receipt_hash")
    if claimed != digest_uri(body):
        raise HILInTrError("hil_intr_hop_receipt_hash_mismatch")
    return dict(receipt)


def build_receipt_chain(
    *,
    ingress_intent: Mapping[str, Any],
    ingress_receipt: Mapping[str, Any],
    custody_intent: Mapping[str, Any],
    custody_receipt: Mapping[str, Any],
    next_intent: Mapping[str, Any],
) -> dict[str, Any]:
    first = validate_hop_receipt(ingress_receipt)
    second = validate_hop_receipt(custody_receipt)
    if first.get("operation_hash") != operation_hash(ingress_intent):
        raise HILInTrError("hil_intr_ingress_receipt_operation_mismatch")
    if first.get("payload_hash") != ingress_intent.get("payload_hash"):
        raise HILInTrError("hil_intr_ingress_receipt_payload_mismatch")
    if first.get("prior_receipt_hash") is not None:
        raise HILInTrError("hil_intr_first_receipt_must_begin_chain")
    if custody_intent.get("prior_transport_receipt_hash") != first.get("receipt_hash"):
        raise HILInTrError("hil_intr_custody_intent_chain_mismatch")
    if second.get("operation_hash") != operation_hash(custody_intent):
        raise HILInTrError("hil_intr_custody_receipt_operation_mismatch")
    if second.get("payload_hash") != ingress_intent.get("payload_hash"):
        raise HILInTrError("hil_intr_custody_receipt_payload_mismatch")
    if second.get("prior_receipt_hash") != first.get("receipt_hash"):
        raise HILInTrError("hil_intr_custody_receipt_chain_mismatch")
    if next_intent.get("prior_transport_receipt_hash") != second.get("receipt_hash"):
        raise HILInTrError("hil_intr_next_intent_chain_mismatch")
    body = {
        "schema": CHAIN_SCHEMA,
        "operation_id": str(ingress_intent["operation_id"]),
        "ingress_transport_intent": dict(ingress_intent),
        "device_stegos_ingress_receipt": first,
        "hil_custody_transport_intent": dict(custody_intent),
        "hil_custody_interlock_receipt": second,
        "next_interlock_intent": dict(next_intent),
        "next_required_transition": "HIL_CUSTODY_TVC_INTERLOCK_ADMISSION",
        "authority_transfer": False,
    }
    return {**body, "chain_hash": digest_uri(body)}
