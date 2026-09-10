"""Canonical Device->KV transport projection for SKAP ciphertext staging.

This module mirrors StegOS Universal-InTr v1 wire semantics at the service
Gateway boundary so the receiver that actually accepts the current-iPhone
request emits the first canonical hop receipt. It contains references/hashes
only; sealed credential bytes remain in the separately staged browser packet.
Downstream StegOS validation remains authoritative for canonical conformance.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping

INTENT_SCHEMA="stegverse.universal-intr-transport/v1"
RECEIPT_SCHEMA="stegverse.intr.hop_receipt/v1"
PAYLOAD_SCHEMA="kv.interlock.request.v1"
SOURCE={"boundary":"DEVICE_SYSTEM","subsystem":"Device:KnowledgeVaultClient"}
DESTINATION={"boundary":"KV","subsystem":"KnowledgeVault:Interlock"}

def canonical_json(value:Any)->str:return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)
def sha256_uri(value:Any)->str:
    if isinstance(value,(bytes,bytearray)):raw=bytes(value)
    elif isinstance(value,str):raw=value.encode("utf-8")
    else:raw=canonical_json(value).encode("utf-8")
    return "sha256:"+hashlib.sha256(raw).hexdigest()
def now()->str:return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def build_device_kv_stage_transport(packet:Mapping[str,Any],*,raw_body:bytes)->dict[str,Any]:
    ingress_id=str(packet.get("ingress_id") or "")
    credential_ref=str(packet.get("credential_ref") or "")
    if not ingress_id or not credential_ref:raise ValueError("device_kv_stage_binding_required")
    payload={
        "schema":PAYLOAD_SCHEMA,
        "request_id":"SKAP-CUSTODY-"+ingress_id,
        "operation":"REQUEST",
        "record_class":"SKAP_CIPHERTEXT_CUSTODY",
        "requested_scope":["credential_reference","sealed_capsule_digest"],
        "credential_ref":credential_ref,
        "browser_ingress_digest":sha256_uri(raw_body),
        "sealed_capsule_digest":sha256_uri(packet.get("sealed_material") or {}),
        "physical_execution_surface":packet.get("physical_execution_surface"),
        "credential_authority":"TV/TVC",
        "secret_plaintext_present":False,
        "authority_effect":"NONE_REQUEST_ONLY",
    }
    payload_bytes=canonical_json(payload).encode("utf-8")
    payload_hash=sha256_uri(payload_bytes)
    operation_id=ingress_id+":device-kv"
    basis={"operation_id":operation_id,"payload_hash":payload_hash,"source_boundary":"DEVICE_SYSTEM","source_subsystem":SOURCE["subsystem"],"destination_boundary":"KV","destination_subsystem":DESTINATION["subsystem"],"boundary_path":["DEVICE_SYSTEM","KV"]}
    intent={
        "schema":INTENT_SCHEMA,"protocol":"InTr","operation_id":operation_id,
        "packet_id":"INTR-"+hashlib.sha256(canonical_json(basis).encode("utf-8")).hexdigest()[:24],
        "payload_hash":payload_hash,"prior_transport_receipt_hash":None,
        "source":dict(SOURCE),"destination":dict(DESTINATION),"boundary_path":["DEVICE_SYSTEM","KV"],"interlock_required":True,
        "transport_semantics":{"event_triggered":True,"always_on_receiver_required":False,"second_user_device_required":False,"receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION","exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False},
        "authority":{"authority_transfer":False,"transport_grants_execution_authority":False,"credential_authority":"TV/TVC"},
        "receipt_chain":{"required":True,"receipt_schema":RECEIPT_SCHEMA,"payload_plaintext_in_receipts":False,"prior_hash_required_after_first_hop":True},
    }
    operation_hash=sha256_uri({"operation_id":operation_id,"packet_id":intent["packet_id"],"payload_hash":payload_hash})
    body={"schema":RECEIPT_SCHEMA,"receipt_id":"DEVICE-KV-"+intent["packet_id"],"packet_id":intent["packet_id"],"hop_index":1,"direction":"FORWARD","from_role":"DEVICE_SYSTEM","to_role":"KV","operation_hash":operation_hash,"payload_hash":payload_hash,"prior_receipt_hash":None,"boundary_identity_ref":"service-gateway://KnowledgeVault:Interlock","boundary_verification":"VERIFIED","transition_state":"RECEIVED","secret_plaintext_present":False,"authority_transfer":False,"recorded_at":now()}
    receipt={**body,"receipt_hash":sha256_uri(body)}
    return {"schema":"stegverse.service-gateway.device-kv-canonical-stage/v1","payload_schema":PAYLOAD_SCHEMA,"payload":payload,"intent":intent,"receipt":receipt,"credential_material_present":False,"authority_effect":"NONE_EVIDENCE_ONLY"}
