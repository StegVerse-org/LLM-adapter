#!/usr/bin/env python3
"""Observe the StegVerse HIL layer and emit the exact next repository-owned action."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKBOARD = ROOT / "data" / "hil-layer-workboard.json"
OUTPUT = Path(os.getenv("HIL_LAYER_OBSERVATION_OUTPUT", "reports/hil-layer-observation.json"))
API = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
TOKEN = os.getenv("GITHUB_TOKEN", "")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def api_get(path: str) -> dict[str, Any] | None:
    request = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "stegverse-hil-layer-observer",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            value = json.load(response)
        require(isinstance(value, dict), f"GitHub API returned non-object for {path}")
        return value
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def issue(repo: str, number: int) -> dict[str, Any] | None:
    return api_get(f"/repos/{repo}/issues/{number}")


def pull(repo: str, number: int) -> dict[str, Any] | None:
    return api_get(f"/repos/{repo}/pulls/{number}")


def content_exists(repo: str, path: str, ref: str = "main") -> bool:
    encoded = urllib.parse.quote(path, safe="/")
    return api_get(f"/repos/{repo}/contents/{encoded}?ref={ref}") is not None


def main() -> int:
    board = json.loads(WORKBOARD.read_text(encoding="utf-8"))
    require(board.get("schema_version") == "HIL-LAYER-WORKBOARD-v1", "workboard schema mismatch")
    require(board.get("organization") == "StegVerse", "workboard organization mismatch")
    require(board.get("no_external_tasks") is True, "external-task posture must remain false")
    require(board.get("authority_effect") == "NONE", "workboard must not grant authority")
    tasks = board.get("tasks")
    require(isinstance(tasks, list) and tasks, "workboard must contain tasks")
    for task in tasks:
        require(isinstance(task, dict), "task must be an object")
        for field in ("id", "title", "repository", "location", "acceptance", "next_action", "state"):
            require(isinstance(task.get(field), str) and task[field], f"task missing {field}")

    pr89 = pull("StegVerse-org/LLM-adapter", 89)
    activation_issue = issue("StegVerse-org/LLM-adapter", 91)
    observer_issue = issue("StegVerse-org/LLM-adapter", 92)
    capacity_issue = issue("StegVerse-org/LLM-adapter", 94)
    site_issue = issue("StegVerse-Labs/Site", 136)
    site_config = api_get("/repos/StegVerse-Labs/Site/contents/data/hil-receiver-config.json?ref=main")

    pr_open = bool(pr89 and pr89.get("state") == "open")
    pr_merged = bool(pr89 and pr89.get("merged_at"))
    activation_open = bool(activation_issue and activation_issue.get("state") == "open")
    observer_open = bool(observer_issue and observer_issue.get("state") == "open")
    capacity_open = bool(capacity_issue and capacity_issue.get("state") == "open")
    site_open = bool(site_issue and site_issue.get("state") == "open")
    managed_files_on_main = all(
        content_exists("StegVerse-org/LLM-adapter", path)
        for path in (
            "render.yaml",
            ".github/workflows/hil-managed-receiver-validation.yml",
            "docs/HIL_HOSTED_RECEIVER_ACTIVATION.md",
        )
    )

    config_text = ""
    if site_config and isinstance(site_config.get("content"), str):
        import base64
        config_text = base64.b64decode(site_config["content"]).decode("utf-8")
    receiver_configured = (
        "CONFORMING_HTTPS_RECEIVER_CONFIGURED" in config_text
        and '"receiver_base_url": null' not in config_text
    )

    if receiver_configured:
        state = "ACTIVATED"
        next_task = {
            "id": "HIL-CYCLE-001",
            "location": "StegVerse-Labs/Site#136",
            "action": "Run and preserve the controlled browser cycle, then continue review/publication/import/Master Record gates.",
        }
    elif managed_files_on_main:
        state = "BUILT_NOT_ACTIVATED"
        if capacity_open:
            next_task = {
                "id": "HIL-CAPACITY-001",
                "location": "StegVerse-org/LLM-adapter#94",
                "action": "Restore StegVerse Render build pipeline capacity, then trigger service srv-d9l4fhijnfac73a8ou20 from main.",
            }
        else:
            next_task = {
                "id": "HIL-ACTIVATE-001",
                "location": "StegVerse-org/LLM-adapter#91",
                "action": "Deploy and verify the managed receiver, then preserve readiness and persistence evidence.",
            }
    elif pr_open:
        state = "BEING_BUILT"
        next_task = {
            "id": "HIL-BUILD-001",
            "location": "StegVerse-org/LLM-adapter#89",
            "action": "Complete the managed receiver implementation and land its required files on main.",
        }
    else:
        state = "CONTRADICTORY"
        next_task = {
            "id": "HIL-REPAIR-001",
            "location": "StegVerse-org/LLM-adapter#92",
            "action": "Repair the missing implementation owner or managed-runtime files before activation proceeds.",
        }

    observation = {
        "schema_version": "HIL-LAYER-OBSERVATION-v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "layer": board["layer"],
        "organization": "StegVerse",
        "state": state,
        "no_external_tasks": True,
        "owner_surfaces": {
            "implementation_pr": "StegVerse-org/LLM-adapter#89",
            "activation_issue": "StegVerse-org/LLM-adapter#91",
            "observer_issue": "StegVerse-org/LLM-adapter#92",
            "capacity_issue": "StegVerse-org/LLM-adapter#94",
            "site_consumption_issue": "StegVerse-Labs/Site#136",
        },
        "observed": {
            "implementation_pr_open": pr_open,
            "implementation_pr_merged": pr_merged,
            "managed_runtime_files_on_main": managed_files_on_main,
            "activation_issue_open": activation_open,
            "observer_issue_open": observer_open,
            "capacity_issue_open": capacity_open,
            "site_consumption_issue_open": site_open,
            "site_receiver_configured": receiver_configured,
        },
        "next_task": next_task,
        "authority_effect": "NONE",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(observation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(observation, indent=2, sort_keys=True))
    return 1 if state == "CONTRADICTORY" else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"HIL_LAYER_OBSERVER_ERROR={exc}", file=sys.stderr)
        raise SystemExit(2)
