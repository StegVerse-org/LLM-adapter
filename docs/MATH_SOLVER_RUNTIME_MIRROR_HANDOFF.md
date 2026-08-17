# Math Solver Runtime Mirror Handoff

## Source of truth

```text
goal_id: MATH-SOLVER-STEGGATE-RUNTIME-001
repository: StegVerse-org/LLM-adapter
canonical_branch: main
runtime_issue: StegVerse-org/LLM-adapter#132
service_gateway_owner: StegVerse-org/LLM-adapter#72
Site activation owner: StegVerse-Labs/Site#240
parent_four_app_goal: StegVerse-Labs/Site#239
canonical_StegGate_owner: StegVerse-Labs/StegCore
credential_authority: TV/TVC
github_token_runtime_authority: NONE
third_party_runtime_dependency: NONE_ALLOWED
session_integration_claim: RELEASED_BY_CONVERGENCE
workflow_cleanup_claim: LLMA-WORKFLOW-CONSOLIDATE-MATH-SOLVER-052
```

Live repository/runtime evidence supersedes historical hosted-carrier prose.

## Integration claim — released

The historical integration branch/PR #144 no longer owns implementation. Its bounded runtime-realignment changes converged to current main through canonical commits; `tasks/MATH-SOLVER-STEGGATE-RUNTIME-001.json` is released as `MERGED_INTO_CANONICAL_WORKSTREAM`. Do not recreate the stale integration claim.

## Required execution chain

```text
math expression
-> StegVerse-owned portable node/service gateway
-> canonical runtime identity
-> canonical StegGate + coherence evaluation
-> deterministic arithmetic executor only after ALLOW
-> decision/request/result evidence
-> replay verification
-> Site#240 consumption/public binding
```

No transport URL, host, provider, workflow, or credential grants StegGate authority.

## Canonical runtime implementation — COMPLETE

```text
llm_adapter/steggate_portable_consumer.py
llm_adapter/math_solver_gateway.py
llm_adapter/deployed_gateway.py
llm_adapter/node_bootstrap.py
llm_adapter/combined_gateway.py
scripts/observe_math_solver_public_runtime.py
tests/test_math_solver_gateway.py
tests/test_node_bootstrap.py
tests/test_node_advertisement.py
```

The portable capability manifest uses `llm_adapter.deployed_gateway:app`, declares Math Solver readiness/solve routes, and records TV/TVC credential authority with GitHub-token runtime authority `NONE`. The node advertisement exposes Math Solver endpoints as health-bound, non-authorizing metadata. `observe_math_solver_public_runtime.py` defaults to `http://127.0.0.1:8000` and accepts an eligible StegVerse-owned/federated origin; no third-party host is required.

## Deterministic validation transport

Historical `.github/workflows/math-solver-governed-runtime.yml` used GitHub-hosted `actions/checkout@v4`, `actions/setup-python@v5`, a pinned StegCore install, and `actions/upload-artifact@v4` with 90-day retention. Its substantive capability was deterministic source validation and replay proof; it did not prove an eligible sovereign carrier.

Under cleanup claim `LLMA-WORKFLOW-CONSOLIDATE-MATH-SOLVER-052` that validation is moved into the canonical credential-clean Goal 4 path:

```text
.github/workflows/math-solver-governed-runtime.yml
  -> CONSOLIDATE_INTO_STABLE_DISPATCHER
  -> removed
scripts/verify_goal4_full.py
  -> executes tests/test_math_solver_gateway.py
  -> executes scripts/verify_math_solver_governed_runtime.py
scripts/verify_math_solver_governed_runtime.py
  -> verifies canonical StegGate runtime identity
  -> verifies deterministic request/result/runtime-identity replay
  -> verifies executor invocation only after ALLOW
  -> verifies result 42 for deterministic 6 * 7 fixture
  -> emits workspace-local evidence only
  -> authority_effect=false
  -> public_deployment_proven=false
  -> sovereign_carrier_observed=false
```

Canonical StegCore is already pinned in the dev dependency set at `8c484e584d60a3bd2763d6948d0eb3f4afd67e0c`, so the global validation path can execute the same identity-bound checks without a separate token-backed setup workflow. The global dispatcher has `permissions: {}`, explicit credential refusal, anonymous exact-source acquisition, no schedule, no repository writeback, no artifact transport, and no activation effect.

Historical source-validation runs remain provenance only:

```text
validate: 31917502963 SUCCESS
capability-runtime: 31917502959 SUCCESS
Architecture Guard: 31917502880 SUCCESS
legacy HIL restart lane: SUPERSEDED_BY_TVC_AND_RETIRED
```

## Credential boundary

```text
credential_authority: TV/TVC
provider_credentials_required_for_math_solver: false
github_token_runtime_authority: NONE
non_tv_tvc_production_secret_or_token_allowed: false
GitHub Actions activation role: NONE
```

Repository-hosted deterministic validation does not grant production authority.

## Completion gates

1. bounded deterministic evaluator — COMPLETE;
2. canonical StegGate pre-execution — COMPLETE;
3. canonical runtime identity binding — COMPLETE / VALIDATED;
4. non-ALLOW cannot invoke executor — COMPLETE;
5. request/result/decision evidence — COMPLETE;
6. deterministic replay tests — COMPLETE;
7. StegVerse portable-node route contains Math Solver — COMPLETE / REPOSITORY VALIDATED;
8. eligible StegVerse carrier directly observed — PENDING MACHINE EXECUTION;
9. Site public client consumes directly proven StegVerse runtime receipt — PENDING gate 8.

## Machine-owned continuation

```text
StegVerse-Labs/.github resident sovereign carrier
StegVerse-org/LLM-adapter#72 service-gateway/portable-node runtime
StegVerse-org/LLM-adapter#132 Math Solver runtime task
scripts/observe_math_solver_public_runtime.py
StegVerse-Labs/Site#240 activation consumer
StegVerse-Labs/StegCore#70 common runtime binding
```

Machine-observable release condition for full activation: an eligible resident StegVerse carrier serves current Math Solver routes, `observe_math_solver_public_runtime.py` records `COMPLETE`, and Site#240 consumes that exact verified runtime receipt.

## Archive / collision rule

Do not create another Math Solver evaluator, provider route, or runtime carrier. HIL lifecycle belongs to TVC. The source implementation/integration claim is released; remaining live execution is machine/Site owned.

```text
source/task implementation gates: 7/9 complete
live carrier/Site gates: 0/2 complete
session integration claim: MERGED_INTO_CANONICAL_WORKSTREAM
workflow cleanup claim: NOT RELEASED until exact-head validation, PR merge, census, claim release and canonical workflow handoff update
```
