# Live Activation Monitor Handoff

## Repository

`StegVerse-org/LLM-adapter`

## Installed result

```text
Result: DURABLE_ACTIVATION_MONITOR_HEARTBEAT_INSTALLED
Manual user action required: false
```

## Purpose

The stable semantic activation status changes only when gate or blocker meaning changes. That design previously made it impossible to distinguish an unchanged pending state from a workflow that had never executed.

The repository now publishes a separate volatile, hash-bound heartbeat on every activation-monitor run:

```text
reports/ecosystem-chat-live-activation-monitor.json
```

## Execution path

```text
15-minute workflow trigger or successful validation
-> bounded live activation verifier
-> canonical observation validation
-> stable semantic status writer
-> volatile monitor heartbeat writer
-> canonical monitor hash validation
-> commit semantic status and heartbeat
-> retain immutable VERIFIED receipt when eligible
```

## Monitor fields

The heartbeat records:

```text
generated_at
workflow_run_id
workflow_run_attempt
workflow_event
observation_present
observation_observed_at
observation_result_sha256
semantic_status_sha256
state
blockers
next_machine_action
monitor_sha256
```

## Initial exact blocker

Until the first scheduled heartbeat is committed:

```text
live_activation_monitor_run_not_yet_recorded
```

After execution, the heartbeat distinguishes:

```text
monitor ran and activation remains pending
monitor ran and exact live blockers were observed
monitor ran and VERIFIED evidence is eligible for immutable retention
```

## Authority boundary

```text
monitor heartbeat != activation authority
monitor heartbeat != deployment authority
monitor heartbeat != custody
monitor heartbeat != release authority
monitor heartbeat != execution authority
```

## Machine-owned continuation

1. The workflow runs every 15 minutes and after successful validation.
2. Every run rewrites and validates the heartbeat even when semantic blockers are unchanged.
3. Pending runs continue automatically with exact blockers.
4. The first blocker-free VERIFIED observation is retained immutably.
5. Site and all three downstream consumers continue automatically.

No workflow dispatch, artifact inspection, blocker transcription, receipt construction, or user confirmation is required.
