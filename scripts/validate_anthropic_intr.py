#!/usr/bin/env python3
"""Source-integrity gate for stegverse.intr.anthropic.transport.v1.

This gate never attests live provider execution, route admission, credentials,
Master Records custody, egress ALLOW, product activation, tag, or release.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = [
    "llm_adapter/anthropic_intr_transport.py",
    "llm_adapter/anthropic_intr_executor.py",
    "schemas/stegverse-intr-anthropic-transport-envelope.schema.json",
    "schemas/stegverse-intr-anthropic-evidence.schema.json",
    "schemas/stegverse-intr-anthropic-capability.json",
    "docs/CANONICALIZATION.md",
    "docs/BRANCH_288_INSTALL.md",
    "docs/ANTHROPIC_INTR_MIRROR_HANDOFF.md",
    "examples/reference_transaction.py",
    "tests/test_anthropic_intr_transport.py",
    "tests/test_anthropic_content_blocks.py",
    "tests/test_anthropic_intr_executor.py",
    "tests/test_anthropic_adversarial.py",
    "tasks/LLMA-ANTHROPIC-INTR-TRANSPORT-288.json",
]


def git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout.strip() if p.returncode == 0 else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", default="feat/anthropic-intr-transport-288")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    checks: list[dict[str, Any]] = []
    def check(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    observed = git("rev-parse", "--abbrev-ref", "HEAD")
    head = git("rev-parse", "HEAD")
    status = git("status", "--porcelain")
    check("branch_identity", observed == ns.branch, observed)
    check("head_commit_present", len(head) == 40, head)
    check("worktree_clean", status == "", status)

    for path in REQUIRED:
        check("required:" + path, (ROOT / path).is_file())

    cap = json.loads((ROOT / "schemas/stegverse-intr-anthropic-capability.json").read_text())
    check("protocol_version", cap.get("protocol_version") == "stegverse.intr.anthropic.transport.v1")
    check("provider_anthropic", cap.get("provider") == "anthropic")
    check("optional_interoperability", cap.get("optional_interoperability") is True)
    check("non_authoritative", cap.get("authoritative") is False)
    check("authority_effect_none", cap.get("authority_effect") == "NONE")
    check("credential_authority_tvtvc", cap.get("credential_authority") == "TV/TVC")
    check("credential_material_absent", cap.get("credential_material_present") is False)
    check("egress_intr_required", cap.get("egress_intr_required") is True)
    check("sovereign_route_not_replaced", cap.get("canonical_sovereign_route_replaced") is False)
    check("hosted_provider_not_required", cap.get("hosted_provider_required") is False)
    check("endpoint_pinned", cap.get("endpoint", {}).get("url") == "https://api.anthropic.com/v1/messages")
    check("api_version_pinned", cap.get("endpoint", {}).get("admitted_api_versions") == ["2023-06-01"])
    check("streaming_not_admitted", "streaming" in cap.get("unsupported", {}))
    check("files_not_admitted", "files_api" in cap.get("unsupported", {}))
    check("batches_not_admitted", "batches_api" in cap.get("unsupported", {}))

    transport_text = (ROOT / "llm_adapter/anthropic_intr_transport.py").read_text()
    executor_text = (ROOT / "llm_adapter/anthropic_intr_executor.py").read_text()
    combined = transport_text + "\n" + executor_text
    check("no_env_api_key_lookup", "ANTHROPIC_API_KEY" not in combined)
    check("no_openai_fallback", "api.openai.com" not in combined)
    check("no_zai_fallback", "api.z.ai" not in combined)
    check("no_deepseek_fallback", "api.deepseek.com" not in combined)
    check("native_endpoint_present", "https://api.anthropic.com/v1/messages" in combined)
    check("tvtvc_literal_present", "TV/TVC" in combined)
    check("egress_verifier_present", "verify_egress" in combined)
    check("master_records_handoff_present", "build_master_records_handoff" in combined)

    snippet = (
        "from llm_adapter.anthropic_intr_transport import digest;"
        "print(digest('test', {'b':[2,1],'a':'x'}))"
    )
    vals = []
    for seed in ("1", "77"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT))
        p = subprocess.run([sys.executable, "-c", snippet], cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        vals.append((p.returncode, p.stdout.strip()))
    check("hashseed_determinism", vals[0][0] == 0 and vals[1][0] == 0 and vals[0][1] == vals[1][1], vals)

    test = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_anthropic_*.py"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    check("anthropic_unittest_suite", test.returncode == 0, test.stdout[-4000:])

    compile_run = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "llm_adapter/anthropic_intr_transport.py", "llm_adapter/anthropic_intr_executor.py", "examples/reference_transaction.py"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    check("compileall", compile_run.returncode == 0, compile_run.stdout[-2000:])

    passed = len(checks) == 43 and all(row["pass"] for row in checks)
    report = {
        "schema": "stegverse.anthropic-intr-source-validation/v1",
        "protocol_version": "stegverse.intr.anthropic.transport.v1",
        "branch_expected": ns.branch,
        "branch_observed": observed,
        "head_commit": head,
        "check_count": len(checks),
        "checks": checks,
        "outcome": "PASS" if passed else "FAIL",
        "merge_permitted": passed,
        "scope": "installed-source integrity only",
        "attests_live_claude_execution": False,
        "attests_custody_acceptance": False,
        "attests_egress_allow": False,
        "attests_product_activation": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
