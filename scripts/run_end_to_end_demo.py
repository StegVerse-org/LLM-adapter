#!/usr/bin/env python3
"""Run the fixture-first governed LLM end-to-end demo."""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RESPONSES = {
    "What is the capital of France?": "Informational answer: the capital of France is Paris.",
    "Please draft a commit message updating the README file.": "Candidate commit message: update README with governed LLM demo notes.",
}

def cjson(v: Any) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"))

def sha(v: Any) -> str:
    return hashlib.sha256(cjson(v).encode("utf-8")).hexdigest()

def build(path: Path) -> dict[str, Any]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    q = fixture["query"]
    expected = fixture.get("expected_outcome", "ALLOW")
    stale = expected == "QUARANTINE" and "stale" in path.name
    action = "DRAFT_ACTION_CANDIDATE" if "commit" in q.lower() or "update" in q.lower() else "NONE"
    decision = "QUARANTINE" if stale or action != "NONE" else "ALLOW"
    packet = {
        "query": q,
        "request_hash": sha({"query": q, "fixture_mode": True, "live_provider_required": False}),
        "provider_response": RESPONSES.get(q, f"Fixture response for: {q}"),
        "evidence": {"sources": ["fixtures/basic_source"], "stale": stale},
        "action": action,
        "authority_decision": decision,
        "receipt_id": f"demo-receipt-{path.stem}",
        "action_route": None,
        "commitment_request": None,
        "execution_handoff": None,
    }
    if action != "NONE":
        packet["action_route"] = {"route": "repository_change_candidate", "executes_side_effect": False}
        packet["commitment_request"] = {"request_type": "commit_candidate", "is_authority": False}
        packet["execution_handoff"] = {"enabled": False, "executes_side_effect": False}
    return {
        "session_packet": packet,
        "manifest": {"schema": "stegverse.governed_llm_demo_manifest.v1", "session_hash": sha(packet), "manifest_binding_is_persistence": False},
        "receipt": {"schema": "stegverse.governed_llm_demo_receipt.v1", "generated_at": datetime.now(timezone.utc).isoformat(), "decision": decision, "provider_output_is_authority": False, "commitment_request_is_authority": False, "authority_decision_executes_side_effect": False, "execution_handoff_executes_side_effect": False},
    }

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fixture", required=True)
    args = p.parse_args()
    fixture = Path(args.fixture)
    if not fixture.is_absolute():
        fixture = ROOT / fixture
    report = build(fixture)
    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"{fixture.stem}.session.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "report": str(out.relative_to(ROOT)), "authority_decision": report["session_packet"]["authority_decision"]}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
