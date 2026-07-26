# HIL Runtime Mirror Handoff

## Source of truth

This document owns continuation for the provider-neutral HIL v1.1 receiver runtime in `StegVerse-org/LLM-adapter`. It does not grant activation, review, publication, execution, custody-transfer, or Master Record authority.

## Current state

```text
Primary: v1.1
Primary SHA-256: a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462
Protocol: HIL-PROTOCOL-v1.1
Prompt: HIL-PROMPT-v1.1
Prompt SHA-256: cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c
Intake router: llm_adapter/hil_intake_v1_1_api.py
Gateway: llm_adapter/combined_gateway.py
Container contract: Dockerfile
Portable composition: compose.yaml
Entrypoint: scripts/container-entrypoint.sh
Bootstrap: scripts/start-hil-runtime.sh
Quickstart: docs/HIL_RUNTIME_QUICKSTART.md
Runtime contract: docs/PLATFORM_AGNOSTIC_RUNTIME.md
Result: IMPLEMENTED_PORTABLE_RUNTIME_NOT_PUBLICLY_ACTIVATED
Authority: NONE
```

## Corrected provider posture

`render.yaml` is an optional, fail-closed provider example. It declares storage as non-durable and therefore cannot make HIL readiness report `READY`. Render, its hostname, and its billing tiers are not dependencies or activation requirements.

The canonical path is the OCI image plus environment, port, volume, HTTPS, and secret-injection contracts. Any conforming host may run the same revision without application-code changes.

## Completed

- HIL v1.1 intake router with optional participant metadata.
- Exact Primary, prompt, response, and provenance hash validation.
- Exact uploaded PDF and manifest persistence beneath `STEGVERSE_HIL_DATA_DIR`.
- Receiver receipt generation.
- Separate private-review and publication token boundaries.
- Provider-neutral Dockerfile, entrypoint, named-volume Compose runtime, and readiness checks.
- Local bootstrap that creates distinct uncommitted secrets and verifies exact v1.1 readiness.
- Provider-neutral public HTTPS deployment instructions.

## Remaining vertical slice

1. Run `sh scripts/start-hil-runtime.sh` on a Docker-capable machine.
2. Confirm local `READY` output with exact v1.1 hashes.
3. Attach the same OCI runtime to any durable public host or standards-compatible HTTPS reverse proxy.
4. Verify the public HTTPS readiness endpoint.
5. Configure `StegVerse-Labs/Site/data/hil-receiver-config.json` with that proven endpoint.
6. Submit one controlled PDF and preserve the returned receipt.
7. Restart or replace the service while retaining the volume and prove exact bytes and manifest persist.
8. Record one authenticated write-once private review.
9. Record one separately authenticated append-only publication.
10. Import the publication into the Site projection and build the first Master Record release.

## Known remaining files and destinations

```text
StegVerse-org/LLM-adapter
- public runtime deployment evidence: pending
- controlled upload evidence: pending
- actual restart persistence evidence: pending
- authenticated private-review evidence: pending
- append-only publication evidence: pending

StegVerse-Labs/Site
- data/hil-receiver-config.json: intentionally unconfigured pending proven HTTPS receiver
- docs/HIL_SITE_MIRROR_HANDOFF.md: must track v1.1 runtime and first controlled cycle
- data/hil-responses.json: first published response pending
- data/hil-master-records.json: first release pending
- issue #81: remains active

GCAT-BCAT-Engine/Publisher
- release verification task: create only after first authorized release/tag

admissibility-wiki
- release verification task: create only after first authorized release/tag

stegguardian-wiki
- release verification task: create only after first authorized release/tag
```

## Completion boundary

The upload path is not complete merely because the browser client and API exist. Completion requires a reachable HTTPS receiver, durable-state proof across an actual restart or replacement, a valid controlled receipt, authenticated private review, append-only publication, Site projection, and Master Record release evidence.
