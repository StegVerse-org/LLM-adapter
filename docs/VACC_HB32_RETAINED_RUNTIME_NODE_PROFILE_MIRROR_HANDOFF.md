# VACC HB32 Retained Runtime Node Profile Mirror Handoff

Updated: 2026-09-09

## Goal Task ID

`VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023`

## Parent runtime convergence

`GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`

Canonical profile:

```text
StegVerse-Labs/.github/control/runtime-node-profiles.json
profile_id: runtime-node:vacp-sovereign-provider-realignment-023
HB protocol: HB32
node_state_class: RETAINED_STEGOS_NODE
execution_session_class: EPHEMERAL_OR_BOUNDED_RUNTIME_LEASE
execution_binding: EXTERNAL_RUNTIME_PROFILE_BRIDGE
```

## Purpose

Bind the already-implemented VACC local-model runtime to the same retained-node lifecycle now used across the global runtime convergence without creating another VACC runtime, heartbeat, scheduler, provider path, or custody path.

The VACC application/runtime state is treated as a task-bound retained StegOS runtime node. A bounded execution opportunity may start and stop while the task/node identity and admitted continuity evidence persist. Provider/session/credential-local execution state must not be treated as retained node identity.

## Existing implementation reused

```text
tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
llm_adapter/va_claims_runtime_core.py
llm_adapter/va_claims_runtime_gateway.py
llm_adapter/va_runtime_http_server.py
llm_adapter/runtime_gateway.py
StegVerse-Labs/.github/workers/va_conversational_runtime_bridge.py
StegVerse-Labs/.github/workers/master_records_sovereign_reconstruction_bridge.py
```

No second VACC gateway/runtime is introduced by the runtime-node profile.

## Retained vs bounded state

```text
RETAINED
VACC task identity
runtime-node profile identity
admitted local-model/runtime identity commitments
TVC route evidence commitments
provider-usage evidence commitments
Master Records reconstruction commitments
persistent VACC readiness state after authentic activation

BOUNDED / EPHEMERAL
individual request execution context
provider request/response transient objects beyond admitted retained evidence
route lease/session-local state
credential material
temporary transport state
```

## Current exact resume classification

The global profile-convergence runner now distinguishes:

```text
PROFILE_BOUND_RUNTIME_LIVE_VERIFIED
PROFILE_BOUND_EXTERNAL_RUNTIME_NOT_MATERIALIZED
PROFILE_BOUND_EXTERNAL_RUNTIME_SOURCE_INCOMPLETE
PROFILE_BOUND_PARENT_RECONSTRUCTION_OR_ROUTE_PENDING
```

This replaces the old generic `NO_REGISTERED_SELECTOR / UNWIRED_CHILD_RUNTIME` umbrella classification.

The child task itself remains `MACHINE_OWNED_READY_FOR_SOVEREIGN_OBSERVATION`. Its authentic completion sequence is unchanged:

1. current local-model runtime proof;
2. TVC `ROUTE_ADMITTED` with credential requirement `NONE`;
3. real VACC request through the exact admitted endpoint;
4. provider-usage custody;
5. same-execution Master Records reconstruction `PASS`;
6. persistent VACC readiness `READY`;
7. admitted public HTTPS transport;
8. real Site -> VACC -> Site observation.

A retained runtime-node profile, HB observation, source merge, CI, or source materialization does not satisfy those runtime predicates.

## HB boundary

HB32 supplies synchronization/freshness/observability context only. It does not replace the existing task, local-model route, TVC route evaluation, WorkerCoordinator claim/fence, Interlock/InTr transition, or Master Records reconstruction.

## README impact

`README.md` was reviewed. Its canonical production path already describes the heartbeat-owned sovereign local runtime, TVC route evaluation, provider usage, and Master Records reconstruction. This profile binding changes runtime coordination/projection metadata, not the adapter's public behavior or provider contract. No README text change is required.

## Manual work

None. The next step is machine-owned authentic resident/profile convergence execution.
