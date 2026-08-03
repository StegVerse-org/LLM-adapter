# StegVerse Security Baseline Requirements

## Governing rule

Applicable United States federal security requirements are the minimum acceptable baseline. StegVerse must implement equal or stronger controls and must not claim certification, authorization, validation, or agency approval without directly inspectable evidence.

## Canonical machine contract

`data/security/exceed-federal-baseline.json`

Validator:

`scripts/check_exceed_federal_security_baseline.py`

Hosted validation:

`.github/workflows/exceed-federal-security-baseline.yml`

## Required control posture

The active runtime must fail closed when applicability or evidence is unknown. Each production surface must eventually carry an evidence-backed mapping for identity and access, cryptography and key management, zero-trust boundaries, software supply chain, audit and continuity, and runtime execution governance.

StegVerse-specific exceedance includes authority separation from model output, identity-bound transition and receipt chains, deterministic replay, reconstruction, custody evidence, commit-time admissibility, health-bound node discovery, consumer pull verification, and explicit separation of local persistence from custody.

## Claim boundary

This contract grants no deployment, provider, custody, publication, release, transaction, or execution authority. It does not assert FedRAMP authorization, FIPS validation, NIST certification, federal compliance, agency approval, or production security.

## Active claim

```text
task: LLMA-SECURITY-EXCEED-FEDERAL-BASELINE-2026-08-02
branch: security/exceed-federal-baseline
role: CLAIMED_FOR_INTEGRATION
claim creation: 2026-08-02T19:35:00-05:00
release condition: merge to main with required checks passing, or supersession by a stronger canonical security handoff
collision boundary: do not weaken or replace existing provider, custody, admissibility, receipt, publication, or deployment controls
```

## Next executable action

Validate and merge this baseline contract. Then add evidence-backed per-surface mappings without asserting certification and without activating provider, custody, publication, or deployment authority.
