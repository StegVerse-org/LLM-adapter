# LLM Adapter Mirror Handoff

## Source of truth

This file is the authoritative continuation record for `StegVerse-org/LLM-adapter`.

## Active goal state

```text
Goal: live governed Ecosystem Chat with provider response, telemetry, authenticated usage retrieval, custody, reconstruction, and automatic downstream propagation
Repository-local result: COMPLETE
Continuation mode: SELF_STARTING_ACCELERATED_FAIL_CLOSED_EVIDENCE_MONITOR
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
.github/workflows/ecosystem-chat-live-activation-monitor.yml
iosnoperiod/github/workflows/validate.yml
```

Validation runs on repository events and schedule. Live activation verification runs every 15 minutes, after successful validation, and whenever the activation workflow, verifier, status writers, contract test, or production blueprint changes. Status changes use `[skip ci]` and are excluded from runtime image publication path filters.

The monitor heartbeat is deliberately **artifact-only**. A fresh timestamp/run identity is generated and hash-validated on every monitor execution, but that volatile heartbeat is no longer committed to `main`. This prevents every 15-minute observation from becoming a deployment-platform source commit and consuming deployment/build capacity when runtime code and semantic activation state are unchanged.

Provider-configuration readiness is also a stable semantic projection. `receipts/ecosystem-chat-authorized-provider-activation.latest.json` contains configuration booleans, blocker identifiers, runtime-path semantics, and authority boundaries but no wall-clock field. Same-run time and attempt identity remain available in Actions run/artifact metadata. The repository receipt therefore changes only when readiness semantics change instead of creating a deployment-triggering commit every 15 minutes.

## Durable pending, monitor, and verified evidence

```text
reports/ecosystem-chat-live-activation-status.json
  stable, hash-bound semantic pending or verified state retained only when semantic state changes

reports/ecosystem-chat-live-activation-monitor.json
  volatile, hash-bound proof generated on every monitor execution and retained as a workflow artifact

receipts/ecosystem-chat-authorized-provider-activation.latest.json
  stable, hash-bound provider/custody configuration readiness projection retained when semantics change

receipts/ecosystem-chat-live-activation.latest.json
  volatile full observation retained as workflow evidence when produced

receipts/ecosystem-chat-live-activation.verified.json
  immutable first VERIFIED receipt, created only with blockers = []
```

The seeded pending semantic status begins fail-closed with `live_activation_observation_not_yet_recorded`. Monitor executions remain separately visible through GitHub Actions artifacts even when semantic state is unchanged.

The status writer converts missing, unreadable, malformed, invalid-state, or internally conflicting observations into durable non-fatal blockers. The monitor writer separately records whether the workflow itself executed, so unchanged semantic state can no longer hide a missing monitor run. The monitor artifact does not itself grant activation, deployment, custody, or release authority.

## Self-starting accelerated observation loop

The live verifier applies bounded retries to gateway health, governed chat, and transition retrieval:

```text
attempts per request: 5
retry delay: 8 seconds
timeout per attempt: 35 seconds
retryable HTTP states: 408, 425, 429, 500, 502, 503, 504
workflow timeout: 12 minutes
schedule: every 15 minutes
bootstrap: push changes to activation implementation paths
```

This removes both the previous single-attempt dependency on a warm deployment instance and the previous dependency on waiting for the first scheduled run after monitor installation. Each observation records retry policy and endpoint attempt counts. Each monitor artifact records workflow run ID, attempt, trigger, semantic-status hash, observation hash, exact blockers, and the next machine action.

Transient failure remains fail-closed. Retry exhaustion and monitor non-execution become distinct machine-readable blockers and never create a user task.

## Installed continuation guards

