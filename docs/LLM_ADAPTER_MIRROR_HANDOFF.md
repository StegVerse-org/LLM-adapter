# LLM Adapter Mirror Handoff

## Source of truth

This is the canonical repository-wide continuation record for `StegVerse-org/LLM-adapter`.

Read it with:

```text
data/llm-adapter-orchestration-state.json
tasks/LLMA-PUBLICATION-ACTIVATION-013.json
tasks/LLMA-SEQUENCE-0001-RELEASE-015.json
docs/STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md
receipts/stegdeploy-image-publication.json
status/stegdeploy-image-publication-readiness.json
reports/ecosystem-chat-live-activation-monitor.json
StegVerse-org/LLM-adapter#18
StegVerse-org/LLM-adapter#72
```

Live Git history, workflow jobs and logs, retained artifacts, committed receipts, and current issues supersede earlier snapshots.

## Mandatory session entry

1. Read this handoff and `data/llm-adapter-orchestration-state.json`.
2. Continue an existing owner before creating another issue, branch, gateway, runtime, workflow, or adapter.
3. Preserve one owner per workload and release completed or superseded claims.
4. Treat CI proof as CI proof, not persistent deployment.
5. Preserve provider output != authority, local persistence != custody, reconstruction != execution authority, and publication != live activation.
6. Update task state, handoff, issue evidence, and machine-observable release conditions before ending an execution lane.

## Primary goal and canonical owner

```text
goal_id: ECOSYSTEM-CHAT-LIVE-ACTIVATION
goal: Complete one governed Ecosystem Chat vertical slice through an authorized persistent runtime.
originating_session_goal: Complete active tasks, activate finished tasks, and durably transfer every remaining requirement.
canonical_owner: StegVerse-org/LLM-adapter#18
repository: StegVerse-org/LLM-adapter
state: BLOCKED_WITH_MACHINE_OWNED_CONTINUATION
manual_user_action_required: false
```

Required vertical slice:

```text
canonical request
-> scoped execution grant
-> receipt-gated provider execution
-> provider usage persistence
-> transition and provider-usage custody
-> reconstruction PASS
-> immutable zero-blocker VERIFIED activation receipt
-> Site activation
-> verified downstream ingestion
```

## Current activation posture

```text
provider-neutral runtime: IMPLEMENTED_AND_VALIDATED
latest canonical image publication: COMPLETE
fresh package consumer pull: VERIFIED
publication readiness: READY
HIL automated full-cycle proof: COMPLETE_EPHEMERAL_CI
provider-owned usage validation: COMPLETE
Service Gateway ephemeral activation proof: REPAIR_IMPLEMENTED_PENDING_HOSTED_REVALIDATION
authorized real-provider execution: NOT_OBSERVED
persistent public runtime: NOT_VERIFIED
Master Records custody: NOT_VERIFIED
reconstruction: NOT_VERIFIED
zero-blocker VERIFIED activation: NOT_OBSERVED
Site activation: NOT_OBSERVED
downstream verified ingestion: NOT_OBSERVED
```

Latest canonical image:

```text
image: ghcr.io/stegverse-org/llm-adapter:main
digest: sha256:980d76c7a1bc43cb7d828ebc9153db8dec8295d92c10bd56e56c9ce0d4ef2a92
publication run: 30965343262
publication job: 92177973489
publication receipt: 745ae55bde7de8f883497f29485922ba73938995e298c977ffe9270e6e8abc65
publication artifact: 8914506620
build record: 8914506923
consumer pull verified: true
readiness: READY
superseded historical publication run: 30964767464
```

## Current work sequence and claim

```text
current sequence: 0002
state: RUNNING
heartbeat model: transition-driven and health-relative
time role: watchdog only
active task: LLMA-SEQUENCE-0001-RELEASE-015
owner: branch/fix/service-gateway-proof-and-release-sequence
role: CLAIMED_FOR_VALIDATION
claim created: 2026-08-04T20:18:00-05:00
release condition: merge after hosted validation; retain the main Service Gateway PASS or exact BLOCKED artifact; finalize task, handoff, and issues #18/#72.
```

