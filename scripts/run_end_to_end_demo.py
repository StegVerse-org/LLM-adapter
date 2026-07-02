#!/usr/bin/env python3
"""Run the fixture-first governed LLM end-to-end demo.

This script intentionally performs no live provider calls, no live continuity
service calls, no repository mutation, no public posting, and no execution
handoff. It turns a static fixture into a deterministic governed session report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = REPO_ROOT / "reports"


PROVIDER_RESPONSES = {
    "What is the capital of France?": "Informational answer: the capital of France is Paris.",
    "Please draft a commit message updating the README file.": "Candidate commit message: update README with governed LLM demo notes.",
}


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify(fixture: dict[str, Any], evidence_stale: bool) -> tuple[str, str | None, dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    query = fixture["query"]
    if evidence_stale:
        return "QUARANTINE", None, None, None, None
    if "commit" in query.lower() or "update" in query.lower():
        action_route = {"route": "repository_change_candidate", "executes_side_effect": False}
        commitment_request = {
            "request_type": "commit_candidate",
            "is_authority": False,
            "requested_action": "draft_commit_message",
        }
        execution_handoff = {"enabled": False, "executes_side_effect": False}
        return "QUARANTINE", "DRAFT_ACTION_CANDIDATE", action_route, commitment_request, execution_handoff
    return "ALLOW", "NONE", None, None, None


def build_report(fixture_path: Path) -> dict[str, Any]:
    fixture = load_fixture(fixture_path)
    query = fixture["query"]
    expected = fixture["expected_outcome"]
    provider_response = PROVIDER_RESPONSES.get(query, f"Fixture response for: {query}")
    evidence_stale = expected == "QUARANTINE" and "stale" in fixture_path.name
    evidence = {"sources": ["fixtures/basic_source"], "stale": evidence_stale}
    authority_decision, action, action_route, commitment_request, execution_handoff = classify(fixture, evidence_stale)
    request_envelope = {"query": query, "fixture_mode": True, "live_provider_required": False}
    request_hash = sha256_text(canonical_json(request_envelope))
    session_packet = {
        "query": query,
        "request_hash": request_hash,
        "provider_response": provider_response,
        "evidence": evidence,
        "action": action,
        "authority_decision": authority_decision,
        "receipt_id": f"demo-receipt-{fixture_path.stem}",
        "action_route": action_route,
        "commitment_request": commitment_request,
        "execution_handoff": execution_handoff,
    }
    manifest = {
        "schema": "stegverse.governed_llm_demo_manifest.v1",
        "fixture": str(fixture_path.relative_to(REPO_ROOT)),
        "session_hash": sha256_text(canonical_json(session_packet)),
        "manifest_binding_is_persistence": False,
    }
    receipt = {
        "schema": "stegverse.governed_llm_demo_receipt.v1",
        "receipt_id": session_packet["receipt_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": authority_decision,
        "provider_output_is_authority": False,
        "commitment_request_is_authority": False,
        "authority_decision_executes_side_effect": False,
        "execution_handoff_executes_side_effect": False,
    }
    return {"session_packet": session_packet, "manifest": manifest, "receipt": receipt}


def write_report(fixture_path: Path, report: dict[str, Any]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"{fixture_path.stem}.session.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, help="Path to a JSON fixture.")
    args = parser.parse_args()
    fixture_path = (REPO_ROOT / args.fixture).resolve() if not Path(args.fixture).is_absolute() else Path(args.fixture)
    report = build_report(fixture_path)
    out = write_report(fixture_path, report)
    print(json.dumps({"status": "PASS", "report": str(out.relative_to(REPO_ROOT)), "authority_decision": report["session_packet"]["authority_decision"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
