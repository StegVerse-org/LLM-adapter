# LLM Adapter Mirror Handoff

## Source of truth

This file is the authoritative continuation record for `StegVerse-org/LLM-adapter`.

## Active goal state

```text
Goal: live governed Ecosystem Chat with provider response, telemetry, authenticated usage retrieval, custody, reconstruction, and automatic downstream propagation
Repository-local result: COMPLETE
Continuation mode: ACCELERATED_SCHEDULED_FAIL_CLOSED_EVIDENCE_MONITOR
Manual user tasks: NONE
Recursive repository-local goal expansion: DISABLED
```

## Installed governed path

```text
Site request
-> governed provider response
-> provider usage persistence
-> authenticated provider-usage custody
-> transition custody
-> reconstruction PASS for both chains
-> stable semantic pending status
-> immutable VERIFIED activation receipt after all gates pass
-> Site automatic import
-> Publisher and wiki projections
```

## Production topology

`render-production.yaml` declares the public gateway and private durable Master-Records custody service. The deployment platform generates custody credentials, binds private routing, retains both databases on persistent disks, and deploys only after checks pass. Browser credentials and repository-exposed custody secrets remain prohibited.

External model-provider credentials remain provider-issued configuration. Missing or invalid provider configuration is surfaced automatically as a semantic blocker and does not create a recurring user task.

## Autonomous workflows

```text
.github/workflows/validate.yml
.github/workflows/ecosystem-chat-live-activation.yml
iosnoperiod/github/workflows/validate.yml
```

Validation runs on repository events and schedule. Live activation verification now runs every 15 minutes and after successful validation.

## Durable pending and verified evidence

```text
reports/ecosystem-chat-live-activation-status.json
  stable, hash-bound semantic pending or verified state

receipts/ecosystem-chat-live-activation.latest.json
  volatile full observation retained as workflow evidence when produced

receipts/ecosystem-chat-live-activation.verified.json
  immutable first VERIFIED receipt, created only with blockers = []
```

The seeded pending status begins fail-closed with:

```text
blocker: live_activation_observation_not_yet_recorded
manual_user_action_required: false
all live gates: false
all authority flags: false
```

The status writer also converts missing, unreadable, malformed, invalid-state, or internally conflicting observations into durable non-fatal blockers. A verifier crash therefore cannot erase continuation state or create a manual artifact-inspection task.

## Accelerated bounded observation loop

The live verifier now applies bounded retries to gateway health, governed chat, and transition retrieval:

```text
attempts per request: 5
retry delay: 8 seconds
timeout per attempt: 35 seconds
retryable HTTP states: 408, 425, 429, 500, 502, 503, 504
workflow timeout: 12 minutes
schedule: every 15 minutes
```

This removes the previous single-attempt dependency on a warm Render instance. Each generated observation records its retry policy and per-endpoint attempt counts. The workflow validates the observation schema, canonical hash, authority boundaries, and VERIFIED-with-zero-blockers rule before writing semantic status or retaining the immutable receipt.

Transient failure remains fail-closed. Retry exhaustion becomes an exact machine-readable blocker and does not create a user task.

## Installed continuation guards

```text
scripts/verify_live_ecosystem_chat_activation.py
scripts/write_live_activation_status.py
tests/test_live_activation_automation_contract.py
```

The live verifier requires:

```text
gateway health OK
durable storage
governed provider enabled
real provider use
local usage persistence remains non-custodial
provider-usage custody RECORDED
provider-usage reconstructability PASS
transition custody RECORDED
transition reconstructability PASS
all authority flags false
```

The contract tests reject authority escalation, mutable receipt retention, invalid verified state, missing-observation fatal behavior, manual-task reintroduction, custody-secret exposure, loss of the 15-minute cadence, and removal of bounded retry validation.

## Current evidence posture

```text
repository-local implementation: COMPLETE
self-contained private custody topology: COMPLETE
scheduled validation: INSTALLED
15-minute live verification: INSTALLED
bounded cold-start and transient retry policy: INSTALLED
generated observation canonical validation: INSTALLED
seeded pending status: PRESENT
crash-resilient semantic blocker publication: INSTALLED
immutable verified receipt publication: INSTALLED AND GUARDED
Site pending-status import: INSTALLED
Site verified-receipt import: INSTALLED
Publisher projection: INSTALLED
admissibility-wiki projection: INSTALLED
StegGuardian projection: INSTALLED
runtime-derived live observation under accelerated loop: NOT YET OBSERVED
immutable VERIFIED receipt: NOT CONFIRMED
Site ACTIVATION_COMPLETE: NOT CONFIRMED
downstream verified public evidence: NOT CONFIRMED
release or tag authority: NOT GRANTED
```

Absent CI, deployment, provider, custody, reconstruction, or downstream evidence does not reopen design or repository implementation work. Missing evidence remains fail-closed and is never treated as success.

## Machine-owned continuation

```text
1. Scheduled validation evaluates current main.
2. The deployment platform synchronizes the declared topology.
3. Fifteen-minute verification probes provider, custody, identity, and reconstruction with bounded retries.
4. Each observation is hash-validated before semantic projection.
5. Semantic blocker state is committed only when it changes.
6. The first VERIFIED result is committed at the immutable receipt path.
7. Site imports pending or verified state automatically.
8. Publisher and both wiki consumers ingest the Site projection automatically.
9. Release readiness remains machine-gated until live and downstream evidence exists.
```

No workflow dispatch, artifact download, file movement, screenshot confirmation, receipt construction, blocker transcription, credential copying, or manual publication task is required.

## Canonical downstream destinations

```text
master-records/orchestration
StegVerse-org/StegVerse-SDK
StegVerse-Labs/Site
GCAT-BCAT-Engine/Publisher
StegVerse-Labs/admissibility-wiki
StegVerse-002/stegguardian-wiki
```

`StegVerse-Labs/Sit` and `StegVerse-Labs/stegguardian-wiki` do not exist and are not destinations.

## Authority boundary

```text
provider output != authority
usage measurement != admissibility
local persistence != custody
submission != custody
custody receipt != execution authority
reconstruction PASS != execution authority
workflow artifact != live evidence
pending status != activation
verified receipt != release authority
terminal monitor != CI success
retry success != admissibility
```

## Release posture

No release or tag is authorized until the existing machine gates receive visible validation, deployment, provider, custody, reconstruction, Site-completion, and downstream evidence. The decision is machine-gated and creates no manual review task.

## Archive determination

No repository-local module, contract, validator, handoff, consumer, or automation remains to install for this activation workstream. The accelerated observation loop is now durable. Remaining conditions are external evidence observations owned by scheduled workflows, the deployment platform, the model provider, and authority-bearing custody systems.

**ARCHIVE NOW.**
