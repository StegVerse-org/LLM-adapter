from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

STAGE_RECEIPT_SCHEMA = "stegverse.service_gateway.coinbase_skap_stage_receipt/v1"
BROWSER_SCHEMA = "stegverse.tvc.coinbase_iphone_skap_ingress/v1"
BROWSER_SEALED_FORMAT = "stegverse.skap.browser_ingress/p256-ecdh-hkdf-sha256-aes256gcm/v1"
ENDPOINT_ORIGIN = "https://api.coinbase.com"
ALLOWED_PURPOSES = {"coinbase.permission_observation", "coinbase.advanced_trade"}
ALLOWED_ORIGINS = {"https://stegverse.org", "https://www.stegverse.org"}
TRANSPORT_MARKER = "InTr-browser-ciphertext-v1"
MAX_BODY_BYTES = 64 * 1024
TVC_ROLE = "service_gateway_coinbase_skap_ciphertext_intake"
FORBIDDEN_PLAINTEXT_KEYS = {
    "api_key_name",
    "api_private_key",
    "private_key",
    "secret",
    "password",
    "authorization",
    "access_token",
    "refresh_token",
}


class CoinbaseSkapStageError(ValueError):
    pass


@dataclass(frozen=True)
class CoinbaseSkapStageRuntime:
    root: Path
    tvc_decision_id: str
    tvc_policy_hash: str | None


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _valid_digest(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and len(value) == 71


def _find_forbidden_plaintext_keys(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in FORBIDDEN_PLAINTEXT_KEYS:
                findings.append(f"{path}.{key}")
            findings.extend(_find_forbidden_plaintext_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_find_forbidden_plaintext_keys(child, f"{path}[{index}]"))
    return findings


def validate_browser_packet(packet: Dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if packet.get("schema") != BROWSER_SCHEMA:
        findings.append("schema_invalid")
    body = {k: v for k, v in packet.items() if k != "ingress_digest"}
    if packet.get("ingress_digest") != digest(body):
        findings.append("ingress_digest_invalid")

    owner = packet.get("owner_authorization") or {}
    if owner.get("method") != "WEBAUTHN":
        findings.append("owner_authorization_method_invalid")
    if owner.get("rp_id") != "stegverse.org":
        findings.append("owner_rp_invalid")
    if owner.get("user_verification") != "REQUIRED" or owner.get("verified") is not True:
        findings.append("owner_verification_not_proven")
    for field in ("assertion_digest", "device_admission_digest", "identity_continuity_digest"):
        if not _valid_digest(owner.get(field)):
            findings.append(f"owner_{field}_invalid")

    if packet.get("physical_execution_surface") != "CURRENT_USER_IPHONE":
        findings.append("physical_execution_surface_invalid")
    if packet.get("transport") != "STEGVERSE_BROWSER_CAPSULE":
        findings.append("transport_invalid")
    if packet.get("provider") != "coinbase_advanced":
        findings.append("provider_invalid")
    if packet.get("endpoint_origin") != ENDPOINT_ORIGIN:
        findings.append("endpoint_origin_invalid")
    if packet.get("purpose") not in ALLOWED_PURPOSES:
        findings.append("purpose_invalid")
    if not str(packet.get("credential_ref") or "").startswith("skap://APIs/coinbase/"):
        findings.append("credential_ref_invalid")
    if not isinstance(packet.get("credential_version"), int) or packet.get("credential_version", 0) < 1:
        findings.append("credential_version_invalid")

    sealed = packet.get("sealed_material") or {}
    if sealed.get("format") != BROWSER_SEALED_FORMAT:
        findings.append("browser_sealed_format_invalid")
    if sealed.get("object_id") != packet.get("credential_ref"):
        findings.append("browser_object_binding_mismatch")
    if sealed.get("credential_version") != packet.get("credential_version"):
        findings.append("browser_version_binding_mismatch")
    if sealed.get("purpose") != packet.get("purpose"):
        findings.append("browser_purpose_binding_mismatch")
    if sealed.get("endpoint_ref") != packet.get("endpoint_origin"):
        findings.append("browser_endpoint_binding_mismatch")
    if not str(sealed.get("recipient_key_id") or "").startswith("tvc://skap/browser-ingress/coinbase/"):
        findings.append("recipient_key_id_invalid")
    jwk = sealed.get("ephemeral_public_jwk") or {}
    if jwk.get("kty") != "EC" or jwk.get("crv") != "P-256" or not jwk.get("x") or not jwk.get("y"):
        findings.append("ephemeral_public_jwk_invalid")
    if "d" in jwk:
        findings.append("ephemeral_private_jwk_forbidden")
    if sealed.get("plaintext_persisted") is not False:
        findings.append("browser_plaintext_persistence_forbidden")
    if sealed.get("device_private_key_persisted") is not False:
        findings.append("device_private_key_persistence_forbidden")
    if sealed.get("skap_private_key_exported") is not False:
        findings.append("skap_private_key_export_forbidden")
    if sealed.get("authority_transfer") is not False:
        findings.append("browser_authority_transfer_forbidden")

    if packet.get("plaintext_present") is not False:
        findings.append("plaintext_present_forbidden")
    if packet.get("device_secret_custody_authority") is not False:
        findings.append("device_secret_custody_forbidden")
    if packet.get("kv_secret_resolution_authority") is not False:
        findings.append("kv_secret_resolution_forbidden")
    if packet.get("github_environment_secret_access") is not False:
        findings.append("github_secret_access_forbidden")
    if packet.get("credential_authority") != "TV/TVC":
        findings.append("credential_authority_invalid")

    forbidden = _find_forbidden_plaintext_keys(packet)
    if forbidden:
        findings.append("plaintext_field_forbidden:" + ",".join(forbidden))
    return findings


def load_runtime() -> CoinbaseSkapStageRuntime:
    raw = os.getenv("STEGVERSE_COINBASE_SKAP_TVC_DECISION_RECEIPT", "").strip()
    path = os.getenv("STEGVERSE_COINBASE_SKAP_TVC_DECISION_RECEIPT_FILE", "").strip()
    if not raw and path:
        raw = Path(path).read_text(encoding="utf-8")
    if not raw:
        raise CoinbaseSkapStageError("coinbase_skap_tvc_decision_receipt_missing")
    receipt = json.loads(raw)
    if receipt.get("role") != TVC_ROLE:
        raise CoinbaseSkapStageError("coinbase_skap_tvc_role_mismatch")
    if receipt.get("admissible") is not True or receipt.get("binding_matched") is not True:
        raise CoinbaseSkapStageError("coinbase_skap_tvc_intake_not_admissible")
    if list(receipt.get("allowed_keys") or []) != [] or list(receipt.get("denied_keys") or []) != []:
        raise CoinbaseSkapStageError("coinbase_skap_tvc_no_value_scope_invalid")
    if receipt.get("credential_values_available") not in (None, False):
        raise CoinbaseSkapStageError("coinbase_skap_tvc_credential_value_scope_forbidden")

    root_value = os.getenv("STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT", "").strip() or os.getenv("STEGVERSE_HIL_STORAGE_ROOT", "").strip()
    if not root_value:
        raise CoinbaseSkapStageError("service_gateway_storage_root_missing")
    root = Path(root_value).expanduser().resolve()
    (root / "coinbase-skap-staging").mkdir(parents=True, exist_ok=True)
    (root / "coinbase-skap-stage-receipts").mkdir(parents=True, exist_ok=True)
    return CoinbaseSkapStageRuntime(
        root=root,
        tvc_decision_id=str(receipt.get("decision_id") or ""),
        tvc_policy_hash=receipt.get("policy_hash"),
    )


def stage_packet(*, raw_body: bytes, packet: Dict[str, Any], runtime: CoinbaseSkapStageRuntime) -> Dict[str, Any]:
    if not raw_body or len(raw_body) > MAX_BODY_BYTES:
        raise CoinbaseSkapStageError("body_size_invalid")
    findings = validate_browser_packet(packet)
    if findings:
        raise CoinbaseSkapStageError("browser_packet_denied:" + ",".join(findings))

    ingress_id = str(packet.get("ingress_id") or "")
    if not ingress_id or len(ingress_id) > 160 or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for ch in ingress_id):
        raise CoinbaseSkapStageError("ingress_id_invalid")

    packet_path = runtime.root / "coinbase-skap-staging" / f"{ingress_id}.json"
    receipt_path = runtime.root / "coinbase-skap-stage-receipts" / f"{ingress_id}.json"
    if packet_path.exists() or receipt_path.exists():
        raise CoinbaseSkapStageError("ingress_replay_denied")

    packet_path.write_bytes(raw_body)
    persisted = packet_path.read_bytes()
    if persisted != raw_body:
        packet_path.unlink(missing_ok=True)
        raise CoinbaseSkapStageError("ciphertext_stage_readback_mismatch")

    sealed_digest = digest(packet["sealed_material"])
    body = {
        "schema": STAGE_RECEIPT_SCHEMA,
        "decision": "STAGED_FOR_TVC",
        "ingress_id": ingress_id,
        "provider": "coinbase_advanced",
        "endpoint_origin": ENDPOINT_ORIGIN,
        "purpose": packet["purpose"],
        "credential_ref": packet["credential_ref"],
        "credential_version": packet["credential_version"],
        "recipient_key_id": packet["sealed_material"]["recipient_key_id"],
        "browser_ingress_digest": digest(packet),
        "browser_sealed_digest": sealed_digest,
        "raw_body_digest": raw_digest(raw_body),
        "staged_packet_ref": str(packet_path),
        "tvc_decision_id": runtime.tvc_decision_id,
        "tvc_policy_hash": runtime.tvc_policy_hash,
        "credential_authority": "TV/TVC",
        "gateway_credential_value_access": False,
        "gateway_decryption_authority": False,
        "gateway_execution_authority": "NONE",
        "browser_ciphertext_mutated": False,
        "decryption_performed": False,
        "rewrap_performed": False,
        "plaintext_persisted": False,
        "device_secret_custody_authority": False,
        "kv_secret_resolution_authority": False,
        "tvc_admission_completed": False,
        "next_required_transition": "TVC_SKAP_CIPHERTEXT_CUSTODY_ADMISSION",
        "blind_retry_allowed": False,
    }
    receipt = {**body, "receipt_digest": digest(body)}
    receipt_path.write_bytes(canonical_bytes(receipt) + b"\n")
    return receipt
