# Repository Hygiene Adoption Mirror Handoff

Updated: 2026-09-21
Repository: `StegVerse-org/LLM-adapter`
Goal Task ID: `HYGIENE-CAUSAL-ROOTS-001`
COSV task.v1: `10100000100000`
Canonical ecosystem handoff: `StegVerse-Labs/.github/docs/REPOSITORY_HYGIENE_MIRROR_HANDOFF.md`
Wave: `1 — shared authority/runtime producer`
Wave-1 branch-count rank: `2`
Observed pre-adoption branch count: `268`

## Adoption

This repository consumes the centrally owned reusable branch-hygiene classifier through a thin caller:

```text
.github/workflows/repository-hygiene.yml
  -> StegVerse-Labs/.github/.github/workflows/repository-hygiene-reusable.yml
  -> scripts/repository_hygiene_inventory.py
```

Pinned shared revision:

```text
739a611afd70bbe5b8e598b03180e62624fb8459
```

## Safety boundary

The caller grants only `contents: read` and retains no credentials after checkout. It classifies branch ancestry, age metadata, exact default-branch source references, protected patterns, retirement candidates requiring owner clearance, and review-required refs.

It never:

- deletes a branch;
- closes a PR or issue;
- treats age or branch naming as deletion authority;
- grants runtime, provider, credential, custody, publication, release, or repository-administration authority.

Actual ref mutation remains outside this workflow under the canonical `HYGIENE-BRANCH-REF-RETIREMENT` authority path.

## Completion predicates

```text
CALLER_MERGED
FIRST_HOSTED_INVENTORY_SUCCESS
MACHINE_BRANCH_COUNT_RECONCILED
RETIREMENT_CANDIDATES_REVIEWED_FOR_OWNER_AND_EVIDENCE_CLEARANCE
NO_AGE_OR_NAME_BASED_REF_DELETION
```

Source installation alone does not satisfy the hosted inventory or ref-retirement predicates.
