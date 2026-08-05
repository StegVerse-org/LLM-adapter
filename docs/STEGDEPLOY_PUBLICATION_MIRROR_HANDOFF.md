# StegDeploy Publication Mirror Handoff

## Source of truth

This is the authoritative scoped continuation record for canonical StegDeploy image publication in `StegVerse-org/LLM-adapter`.

```text
.github/workflows/stegdeploy-image.yml
receipts/stegdeploy-image-publication.json
receipts/stegdeploy-image-verification-pull.log
status/stegdeploy-image-publication-readiness.json
tasks/LLMA-PUBLICATION-ACTIVATION-013.json
data/llm-adapter-orchestration-state.json
StegVerse-org/LLM-adapter#18
StegVerse-Labs/StegVerse-Healer/docs/HEALER_MIRROR_HANDOFF.md
```

Live Git history, workflow jobs and logs, retained artifacts, committed receipts, and the latest successful publication run supersede earlier evidence snapshots.

## Goal and released claim

```text
task_id: LLMA-PUBLICATION-ACTIVATION-013
originating_goal: complete tasks while active and activate finished Ecosystem Chat tasks
canonical_issue: StegVerse-org/LLM-adapter#18
claim_state: COMPLETE
claimant: none
claimed_at: 2026-08-04T19:33:00-05:00
released_at: 2026-08-04T19:55:07-05:00
activation PR: #111
activation merge: 260e4b851a8b0e6ee72c361675670b2a4d92b515
repair PR: #112
repair merge: 4c6d8a47a4695adc793ad0ab4577c1e9aa0488dc
claim-release PR: #113
claim-release merge: 7f70c326db25e5a2cb6fce9a03858ec9de537ec4
```

The task remains complete because the latest canonical image was built, published, attested, freshly pulled as a consumer, recorded in a zero-blocker v2 receipt, projected READY, retained on `main`, and preserved in workflow artifacts.

## Latest published image evidence

```text
image: ghcr.io/stegverse-org/llm-adapter:main
digest: sha256:980d76c7a1bc43cb7d828ebc9153db8dec8295d92c10bd56e56c9ce0d4ef2a92
source commit: 7f70c326db25e5a2cb6fce9a03858ec9de537ec4
evidence-retention commit: 0afd1fab8e339b2b7f358eca05e2379ddcb9e8bd
publication run: 30965343262
publication job: 92177973489
receipt schema: stegdeploy.image-publication.v2
receipt state: PUBLISHED
receipt blockers: []
receipt sha256: 745ae55bde7de8f883497f29485922ba73938995e298c977ffe9270e6e8abc65
consumer pull verified: true
readiness state: READY
manual user action required: false
```

All stages passed:

```text
registry_login: success
build_publish: success
attestation: success
verification_pull: success
repository_retention: success
artifact_upload: success
final_enforcement: success
```

The retained pull evidence records the exact latest digest and a newly downloaded `ghcr.io/stegverse-org/llm-adapter:main` image.

## Artifacts and attestation

```text
publication artifact: 8914506620
publication artifact digest: sha256:0861bc65d64f8b6532ef7ec85a9396679ca6a8a5e63dbc32db1a2f05541461e3
build-record artifact: 8914506923
build-record digest: sha256:fad06982940329abae2eb569113a1603e641cc435eb2ef015a9a967e397e4340
attestation id: 38927431
Rekor log index: 2341858582
```

Historical run `30964767464` proved the repaired path and remains valid historical evidence. Run `30965343262` is the current authoritative publication observation because it is later, successful, repository-retained, freshly pull-verified, and bound to the latest committed receipt.

## Scheduler authority

Managed schedules remain prohibited outside StegVerse-Healer.

```text
repository: StegVerse-Labs/StegVerse-Healer
workflow: .github/workflows/stegdeploy-publication-relay.yml
schedule: cron "37 * * * *"
state: BLOCKED
observed result: HTTP 403
release condition: HEALER_GH_TOKEN creates the bounded LLM-adapter workflow-dispatch event without exposing the token
```

The relay blocker does not invalidate the completed one-shot publication or the latest retained evidence.

## Orchestration reconciliation

```text
closed PR #44: SUPERSEDED
merged PR #56 HIL full cycle: COMPLETE
provider-owned usage validation: COMPLETE
provider-layer consolidation PR #95: MERGED_AND_RELEASED
image publication task: COMPLETE
image recurrence: STEGVERSE_HEALER_OWNED
exclusive live-provider execution: BLOCKED_AND_QUEUED
```

Published-package consumer access is complete. Remaining live-provider blockers are:

```text
authorized provider configuration and scoped execution grant
persistent endpoint
authenticated Master Records custody configuration
current bounded task sequence completion
```

## Authority boundary

Publication does not grant or prove provider execution, persistent deployment, custody, reconstruction, Site activation, downstream ingestion, release authority, general publication authority, or sovereign platform retirement. All corresponding authority projections remain false.

## Next executable action

Issue #18 remains the canonical owner for consuming the latest immutable digest on an authorized persistent runtime, executing one receipt-gated real provider request, preserving usage and transition custody, reconstructing the transition, producing a zero-blocker VERIFIED activation receipt, activating Site, and propagating verified downstream evidence.

StegVerse-Healer remains the owner of recurring publication observation and its exact HTTP 403 token-scope release condition.

## Session consolidation

The latest publication, historical supersession, validation, evidence retention, scheduler delegation, remaining blocker set, and next executable path are durably preserved. No unique publication state remains only in chat.
