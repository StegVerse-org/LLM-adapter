"""Hand completed, already-closed transitions downstream to Master Records.

Each transition closed on its final receipt before it was queued; Master Records is
the downstream recorder of released organization batch receipts, so this worker is
optional and never gates, reopens, or delays a transition. It is safe to run at
service startup or on a schedule, writes nothing when the Master Records recorder is
disabled, and never invents record state.
"""
from __future__ import annotations

import json
import os

from llm_adapter.master_records_organization_record_client import enabled, process_pending


def configured_limit(default: int = 20) -> int:
    """Resolve an explicit bounded worker limit without inferring authority."""
    raw = os.getenv("STEGVERSE_CUSTODY_WORKER_LIMIT", "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("STEGVERSE_CUSTODY_WORKER_LIMIT must be a non-negative integer") from exc
    if value < 0 or value > 100:
        raise ValueError("STEGVERSE_CUSTODY_WORKER_LIMIT must be between 0 and 100")
    return value


def run(limit: int = 20) -> dict[str, object]:
    if not enabled():
        return {
            "worker": "master_records_organization_record",
            "enabled": False,
            "processed": 0,
            "recorded": 0,
            "retry": 0,
            "authority_effect": "NONE",
        }
    results = process_pending(limit=limit)
    return {
        "worker": "master_records_organization_record",
        "enabled": True,
        "processed": len(results),
        "recorded": sum(1 for item in results if item.get("state") == "RECORDED"),
        "retry": sum(1 for item in results if item.get("state") == "RETRY"),
        "authority_effect": "NONE_DOWNSTREAM_RECORDING_ONLY",
    }


def main() -> int:
    """Run once and always exit 0: service startup never waits on Master Records.

    The container entrypoint and the portable node preflight run this before the
    gateway starts. A Master Records or configuration failure is reported as a
    six-field non-ALLOW and never blocks startup.
    """
    try:
        result = run(limit=configured_limit())
    except Exception as exc:  # downstream recording never gates startup
        result = {
            "worker": "master_records_organization_record",
            "disposition": "NOT_RECORDED",
            "failure_code": f"downstream_recording_worker_failed:{type(exc).__name__}",
            "failed_predicate": "master_records_downstream_recording_completed",
            "required_evidence_or_repair": "correct the Master Records recorder or STEGVERSE_CUSTODY_WORKER_LIMIT configuration named by the error",
            "retry_entrypoint": "python -m llm_adapter.custody_worker",
            "owning_existing_goal": "LLMA-DECLARED-PATH-CONFORMANCE-368",
            "next_attempt": "rerun the worker; queued transitions are already closed and stay queued",
            "error": str(exc)[:200],
            "gates_startup": False,
            "authority_effect": "NONE_DOWNSTREAM_RECORDING_ONLY",
        }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
