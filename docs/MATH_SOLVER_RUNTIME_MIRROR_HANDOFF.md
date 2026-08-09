# Math Solver Runtime Mirror Handoff

## Source of truth

Goal ID: `MATH-SOLVER-STEGGATE-RUNTIME-001`

Originating session goal: convert the public StegVerse Math Solver from `RESEARCH_NOTE` into a real deterministic public application whose execution is gated by the canonical StegGate runtime, with inspectable decision and replay evidence.

Repository: `StegVerse-org/LLM-adapter`
Branch: `main`
Canonical application tracker: `StegVerse-Labs/Site#240`
Parent four-app goal: `StegVerse-Labs/Site#239`
Canonical StegGate owner: `StegVerse-Labs/StegCore#68`
Common integration owner: `StegVerse-Labs/StegCore#70`
Runtime implementation issue: `StegVerse-org/LLM-adapter#132`

## Claim

Task ID: `MATH-SOLVER-STEGGATE-RUNTIME-001`
Role: implementation + validation + hosted integration of the non-LLM deterministic runtime adapter.
Claimant: this repository execution lane.
Claim creation: 2026-08-08T21:15:00-05:00.
Release condition: hosted route and public Site solve/replay path are directly observed and Site#240 acceptance evidence is complete.
Collision boundary: do not create a parallel StegGate evaluator; use `llm_adapter/steggate_portable_consumer.py` and canonical StegCore.
Current claim state: `BLOCKED / CLAIMED_FOR_INTEGRATION`.

## Authoritative files

- `llm_adapter/steggate_portable_consumer.py`
- `llm_adapter/math_solver_gateway.py`
- `llm_adapter/deployed_gateway.py`
- `tests/test_math_solver_gateway.py`
- `.github/workflows/math-solver-governed-runtime.yml`
- `scripts/observe_math_solver_public_runtime.py`
- `.github/workflows/observe-math-solver-public-runtime.yml`
- `tasks/MATH-SOLVER-STEGGATE-RUNTIME-001.json`
- `receipts/math-solver-runtime-claim.latest.json`
- `receipts/math-solver-public-runtime.latest.json`
- `pyproject.toml`
- this handoff

Public client owner:

- `StegVerse-Labs/Site/math-solver/index.html`
- `StegVerse-Labs/Site#240`

## Required execution chain

```text
public math expression
-> normalized request hash
-> canonical portable StegGate package
-> canonical StegGate + coherence evaluation
-> deterministic arithmetic executor only after ALLOW
-> execution observation + decision/hash evidence
-> response receipt
-> public Site display
-> deterministic replay/verification
```

## Completion gates

1. safe bounded deterministic arithmetic evaluator exists — COMPLETE + VALIDATED;
2. canonical StegGate is in the pre-execution path — COMPLETE + VALIDATED IN CI;
3. non-ALLOW cannot invoke the evaluator — IMPLEMENTED + canonical consumer boundary retained;
4. request/result hashes and StegGate execution evidence are returned — COMPLETE + VALIDATED IN CI;
5. tests prove ALLOW, bounded rejection, HTTP readiness, and deterministic replay — COMPLETE;
6. hosted service route is directly observed — BLOCKED; current public route returns 404 because new source has not deployed;
7. Site public client calls the hosted route fail-closed — IMPLEMENTED, deployment/runtime behavior not yet directly verified;
8. deployed public request and replay/verification are directly observed — WAITING ON gate 6 and deployed Site observation.

## Validation evidence

GitHub Actions workflow: `.github/workflows/math-solver-governed-runtime.yml`

Successful run:

```text
run_id: 31290093572
job_id: 93185673393
head_sha: e9fda1911915964e002dcb2d2c4c3aaf02a420cd
conclusion: SUCCESS
all workflow steps: SUCCESS
artifact_id: 9031088299
artifact: math-solver-steggate-integration
artifact_digest: sha256:e863d4aaa6bf6fbc34746e1f0eb10028a320bf861bf2d2246cd673fdf0de67c1
```

The workflow installs canonical StegCore commit `819884022b32e283ac36eddbab97a2b9ecebc874`, runs dedicated Math Solver tests, executes two governed `6 * 7` requests, verifies request/result replay hash equality, requires canonical pre-execution ALLOW with the executor actually invoked, and retains the integration evidence artifact. CI evidence does not prove hosted deployment.

