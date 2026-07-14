# LLM Adapter Mirror Handoff

## Source of truth

This file is the current continuation source for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: governed Ecosystem Chat and External Chat with provider telemetry, authenticated usage retrieval, bounded review, publication, mutation, and non-authorizing system-boundary evidence
Phase: system-boundary-lifecycle-binding-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_CURRENT_MAIN_GREEN_VALIDATION_PENDING
```

## Installed core surfaces

```text
llm_adapter/combined_gateway.py
llm_adapter/ecosystem_chat_gateway.py
llm_adapter/provider_usage.py
llm_adapter/provider_usage_submission.py
llm_adapter/usage_session_api.py
llm_adapter/external_framework_compatibility.py
llm_adapter/external_review_api.py
llm_adapter/external_review_store.py
llm_adapter/external_publication_mutation.py
scripts/verify_usage_session_api.py
scripts/verify_external_publication_staging.py
scripts/check_ai_entry_no_manual_tasks.py
tests/test_provider_usage.py
tests/test_usage_session_api.py
tests/test_external_review_api.py
.github/workflows/validate.yml
iosnoperiod/github/workflows/validate.yml
```

## Usage-session contract

```text
POST /api/usage/sessions
GET  /api/usage/sessions/{session_id}
```

The endpoint preserves session identity, validates evidence classes and event hashes, deduplicates by `metric_owner + measurement_id`, and returns a bounded retrieval receipt. Local persistence is not Master-Records custody, and retrieval grants no authority or admissibility.

## Completed repository-local validation progression

Observed workflow evidence established that all functional checks and all External Chat compatibility, review, publication, and mutation tests passed through the workflow-parity step. Workflow parity was then repaired by synchronizing the canonical and iOS-safe workflows.

```text
Run 29302364047: all functional and External Chat tests PASS; workflow parity FAIL
Commit 4e74df7e4e7de6a33e3f7224f92aa5b09ae121f8: canonical/iOS workflow parity synchronized
```

## Provider-owned usage lifecycle integration

```text
23cc19ac6ae2b99d9126bf928bdc3c1e3567e089  internal provider usage persistence
4f6abaeda313afb0c8598b9eb750a86f47ce9e30  combined gateway lifecycle hook
16d8b68af1bd73b28c66d2bfd947012c42ee2c46  lifecycle tests
8c04360a0cc3c294250ecc06575c73b2b9ea1821  deterministic replay repair
1592c9219d16e9896fec6848470b4ed3f4646e8e  repair receipt
```

Behavior:

```text
provider result used == true -> persist one session-bound provider usage event
provider disabled, blocked, failed, or fallback -> persist no provider usage event
identical replay -> idempotent
conflicting measurement identity -> fail closed
usage event authority -> false
local usage persistence custody -> false
repository mutation -> false
```

## System-boundary declaration workstream

This subordinate workstream preserves the active provider-usage goal while installing the runtime side of the governed system-boundary contract.

Installed files:

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
SYSTEM_BOUNDARY_MIRROR_HANDOFF.md
receipts/system-boundary-adapter-implementation-2026-07-14.json
receipts/system-boundary-lifecycle-binding-2026-07-14.json
adapter.capabilities.json
```

Source and destination chain:

```text
StegVerse-Labs/admissibility-wiki doctrine and schema
-> StegVerse-org/LLM-adapter runtime inventory and declaration generation
-> explicit governed session/response lifecycle binding
-> system_boundary_declaration_ref persistence in the bound payload
-> StegVerse-org/StegVerse-SDK validation
-> governed session manifest field: system_boundary_declaration
-> receipt reference field: system_boundary_declaration_ref
-> bounded Site status display after verification
```

Required invariants:

```text
model persistence: invocation
model mutable_by_inference: false
model_has_execution_authority: false
trajectory dependence requires explicit feedback paths
reconstructability requires evidence references
consciousness_claim: not_evaluated
personhood_claim: not_evaluated
welfare_claim: not_evaluated
binding authorizing: false
binding custody_transferred: false
binding admissibility_determined: false
production_binding_enabled: false
```

The opt-in payload binder and lifecycle binder add canonical SHA-256 references and refuse reserved-field overwrite, partial prior binding, digest drift, identifier mismatch, session/transition/run mismatch, authority escalation, custody escalation, admissibility escalation, and consciousness/personhood/welfare claim escalation. Identical complete binding replay is idempotent. Material lifecycle evidence changes rotate declaration identity. Receipt-chain-only changes rotate the receipt while preserving declaration identity.

