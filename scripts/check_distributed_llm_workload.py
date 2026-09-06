#!/usr/bin/env python3
"""Validate the Ecosystem Chat distributed named-source LLM source contract.

This checker is source/fixture evidence only.  It must not be interpreted as live
provider fan-out, route admission, runtime activation, custody, or publication.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "llm_adapter/distributed_workload.py",
    "schemas/ecosystem-chat-distributed-llm-workload.schema.json",
    "schemas/ecosystem-chat-llm-contribution.schema.json",
    "schemas/ecosystem-chat-llm-reconciliation-request.schema.json",
    "schemas/ecosystem-chat-governed-result.schema.json",
    "tests/test_distributed_workload.py",
    "scripts/check_distributed_llm_workload.py",
    "docs/DISTRIBUTED_LLM_WORKLOAD_MIRROR_HANDOFF.md",
    "tasks/LLMA-DISTRIBUTED-LLM-WORKLOAD-272.json",
    "data/preflight/LLMA-DISTRIBUTED-LLM-WORKLOAD-272-20260906.json",
    "README.md",
]

README_MARKERS = [
    "## Ecosystem Chat distributed LLM service",
    "distributed service across named model sources",
    "No reactive guardrails. Native governance instead.",
    "12-lane analysis",
    "Optional named external sources may expand capability",
    "model majority != governance authority",
]

SOURCE_MARKERS = [
    'ROUTING_MODES = frozenset({"single", "parallel", "sequential", "challenge", "fallback"})',
    "class SourceDescriptor",
    "class DistributedLLMWorkload",
    "class LLMContribution",
    "class ReconciliationRequest",
    "class GovernedLLMResult",
    "EVIDENCE_FOR_EXISTING_GOVERNANCE",
    "embedded provider credential field prohibited",
    "required source contribution missing",
]

PROHIBITED_SOURCE_MARKERS = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "Authorization: Bearer",
]

SCHEMA_VERSIONS = {
    "schemas/ecosystem-chat-distributed-llm-workload.schema.json": "stegverse.ecosystem_chat.distributed_llm_workload.v1",
    "schemas/ecosystem-chat-llm-contribution.schema.json": "stegverse.ecosystem_chat.llm_contribution.v1",
    "schemas/ecosystem-chat-llm-reconciliation-request.schema.json": "stegverse.ecosystem_chat.llm_reconciliation_request.v1",
    "schemas/ecosystem-chat-governed-result.schema.json": "stegverse.ecosystem_chat.governed_llm_result.v1",
}


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def main() -> int:
    failures: list[str] = []

    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            fail(f"missing required file: {relative}", failures)

    module_path = ROOT / "llm_adapter/distributed_workload.py"
    module = module_path.read_text(encoding="utf-8") if module_path.exists() else ""
    for marker in SOURCE_MARKERS:
        if marker not in module:
            fail(f"distributed workload source missing marker: {marker}", failures)
    for marker in PROHIBITED_SOURCE_MARKERS:
        if marker in module:
            fail(f"distributed workload source contains prohibited credential/runtime marker: {marker}", failures)

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    for marker in README_MARKERS:
        if marker not in readme:
            fail(f"README completeness missing marker: {marker}", failures)

    preflight_path = ROOT / "data/preflight/LLMA-DISTRIBUTED-LLM-WORKLOAD-272-20260906.json"
    if preflight_path.exists():
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        if preflight.get("verdict") != "PASS":
            fail("machine preflight verdict is not PASS", failures)
        impact = preflight.get("readme_impact") or {}
        if impact.get("readme_impact_required") is not True or impact.get("readme_updated_in_change_set") is not True:
            fail("README impact completeness predicate not satisfied", failures)
    else:
        fail("machine preflight missing", failures)

    claim_path = ROOT / "tasks/LLMA-DISTRIBUTED-LLM-WORKLOAD-272.json"
    if claim_path.exists():
        claim = json.loads(claim_path.read_text(encoding="utf-8"))
        authority = claim.get("authority_contract") or {}
        prohibited_true = [key for key, value in authority.items() if key != "canonical_local_route_remains_sufficient" and value is True]
        if prohibited_true:
            fail(f"task claim contains authority escalation: {prohibited_true}", failures)
        if authority.get("canonical_local_route_remains_sufficient") is not True:
            fail("canonical sovereign local route is not preserved as independently sufficient", failures)
        if authority.get("optional_external_sources_may_be_required_for_canonical_operation") is not False:
            fail("optional external sources became a canonical dependency", failures)
    else:
        fail("distributed workload task claim missing", failures)

    for relative, expected_schema in SCHEMA_VERSIONS.items():
        path = ROOT / relative
        if not path.exists():
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON schema {relative}: {exc}", failures)
            continue
        if schema.get("type") != "object":
            fail(f"schema root must be object: {relative}", failures)
        version_property = ((schema.get("properties") or {}).get("schema_version") or {}).get("const")
        if version_property != expected_schema:
            fail(f"schema version mismatch {relative}: {version_property!r}", failures)

    if not failures:
        process = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_distributed_workload.py", "-q"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if process.returncode != 0:
            fail("distributed workload tests failed:\n" + process.stdout + process.stderr, failures)

    if failures:
        print("DISTRIBUTED_LLM_WORKLOAD_FAIL")
        for item in failures:
            print(f"- {item}")
        return 1

    print("DISTRIBUTED_LLM_WORKLOAD_PASS")
    print("authority_effect=NONE_SOURCE_VALIDATION_ONLY")
    print("live_distributed_provider_execution_observed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