## Hosted deployment state

Existing authorized deployment surface:

```text
Render service: stegverse-ecosystem-chat-gateway
service_id: srv-d9epkh3rjlhs73csc3qg
origin: https://stegverse-ecosystem-chat-gateway.onrender.com
repo: StegVerse-org/LLM-adapter
branch: main
auto_deploy: yes
entrypoint: llm_adapter.deployed_gateway:app
```

`llm_adapter/deployed_gateway.py` includes the Math Solver router and the service runtime extra pins canonical StegCore.

Latest observed source deploy containing the Math Solver route:

```text
head: e9fda1911915964e002dcb2d2c4c3aaf02a420cd
deploy_id: dep-d9ru79jbc2fs73av1qsg
status: build_failed
machine cause: Render workspace build pipeline minutes exhausted
```

Render cancels the deployment before source build. Paid workspace upgrade/spend increase is not implied or authorized by this lane.

## Public runtime observer — ACTIVE

Repository-native observer:

```text
script: scripts/observe_math_solver_public_runtime.py
workflow: .github/workflows/observe-math-solver-public-runtime.yml
schedule: hourly at minute 43 plus relevant pushes/manual dispatch
receipt: receipts/math-solver-public-runtime.latest.json
```

First observed cycle:

```text
run_id: 31290234186
job_id: 93186026342
artifact_id: 9031127945
artifact_digest: sha256:9672ad10fab8a534d77e8d38cee2ba5f9fa5e7e092b31008dcfe03506141449a
state: BLOCKED
public result: HTTP 404 /api/math-solver/v1/readiness
```

This confirms the new route is not live; it does not treat a 404 as progress. The observer retries automatically and retains evidence. A persistence bug in its first commit check was corrected by using `git status --porcelain`, and the first blocker receipt was committed explicitly.

Machine-observable release condition: a later deployment containing the Math Solver runtime reaches `live`, then the observer must verify readiness, two `6 * 7` solve calls, ALLOW + EXECUTED + executor invoked, request/result replay hash equality, decision hash presence, and Site-compatible CORS.

## Site client state

`StegVerse-Labs/Site/math-solver/index.html` was upgraded from the research-only page to a fail-closed interactive governed client in commit `f45fe0ae7e21dd19b20b119ab78956a7c77eb72c`.

The client:

- probes `/api/math-solver/v1/readiness`;
- disables execution when readiness is unavailable;
- sends arithmetic requests only to the governed hosted route;
- provides no ungated local solver fallback;
- displays disposition, execution state, decision/hash evidence, matrix, result hash, and replay comparison;
- withholds the production claim until hosted readiness + solve + replay are directly observed.

Site machine status correctly remains at Math Solver 1/7 execution gates because implementation/CI evidence is not substituted for public runtime evidence.

## Current state

`IMPLEMENTED_AND_CI_VALIDATED / FAIL_CLOSED_SITE_CLIENT_IMPLEMENTED / HOST_DEPLOYMENT_BLOCKED / PUBLIC_OBSERVER_ACTIVE`.

This is not product activation.

## Exact next tasks

1. Machine observer retries the public route hourly.
2. Existing Render auto-deploy remains the deployment lane; successful build capacity is the machine-observable unblock condition.
3. On observer COMPLETE, consume the receipt in `StegVerse-Labs/Site#240` and verify the deployed Site client end-to-end.
4. Advance `StegVerse-Labs/Site/data/steggate-four-app-status.json` only for directly observed gates.
5. Close LLM-adapter#132 only after hosted route + Site binding + deployed replay acceptance pass.

## Cross-repository continuation

MERGED INTO: `StegVerse-Labs/Site#240` for public application activation and `StegVerse-Labs/Site/docs/STEGGATE_FOUR_APP_MIRROR_HANDOFF.md` for four-app status.

## Progress

```text
runtime/application implementation deliverables: 7/7 implemented
CI validation gates: 5/5 complete
hosted deployment gate: 0/1
public observer: ACTIVE + first BLOCKED receipt retained
Site client implementation: complete; deployed execution observation pending
runtime-lane goal activation: 5/8 execution gates complete = 62%
```

## Archive condition

Product-level archival remains governed by Site#239. This Math Solver lane has a durable task, issue, handoff, blocker receipt, and active hourly observer, but this originating session is not to be described as product-complete from that transfer alone.
