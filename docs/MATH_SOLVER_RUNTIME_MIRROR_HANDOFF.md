# Math Solver Runtime Mirror Handoff

## Source of truth

Goal ID: `MATH-SOLVER-STEGGATE-RUNTIME-001`

Originating session goal: convert the public StegVerse Math Solver from `RESEARCH_NOTE` into a real deterministic public application whose execution is gated by the canonical StegGate runtime, with inspectable decision and replay evidence.

Repository: `StegVerse-org/LLM-adapter`
Branch: `main`
Canonical application tracker: `StegVerse-Labs/Site#240`
Parent four-app goal: `StegVerse-Labs/Site#239`
Canonical StegGate owner: `StegVerse-Labs/StegCore#68` — COMPLETE/CLOSED
Common integration owner: `StegVerse-Labs/StegCore#70` — ACTIVE
Runtime implementation issue: `StegVerse-org/LLM-adapter#132`

## Claim and ownership

Task ID: `MATH-SOLVER-STEGGATE-RUNTIME-001`
Original role: implementation + validation + hosted integration of the non-LLM deterministic runtime adapter.
Original claim created: 2026-08-08T21:15:00-05:00.
Original chat claim released: 2026-08-08T23:56:00-05:00.
Current host-observation state: `MACHINE_OWNED / BLOCKED_HOST_OBSERVATION`.
Current common-runtime binding role: consumed from `StegVerse-Labs/StegCore#70` without creating a parallel evaluator.
Collision boundary: use canonical StegCore; do not make a transport URL into StegGate identity or authority.

Machine owners:

- `StegVerse-org/LLM-adapter/.github/workflows/observe-math-solver-public-runtime.yml` — hourly backend public-runtime observation and durable receipt;
- `StegVerse-Labs/Site/.github/workflows/math-solver-public-activation.yml` — hourly cross-repository receipt consumption, public Site binding verification, status validation, handoff synchronization, and proven-gate persistence.

No chat polling, manual workflow dispatch, blocker transcription, artifact copying, or status advancement is required for the hosted observation lane.

## Authoritative files

- `llm_adapter/steggate_portable_consumer.py`
- `llm_adapter/math_solver_gateway.py`
- `llm_adapter/deployed_gateway.py`
- `tests/test_math_solver_gateway.py`
- `.github/workflows/math-solver-governed-runtime.yml`
- `scripts/observe_math_solver_public_runtime.py`
- `.github/workflows/observe-math-solver-public-runtime.yml`
- `tasks/MATH-SOLVER-STEGGATE-RUNTIME-001.json`
- `receipts/math-solver-public-runtime.latest.json`
- `pyproject.toml`
- this handoff

Cross-repository identity authority:

- `StegVerse-Labs/StegCore/docs/STEGGATE_RUNTIME_IDENTITY_CONTRACT.md`
- `StegVerse-Labs/StegCore/management/steggate-four-app-runtime-binding.json`
- `GET /v1/runtime-identity`

Cross-repository public activation owner:

- `StegVerse-Labs/Site/math-solver/index.html`
- `StegVerse-Labs/Site/scripts/advance_math_solver_public_activation.py`
- `StegVerse-Labs/Site/.github/workflows/math-solver-public-activation.yml`
- `StegVerse-Labs/Site/data/math-solver-public-activation.latest.json`
- `StegVerse-Labs/Site/data/steggate-four-app-status.json`
- `StegVerse-Labs/Site#240`

## Required execution chain

```text
public math expression
-> canonical StegGate runtime identity validation
-> normalized request hash bound to runtime identity/version
-> canonical portable StegGate package
-> canonical StegGate + coherence evaluation
-> deterministic arithmetic executor only after ALLOW
-> execution observation + decision/hash evidence + runtime identity
-> response receipt
-> public Site display
-> deterministic replay/verification
```

## Canonical runtime identity binding — IMPLEMENTED + CI VALIDATED

Math Solver now consumes the StegCore #70 identity contract and fails closed if the installed canonical runtime does not match:

```text
contract_version: stegverse.steggate.runtime-identity.v1
runtime_identity: stegverse:steggate:canonical:three-layer:v1
canonical_owner: StegVerse-Labs/StegCore
canonical_admissibility_runtime: stegcore.three_layer.evaluate_three_layer
transport_identity_authoritative: false
```

The identity is returned by Math Solver readiness and solve responses, bound into request hashing and declared execution context, and included in deterministic replay evidence. This is CI-level application binding evidence; it is not substituted for public-host observation.

Implementation commits:

```text
math_solver_gateway.py identity consumption/evidence: 77932e74295db4e6e408b71267cd353fbb16b0fe
tests: cd9d484b92797c3f2d375108c630375ca0e9da30
StegCore service dependency pin: b1446855e94fd2041dfecc8dce4a10511c033166
workflow identity validation/evidence: e212309d43f26956c68df5d41f15dc5bed0e1d3e
```

The first identity-bound CI attempts exposed the workflow's stale explicit StegCore install pin. That failure was inspected rather than ignored. Both the service dependency and workflow install/evidence pin now use StegCore contract commit `8c484e584d60a3bd2763d6948d0eb3f4afd67e0c`.

Strongest current identity-bound validation:

```text
workflow: .github/workflows/math-solver-governed-runtime.yml
run_id: 31338939595
job_id: 93309372914
conclusion: SUCCESS
artifact_id: 9045196248
artifact: math-solver-steggate-integration
artifact_digest: sha256:5389162e3bef48594802aead69d309d5726bf0e046121129696179c60bce293d
```

