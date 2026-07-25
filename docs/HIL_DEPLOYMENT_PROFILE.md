# HIL Deployment Profile

Version: `HIL-DEPLOYMENT-PROFILE-v1`

## Purpose

This document defines the minimum deployable runtime contract for the `Humans as the Interoperability Layer` controlled cycle. It converts the merged HIL gateway implementation into an operator-verifiable deployment profile without granting activation, publication, or Master Record authority.

## Required application

Deploy the repository default branch at or after:

```text
b2e612dd74d311e0cbe66cd1c1d4758bff129fd4
```

The service entry point must expose `llm_adapter.combined_gateway:app` and the following endpoints:

```text
GET  /health
GET  /api/hil/readiness
POST /api/hil/submissions
GET  /api/hil/publication-readiness
```

Review and publication mutation endpoints remain authenticated and are not public operator shortcuts.

## Required runtime configuration

| Variable | Requirement | Secret |
|---|---|---|
| `STEGVERSE_HIL_INTAKE_ENABLED` | Must be `true` only for the controlled deployment | No |
| `STEGVERSE_HIL_DATA_DIR` | Absolute path on durable mounted storage | No |
| `STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS` | Must be `true` only after durable storage is actually attached | No |
| `STEGVERSE_HIL_REVIEW_TOKEN` | Strong credential dedicated to private review | Yes |
| `STEGVERSE_HIL_PUBLICATION_TOKEN` | Strong credential dedicated to publication | Yes |

The review and publication credentials must be distinct. Neither token may be committed, logged, returned by readiness endpoints, placed in workflow artifacts, or reused as a provider credential.

## Storage contract

`STEGVERSE_HIL_DATA_DIR` must refer to storage that survives:

1. process restart;
2. container replacement;
3. service redeploy;
4. host rescheduling within the selected platform's documented persistence boundary.

The directory contains response PDFs, normalized provenance manifests, SQLite state, receipts, and publication artifacts. Declaring durability without an attached persistent volume is a false readiness state.

## Fail-closed deployment sequence

```text
provision persistent volume
-> bind absolute HIL data path
-> configure separate review and publication credentials
-> deploy merged gateway
-> leave public acquisition closed
-> query readiness endpoints
-> record redacted configuration fingerprints
-> run one controlled submission
-> restart or redeploy service
-> prove exact-byte persistence
-> perform private review
-> perform append-only publication
-> export evidence to Site
```

## Readiness acceptance

The intake readiness response must identify:

```text
primary_sha256 = 52102cccb9ba9016c76434a64e22031b6a8c3edd3b8806e7b664e609216b2946
prompt_sha256  = 0ebe215318b4eeeb8ed6422e0954372c314fadc8fac9254e452bc7670a1b9922
state          = READY
private_review_configured = true
```

Publication readiness must independently report that publication configuration is present and append-only. A readiness response grants no publication authority.

## Credential fingerprint evidence

For evidence packets, compute a one-way SHA-256 fingerprint locally for each configured credential and preserve only:

```json
{
  "credential_role": "private_review",
  "fingerprint_sha256": "<64 lowercase hex characters>",
  "secret_disclosed": false
}
```

The intake, private-review, and publication roles must not share a fingerprint. The raw values must never enter the repository.

## Restart proof

A valid restart proof must bind:

- deployment identifier before restart;
- deployment identifier after restart;
- restart or redeploy timestamps;
- submission identifier;
- response SHA-256 before and after restart;
- provenance-manifest SHA-256 before and after restart;
- storage path class or mounted-volume reference;
- post-restart lookup result.

An in-process test client, application object recreation, or CI fixture does not satisfy this requirement.

## Non-authority boundaries

```text
deployment configured != public acquisition authorized
readiness READY != controlled cycle complete
credential present != mutation authorized for an actor
receiver receipt != private acceptance
private acceptance != publication
publication != Master Record custody
restart success != evidence packet approval
```

## Completion handoff

Runtime evidence must be transferred into the Site-owned governed records:

```text
StegVerse-Labs/Site/data/hil-activation-state.json
StegVerse-Labs/Site/data/hil-deployed-controlled-cycle-evidence.json
```

This repository owns gateway behavior and deployment conformance. The Site repository owns public activation state and the evidence chain leading to the first HIL Master Record release.
