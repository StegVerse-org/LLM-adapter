from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Mapping

RELATIONSHIP_SCHEMA = "stegverse.sdk.evaluation-relationship-result.v1"
REQUEST_SCHEMA = "stegverse.sdk.evaluator-llm-entry-request.v1"
RECEIPT_SCHEMA = "stegverse.llm-adapter.evaluator-entry-receipt.v1"
CAPABILITY_ID = "llm_adapter.evaluator_interaction"
ROUTE = "sdk://StegVerse-org/LLM-adapter/evaluator-entry"


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def verify_sdk_relationship(relationship: Mapping[str, Any]) -> bool:
    if relationship.get("schema") != RELATIONSHIP_SCHEMA:
        return False
    for key in ("participant_id", "terms_acceptance_receipt_hash", "receipt_hash"):
        if not isinstance(relationship.get(key), str) or not str(relationship.get(key)).strip():
            return False
    for key in ("recipient_specific_package","identity_bound_package","execution_authority_granted","mutation_authority_granted","publication_authority_granted","wallet_authority_granted","credential_authority_granted","repository_access_granted","unknown_interest_auto_admitted"):
        if relationship.get(key) is not False:
            return False
    admitted = {str(v.get("capability_id")): v for v in relationship.get("admitted_capabilities") or [] if isinstance(v, Mapping)}
    capability = admitted.get(CAPABILITY_ID)
    if capability is None or capability.get("route") != ROUTE:
        return False
    candidate = dict(relationship); expected = candidate.pop("receipt_hash", None)
    return isinstance(expected, str) and expected == _hash(candidate)


def verify_sdk_evaluator_request(request: Mapping[str, Any], relationship: Mapping[str, Any]) -> bool:
    if request.get("schema") != REQUEST_SCHEMA or not verify_sdk_relationship(relationship):
        return False
    if request.get("participant_id") != relationship.get("participant_id"):
        return False
    if request.get("relationship_receipt_hash") != relationship.get("receipt_hash"):
        return False
    if request.get("terms_acceptance_receipt_hash") != relationship.get("terms_acceptance_receipt_hash"):
        return False
    if request.get("capability_id") != CAPABILITY_ID or request.get("route") != ROUTE:
        return False
    if request.get("evaluation_model_scope") != "local_reference_only":
        return False
    if not isinstance(request.get("prompt"), str) or not request["prompt"].strip():
        return False
    if not isinstance(request.get("max_output_tokens"), int) or not 1 <= request["max_output_tokens"] <= 512:
        return False
    for key in ("provider_selection_authority","credential_access_granted","execution_authority_granted","repository_access_granted"):
        if request.get(key) is not False:
            return False
    candidate = dict(request); expected = candidate.pop("request_hash", None)
    return isinstance(expected, str) and expected == _hash(candidate)


def execute_evaluator_entry(*, request: Mapping[str, Any], relationship: Mapping[str, Any], local_reference_executor: Callable[[str, int], Mapping[str, Any]]) -> dict[str, Any]:
    """Execute only the SDK-admitted local-reference evaluator facade."""
    if not verify_sdk_evaluator_request(request, relationship):
        raise PermissionError("sdk_evaluator_entry_not_admitted")
    raw = local_reference_executor(str(request["prompt"]), int(request["max_output_tokens"]))
    text = str(raw.get("text") or "")
    model_id = str(raw.get("model_id") or "")
    if not text.strip() or not model_id.strip():
        raise RuntimeError("evaluator_local_reference_response_invalid")
    usage = raw.get("measured_usage")
    if not isinstance(usage, Mapping):
        raise RuntimeError("evaluator_measured_usage_missing")
    receipt: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "request_id": request["request_id"],
        "participant_id": request["participant_id"],
        "relationship_receipt_hash": request["relationship_receipt_hash"],
        "terms_acceptance_receipt_hash": request["terms_acceptance_receipt_hash"],
        "request_hash": request["request_hash"],
        "capability_id": CAPABILITY_ID,
        "evaluation_model_scope": "local_reference_only",
        "model_id": model_id,
        "response_text": text,
        "response_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "measured_usage": dict(usage),
        "provider_credentials_exposed": False,
        "provider_selection_authority": False,
        "sovereign_route_authority_exposed": False,
        "execution_authority_granted": False,
        "credential_authority_granted": False,
        "repository_access_granted": False,
        "wallet_authority_granted": False,
        "github_token_required": False,
        "third_party_execution_platform_required": False,
        "authority_effect": "NONE",
    }
    receipt["receipt_hash"] = _hash(receipt)
    return receipt


def verify_evaluator_entry_receipt(receipt: Mapping[str, Any]) -> bool:
    if receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("capability_id") != CAPABILITY_ID:
        return False
    if receipt.get("evaluation_model_scope") != "local_reference_only" or receipt.get("authority_effect") != "NONE":
        return False
    for key in ("provider_credentials_exposed","provider_selection_authority","sovereign_route_authority_exposed","execution_authority_granted","credential_authority_granted","repository_access_granted","wallet_authority_granted","github_token_required","third_party_execution_platform_required"):
        if receipt.get(key) is not False:
            return False
    candidate = dict(receipt); expected = candidate.pop("receipt_hash", None)
    return isinstance(expected, str) and expected == _hash(candidate)
