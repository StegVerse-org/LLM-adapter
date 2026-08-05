# StegDeploy Publication Mirror Handoff

## Canonical source of truth

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

Live Git history, workflow jobs and logs, retained artifacts, and the committed v2 receipt supersede earlier snapshots.

## Released task

```text
task_id: LLMA-PUBLICATION-ACTIVATION-013
claim_state: COMPLETE
claimant: none
canonical_issue: StegVerse-org/LLM-adapter#18
scheduler_owner: StegVerse-Labs/StegVerse-Healer
```

## Current successful publication

```text
image: ghcr.io/stegverse-org/llm-adapter:main
source commit: 77fe06c5002fa14193a7972b2c653013a5bdb671
evidence-retention commit: f81ff1bd9c2b57c06d33b6f82c7241525c63a97d
publication run: 30967405336
publication job: 92184247965
digest: sha256:a5049d8d1a02f32475e4c9034eb6d9e626a1203507ae53da651237e39a04a961
receipt schema: stegdeploy.image-publication.v2
receipt state: PUBLISHED
receipt blockers: []
receipt sha256: 80b0bc5063531a74194adedfcbf48677ca832ae29156b46ece14f188e58c7432
consumer pull verified: true
readiness state: READY
publication artifact: 8915264878
publication artifact digest: sha256:1adae9a0ea4b7cf9d712acdf1335d5a404f3c7647bac3ace2c9737e7c9389099
build-record artifact: 8915265368
build-record digest: sha256:e329302f0b29cf98dde775aede639c057740bb1b5cc5f2598d9a525fcb4f2958
```

Every publication stage passed: registry login, build and push, attestation, fresh consumer pull, receipt construction, readiness projection, repository retention, artifact upload, and final enforcement.

Historical successful runs `30964767464` and `30965343262` remain inspectable but are superseded by the committed receipt above.

## Stable publication trigger

PR #116 owns the bounded trigger correction. After merge, push publication is restricted to runtime-affecting files:

```text
Dockerfile
pyproject.toml
llm_adapter/**
scripts/container-entrypoint.sh
compose.stegdeploy.yaml
.github/workflows/stegdeploy-image.yml
```

Documentation, receipts, status projections, and validation-only scripts do not rebuild or supersede the runtime image. Explicit `workflow_dispatch` remains available, and all recurring scheduling remains owned by StegVerse-Healer.

## Healer observer

```text
repository: StegVerse-Labs/StegVerse-Healer
workflow: .github/workflows/stegdeploy-publication-relay.yml
state: BLOCKED
observed result: HTTP 403
release condition: HEALER_GH_TOKEN creates the bounded workflow-dispatch event without exposing the token
```

The relay blocker does not invalidate completed one-shot publication evidence.

## Remaining activation boundary

Publication is not provider execution, persistent deployment, custody, reconstruction, Site activation, downstream ingestion, release authority, or sovereign platform retirement. All such authority projections remain false.

Issue #18 owns consumption of the stable digest only after authorized provider execution, persistent endpoint, and authenticated Master Records custody boundaries clear.

## Next action

Merge PR #116 after all hosted gates pass, observe the one final publication caused by the workflow change, then bind the final claim-release records to that stable digest. Handoff-only finalization will no longer trigger another image build.