The retained artifact includes the canonical runtime identity, replay identity equality, request/result replay equality, and canonical StegGate pre-execution ALLOW with actual executor invocation. `public_deployment_proven` remains false by design.

## Completion gates

1. safe bounded deterministic arithmetic evaluator exists — COMPLETE + VALIDATED;
2. canonical StegGate is in the pre-execution path — COMPLETE + VALIDATED IN CI;
3. canonical #70 runtime identity is consumed and retained — COMPLETE + VALIDATED IN CI;
4. non-ALLOW cannot invoke the evaluator — COMPLETE at the canonical consumer boundary;
5. request/result hashes and StegGate execution evidence are returned — COMPLETE + VALIDATED IN CI;
6. tests prove ALLOW, bounded rejection, HTTP readiness, deterministic replay, and runtime identity binding — COMPLETE;
7. hosted service route is directly observed — BLOCKED; latest durable backend receipt remains authoritative;
8. Site public client calls the hosted route fail-closed — IMPLEMENTED; deployed success awaits gate 7;
9. deployed public request and replay/verification are directly observed — MACHINE WAITING on gate 7.

## Validation evidence

Earlier successful governed runtime evidence remains retained:

```text
workflow: .github/workflows/math-solver-governed-runtime.yml
run_id: 31290093572
job_id: 93185673393
head_sha: e9fda1911915964e002dcb2d2c4c3aaf02a420cd
conclusion: SUCCESS
artifact_id: 9031088299
artifact_digest: sha256:e863d4aaa6bf6fbc34746e1f0eb10028a320bf861bf2d2246cd673fdf0de67c1
```

The current stronger run is `31338939595` because it additionally proves the common runtime identity contract.

## Hosted deployment state

Authorized deployment surface:

```text
Render service: stegverse-ecosystem-chat-gateway
service_id: srv-d9epkh3rjlhs73csc3qg
origin: https://stegverse-ecosystem-chat-gateway.onrender.com
repo: StegVerse-org/LLM-adapter
branch: main
auto_deploy: yes
entrypoint: llm_adapter.deployed_gateway:app
```

The Math Solver router is mounted on that entrypoint. The backend observer's latest durable receipt is the authoritative public-host release-state signal; CI success does not prove hosted deployment.

## Repository-native backend observer — ACTIVE

```text
script: scripts/observe_math_solver_public_runtime.py
workflow: .github/workflows/observe-math-solver-public-runtime.yml
schedule: hourly at minute 43 plus relevant pushes/manual dispatch
receipt: receipts/math-solver-public-runtime.latest.json
```

The observer verifies readiness, two governed solve calls, ALLOW + EXECUTED + executor invocation, decision identity, request/result replay equality, and Site-compatible CORS. Missing or unhealthy public runtime is retained as BLOCKED, never success.

Machine release condition: this receipt becomes `COMPLETE` only after the public runtime satisfies all checks.

## Repository-native Site activation consumer — ACTIVE

Installed in `StegVerse-Labs/Site`:

```text
script: scripts/advance_math_solver_public_activation.py
workflow: .github/workflows/math-solver-public-activation.yml
schedule: hourly at minute 47 plus workflow dispatch/relevant push
durable receipt: data/math-solver-public-activation.latest.json
canonical status: data/steggate-four-app-status.json
canonical handoff: docs/STEGGATE_FOUR_APP_MIRROR_HANDOFF.md
```

The Site consumer fails closed: while the LLM-adapter receipt is not COMPLETE it only records the blocker. After COMPLETE it verifies the public Site page binding, advances only the Math Solver gates represented by complete evidence, runs the canonical four-app validator, synchronizes the handoff, commits the state transition, and retains an artifact.

## Current state

`IMPLEMENTED_AND_CI_VALIDATED / CANONICAL_RUNTIME_IDENTITY_CI_BOUND / FAIL_CLOSED_SITE_CLIENT_IMPLEMENTED / HOST_RUNTIME_OBSERVATION_PENDING / BACKEND_OBSERVER_ACTIVE / SITE_ACTIVATION_CONSUMER_ACTIVE`.

This is not public product activation.

## Cross-repository continuation

Public completion remains owned by `StegVerse-Labs/Site#240` and `StegVerse-Labs/Site/docs/STEGGATE_FOUR_APP_MIRROR_HANDOFF.md`.

Common identity integration is owned by `StegVerse-Labs/StegCore#70` and `management/steggate-four-app-runtime-binding.json`.

Parent continuation: `StegVerse-Labs/Site#239`.

## Progress

```text
runtime/application implementation deliverables: 9/9 implemented
CI validation gates: 7/7 complete
canonical runtime identity binding: CI_COMPLETE / PUBLIC_PENDING
hosted deployment gate: 0/1
backend public observer: ACTIVE
Site activation consumer: ACTIVE
runtime-lane goal activation: 7/9 execution/identity gates complete = 78%
parent four-app public gate effect from CI-only identity evidence: NONE
```

## Archive condition for the originating Math Solver implementation lane

The original Math Solver implementation lane remains durably transferred to its machine owners. The broader current conversation, however, owns active StegCore #70 four-app binding work and must not be treated as archiveable until that active claim is released or the parent four-app goal is complete under its canonical archive rule.
