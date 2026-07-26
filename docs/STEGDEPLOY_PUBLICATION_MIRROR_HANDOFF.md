# StegDeploy Publication Mirror Handoff

## Purpose

This is the authoritative continuation record for canonical StegDeploy image publication readiness owned by `StegVerse-org/LLM-adapter`.

## Current State

```text
Canonical workflow: .github/workflows/stegdeploy-image.yml
Retained receipt: receipts/stegdeploy-image-publication.json
Retained readiness projection: status/stegdeploy-image-publication-readiness.json
Observed receipt schema before next publication run: stegdeploy.image-publication.v1
Current readiness: BLOCKED
PR #38 merge: a21aa50526487fd16a46bd62488a7965d29aa3ed
PR #39 merge: 14724798fef253b4aca34c5da6ed34fe8ed6fcb8
Healer relay merge: 1b0d0660da8a0597137c6cb822a0ef751c2bf352
Core-node intake merge: f742105877541f67a85abd7fbe23154ce4addee7
Canonical evidence trigger requested: 2026-07-26
Manual user action required: false
Provider execution authority: false
Persistent deployment authority: false
Custody authority: false
Site activation authority: false
```

## Exact Blockers

```text
current retained receipt predates v2 publication contract
fresh consumer pull verification not retained
```

The workflow contains the v2 contract, exact stage outcomes, fresh pull verification, durable evidence retention, and fail-closed enforcement. The readiness validator is merged into Goal 4 validation.

## Canonical Publication Trigger

This handoff update is intentionally within the canonical workflow's `push.paths` boundary. Its merge to `main` requests the repository to run `.github/workflows/stegdeploy-image.yml` automatically and retain the resulting v2 evidence set.

The trigger changes no runtime code and grants no publication, deployment, provider, custody, release, or activation authority by itself. Its only purpose is to cause the already-governed publication workflow to produce fresh evidence.

Expected machine-owned sequence:

```text
merge this handoff update to main
→ run StegDeploy image workflow
→ attempt registry login, image build/publish, attestation, and fresh pull
→ write v2 PUBLISHED or BLOCKED receipt
→ refresh readiness projection
→ retain receipt, pull log, and readiness status together
→ allow Healer to relay only a verified PUBLISHED receipt
```

## Retention Repair

The canonical image workflow retains the readiness projection in the same run that writes the publication receipt. This prevents the receipt from advancing while repository-owned status remains stale because evidence commits use `[skip ci]`.

```text
write v2 PUBLISHED or BLOCKED receipt
→ run scripts/check_stegdeploy_image_publication_readiness.py
→ retain receipt, pull log, and readiness status together
→ upload all three artifacts
→ enforce publication result fail-closed
```

## Built Files

```text
scripts/check_stegdeploy_image_publication_readiness.py
status/stegdeploy-image-publication-readiness.json
scripts/verify_goal4_full.py
.github/workflows/stegdeploy-image.yml
docs/STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md
```

## Validation Boundary

The checker passes when the workflow contract is structurally valid, while truthfully recording `BLOCKED` until a retained v2 receipt proves:

```text
state = PUBLISHED
digest = sha256:...
consumer_pull_verified = true
```

A passing structural validator does not mean the image is published, publicly accessible, deployed, provider-authorized, custody-authorized, or Site-activated.

## Next Machine-Owned Actions

1. Observe the main-branch StegDeploy image workflow triggered by this handoff update.
2. Retain the resulting v2 `PUBLISHED` or exact `BLOCKED` receipt, pull log, and readiness status automatically.
3. If `BLOCKED`, repair only the first exact retained blocker.
4. If `PUBLISHED`, allow the merged Healer relay to dispatch the bounded publication event.
5. Verify core-node intake retains matching receipt-hash and image-digest compatibility evidence.
6. Persistent hosting and real-provider/custody configuration remain separate authority-gated boundaries.
