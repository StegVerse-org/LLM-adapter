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

The workflow contains the v2 contract, exact stage outcomes, fresh pull verification, durable evidence retention, and fail-closed enforcement. The readiness validator is now merged into Goal 4 validation.

## Retention Repair

The canonical image workflow must retain the readiness projection in the same run that writes the publication receipt. Otherwise the receipt may advance to v2 while the repository-owned status remains stale because the evidence commit intentionally uses `[skip ci]`.

The current repair adds:

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

1. Validate and merge the retention repair.
2. Observe the canonical main-branch image workflow.
3. Retain the resulting v2 `PUBLISHED` or `BLOCKED` receipt, pull log, and readiness status automatically.
4. If `BLOCKED`, repair only the first exact retained blocker.
5. If `PUBLISHED`, re-run canonical core-node image intake and retain consumer compatibility evidence.
6. Persistent hosting and real-provider/custody configuration remain separate authority-gated boundaries.