The active task repairs four proven consistency defects without changing authority:

1. `HIL-RECEIVER-RECEIPT-v2` hashes the receiver signature and excludes only `receipt_sha256`; the stale test excluded both fields.
2. The always-run workflow summary did not create `activation-evidence/result` after an early failure.
3. The workflow expected stale TVC blob `7c8d3965eafd6048ea38e525647b898500c30531` instead of repository-retained blob `e376f2c276bda75ff497709637aac693853bf9cc` at TVC commit `b1a817e629aff483ab80679297013b33e692b567`.
4. Task and handoff records retained historical publication run `30964767464` after later successful run `30965343262` became authoritative.

The pinned public-safe TVC evaluator mirror, no-value decision boundary, provider separation, custody separation, and ephemeral-CI boundary remain unchanged.

## Completed and released tasks

### Latest image publication

```text
task: LLMA-0001-IMAGE-PUBLICATION / LLMA-PUBLICATION-ACTIVATION-013
state: COMPLETE
run: 30965343262
job: 92177973489
digest: sha256:980d76c7a1bc43cb7d828ebc9153db8dec8295d92c10bd56e56c9ce0d4ef2a92
receipt: 745ae55bde7de8f883497f29485922ba73938995e298c977ffe9270e6e8abc65
consumer pull: VERIFIED
readiness: READY
```

### HIL full cycle

```text
task_id: LLMA-0001-HIL-CYCLE
state: COMPLETE
owner: merged PR #56
superseded owner: closed PR #44
merge: e320c33189c1b6cf9d51a666a4505592b6fb981b
workflow run: 30966031698
job: 92180065119
result: PASS
receipt sha256: f4d0a8b90b05017b5abf77f3c96c3b8ad3efb99eb57d9c68b90a611b928888da
artifact: 8914746865
artifact digest: sha256:e9fe894eb2331c9d3792545cbb68d2f0d9762b2b05327732ec4482adf20d1350
boundary: ephemeral GitHub-hosted full-cycle proof; persistent deployment false
```

### Provider-owned usage validation

```text
task_id: LLMA-0001-GOAL8
state: COMPLETE
owner: main/provider-usage-event
workflow run: 30966031661
Python matrix: 3.9, 3.11, 3.12
canonical fixture: PASS
adversarial validation: PASS
main integration: e320c33189c1b6cf9d51a666a4505592b6fb981b
authority effect: false
```

Companion merged-main evidence:

```text
Architecture Guard: 30966031667 — PASS
Full repository validation: 30966031655 — PASS
LLMA-SESSION-PROVIDER-LAYER-2026-08-02: MERGED_AND_RELEASED at 1505aac0073bc6466769ca84c6ae28d887abdefd
```

No completed or superseded task may remain represented as active.

## Queued exclusive provider task

```text
task_id: LLMA-0002-LIVE-PROVIDER
owner: StegVerse-org/LLM-adapter#18
execution_class: EXCLUSIVE
state: BLOCKED
blocked_until: end of sequence 0002, no tasks running, and all authority-bound blockers cleared
```

Machine-observable blockers:

```text
authorized provider configuration and scoped execution grant
persistent endpoint
authenticated Master Records custody configuration
```

Completed dependencies:

```text
published package: READY
latest image digest: sha256:980d76c7a1bc43cb7d828ebc9153db8dec8295d92c10bd56e56c9ce0d4ef2a92
latest publication run: 30965343262
HIL full-cycle run: 30966031698
provider usage validation run: 30966031661
```

The basic HIL intake proof uses TV/TVC no-value authorization and does not require provider or Master Records secrets. The full real-provider vertical slice still requires its own provider execution grant, persistent runtime, and authenticated custody configuration.

## Canonical owners and convergence

