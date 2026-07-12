"""Bounded per-request governed pipeline for Ecosystem Chat.

This module advances one canonical transition relationship through the logical
bridge, delegation, standing, executor, and response-receipt boundaries. It is
limited to non-mutating chat response generation. It does not grant repository
mutation, publication, credential, or Master-Records custody authority.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from threading import RLock
from typing import Any

_STORE: dict[str, dict[str, Any]] = {}
_LOCK = RLock()


def _receipt(prefix: str, *parts: str) -> str:
    material = "\n".join(parts)
    return f"{prefix}:sha256:{sha256(material.encode('utf-8')).hexdigest()}"


def _append_unique(values: list[str], *items: str) -> list[str]:
    return list(dict.fromkeys([*values, *items]))


def build_relationship(*, candidate: dict[str, Any], message: str, gateway_receipt_id: str) -> dict[str, Any]:
    identity = {
        "transition_id": candidate["transition_id"],
        "run_id": candidate["run_id"],
    }
    origin = candidate.get("origin", {})
    relationships = candidate.get("relationships", {})
    return {
        "schema_version": "1.0.0",
        "record_type": "governed_transition_relationship",
        **identity,
        "lifecycle_state": "DECLARED",
        "origin": {
            "origin_class": "SITE_INPUT",
            "event_id": origin["event_id"],
            "origin_manifest_id": origin["origin_manifest_id"],
            "observed_at": origin.get("observed_at"),
            "source_ref": origin.get("source_ref", "StegVerse-Labs/Site/ecosystem-chat.html"),
        },
        "relationships": {
            "parent_transition_id": relationships.get("parent_transition_id"),
            "previous_receipt_id": relationships.get("previous_receipt_id"),
            "actor_ref": relationships.get("actor_ref", "site-session:unknown"),
            "target_ref": "repository:StegVerse-Labs/hybrid-collab-bridge",
            "repository_ref": "StegVerse-Labs/Site",
            "handoff_ref": "docs/SITE_MIRROR_HANDOFF.md",
            "task_ref": relationships.get("task_ref", "task:ecosystem-chat:explain"),
            "next_task_ref": None,
        },
        "governance": {
            "policy_refs": ["policy:ecosystem-chat-bounded-response"],
            "delegation_refs": [],
            "evidence_refs": [gateway_receipt_id],
            "micro_node_manifest_ref": None,
            "admissibility_result": "PENDING",
            "commit_time_validity": "PENDING",
        },
        "execution": {
            "action_ref": None,
            "verification_ref": None,
            "resulting_state_ref": None,
        },
        "continuity": {
            "final_receipt_id": None,
            "master_record_ref": None,
            "master_record_status": "NOT_YET_SUBMITTED",
            "reconstruction_status": "NOT_YET_CHECKED",
        },
        "projection": {
            "site_visibility": "SUMMARY",
            "wiki_visibility": "SUMMARY",
            "redaction_class": "PUBLIC_REDACTED",
        },
        "request": {
            "message_sha256": sha256(message.encode("utf-8")).hexdigest(),
            "raw_message_retained": False,
        },
    }


def progress_bounded_response(
    *,
    relationship: dict[str, Any],
    response_text: str,
    restricted: bool,
) -> dict[str, Any]:
    record = deepcopy(relationship)
    transition_id = record["transition_id"]
    run_id = record["run_id"]

    if restricted:
        record["lifecycle_state"] = "VERIFICATION_REQUIRED"
        record["relationships"]["target_ref"] = "authority:restricted-admin-review"
        record["governance"]["evidence_refs"] = _append_unique(
            record["governance"]["evidence_refs"],
            "bridge-decision:REVIEW",
            "delegation-decision:REVIEW_DELEGATION",
        )
        record["execution"]["verification_ref"] = "verification:separate-authority-required"
        with _LOCK:
            _STORE[transition_id] = record
        return record

    bridge_receipt = _receipt("bridge-receipt", transition_id, run_id, "ALLOW_NEXT_BOUNDARY")
    delegation_receipt = _receipt("delegation-receipt", transition_id, run_id, "ALLOW_DELEGATION")
    standing_receipt = _receipt("standing-receipt", transition_id, run_id, "ALLOW_BOUNDED_RESPONSE")
    response_hash = sha256(response_text.encode("utf-8")).hexdigest()
    final_receipt = _receipt(
        "final-response-receipt",
        transition_id,
        run_id,
        response_hash,
        bridge_receipt,
        delegation_receipt,
        standing_receipt,
    )

    record["lifecycle_state"] = "COMPLETED"
    record["relationships"]["target_ref"] = "executor:STEGVERSE_AI_ENTITY"
    record["relationships"]["next_task_ref"] = None
    record["governance"]["delegation_refs"] = [delegation_receipt]
    record["governance"]["evidence_refs"] = _append_unique(
        record["governance"]["evidence_refs"],
        bridge_receipt,
        "bridge-decision:ALLOW_NEXT_BOUNDARY",
        delegation_receipt,
        "delegation-decision:ALLOW_DELEGATION",
        standing_receipt,
        "standing-decision:ALLOW_BOUNDED_RESPONSE",
        "executor-activation-receipt:stegverse-ai:example-001",
    )
    record["governance"]["micro_node_manifest_ref"] = "manifest:ecosystem-chat-bounded-response:v1"
    record["governance"]["admissibility_result"] = "ALLOW"
    record["governance"]["commit_time_validity"] = "VALID"
    record["execution"] = {
        "action_ref": "action:bounded-chat-response-generation",
        "verification_ref": final_receipt,
        "resulting_state_ref": f"response:sha256:{response_hash}",
    }
    record["continuity"]["final_receipt_id"] = final_receipt
    # Persistence/custody is intentionally not claimed by this stateless service.
    record["continuity"]["master_record_status"] = "NOT_YET_SUBMITTED"
    record["continuity"]["reconstruction_status"] = "PARTIAL"

    with _LOCK:
        _STORE[transition_id] = record
    return record


def get_transition_status(transition_id: str) -> dict[str, Any] | None:
    with _LOCK:
        record = _STORE.get(transition_id)
        return deepcopy(record) if record else None
