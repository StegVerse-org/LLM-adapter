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

## Released publication task

```text
task_id: LLMA-PUBLICATION-ACTIVATION-013
claim_state: COMPLETE
claimant: none
released_at: 2026-08-04T21:01:00-05:00
canonical_issue: StegVerse-org/LLM-adapter#18
scheduler_owner: StegVerse-Labs/StegVerse-Healer
```

## Final stable canonical image

```text
image: ghcr.io/stegverse-org/llm-adapter:main
source commit: f7ca640d44a5e7703e9d3f599717375bfae2e183
evidence-retention commit: f1fd7b6f7293af270e158c6daf65a9b17765d4c1
publication run: 30967973138
publication job: 92185969448
digest: sha256:ae309681c4b1411c39860bcb349acc5cf727b70f8876a9e61fccfbb9e767a901
receipt schema: stegdeploy.image-publication.v2
receipt state: PUBLISHED
receipt blockers: []
receipt sha256: d70f19a0a3afd9a34f313b3e0a4959e3343b00194c86fd85e3cdec5b3c0a7d87
consumer pull verified: true
readiness state: READY
publication artifact: 8915473468
publication artifact digest: sha256:1f90b7ed6adfc1120d440fef24cf6f595a0cbec529fadb4c004498e63e4ae404
build-record artifact: 8915473881
build-record digest: sha256:9a8bf145b72f6ea8c8da80467085dcc4cf77b0d71c784ba1c2af8551b3f40524
```

Every publication stage passed: registry login, build and push, attestation, fresh consumer pull, receipt construction, readiness projection, repository retention, artifact upload, and final enforcement.

Historical successful runs `30964767464`, `30965343262`, and `30967405336` remain inspectable but are superseded by run `30967973138` and the committed receipt above.

## Stable runtime-only trigger

PR #116 merged at `f7ca640d44a5e7703e9d3f599717375bfae2e183` and restricts push publication to runtime-affecting surfaces:

```text
Dockerfile
pyproject.toml
llm_adapter/**
scripts/container-entrypoint.sh
compose.stegdeploy.yaml
.github/workflows/stegdeploy-image.yml
```

Documentation, receipts, status projections, and validation-only scripts do not rebuild or supersede the runtime image. Explicit `workflow_dispatch` remains available. Managed recurrence remains exclusively owned by StegVerse-Healer.

## Healer observer

```text
repository: StegVerse-Labs/StegVerse-Healer
workflow: .github/workflows/stegdeploy-publication-relay.yml
state: BLOCKED
observed result: HTTP 403
release condition: HEALER_GH_TOKEN creates the bounded workflow-dispatch event without exposing the token
effect on completed publication: none
```

## Remaining activation boundary

Publication is not provider execution, persistent deployment, custody, reconstruction, Site activation, downstream ingestion, release authority, or sovereign platform retirement. All corresponding authority projections remain false.

Issue `StegVerse-org/LLM-adapter#18` owns consumption of the stable digest only after these machine-observable boundaries clear:

```text
authorized provider configuration and scoped execution grant
persistent endpoint
authenticated Master Records custody configuration
```

## Consolidation state

The publication implementation, final digest, receipt, readiness, consumer pull, artifacts, trigger stabilization, scheduler delegation, remaining blockers, and canonical owner are durably preserved. No unique publication state remains only in chat.

MERGED INTO: `StegVerse-org/LLM-adapter#18` and `StegVerse-Labs/StegVerse-Healer/.github/workflows/stegdeploy-publication-relay.yml`.