```text
live-provider execution and final activation: StegVerse-org/LLM-adapter#18
Service Gateway proof and intake contract: StegVerse-org/LLM-adapter#72
Service Gateway secret governance and execution-grant authority: StegVerse-Labs/TVC#6
persistent custody and reconstruction: master-records/orchestration issue #2
Site activation after VERIFIED receipt: StegVerse-Labs/Site#24
Publisher propagation: GCAT-BCAT-Engine/Publisher current handoff
sovereign platform migration: StegVerse-002/micro-node-runtime#16
certificate control: StegVerse-002/StegGuardian#4
publication recurrence: StegVerse-Labs/StegVerse-Healer
```

MERGED INTO: `StegVerse-org/LLM-adapter#18`, `StegVerse-org/LLM-adapter#72`, and `StegVerse-Labs/TVC#6` for all work beyond this bounded sequence-release task.

## Managed observers

Publication scheduling remains Healer-only:

```text
owner: StegVerse-Labs/StegVerse-Healer
workflow: .github/workflows/stegdeploy-publication-relay.yml
state: BLOCKED
observed result: HTTP 403
release condition: HEALER_GH_TOKEN creates the bounded dispatch without exposing the token
```

Live activation monitoring remains repository-owned and fail-closed:

```text
workflow: .github/workflows/ecosystem-chat-live-activation-monitor.yml
state: PENDING
release condition: retain a zero-blocker VERIFIED observation after authorized persistent execution, custody, and reconstruction
```

## Validation commands

```text
python scripts/check_llm_adapter_orchestration_state.py
python scripts/check_session_provider_layer_consolidation.py
python scripts/check_session_provider_layer_archive_disposition.py
python scripts/check_stegdeploy_image_publication_readiness.py
python scripts/verify_provider_usage_event.py
python -m unittest tests.test_provider_usage_event
pytest tests/test_service_gateway.py -v
```

Hosted workflow jobs, logs, and artifacts are authoritative over file presence.

## Exact next executable actions

1. Re-run every PR-head gate for `fix/service-gateway-proof-and-release-sequence`.
2. Merge only when architecture, provider-event, security, consolidation, full validation, and Service Gateway proof pass.
3. Inspect the main Service Gateway activation job, receipt, idempotence test, summary, and artifact.
4. Record the exact result in `tasks/LLMA-SEQUENCE-0001-RELEASE-015.json`, this handoff, and issues #18/#72.
5. Release the sequence 0002 claim and mark the repository sequence idle.
6. Leave full provider activation blocked and owned by issue #18 until its declared authority boundaries clear.

There are no unspecified external tasks.

## Authority invariants

```text
provider_output_is_authority == false
configured_secret_is_authority == false
TVC_decision_contains_secret_value == false
CI_success_is_persistent_deployment == false
local_persistence_is_custody == false
image_publication_is_live_activation == false
reconstruction_is_execution_authority == false
all_repository_authority_flags == false
```

## Session consolidation and archive conditions

This session's unique requirements are installed in the task, registry, validator, handoffs, issue #18, issue #72, and TVC issue #6. The session is not archive-ready while `LLMA-SEQUENCE-0001-RELEASE-015` remains claimed or the corrected Service Gateway proof lacks a retained main-branch result.

## Completion measures

For the current bounded goal:

```text
task completion: 4/6 = 67%
developed files: 8/8 = 100%
validation: 4/6 = 67%
integration: 3/5 = 60%
goal activation: 67%
session consolidation: 7/8 = 88%
```

For the full Ecosystem Chat goal:

```text
image publication: COMPLETE
HIL ephemeral cycle: COMPLETE
provider usage validation: COMPLETE
Service Gateway ephemeral proof: PENDING_HOSTED_REVALIDATION
real provider execution: INCOMPLETE
persistent runtime: INCOMPLETE
custody and reconstruction: INCOMPLETE
VERIFIED activation, Site, and downstream propagation: INCOMPLETE
```
