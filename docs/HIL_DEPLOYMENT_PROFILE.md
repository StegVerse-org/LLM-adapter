# HIL Compatibility Runtime Profile

Version: `HIL-RUNTIME-COMPATIBILITY-PROFILE-v3`

## Purpose

This document defines the non-authorizing LLM-adapter compatibility contract for the `Humans as the Interoperability Layer` v1.1 controlled-cycle interface.

Production HIL runtime construction, protected configuration delivery, lifecycle transitions, restart, persistence, private review, and evidence authority belong to TV/TVC. The canonical production handoff is:

```text
StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
backend: tvc.experiment.controlled-cycle.v1
private_review_owner: StegVerse-Labs/TVC#8
credential_authority: TV/TVC
github_token_runtime_authority: NONE
third_party_runtime_dependency: NONE_ALLOWED
```

LLM-adapter does not require or select a vendor host, hosted compute provider, external secret store, or third-party runtime for HIL production continuity.

## Required compatibility boundary

The compatibility application surface is `llm_adapter.combined_gateway:app` and exposes protocol-compatible endpoints including:

```text
GET  /health
GET  /api/hil/readiness
POST /api/hil/submissions
GET  /api/hil/publication-readiness
```

Review and publication mutation endpoints remain separately governed and authenticated. Endpoint presence is not authority.

## Canonical HIL v1.1 identity

```text
Primary: v1.1
Primary SHA-256: a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462
Protocol: HIL-PROTOCOL-v1.1
Prompt: HIL-PROMPT-v1.1
Prompt SHA-256: cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c
```

These values must agree with the canonical TVC/Site HIL v1.1 state. Historical hashes are provenance only and must not be accepted as current activation identity.

## TV/TVC configuration ownership

Compatibility keys may still be consumed by adapter code, but protected values are issued and managed only by TV/TVC:

| Compatibility key | Governed meaning |
|---|---|
| `STEGVERSE_HIL_INTAKE_ENABLED` | Controlled-cycle intake gate |
| `STEGVERSE_HIL_DATA_DIR` | Governed durable-state namespace or resolved local projection |
| `STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS` | Durability attestation result |
| `STEGVERSE_HIL_REVIEW_TOKEN` | TV/TVC-owned private-review capability credential |
| `STEGVERSE_HIL_PUBLICATION_TOKEN` | Separately governed publication capability credential |

These names are compatibility inputs. They do not authorize a repository workflow, GitHub token, shell, `.env` file, or deployment dashboard to mint or own production credentials.

Raw credential or capability material must never enter repository records, workflow artifacts, logs, or public projections.

## Persistence compatibility

The protocol requires exact-byte and provenance continuity across an authorized runtime replacement. The canonical TVC backend owns the production state transition and custody proof. LLM-adapter compatibility tests may verify data-shape and fail-closed behavior, but they do not create custody or activation evidence.

Required preserved state includes:

- exact response bytes;
- normalized provenance manifests;
- submission and review state;
- receipts;
- publication records;
- stable identifiers and hashes.

No vendor-specific storage product or hosted service class is required by the protocol.

## Runtime lifecycle authority

Canonical production lifecycle:

```text
TVC admits HIL profile/package identity
-> TV/TVC resolves protected capability bindings
-> StegVerse runtime executes the admitted controlled-cycle task
-> custody/reconstruction evidence is retained
-> authenticated private review occurs under TVC#8
-> publication remains a separate authority boundary
-> Site receives only admissible projection
-> Master Records assembly/release remains separately governed
```

LLM-adapter compatibility code does not independently perform or authorize these production lifecycle transitions.

## Readiness acceptance

Compatibility readiness must bind the current HIL v1.1 identity:

```text
primary_sha256 = a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462
prompt_sha256  = cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c
state          = READY
```

A READY response is protocol compatibility evidence only. It does not establish authenticated private review, publication, Master Record custody, release, or product activation.

## Capability-separation projection

A non-secret compatibility projection may identify role binding without revealing capability material:

```json
{
  "capability_role": "private_review",
  "binding_fingerprint_sha256": "<64 lowercase hex characters>",
  "secret_disclosed": false,
  "tv_tvc_governed": true
}
```

## Non-authority boundaries

```text
compatibility validated != production runtime activated
readiness READY != controlled cycle complete
receiver receipt != private acceptance
private acceptance != publication
publication != Master Record custody
restart compatibility != TVC lifecycle proof
GitHub workflow success != HIL activation
GitHub token != HIL runtime authority
LLM-adapter != production credential authority
```

## Activation denominator

Canonical HIL product activation remains governed by the TVC handoff:

```text
1 generalized TVC backend merged/validated: COMPLETE
2 authentic participant custody/reconstruction: COMPLETE
3 authenticated private review: PENDING / TVC#8
4 separately authenticated publication: PENDING
5 Site projection after authenticated decision: PENDING
6 Master Record assembly/release: PENDING
7 downstream verification/publication: PENDING
```

Therefore compatibility validation in this repository does not advance the product activation denominator beyond the canonical **2/7** state.

## Canonical continuation

```text
StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
StegVerse-Labs/TVC#8
StegVerse-Labs/Site#67
master-records/orchestration#13
```

`LLM-adapter` retains compatibility code and deterministic tests only. TV/TVC retains credential and runtime authority. Site and Master Records retain their separately governed downstream roles.
