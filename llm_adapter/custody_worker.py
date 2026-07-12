"""Process pending Master-Records custody submissions.

The worker is safe to run at service startup or on a schedule. It performs no
submission when the endpoint is disabled and never invents custody state.
"""
from __future__ import annotations

import json

from llm_adapter.master_records_client import enabled, process_pending


def run(limit: int = 20) -> dict[str, object]:
    if not enabled():
        return {
            "worker": "master_records_custody",
            "enabled": False,
            "processed": 0,
            "recorded": 0,
            "retry": 0,
            "authority_effect": "NONE",
        }
    results = process_pending(limit=limit)
    return {
        "worker": "master_records_custody",
        "enabled": True,
        "processed": len(results),
        "recorded": sum(1 for item in results if item.get("state") == "RECORDED"),
        "retry": sum(1 for item in results if item.get("state") == "RETRY"),
        "authority_effect": "REMOTE_CUSTODY_ONLY_WHEN_RECEIPTED",
    }


def main() -> int:
    result = run()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
