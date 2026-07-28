# StegDeploy Publication Mirror Handoff

## Purpose

This is the authoritative continuation record for canonical StegDeploy image publication readiness owned by `StegVerse-org/LLM-adapter`.

## Current State

```text
Canonical workflow: .github/workflows/stegdeploy-image.yml
Retained receipt: receipts/stegdeploy-image-publication.json
Retained readiness projection: status/stegdeploy-image-publication-readiness.json
Observed retained receipt schema: stegdeploy.image-publication.v1
Current readiness: BLOCKED
Current exact blockers:
- current retained receipt predates v2 publication contract
- fresh consumer pull verification not retained
Fresh canonical evidence trigger requested: 2026-07-28
Manual user action required: false
Provider execution authority: false
Persistent deployment authority: false
Custody authority: false
Site activation authority: false
```

## Why This Refresh Is Required

The repository now contains the repaired v2 publication workflow, but the retained canonical receipt still comes from run `29866501493` and uses `stegdeploy.image-publication.v1`. That receipt does not contain the v2 state, stage outcomes, exact blockers, fresh consumer pull result, or current source commit required by the activation chain.

This handoff update is intentionally within the canonical workflow's `push.paths` boundary. Its merge to `main` requests the repository to execute `.github/workflows/stegdeploy-image.yml` and retain a fresh v2 evidence set.

The trigger changes no runtime code and grants no deployment, provider, custody, release, publication-policy, or Site activation authority. The workflow's authority effect remains limited to canonical image publication evidence.

## Required Machine-Owned Sequence

```text
merge this handoff update to main
→ run StegDeploy image workflow
→ attempt registry login
→ build and publish immutable image
→ attest the image
→ remove any local main image and perform a fresh registry pull
→ write a v2 PUBLISHED or exact BLOCKED receipt
→ refresh readiness projection
→ retain receipt, pull log, and readiness status together
→ enforce the result fail-closed
```

## Required v2 Evidence

A `PUBLISHED` result must establish all of the following in the retained receipt:

```text
schema = stegdeploy.image-publication.v2
state = PUBLISHED
digest = sha256:...
stage_outcomes.registry_login = success
stage_outcomes.build_publish = success
stage_outcomes.attestation = success
stage_outcomes.verification_pull = success
consumer_pull_verified = true
repository_retained = true
```

A `BLOCKED` result must retain the exact first observable publication or pull blocker. It must not be treated as package publication, deployment readiness, provider execution, custody, or Site activation evidence.

## Retention Contract

The canonical image workflow retains these artifacts together:

```text
receipts/stegdeploy-image-publication.json
receipts/stegdeploy-image-verification-pull.log
status/stegdeploy-image-publication-readiness.json
```

The readiness checker may validate the workflow contract structurally while truthfully keeping readiness `BLOCKED` until a retained v2 receipt proves publication and fresh consumer pull success.

## Built Files

```text
scripts/check_stegdeploy_image_publication_readiness.py
status/stegdeploy-image-publication-readiness.json
scripts/verify_goal4_full.py
.github/workflows/stegdeploy-image.yml
docs/STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md
```

## Next Machine-Owned Actions

1. Merge this bounded trigger update.
2. Observe the resulting main-branch `StegDeploy image` workflow.
3. Retain the v2 `PUBLISHED` or exact `BLOCKED` evidence automatically.
4. If `BLOCKED`, repair only the first retained publication or pull blocker.
5. If `PUBLISHED`, rerun the existing core-node intake against the published image and verify matching digest and receipt-hash continuity.
6. Persistent hosting and real provider/Master-Records configuration remain separate authority-gated boundaries.
