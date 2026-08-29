from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

INGRESS_SCHEMA = "stegverse.hil.intr_ingress_envelope/v1"
EGRESS_SCHEMA = "stegverse.hil.intr_egress_envelope/v1"
HOP_RECEIPT_SCHEMA = "stegverse.intr.hop_receipt/v1"
PAYLOAD_BINDING_SCHEMA = "stegverse.hil.intr_payload_binding/v1"
CHAIN_SCHEMA = "stegverse.hil.intr_receipt_chain/v1"

PRIMARY_SHA256 = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT_SHA256 = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"
PROTOCOL_VERSION = "HIL-PROTOCOL-v1.1"

INGRESS_FIELDS = {
    "schema", "protocol", "packet_id", "operation_id", "from_role", "to_role",
    "payload_hash", "response_sha256", "provenance_sha256", "prior_receipt_hash",
    "created_at", "secret_plaintext_present", "authority_transfer",
    "transport_grants_execution_authority", "envelope_hash",
}

HOP_FIELDS = {
    "schema", "receipt_id", "packet_id", "hop_index", "direction", "from_role",
    "to_role", "operation_hash", "payload_hash", "prior_receipt_hash",
    "boundary_identity_ref", "boundary_verification", "transition_state",
    "secret_plaintext_present", "authority_transfer", "recorded_at", "receipt_hash",
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


def validate_ingress_envelope(
    envelope: Mapping[str, Any],
    *,
    response_sha256: str,
    provenance_sha256: str,
) -> dict[str, Any]:
    if set(envelope) != INGRESS_FIELDS:
        raise HILInTrError("hil_intr_ingress_field_set_invalid")
    expected = {
        "schema": INGRESS_SCHEMA,
        "protocol": "InTr",
        "from_role": "DEVICE",
        "to_role": "HIL_INGRESS",
        "prior_receipt_hash": None,
        "secret_plaintext_present": False,
        "authority_transfer": False,
        "transport_grants_execution_authority": False,
        "response_sha256": f"sha256:{response_sha256}",
        "provenance_sha256": f"sha256:{provenance_sha256}",
    }
    for field, value in expected.items():
        if envelope.get(field) != value:
            raise HILInTrError(f"hil_intr_ingress_{field}_invalid")
    for field in ("packet_id", "operation_id", "created_at"):
        if not isinstance(envelope.get(field), str) or not envelope[field]:
            raise HILInTrError(f"hil_intr_ingress_{field}_required")
    binding = payload_binding(
        response_sha256=response_sha256,
        provenance_sha256=provenance_sha256,
    )
    expected_payload_hash = digest_uri(binding)
    if envelope.get("payload_hash") != expected_payload_hash:
        raise HILInTrError("hil_intr_ingress_payload_hash_mismatch")
    if not is_digest_uri(envelope.get("envelope_hash")):
        raise HILInTrError("hil_intr_ingress_envelope_hash_invalid")
    body = dict(envelope)
    claimed = body.pop("envelope_hash")
    if claimed != digest_uri(body):
        raise HILInTrError("hil_intr_ingress_envelope_hash_mismatch")
    return dict(envelope)


def build_hop_receipt(
    *,
    ingress_envelope: Mapping[str, Any],
    hop_index: int,
    from_role: str,
    to_role: str,
    boundary_identity_ref: str,
    prior_receipt_hash: str | None,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    if hop_index < 1:
        raise HILInTrError("hil_intr_hop_index_invalid")
    if prior_receipt_hash is not None and not is_digest_uri(prior_receipt_hash):
        raise HILInTrError("hil_intr_prior_receipt_hash_invalid")
    body = {
        "schema": HOP_RECEIPT_SCHEMA,
        "receipt_id": f"HIL-INTR-RCPT-{uuid4().hex[:16].upper()}",
        "packet_id": str(ingress_envelope["packet_id"]),
        "hop_index": hop_index,
        "direction": "FORWARD",
        "from_role": from_role,
        "to_role": to_role,
        "operation_hash": str(ingress_envelope["envelope_hash"]),
        "payload_hash": str(ingress_envelope["payload_hash"]),
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


def build_egress_envelope(
    *,
    ingress_envelope: Mapping[str, Any],
    submission_id: str,
    custody_receipt_hash: str,
) -> dict[str, Any]:
    if not is_digest_uri(custody_receipt_hash):
        raise HILInTrError("hil_intr_custody_receipt_hash_invalid")
    body = {
        "schema": EGRESS_SCHEMA,
        "protocol": "InTr",
        "packet_id": f"{ingress_envelope['packet_id']}:egress",
        "operation_id": str(ingress_envelope["operation_id"]),
        "from_role": "HIL_CUSTODY",
        "to_role": "TVC_HIL_LIFECYCLE",
        "payload_hash": str(ingress_envelope["payload_hash"]),
        "prior_receipt_hash": custody_receipt_hash,
        "source_submission_id": submission_id,
        "state": "READY_FOR_INTERLOCK_ADMISSION",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "secret_plaintext_present": False,
        "authority_transfer": False,
        "transport_grants_execution_authority": False,
    }
    return {**body, "envelope_hash": digest_uri(body)}


def build_receipt_chain(
    *,
    ingress_envelope: Mapping[str, Any],
    ingress_receipt: Mapping[str, Any],
    custody_receipt: Mapping[str, Any],
    egress_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    validate_hop_receipt(ingress_receipt)
    validate_hop_receipt(custody_receipt)
    if ingress_receipt.get("prior_receipt_hash") is not None:
        raise HILInTrError("hil_intr_first_hop_must_begin_chain")
    if custody_receipt.get("prior_receipt_hash") != ingress_receipt.get("receipt_hash"):
        raise HILInTrError("hil_intr_custody_chain_mismatch")
    if egress_envelope.get("prior_receipt_hash") != custody_receipt.get("receipt_hash"):
        raise HILInTrError("hil_intr_egress_chain_mismatch")
    body = {
        "schema": CHAIN_SCHEMA,
        "operation_id": str(ingress_envelope["operation_id"]),
        "ingress_envelope_hash": str(ingress_envelope["envelope_hash"]),
        "device_hil_ingress_receipt": dict(ingress_receipt),
        "hil_custody_interlock_receipt": dict(custody_receipt),
        "tvc_egress_interlock_envelope": dict(egress_envelope),
        "next_required_transition": "HIL_CUSTODY_TVC_INTERLOCK_ADMISSION",
        "transport_grants_execution_authority": False,
        "authority_transfer": False,
    }
    return {**body, "chain_hash": digest_uri(body)}
