# Math Solver Runtime Mirror Handoff

## Source of truth

```text
goal_id: MATH-SOLVER-STEGGATE-RUNTIME-001
repository: StegVerse-org/LLM-adapter
integration_branch: fix/math-solver-stegverse-portable-node-20260815
runtime_issue: StegVerse-org/LLM-adapter#132
service_gateway_owner: StegVerse-org/LLM-adapter#72
Site activation owner: StegVerse-Labs/Site#240
parent four-app goal: StegVerse-Labs/Site#239
canonical StegGate owner: StegVerse-Labs/StegCore
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

Live repository/runtime evidence supersedes historical hosted-carrier prose.

## Current claim

```text
role: CLAIMED_FOR_INTEGRATION
claim: STEGVERSE_PORTABLE_NODE_RUNTIME_REALIGNMENT
created: 2026-08-15T18:58:00-05:00
release: merge with validation, then return execution to canonical StegVerse carrier + Site#240
```

The original deterministic Math Solver and canonical StegGate integration are already implemented and CI-validated. This claim only removes the obsolete third-party required-host assumption and binds the existing Math Solver route into the existing StegVerse portable-node/service-gateway execution surface.

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

No transport URL, host, provider, or workflow grants StegGate authority.

## Canonical runtime implementation — COMPLETE

Implemented surfaces remain:

```text
llm_adapter/steggate_portable_consumer.py
llm_adapter/math_solver_gateway.py
llm_adapter/deployed_gateway.py
tests/test_math_solver_gateway.py
.github/workflows/math-solver-governed-runtime.yml
```

The strongest retained identity-bound CI evidence remains run `31338939595` / artifact `9045196248`, proving canonical runtime identity, ALLOW-before-execution, executor invocation, request/result replay equality, and decision evidence. CI is validation only, not activation.

## StegVerse runtime realignment — IMPLEMENTED / VALIDATION PENDING

This integration tranche changes the required carrier from a third-party hosted service to the already-existing StegVerse portable-node/service-gateway path:

```text
llm_adapter.node_bootstrap
-> llm_adapter.node_service
-> uvicorn llm_adapter.deployed_gateway:app
-> /api/stegverse-node
-> /api/math-solver/v1/readiness
-> /api/math-solver/v1/solve
```

`node_bootstrap` now materializes `llm_adapter.deployed_gateway:app`, which contains the combined gateway plus the Math Solver router and bounded user-LLM surface. The capability manifest declares Math Solver readiness/solve routes, TV/TVC credential authority, and GitHub-token runtime authority `NONE`.

The StegVerse node advertisement now exposes Math Solver readiness/solve endpoints as health-bound, non-authorizing endpoint metadata.

`observe_math_solver_public_runtime.py` no longer defaults to a third-party origin. Its default is the node-local StegVerse portable runtime at `http://127.0.0.1:8000`; an authorized StegVerse carrier may provide `MATH_SOLVER_RUNTIME_ORIGIN` when it binds a reachable StegVerse-owned/federated endpoint.

## Superseded dependency

```text
required Render service: SUPERSEDED
Render build capacity as blocker: SUPERSEDED
third_party_host_required: false
third_party_host_release_condition: false
```

Historical hosted observations remain provenance only. They are not a production/runtime dependency and must not be revived as one.

## Credential boundary

```text
credential_authority: TV/TVC
provider_credentials_required_for_math_solver: false
github_token_runtime_authority: NONE
hosted_provider_fallback_required: false
```

Existing GitHub-hosted CI may still use repository credentials for GitHub mechanics; that does not make those credentials runtime authority and remains separate workflow/token-cleanup debt.

## Validation required for this tranche

```text
python -m pytest tests/test_node_bootstrap.py tests/test_node_advertisement.py tests/test_math_solver_gateway.py -q
portable-node start/health proof when an eligible StegVerse carrier is available
GET /api/stegverse-node includes Math Solver endpoints
GET /api/math-solver/v1/readiness -> READY + canonical_steggate_bound=true
POST /api/math-solver/v1/solve twice -> ALLOW + EXECUTED + replay equality
```

## Completion gates

1. bounded deterministic evaluator — COMPLETE;
2. canonical StegGate pre-execution — COMPLETE;
3. canonical runtime identity binding — COMPLETE / CI VALIDATED;
4. non-ALLOW cannot invoke executor — COMPLETE;
5. request/result/decision evidence — COMPLETE;
6. deterministic replay tests — COMPLETE;
7. StegVerse portable-node route contains Math Solver — IMPLEMENTED / VALIDATION PENDING;
8. eligible StegVerse carrier directly observed — PENDING MACHINE EXECUTION;
9. Site public client consumes directly proven StegVerse runtime receipt — PENDING gate 8.

## Machine-owned continuation after merge

```text
StegVerse-Labs/.github resident sovereign carrier
StegVerse-org/LLM-adapter#72 service-gateway/portable-node runtime
StegVerse-org/LLM-adapter#132 Math Solver runtime task
StegVerse-Labs/Site#240 activation consumer
StegVerse-Labs/StegCore#70 common runtime binding
```

## Archive / collision rule

Do not create another Math Solver evaluator, provider route, or runtime carrier. Once this integration claim is merged/released, live execution belongs to the canonical StegVerse carrier and Site consumer. This session may then move to another distinct backend-support dependency rather than polling the runtime.