```text
scripts/verify_live_ecosystem_chat_activation.py
scripts/write_live_activation_status.py
scripts/write_live_activation_monitor_status.py
tests/test_live_activation_automation_contract.py
tests/test_live_activation_monitor_no_deploy_churn.py
tests/test_provider_readiness_stable_projection.py
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

The contract tests reject authority escalation, mutable verified-receipt retention, invalid verified state, missing-observation fatal behavior, manual-task reintroduction, custody-secret exposure, loss of the 15-minute cadence, removal of bounded retries, removal of monitor hashing, reintroduction of monitor repository writes, and time-driven provider-readiness repository churn.

## Current evidence posture

```text
repository-local implementation: COMPLETE
self-contained private custody topology: COMPLETE
scheduled validation: INSTALLED
15-minute live verification: INSTALLED
self-starting activation implementation trigger: INSTALLED
bounded cold-start and transient retry policy: INSTALLED
generated observation canonical validation: INSTALLED
monitor heartbeat generation and validation: INSTALLED
monitor heartbeat retention: ARTIFACT_ONLY_BY_DESIGN
provider readiness persistence: SEMANTIC_CHANGE_ONLY
semantic status persistence: STATE_CHANGE_ONLY
seeded semantic pending status: PRESENT
crash-resilient semantic blocker publication: INSTALLED
immutable verified receipt publication: INSTALLED AND GUARDED
Site pending-status import: INSTALLED
Site verified-receipt import: INSTALLED
Publisher projection: INSTALLED
admissibility-wiki projection: INSTALLED
StegGuardian projection: INSTALLED
canonical StegDeploy image publication: PUBLISHED
portable StegGate governed-package consumer: VERIFIED
live gateway health: OBSERVED
real provider execution: NOT CONFIRMED
provider-usage custody/reconstruction: NOT CONFIRMED
immutable VERIFIED receipt: NOT CONFIRMED
Site ACTIVATION_COMPLETE: NOT CONFIRMED
downstream verified public evidence: NOT CONFIRMED
release or tag authority: NOT GRANTED
```

Absent CI, deployment, provider, custody, reconstruction, or downstream evidence does not reopen completed design work. Missing evidence remains fail-closed and is never treated as success.

## Portable StegGate consumer integration — VERIFIED

This repository now consumes the canonical StegCore portable/ephemeral StegGate topology without duplicating decision authority.

Installed surfaces:

```text
llm_adapter/steggate_portable_consumer.py
tests/test_steggate_portable_consumer.py
.github/workflows/steggate-portable-consumer.yml
receipts/steggate-portable-consumer-integration.latest.json
```

Canonical StegCore dependency for the verified integration is pinned to commit:

```text
2f0076a25fdf7ee020dca85f3934c6bca385b310
```

The consumer maps explicit Ecosystem Chat/user-LLM governance facts into StegCore's canonical `AdmissibilityRequest`, creates a `stegcore.governed_transition_package`, and delegates the consequence boundary to `execute_governed_package`. It does **not** implement a second policy engine.

Provider callbacks are unreachable unless portable StegGate returns ALLOW and independent commit coherence returns ALLOW. Policy drift produces DENY and leaves the provider callback untouched. Package transport is JSON-serializable, carries no provider credential, and does not require a public StegGate ingress endpoint.

Hosted verification:

```text
workflow: StegGate Portable Consumer Integration
run: 31286444819
job: 93176065654
result: SUCCESS
artifact: 9029971776
artifact digest: sha256:c555e9035d480120d36184308d165e8e0987a0765c3020a60abf0c45f425c4f4
```

Durable receipt: `receipts/steggate-portable-consumer-integration.latest.json`.

This proves a real StegVerse consumer can carry/instantiate the portable governance boundary locally. It does **not** claim that external model-provider execution, provider-usage custody/reconstruction, immutable zero-blocker activation, or Site/downstream activation are complete.

## Machine-owned continuation

```text
1. Activation implementation changes start the monitor immediately.
2. Scheduled validation evaluates current main.
3. Fifteen-minute verification probes provider, custody, identity, and reconstruction with bounded retries.
4. Each observation and monitor heartbeat is hash-validated before retention.
5. Provider readiness and semantic blocker projections are committed only when their semantic content changes; monitor heartbeat is retained as a workflow artifact on every execution.
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
monitor artifact != activation
provider readiness != provider execution authority
pending status != activation
verified receipt != release authority
terminal monitor != CI success
retry success != admissibility
portable package transport != policy authority
portable micro-node identity != execution authority
portable consumer integration != real provider execution
```

## Release posture

No release or tag is authorized until the existing machine gates receive visible validation, deployment, provider, custody, reconstruction, Site-completion, and downstream evidence. The decision is machine-gated and creates no manual review task.

## Continuation posture

Repository implementation is complete. Portable StegGate consumer integration is verified and no longer depends on resident StegGate HTTP hosting. Runtime activation remains machine-owned by issue #18. Current blockers are real-provider execution authority/configuration, authenticated Master-Records runtime binding for the same execution, provider-usage custody/reconstruction, immutable zero-blocker activation evidence, Site/downstream activation, and sovereign migration. Volatile heartbeat commits and time-only provider-readiness commits are intentionally suppressed to preserve deployment capacity for meaningful state transitions.
