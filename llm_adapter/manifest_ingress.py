from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Mapping

INGRESS_SCHEMA = "stegverse.llm-adapter.manifest-ingress.v1"
RESULT_SCHEMA = "stegverse.llm-adapter.manifest-ingress-result.v1"
PROFILE_ID = "stegverse.manifest-ingress.v1"
ALLOWED_MODES = {"TEST", "LIVE_STREAM"}
ALLOWED_DECISIONS = {"ALLOW", "DENY", "REVIEW", "FAIL_CLOSED"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def validate_ingress_request(request: Mapping[str, Any]) -> tuple[bool, str]:
    if request.get("schema") != INGRESS_SCHEMA:
        return False, "invalid_schema"
    if request.get("profile_id") != PROFILE_ID:
        return False, "invalid_profile"
    mode = request.get("mode")
    if mode not in ALLOWED_MODES:
        return False, "invalid_mode"
    for key in ("request_id", "unit_id", "idempotency_key"):
        value = request.get(key)
        if not isinstance(value, str) or not value.strip():
            return False, f"missing_{key}"
    manifest = request.get("manifest")
    if not isinstance(manifest, Mapping) or not manifest:
        return False, "manifest_missing_or_empty"

    # This ingress surface never receives credential, provider-selection, route,
    # governance, repository, wallet, publication, or release authority.
    for key in (
        "provider_selection_authority",
        "credential_access_granted",
        "route_authority_granted",
        "governance_authority_granted",
        "repository_access_granted",
        "wallet_authority_granted",
        "publication_authority_granted",
        "release_authority_granted",
    ):
        if request.get(key) is not False:
            return False, f"authority_escalation:{key}"

    if request.get("github_token_required") is not False:
        return False, "github_token_not_allowed"

    if mode == "LIVE_STREAM":
        stream_id = request.get("stream_id")
        sequence = request.get("sequence")
        if not isinstance(stream_id, str) or not stream_id.strip():
            return False, "stream_id_required"
        if not isinstance(sequence, int) or sequence < 0:
            return False, "invalid_sequence"
        if sequence > 0:
            predecessor = request.get("predecessor_manifest_receipt_id")
            if not isinstance(predecessor, str) or not predecessor.strip():
                return False, "predecessor_receipt_required"
    else:
        if request.get("stream_id") not in (None, ""):
            return False, "test_mode_stream_id_forbidden"
        if request.get("sequence") not in (None, 0):
            return False, "test_mode_sequence_forbidden"

    declared_hash = request.get("request_hash")
    if not isinstance(declared_hash, str) or not declared_hash:
        return False, "request_hash_missing"
    candidate = dict(request)
    candidate.pop("request_hash", None)
    if declared_hash != canonical_sha256(candidate):
        return False, "request_hash_mismatch"
    return True, "PASS"


def _fail_closed(request: Mapping[str, Any], reason: str) -> dict[str, Any]:
    response: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "request_id": request.get("request_id"),
        "unit_id": request.get("unit_id"),
        "mode": request.get("mode"),
        "decision": "FAIL_CLOSED",
        "reason": reason,
        "manifest_receipt_id": None,
        "governed_result": None,
        "verification_refs": [],
        "consequence_executed": False,
        "idempotent_replay": False,
        "provider_selection_authority": False,
        "credential_authority_granted": False,
        "route_authority_granted": False,
        "governance_authority_granted": False,
        "wallet_authority_granted": False,
        "publication_authority_granted": False,
        "release_authority_granted": False,
        "github_token_required": False,
        "authority_effect": "NONE",
    }
    response["result_hash"] = canonical_sha256(response)
    return response


def execute_manifest_ingress(
    *,
    request: Mapping[str, Any],
    governed_ingest: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate a TEST/LIVE_STREAM envelope and hand it to canonical governance.

    ``governed_ingest`` is an injected adapter to the ordinary StegVerse manifested
    ingestion path. This module deliberately does not implement a second evaluator,
    provider registry, credential path, route authority, or custody system.
    """

    valid, reason = validate_ingress_request(request)
    if not valid:
        return _fail_closed(request, reason)

    manifest = dict(request["manifest"])
    context = {
        "profile_id": PROFILE_ID,
        "mode": request["mode"],
        "request_id": request["request_id"],
        "unit_id": request["unit_id"],
        "idempotency_key": request["idempotency_key"],
        "manifest_sha256": canonical_sha256(manifest),
        "stream_id": request.get("stream_id"),
        "sequence": request.get("sequence"),
        "predecessor_manifest_receipt_id": request.get("predecessor_manifest_receipt_id"),
    }

    try:
        raw = governed_ingest(manifest, context)
    except Exception as exc:  # fail closed at the adapter boundary
        return _fail_closed(request, f"governed_ingest_error:{type(exc).__name__}")

    if not isinstance(raw, Mapping):
        return _fail_closed(request, "governed_ingest_result_invalid")
    decision = raw.get("decision")
    if decision not in ALLOWED_DECISIONS:
        return _fail_closed(request, "governed_decision_invalid")
    receipt_id = raw.get("manifest_receipt_id")
    if not isinstance(receipt_id, str) or not receipt_id.strip():
        return _fail_closed(request, "manifest_receipt_id_missing")
    refs = raw.get("verification_refs")
    if not isinstance(refs, list) or not all(isinstance(v, str) and v for v in refs):
        return _fail_closed(request, "verification_refs_invalid")
    executed = raw.get("consequence_executed")
    if not isinstance(executed, bool):
        return _fail_closed(request, "consequence_executed_invalid")
    if decision != "ALLOW" and executed:
        return _fail_closed(request, "non_allow_consequence_execution_forbidden")
    idempotent_replay = raw.get("idempotent_replay", False)
    if not isinstance(idempotent_replay, bool):
        return _fail_closed(request, "idempotent_replay_invalid")

    response: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "request_id": request["request_id"],
        "unit_id": request["unit_id"],
        "mode": request["mode"],
        "input_manifest_sha256": context["manifest_sha256"],
        "decision": decision,
        "reason": str(raw.get("reason") or ""),
        "manifest_receipt_id": receipt_id,
        "governed_result": raw.get("governed_result"),
        "verification_refs": list(refs),
        "consequence_executed": executed,
        "idempotent_replay": idempotent_replay,
        "stream_id": request.get("stream_id"),
        "sequence": request.get("sequence"),
        "predecessor_manifest_receipt_id": request.get("predecessor_manifest_receipt_id"),
        "provider_selection_authority": False,
        "credential_authority_granted": False,
        "route_authority_granted": False,
        "governance_authority_granted": False,
        "wallet_authority_granted": False,
        "publication_authority_granted": False,
        "release_authority_granted": False,
        "github_token_required": False,
        "authority_effect": "NONE",
    }
    response["result_hash"] = canonical_sha256(response)
    return response


def verify_manifest_ingress_result(result: Mapping[str, Any]) -> bool:
    if result.get("schema") != RESULT_SCHEMA:
        return False
    if result.get("decision") not in ALLOWED_DECISIONS:
        return False
    if result.get("authority_effect") != "NONE" or result.get("github_token_required") is not False:
        return False
    for key in (
        "provider_selection_authority",
        "credential_authority_granted",
        "route_authority_granted",
        "governance_authority_granted",
        "wallet_authority_granted",
        "publication_authority_granted",
        "release_authority_granted",
    ):
        if result.get(key) is not False:
            return False
    candidate = dict(result)
    expected = candidate.pop("result_hash", None)
    return isinstance(expected, str) and expected == canonical_sha256(candidate)