Local verification is now included in both canonical and iOS-safe workflows:

```text
pytest tests/test_system_boundary.py
pytest tests/test_system_boundary_binding.py
pytest tests/test_system_boundary_receipt.py
pytest tests/test_system_boundary_lifecycle.py
```

Current system-boundary state:

```text
runtime declaration builder: INSTALLED
runtime surface inventory: INSTALLED
feedback-path recorder: INSTALLED
claim and authority guards: INSTALLED
optional governed response/session binding: INSTALLED
explicit lifecycle binding: INSTALLED
system_boundary_declaration_ref persistence: INSTALLED IN BOUND PAYLOAD
replay and conflict handling: INSTALLED
deterministic declaration and receipt identity: INSTALLED
canonical and iOS workflow integration: INSTALLED
current-main workflow evidence containing lifecycle files: NOT OBSERVED
production gateway activation of binding: DISABLED PENDING SEPARATE AUTHORIZATION
SDK receipt round-trip evidence: PENDING
Site bounded display: PENDING
```

## Current evidence state

```text
Usage-session implementation: INSTALLED
Usage-session focused checks: OBSERVED PASS
External Review tests: OBSERVED PASS
External publication and mutation tests: OBSERVED PASS
Workflow parity repair: INSTALLED
Provider-owned usage persistence: INSTALLED
Provider lifecycle hook: INSTALLED
Provider lifecycle tests: INSTALLED
Provider replay repair: INSTALLED
System-boundary runtime declaration: INSTALLED
System-boundary payload binding: INSTALLED OPT-IN
System-boundary lifecycle binding: INSTALLED EXPLICIT
System-boundary receipt replay: INSTALLED
System-boundary canonical workflow test step: INSTALLED
Successor green current-main validation: NOT OBSERVED
Same-origin deployment: NOT OBSERVED
Live provider-owned event submission in deployed service: NOT OBSERVED
Master-Records usage custody: NOT OBSERVED
SDK system-boundary round trip: NOT OBSERVED
```

## Ownership and continuation assignment

```text
Completed session work: provider usage lifecycle integration, deterministic replay repair, system-boundary generation, receipt support, opt-in payload binding, explicit session lifecycle binding, replay/conflict tests, and canonical/iOS workflow integration
Latest system-boundary commits: 29b562b, fec355f, f3b73c8, 9d15f54, 63cf2a9, 840eb01
Active task owner: successor repository continuation / orchestrator assignment
Pending observation: canonical validate run containing 9d15f54a2027242e50a82c5fec1f1b2bbbc36cd6 or later
Permitted continuation scope: bounded repository-local observation and repair preserving every validation surface and all authority, custody, mutation, deployment, and consciousness-claim boundaries
```

All remaining work is reconstructable from this handoff, the subordinate system-boundary handoff, repository history, workflow runs, receipts, and notifications.

## Next task

```text
1. Observe successor validation containing 9d15f54a2027242e50a82c5fec1f1b2bbbc36cd6 or later.
2. Repair only the first repository-local failing step, if any.
3. Preserve all existing validation surfaces and canonical/iOS workflow parity.
4. Keep automatic production gateway system-boundary binding disabled until separately authorized.
5. Review the current StegVerse-SDK handoff before downstream mutation.
6. Preserve system_boundary_declaration_ref through an SDK receipt round trip and verify the declaration/receipt hashes.
7. Add Master-Records usage-custody submission after local provider-usage persistence, without treating local storage as custody.
8. Keep production mutation disabled until separately authorized.
9. Establish the authorized same-origin Site retrieval path before enabling live transport.
10. Preserve deployed retrieval, declaration, SDK, and custody receipts before activation claims.
```

## Downstream destinations

```text
StegVerse-org/StegVerse-SDK
StegVerse-Labs/Site
GCAT-BCAT-Engine/Publisher
StegVerse-Labs/admissibility-wiki
StegVerse-Labs/stegguardian-wiki
master-records/orchestration
```

## Release posture

No deployment, automatic production system-boundary binding, live transport activation, Master-Records custody claim, release, tag, production mutation, publication authority, consciousness classification, personhood classification, or welfare classification is granted by this handoff.

## Archive readiness

This handoff preserves the session decisions, discovered blockers, completed work, remaining work, active ownership, pending validation requirements, and permitted continuation scope. No future continuation requires access to the conversation that created these commits.
