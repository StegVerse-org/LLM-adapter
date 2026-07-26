# LLM Adapter Mirror Handoff

## Current source of truth

This file is the authoritative continuation record for `StegVerse-org/LLM-adapter`. It preserves Goal 8 while adding repository-wide workload ownership and live orchestration state for the HIL activation path.

## Mandatory session entry

Every arriving session must:

```text
1. Read docs/LLM_ADAPTER_MIRROR_HANDOFF.md.
2. Read data/llm-adapter-orchestration-state.json.
3. Treat the incoming request as a candidate workload, not automatic authority.
4. Continue an existing admitted workload before creating a new issue, branch, or pull request.
5. Preserve one active owner per workload.
6. Join the current sequence only when paths and dependencies are parallel-safe.
7. Queue exclusive work until the live state says: end of current work task sequence ####, no tasks running.
8. Update this handoff and the orchestration state before closure.
```

## Active goal 8

```text
Goal: provider-owned LLM usage events and bounded reasoning provenance
Goal number: 8
Schema: schemas/provider_usage_event.schema.json
Fixture: fixtures/provider_usage_event.json
Validator: scripts/verify_provider_usage_event.py
Tests: tests/test_provider_usage_event.py
Workflow: .github/workflows/validate-provider-usage-event.yml
Documentation: docs/PROVIDER_OWNED_USAGE_EVENTS.md
Manual user action required: false
State: IMPLEMENTED_PENDING_CANONICAL_VALIDATION
```

## HIL activation goal

```text
Complete the first seamless HIL vertical slice through the canonical governed gateway:
request
-> canonical event
-> provider use
-> usage persistence
-> transition custody
-> provider-usage custody
-> reconstruction PASS
-> immutable zero-blocker VERIFIED receipt
-> Site activation
-> verified downstream ingestion
```

Current result:

```text
ACTIVATION_PENDING_AUTHORIZED_REAL_PROVIDER_AND_PERSISTENT_ENDPOINT
```

## Current task sequence

```text
current work task sequence 0001
state: RUNNING
heartbeat model: transition-driven and health-relative
time role: watchdog only
```

Active parallel-safe workloads:

```text
LLMA-0001-HIL-CYCLE: PR #44 — automated persisted HIL cycle
LLMA-0001-HANDOFF: issue #54 — repository handoff and orchestration-state installation
LLMA-0001-GOAL8: existing provider-owned usage-event validation path
```

Queued or dependency-blocked workloads:

```text
LLMA-0002-LIVE-PROVIDER: issue #18 — EXCLUSIVE; authorized provider configuration and persistent endpoint required
LLMA-0002-AUTHORIZED-RUNTIME: PR #27 — retained implementation candidate for authorized provider runtime
LLMA-0002-PACKAGE-PUBLICATION: issue #18 next step — retain exact image publication and pull result
```

Existing branches to inspect before new work is admitted:

```text
PR #51 internal governed reference test suite
PR #36 StegWallet SIWE gateway
PR #35 portable-node restart proof
PR #28 current-main local node request slice
PR #25 earlier local node request slice
PR #23 non-canonical Render path; do not merge or apply
PR #13 earlier Render-independent runtime path
PR #10 probe only; do not merge
```

## Required invariants

```text
adapter_is_execution_authority == false
provider_response_is_admissibility == false
model_output_is_publication_authority == false
reasoning_provenance_is_full_chain_of_thought == false
usage_measurement_is_value_claim == false
provider_identity_is_actor_authority == false
return_receipt_required == true
hashes_are_independently_recomputed == true
```

## Goal 8 completion boundary

Goal 8 is complete only when the canonical fixture validates deterministically, request and response hashes are well formed, token totals reconcile, bounded reasoning provenance excludes full chain-of-thought, all authority dimensions remain false, return-to-origin receipt requirement remains true, adversarial tests pass on Python 3.9, 3.11, and 3.12, canonical CI succeeds, and the work is merged to `main`.

## Current HIL evidence posture

```text
Canonical provider-neutral StegDeploy runtime: implemented
Authoritative-source fallback build: verified
Gateway health in ephemeral execution: verified
Persistent public health endpoint: not verified
Published-package consumer access: blocked / not yet retained as canonical result
Authorized real provider use: not verified
Provider-usage persistence: not verified
Provider-usage custody: not verified
Provider-usage reconstruction: not verified
Immutable zero-blocker VERIFIED receipt: not observed
Site ACTIVATION_COMPLETE: not observed
Downstream verified ingestion: not observed
```

## System-health interpretation

```text
healthy idle: no admitted work expected
healthy blocked: dependency is explicit and orchestration remains observable
degraded: an active owner fails to produce an expected transition
partitioned: repository, package, host, provider, or custody endpoint is unreachable
critical: continuity or state integrity cannot be reconstructed
```

Heartbeat volume alone is not health. Meaning depends on expected activity, dependency state, validation state, reachability, ownership, recovery behavior, and transition-chain integrity.

## Next executable steps

```text
1. Complete issue #54 without touching PR #44 runtime paths.
2. Preserve PR #44 as owner of the automated persisted HIL cycle.
3. Complete Goal 8 canonical validation and merge when its explicit gates pass.
4. Run the repaired existing stegdeploy image workflow and retain exact PUBLISHED or BLOCKED evidence.
5. If PUBLISHED, rerun the existing core-node intake against the published image.
6. If BLOCKED, repair only the first retained publication or pull blocker.
7. Do not begin exclusive live-provider execution until the current parallel sequence closes.
8. Once authorized configuration exists, execute one real governed request through issue #18's canonical path.
9. Retain exact persistence, custody, reconstruction, receipt, Site activation, and downstream ingestion evidence.
```

## Successor integration

After Goal 8 is complete, connect provider-owned events to the StegVerse SDK session-usage aggregation path while preserving:

```text
sdk_validation_is_execution == false
aggregation_is_authority == false
session_receipt_is_custody == false
```

## Authority boundary

```text
handoff entry != execution authority
heartbeat != progress unless tied to an admitted transition
watchdog != progress
provider readiness != provider authorization
provider output != authority
local persistence != custody
submission != custody
reconstruction PASS != execution authority
CI success != persistent deployment
package publication != consumer access
persistent endpoint != provider credential authority
receipt import != Site activation authority
```

No provider credential, deployment, paid host, custody, release, publication, execution, transaction, or heartbeat authority is granted by this handoff.

## Archive readiness

This handoff, issue #18, issue #54, active pull requests, repository history, workflow artifacts, and orchestration state preserve continuation without requiring conversation context.
