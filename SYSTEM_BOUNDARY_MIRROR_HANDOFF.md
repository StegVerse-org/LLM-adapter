# System-Boundary Adapter Mirror Handoff

## Authority

This is the bounded continuation record for system-boundary declaration generation in `StegVerse-org/LLM-adapter`.

Repository-wide authority remains `LLM_ADAPTER_MIRROR_HANDOFF.md`. Source doctrine remains `StegVerse-Labs/admissibility-wiki/docs/governance/SYSTEM_BOUNDARY_MIRROR_HANDOFF.md`.

## Installed surfaces

```text
llm_adapter/system_boundary.py
llm_adapter/system_boundary_binding.py
llm_adapter/system_boundary_receipt.py
llm_adapter/system_boundary_lifecycle.py
tests/test_system_boundary.py
tests/test_system_boundary_binding.py
tests/test_system_boundary_receipt.py
tests/test_system_boundary_lifecycle.py
docs/SYSTEM_BOUNDARY_DECLARATION.md
receipts/system-boundary-adapter-implementation-2026-07-14.json
receipts/system-boundary-lifecycle-binding-2026-07-14.json
```

## Current state

```text
runtime surface inventory: installed
feedback path recording: installed
commit boundary declaration: installed
model execution authority: false
deterministic declaration identity: installed
replayable declaration receipt: installed
optional governed payload binding: installed
explicit governed-session lifecycle binding: installed
declaration reference persistence: installed in returned bound payload
replay and conflict handling: installed
automatic production gateway binding: disabled
canonical workflow test step: installed
ios workflow mirror test step: installed
canonical workflow observation: pending
sdk ingestion observation: pending
site publication: not authorized
publisher propagation: not authorized
```

## Identity and receipt rule

Declaration identity is derived from canonical operational content:

```text
schema version
system id
runtime surfaces
continuity and feedback paths
authority boundary
claims boundary
```

Observation time is excluded from identity so identical runtime boundaries replay to the same identifier. Changes to material runtime boundaries produce a different identifier.

The receipt binds the canonical declaration hash, evidence references, optional source commit, and optional previous receipt hash. Receipt-chain changes rotate the receipt hash without changing the declaration identity when the underlying runtime boundary is unchanged.

## Lifecycle binding rule

The lifecycle binder is explicit and post-response. It is not automatically enabled in `combined_gateway.py`.

```text
governed response exists
-> session_id, transition_id, and run_id must match
-> transition/run/final/gateway receipt references become evidence
-> canonical declaration identity is derived
-> deterministic declaration receipt is generated
-> system_boundary_declaration_ref is persisted in the returned payload
```

Replay behavior:

```text
identical complete prior binding -> return idempotently
partial prior binding -> fail closed
tampered prior receipt -> fail closed
identity mismatch -> fail closed
material lifecycle evidence change -> rotate declaration identity
receipt-chain-only change -> preserve declaration identity and rotate receipt
```

## Preserved boundaries

```text
model output != execution authority
self-report != continuity evidence
recurrence != identity continuity
state persistence != consciousness
feedback paths != admissibility
system-boundary declaration != permission to execute
receipt != master-records custody
receipt presence != public validation
explicit lifecycle binding != production activation
declaration reference persistence != SDK acceptance
```

## Completed goal

```text
goal_id: system-boundary-runtime-lifecycle-binding
result: STRUCTURALLY_INSTALLED_PENDING_WORKFLOW_OBSERVATION
completed work:
- lifecycle integration point
- declaration reference persistence
- replay/conflict handling
- canonical and iOS-safe workflow test integration
- durable installation receipt
```

## Next goal

```text
goal_id: system-boundary-workflow-and-sdk-roundtrip-evidence
goal: observe canonical validation for all four system-boundary test modules, repair only the first repository-local failure if present, then preserve system_boundary_declaration_ref through an authorized SDK receipt round trip
required work:
- workflow run containing 9d15f54a2027242e50a82c5fec1f1b2bbbc36cd6 or later
- workflow result and job evidence
- failure repair receipt only if needed
- SDK handoff review before downstream mutation
- SDK declaration and receipt reference round-trip fixture
- SDK validation evidence
```

## Remaining destination work

```text
StegVerse-org/LLM-adapter:
- canonical workflow PASS covering all four system-boundary test modules
- production gateway migration remains separately gated
- replay conflict observation receipt from workflow evidence

StegVerse-org/StegVerse-SDK:
- destination handoff review before mutation
- workflow observation of SDK system-boundary tests
- receipt serialization and system_boundary_declaration_ref round-trip evidence

StegVerse-Labs/Site:
- bounded public status only after adapter and SDK verification

GCAT-BCAT-Engine/Publisher:
- governed bundle metadata only after destination handoff authorization
```

## Permitted continuation

A successor session may inspect canonical workflow evidence, repair the first repository-local failing step, update local receipts and handoffs, and review the SDK destination handoff. No automatic production binding or downstream repository mutation is authorized by this file.

## Archival status

All workstream-specific decisions, installed files, remaining work, ownership, and boundaries are durable here. Earlier conversation context is not required for continuation.
