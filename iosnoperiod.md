# iosnoperiod

This repository may mirror leading-period workflow paths under `iosnoperiod/` for iOS-safe review and restoration.

The canonical workflow path remains authoritative.

## Current mirrored workflows

```text
Canonical: .github/workflows/validate.yml
Mirror: iosnoperiod/github/workflows/validate.yml
```

## Validate purpose

The validate workflow runs:

```bash
python scripts/verify_goal4.py
```

This keeps validation consolidated in one general workflow and preserves the max-two-workflows standard.
