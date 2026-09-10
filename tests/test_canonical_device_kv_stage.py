import copy

from llm_adapter.canonical_device_kv_stage import (
    INTENT_SCHEMA, RECEIPT_SCHEMA, build_device_kv_stage_transport, canonical_json, sha256_uri,
)


def packet():
    return {
        "ingress_id":"ingress-1",
        "credential_ref":"skap://APIs/coinbase/owner/1",
        "physical_execution_surface":"CURRENT_USER_IPHONE",
        "sealed_material":{"recipient_key_id":"tvc://skap/browser-ingress/coinbase/v1","ciphertext_b64":"opaque"},
    }


def test_builds_exact_canonical_device_kv_receipt_without_secret_payload():
    p=packet(); raw=b'{"opaque":"browser-packet"}'
    out=build_device_kv_stage_transport(p,raw_body=raw)
    intent=out["intent"];receipt=out["receipt"]
    assert intent["schema"]==INTENT_SCHEMA
    assert intent["boundary_path"]==["DEVICE_SYSTEM","KV"]
    assert intent["prior_transport_receipt_hash"] is None
    assert intent["authority"]["credential_authority"]=="TV/TVC"
    assert intent["authority"]["transport_grants_execution_authority"] is False
    assert receipt["schema"]==RECEIPT_SCHEMA
    assert receipt["from_role"]=="DEVICE_SYSTEM" and receipt["to_role"]=="KV"
    assert receipt["prior_receipt_hash"] is None
    body=dict(receipt); claimed=body.pop("receipt_hash")
    assert claimed==sha256_uri(body)
    payload_raw=canonical_json(out["payload"]).encode()
    assert intent["payload_hash"]==sha256_uri(payload_raw)
    assert "ciphertext_b64" not in canonical_json(out)
    assert out["credential_material_present"] is False


def test_packet_hash_change_changes_device_kv_payload_identity():
    p=packet();a=build_device_kv_stage_transport(p,raw_body=b"one");b=build_device_kv_stage_transport(copy.deepcopy(p),raw_body=b"two")
    assert a["payload"]["browser_ingress_digest"]!=b["payload"]["browser_ingress_digest"]
    assert a["intent"]["payload_hash"]!=b["intent"]["payload_hash"]
    assert a["receipt"]["receipt_hash"]!=b["receipt"]["receipt_hash"]
