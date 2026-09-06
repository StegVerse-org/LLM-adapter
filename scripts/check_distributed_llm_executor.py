#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REQUIRED=["llm_adapter/distributed_executor.py","schemas/ecosystem-chat-distributed-llm-execution.schema.json","tests/test_distributed_executor.py","scripts/check_distributed_llm_executor.py","docs/DISTRIBUTED_LLM_EXECUTOR_MIRROR_HANDOFF.md","tasks/LLMA-DISTRIBUTED-LLM-EXECUTOR-274.json","data/preflight/LLMA-DISTRIBUTED-LLM-EXECUTOR-274-20260906.json","README.md"]
MARKERS=["SUPPORTED_EXECUTION_MODES","UNSUPPORTED_DERIVED_INPUT_MODES","ProviderRefusalError","OPTIONAL_SOURCE_CLIENT_UNAVAILABLE","requires a governed derived-input contract","DistributedExecutionSummary","execute_distributed_workload"]
README_MARKERS=["Bounded executor support","single`, `parallel`, and `fallback","sequential` and `challenge","Fixture-provider execution","canonical sovereign local/private route remains independently sufficient"]
PROHIBITED=["OPENAI_API_KEY","ANTHROPIC_API_KEY","GITHUB_TOKEN","GH_TOKEN","Authorization: Bearer","https://api.openai.com"]
def main()->int:
    failures=[]
    for p in REQUIRED:
        if not (ROOT/p).is_file(): failures.append(f"missing required file: {p}")
    src=(ROOT/"llm_adapter/distributed_executor.py").read_text() if (ROOT/"llm_adapter/distributed_executor.py").exists() else ""
    for m in MARKERS:
        if m not in src: failures.append(f"missing executor marker: {m}")
    for m in PROHIBITED:
        if m in src: failures.append(f"prohibited credential/endpoint marker: {m}")
    readme=(ROOT/"README.md").read_text() if (ROOT/"README.md").exists() else ""
    for m in README_MARKERS:
        if m not in readme: failures.append(f"README missing marker: {m}")
    pre=json.loads((ROOT/"data/preflight/LLMA-DISTRIBUTED-LLM-EXECUTOR-274-20260906.json").read_text()) if (ROOT/"data/preflight/LLMA-DISTRIBUTED-LLM-EXECUTOR-274-20260906.json").exists() else {}
    if pre.get("verdict")!="PASS": failures.append("preflight not PASS")
    impact=pre.get("readme_impact",{})
    if impact.get("readme_impact_required") is not True or impact.get("readme_updated_in_change_set") is not True: failures.append("README completeness predicate unsatisfied")
    task=json.loads((ROOT/"tasks/LLMA-DISTRIBUTED-LLM-EXECUTOR-274.json").read_text()) if (ROOT/"tasks/LLMA-DISTRIBUTED-LLM-EXECUTOR-274.json").exists() else {}
    auth=task.get("authority_contract",{})
    if auth.get("canonical_local_route_remains_sufficient") is not True: failures.append("canonical local route not preserved")
    for k,v in auth.items():
        if k!="canonical_local_route_remains_sufficient" and v is True: failures.append(f"authority/dependency escalation: {k}")
    schema_path=ROOT/"schemas/ecosystem-chat-distributed-llm-execution.schema.json"
    if schema_path.exists():
        schema=json.loads(schema_path.read_text())
        if ((schema.get("properties") or {}).get("schema_version") or {}).get("const") != "stegverse.ecosystem_chat.distributed_llm_execution.v1": failures.append("execution schema version mismatch")
    if not failures:
        p=subprocess.run([sys.executable,"-m","pytest","tests/test_distributed_executor.py","-q"],cwd=ROOT,text=True,capture_output=True)
        if p.returncode: failures.append("executor tests failed:\n"+p.stdout+p.stderr)
    if failures:
        print("DISTRIBUTED_LLM_EXECUTOR_FAIL")
        for f in failures: print("-",f)
        return 1
    print("DISTRIBUTED_LLM_EXECUTOR_PASS")
    print("authority_effect=NONE_SOURCE_VALIDATION_ONLY")
    print("live_external_named_source_execution_observed=false")
    return 0
if __name__=="__main__": raise SystemExit(main())
