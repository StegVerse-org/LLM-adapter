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
sdk round-trip verifier: installed
sdk round-trip tests: installed
sdk explicit workflow step: installed
sdk workflow observation: pending
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

## SDK round-trip rule

Destination handoff reviewed:

```text
StegVerse-org/StegVerse-SDK/SDK_MIRROR_HANDOFF.md
```

Installed destination surfaces:

```text
stegverse/system_boundary_round_trip.py
tests/test_system_boundary_round_trip.py
.github/workflows/sdk-demo-test.yml -> explicit round-trip test step
receipts/system-boundary-round-trip-installation-2026-07-14.json
```

The SDK independently reconstructs canonical declaration identity, declaration content hash, receipt body, receipt hash, declaration-reference digest, declaration-reference receipt hash, and evidence-reference preservation. It fails closed on tamper, hash drift, authority escalation, custody escalation, admissibility escalation, production-binding escalation, and consciousness reclassification.

Relevant SDK commits:

```text
874063c94397a11a439fa674e6cebcf69c439da6
610c3c571086bf6884122cd061d9a74fe770252f
49085cc67ac9a68d64feb6378c76e020cf4b822a
37a61dfbdcf161abf51d15fc6da9f5101224e7ea
c4d5f42fb9e11a4407000c876bb6df107a953918
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
declaration reference persistence != SDK execution authority
SDK round-trip acceptance != admissibility, custody, standing, or publication authority
```

## Completed goals

```text
goal_id: system-boundary-runtime-lifecycle-binding
result: STRUCTURALLY_INSTALLED_PENDING_WORKFLOW_OBSERVATION

goal_id: system-boundary-sdk-roundtrip-installation
result: STRUCTURALLY_INSTALLED_PENDING_SDK_WORKFLOW_OBSERVATION
```

Completed work:

```text
- lifecycle integration point
- declaration reference persistence
- replay/conflict handling
- canonical and iOS-safe adapter workflow integration
- SDK declaration/receipt/reference verifier
- SDK deterministic replay and tamper fixtures
- SDK explicit workflow integration
- durable adapter and SDK installation receipts
- synchronized adapter and SDK handoffs
```

## Next goal

```text
goal_id: system-boundary-workflow-observation-closure
goal: observe adapter and SDK canonical workflows containing the installed system-boundary suites, repair only the first repository-local failure if present, and preserve run-bound evidence without enabling production binding
required work:
- LLM-adapter workflow run containing 9d15f54a2027242e50a82c5fec1f1b2bbbc36cd6 or later
- SDK workflow run containing 49085cc67ac9a68d64feb6378c76e020cf4b822a or later
- workflow result and job evidence
- failure repair receipt only if needed
- successful run-bound observation receipt
```

## Remaining destination work

```text
StegVerse-org/LLM-adapter:
- canonical workflow PASS covering all four system-boundary test modules
- production gateway migration remains separately gated
- replay conflict observation receipt from workflow evidence

StegVerse-org/StegVerse-SDK:
- workflow PASS covering declaration and receipt round-trip tests
- run-bound receipt preserving system_boundary_declaration_ref verification

StegVerse-Labs/Site:
- bounded public status only after adapter and SDK verification

GCAT-BCAT-Engine/Publisher:
- governed bundle metadata only after destination handoff authorization
```

## Permitted continuation

A successor session may inspect adapter and SDK canonical workflow evidence, repair the first repository-local failing step, and update local receipts and handoffs. No automatic production binding, Site publication, Publisher propagation, Master-Records custody claim, execution authority, admissibility, standing, or classification claim is authorized by this file.

## Archival status

All workstream-specific decisions, installed files, destination work, remaining observations, ownership, and boundaries are durable here. Earlier conversation context is not required for continuation.
