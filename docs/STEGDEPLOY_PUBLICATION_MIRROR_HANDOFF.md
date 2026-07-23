# StegDeploy Publication Mirror Handoff

## Purpose

This is the authoritative continuation record for canonical StegDeploy image publication readiness owned by `StegVerse-org/LLM-adapter`.

## Current State

```text
Canonical workflow: .github/workflows/stegdeploy-image.yml
Retained receipt: receipts/stegdeploy-image-publication.json
Observed receipt schema: stegdeploy.image-publication.v1
Current readiness: BLOCKED
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

The workflow already contains the v2 contract, exact stage outcomes, fresh pull verification, durable evidence retention, and fail-closed enforcement. The repository lacked a canonical readiness validator binding the retained receipt to that contract.

## Built Files

```text
scripts/check_stegdeploy_image_publication_readiness.py
status/stegdeploy-image-publication-readiness.json
scripts/verify_goal4_full.py
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

1. Merge only after repository validation succeeds.
2. Let the canonical main-branch image workflow execute from an applicable push or authorized workflow run.
3. Retain the resulting v2 `PUBLISHED` or `BLOCKED` receipt automatically.
4. If `BLOCKED`, repair only the first exact retained blocker.
5. If `PUBLISHED`, re-run canonical core-node image intake and retain consumer compatibility evidence.
6. Persistent hosting and real-provider/custody configuration remain separate authority-gated boundaries.
