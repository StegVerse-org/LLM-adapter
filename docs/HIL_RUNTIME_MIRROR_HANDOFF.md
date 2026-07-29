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

## Correct diagnosis of the current blocker

The public Site upload control is `NOT READY` because no verified public HTTPS receiver is configured in `StegVerse-Labs/Site/data/hil-receiver-config.json`.

The browser client already exists. The missing capability is hosted receiver deployment with HTTPS and durable storage. A loopback receiver such as `http://127.0.0.1:8000` is diagnostic only and can never satisfy public Site readiness.

## Binding dependency rule

The current state is `BLOCKED_PENDING_INTERNAL_UNBLOCK_SEARCH`, not a request for participant hardware.

All reasonable ecosystem-owned, managed, ephemeral, serverless, or existing-host alternatives must be evaluated before any external hardware role may be proposed. A participant may not be made the hardware provider, hardware rehabilitator, installer, node operator, student, experiment operator, schema interpreter, troubleshooter, recovery mechanism, or continuity layer because those system roles are unfilled.

Local validation may run only in repository-owned CI, an ephemeral managed container, an existing enrolled StegVerse node, or an already-ready developer environment. It must not require construction of participant infrastructure and must not be represented as public activation.

## Corrected provider posture

`render.yaml` and any other provider manifest are optional, fail-closed provider examples. No provider, hostname, or billing tier is an architectural dependency or participant-facing requirement.

The canonical path is the OCI image plus environment, port, volume, HTTPS, and secret-injection contracts. Any conforming managed host may run the same revision without application-code changes.

## Completed

- HIL v1.1 intake router with optional participant metadata.
- Exact Primary, prompt, response, and provenance hash validation.
- Exact uploaded PDF and manifest persistence beneath `STEGVERSE_HIL_DATA_DIR`.
- Receiver receipt generation.
- Separate private-review and publication token boundaries.
- Provider-neutral Dockerfile, entrypoint, named-volume Compose runtime, and readiness checks.
- Local bootstrap for authorized ready environments.
- Provider-neutral public HTTPS deployment contract.
- Receiver-hosted browser submission surface for diagnostic and managed deployments.

## Remaining vertical slice

1. Run the unchanged OCI/runtime validation in repository-owned CI or another authorized ephemeral venue.
2. Select a conforming managed/serverless host that supplies HTTPS termination, runtime secret injection, durable storage, restart/replacement support, and exportable evidence.
3. Deploy the unchanged provider-neutral runtime without requiring participant-owned continuously live hardware.
4. Configure separate private-review and publication credentials at the host secret boundary.
5. Verify public `/api/hil/readiness` and `/api/hil/publication-readiness` against the exact v1.1 hashes.
6. Perform a controlled hosted restart or replacement while retaining storage and prove exact PDF bytes and manifest persistence.
7. Configure `StegVerse-Labs/Site/data/hil-receiver-config.json` with the proven HTTPS endpoint and `CONFORMING_HTTPS_RECEIVER_CONFIGURED`.
8. Confirm the public Site upload control transitions from `NOT READY` to `READY`.
9. Submit one controlled PDF through the existing Site browser client and preserve the returned receipt.
10. Record one authenticated write-once private review.
11. Record one separately authenticated append-only publication.
12. Import the publication into the Site projection and build the first Master Record release.

## Prohibited substitutions

```text
participant laptop as canonical receiver
participant hardware rehabilitation as unblock work
manual Swagger submission as the primary participant path
manual hashes or provenance JSON assigned to the participant
local Docker success represented as hosted activation
local validation treated as production hosting
external dependency declared before internal/managed alternatives are exhausted
```

## Known remaining files and destinations

```text
StegVerse-org/LLM-adapter
- authorized-venue automated runtime validation evidence: pending
- public managed/serverless runtime deployment evidence: pending
- controlled Site upload evidence: pending
- hosted restart/replacement persistence evidence: pending
- authenticated private-review evidence: pending
- append-only publication evidence: pending

StegVerse-Labs/Site
- data/hil-receiver-config.json: intentionally unconfigured pending proven HTTPS receiver
- docs/HIL_SITE_MIRROR_HANDOFF.md: corrected hosting and burden rules
- data/hil-responses.json: first published response pending
- data/hil-master-records.json: first release pending
- issue #81: active hosted-receiver activation tracker

GCAT-BCAT-Engine/Publisher
- release verification task: create only after first authorized release/tag

admissibility-wiki
- release verification task: create only after first authorized release/tag

stegguardian-wiki
- release verification task: create only after first authorized release/tag
```

## Completion boundary

The upload path is not complete merely because the browser client and API exist. Completion requires a reachable HTTPS receiver on managed/serverless or already-enrolled infrastructure, durable-state proof across an actual hosted restart or replacement, a valid controlled Site receipt, authenticated private review, append-only publication, Site projection, and Master Record release evidence.

Participant-owned continuously live hardware is not a completion prerequisite.