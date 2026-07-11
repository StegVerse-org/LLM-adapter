from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def emit_llm_transition_candidate(
    *,
    transition_id: str,
    run_id: str,
    event_id: str,
    actor_ref: str,
    target_ref: str,
    repository_ref: str,
    task_ref: str | None = None,
    handoff_ref: str | None = None,
    policy_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Emit an LLM-origin candidate compatible with orchestration's relationship contract.

    This is an entry manifest only. It grants no execution, delegation, publication,
    retention, or final-receipt authority.
    """
    for name, value in {
        "transition_id": transition_id,
        "run_id": run_id,
        "event_id": event_id,
        "actor_ref": actor_ref,
        "target_ref": target_ref,
        "repository_ref": repository_ref,
    }.items():
        if not value:
            raise ValueError(f"{name} is required")

    return {
        "schema_version": "1.0.0",
        "record_type": "governed_transition_relationship",
        "transition_id": transition_id,
        "run_id": run_id,
        "lifecycle_state": "DECLARED",
        "origin": {
            "origin_class": "LLM_ADAPTER_INPUT",
            "event_id": event_id,
            "origin_manifest_id": f"origin.llm-adapter.{run_id}",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "source_ref": "StegVerse-org/LLM-adapter",
        },
        "relationships": {
            "parent_transition_id": None,
            "previous_receipt_id": None,
            "actor_ref": actor_ref,
            "target_ref": target_ref,
            "repository_ref": repository_ref,
            "handoff_ref": handoff_ref,
            "task_ref": task_ref,
            "next_task_ref": None,
        },
        "governance": {
            "policy_refs": policy_refs or [],
            "delegation_refs": [],
            "evidence_refs": evidence_refs or [],
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
    }
