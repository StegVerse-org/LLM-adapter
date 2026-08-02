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
One-shot trigger commit: d4ab0cd9c034638463a03b171ae1864e0ce2e0f3
Recurring observer commit: af01d1e79a2e9b635ba9e8071bae08e3530818e2
Trigger owner: .github/workflows/stegdeploy-image.yml
Trigger role: MACHINE_OWNED publication evidence generation and retry
Trigger cadence: hourly at minute 17, plus owned-path push and workflow_dispatch
Concurrency group: stegdeploy-image-publication
Execution ceiling: 45 minutes
Trigger release condition: repository retains a v2 PUBLISHED or BLOCKED receipt, pull log, and refreshed readiness projection from the same run
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

The workflow contains the v2 contract, exact stage outcomes, fresh pull verification, durable evidence retention, scheduled retry, bounded concurrency, and fail-closed enforcement. The readiness validator is merged into Goal 4 validation.

## Canonical Publication Trigger

The original handoff-path push did not produce a retained v2 evidence set or a visible commit status. The canonical workflow therefore now owns recurring execution rather than relying on a one-shot push event.

The recurring observer changes no runtime behavior and grants no provider, deployment, custody, release, or Site-activation authority. It repeatedly executes only the existing image publication and verification contract.

Expected machine-owned sequence:

```text
owned-path push, hourly schedule, or explicit workflow dispatch
→ run StegDeploy image workflow
→ attempt registry login, image build/publish, attestation, and fresh pull
→ write v2 PUBLISHED or BLOCKED receipt
→ refresh readiness projection
→ retain receipt, pull log, and readiness status together
→ upload all three artifacts
→ enforce publication result fail-closed
→ retry hourly while evidence remains BLOCKED or stale
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

1. The hourly workflow retries the complete v2 publication evidence cycle.
2. Retain the resulting v2 `PUBLISHED` or exact `BLOCKED` receipt, pull log, and readiness status automatically.
3. If `BLOCKED`, issue `StegVerse-org/LLM-adapter#18` owns repair of only the first retained stage blocker.
4. If `PUBLISHED`, allow the merged Healer relay to dispatch the bounded publication event.
5. Verify core-node intake retains matching receipt-hash and image-digest compatibility evidence.
6. Persistent hosting and real-provider/custody configuration remain separate authority-gated boundaries.

## Session consolidation

The publication-evidence task is now durably machine-owned and recurring. The current session retains a distinct observation and first-blocker-reconciliation role until a v2 receipt is inspected. Ecosystem Chat remains incomplete until persistent provider/custody execution, immutable verification, Site activation, and required downstream evidence exist or are actually transferred to verified active executors.
