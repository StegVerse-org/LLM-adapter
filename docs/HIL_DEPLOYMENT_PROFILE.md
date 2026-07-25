# HIL Runtime Activation Profile

Version: `HIL-RUNTIME-ACTIVATION-PROFILE-v2`

## Purpose

This document defines the platform-agnostic runtime contract for the `Humans as the Interoperability Layer` controlled cycle.

There is no hosting-platform dependency, hosting-provider requirement, container-platform requirement, or external secret-store requirement. Runtime construction, configuration delivery, lifecycle transitions, restart, persistence binding, and evidence emission are governed by TV/TVC.

```text
application code != hosting platform
runtime environment != vendor environment
configuration != unmanaged environment variables
process restart != provider redeploy
```

## Required application boundary

The runtime must execute repository code at or after:

```text
b2e612dd74d311e0cbe66cd1c1d4758bff129fd4
```

The application boundary is `llm_adapter.combined_gateway:app` and must expose:

```text
GET  /health
GET  /api/hil/readiness
POST /api/hil/submissions
GET  /api/hil/publication-readiness
```

Review and publication mutation endpoints remain separately governed and authenticated.

## TV/TVC configuration ownership

TV/TVC owns all runtime values, including values currently consumed through process-environment compatibility keys.

| Compatibility key | TV/TVC-governed meaning |
|---|---|
| `STEGVERSE_HIL_INTAKE_ENABLED` | Controlled-cycle intake gate |
| `STEGVERSE_HIL_DATA_DIR` | Governed durable-state namespace or resolved local projection |
| `STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS` | TV/TVC durability attestation result |
| `STEGVERSE_HIL_REVIEW_TOKEN` | Ephemeral or durable capability credential for private review |
| `STEGVERSE_HIL_PUBLICATION_TOKEN` | Separate capability credential for publication |

These names are adapter compatibility inputs, not a requirement that a human, hosting provider, shell, `.env` file, or platform dashboard manage them.

TV/TVC may inject them into a process environment, bind them through a runtime adapter, resolve them from governed capability records, or replace the compatibility interface later without changing the HIL protocol.

## Storage contract

HIL state must survive a TV/TVC-governed runtime restart. The persistence implementation is abstract and may be local, distributed, replicated, content-addressed, database-backed, filesystem-backed, or another admissible TV/TVC storage capability.

The persistence contract must preserve:

- exact response bytes;
- normalized provenance manifests;
- submission and review state;
- receipts;
- publication records;
- stable identifiers and hashes.

No mounted volume, container, host, service provider, or vendor storage class is required by the protocol.

## Runtime lifecycle

```text
TV/TVC resolves runtime capability set
-> TV/TVC binds governed storage namespace
-> TV/TVC issues distinct review and publication capabilities
-> TV/TVC starts gateway runtime
-> readiness contracts are observed
-> controlled response is submitted
-> TV/TVC terminates the runtime instance
-> TV/TVC starts a new runtime instance against the same governed state
-> exact-byte and provenance persistence are verified
-> private review is executed under review capability
-> publication is executed under separate publication capability
-> governed evidence is transferred to Site
```

## Readiness acceptance

The intake readiness response must identify:

```text
primary_sha256 = 52102cccb9ba9016c76434a64e22031b6a8c3edd3b8806e7b664e609216b2946
prompt_sha256  = 0ebe215318b4eeeb8ed6422e0954372c314fadc8fac9254e452bc7670a1b9922
state          = READY
private_review_configured = true
```

Publication readiness must independently report that publication configuration is present and append-only. Readiness grants no mutation authority.

## Capability-separation evidence

Evidence must establish that intake, private review, and publication are distinct TV/TVC capability bindings. Raw credentials or capability material must never enter repository records.

A permitted projection is:

```json
{
  "capability_role": "private_review",
  "binding_fingerprint_sha256": "<64 lowercase hex characters>",
  "secret_disclosed": false,
  "tv_tvc_governed": true
}
```

## Restart proof

A valid restart proof must bind:

- TV/TVC transition identifier for termination;
- TV/TVC transition identifier for subsequent start;
- prior and successor runtime-instance identifiers;
- submission identifier;
- response SHA-256 before and after restart;
- provenance-manifest SHA-256 before and after restart;
- governed storage-state reference;
- post-restart lookup result.

An in-process application-object recreation does not satisfy this requirement. A TV/TVC-governed process or runtime-instance replacement does.

## Non-authority boundaries

```text
runtime configured != public acquisition authorized
readiness READY != controlled cycle complete
capability bound != mutation authorized for every actor
receiver receipt != private acceptance
private acceptance != publication
publication != Master Record custody
restart success != evidence packet approval
TV/TVC orchestration != automatic release authority
```

## Completion handoff

Runtime evidence is transferred into:

```text
StegVerse-Labs/Site/data/hil-activation-state.json
StegVerse-Labs/Site/data/hil-deployed-controlled-cycle-evidence.json
```

`LLM-adapter` owns gateway behavior. TV/TVC owns runtime configuration and lifecycle. Site owns public activation state and the evidence chain leading to the first HIL Master Record release.
