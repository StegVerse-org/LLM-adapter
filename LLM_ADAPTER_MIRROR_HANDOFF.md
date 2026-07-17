# LLM Adapter Mirror Handoff

## Source of truth

This file is the current continuation source for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat with provider response, telemetry, authenticated usage retrieval, custody, reconstruction, and automatic downstream propagation
Phase: immutable-verified-receipt-publication-contract-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_CURRENT_MAIN_AND_LIVE_EVIDENCE_PENDING
Manual user action required: false
```

## Installed path

```text
Site request
-> governed provider response
-> provider usage persistence
-> authenticated custody submission
-> transition custody
-> reconstruction PASS
-> immutable verified activation receipt
-> Site automatic import
-> Publisher and wiki projections
```

## Production topology

The existing production blueprint declares the public gateway and private durable custody service. Service identity, private routing, and protected configuration are platform-managed. Browser credentials and repository-exposed secrets remain prohibited.

## Autonomous workflows

```text
.github/workflows/validate.yml
.github/workflows/ecosystem-chat-live-activation.yml
iosnoperiod/github/workflows/validate.yml
```

Validation runs on repository events and schedule. Live activation verification runs hourly and after successful validation. Pending observations remain workflow artifacts. The first verified observation is retained automatically and is never replaced.

## Immutable receipt contract repair

A propagation defect was repaired: the live workflow previously retained the mutable observation filename while Site imports the immutable verified filename.

```text
e1fc89ab06bc0efad4ffa6539ebab6a14feb5584
  publish the first verified observation at receipts/ecosystem-chat-live-activation.verified.json
fe1341d2688d22e55fb0f72ca56ff2c62d7e692d
  fail-closed verified-receipt publication guard
3dc8d4bba106f3b4ddfcd679b942069cdeb06c9d
  canonical validation integration
dff8988b3e25b7a92d65e35a1cc2036674458498
  iOS-safe workflow synchronization
```

The guard requires an explicit mutable-observation to immutable-verified copy, verified state, empty blocker list, and retention of only the immutable verified path. It rejects use of the mutable observation as the durable activation receipt.

## Current evidence state

```text
repository implementation: INSTALLED
self-contained custody topology: INSTALLED
scheduled validation: INSTALLED
scheduled live verification: INSTALLED
immutable verified receipt publication: INSTALLED AND GUARDED
Site import contract alignment: INSTALLED
current-main combined status for dff8988b: NO STATUS RECORDS EXPOSED
live deployment containing latest topology: NOT YET OBSERVED
real provider use: NOT YET OBSERVED
live custody and reconstruction: NOT YET OBSERVED
retained immutable verified receipt: NOT YET OBSERVED
Site and downstream ingestion: NOT YET OBSERVED
```

Missing status records are not treated as success and do not create a user task. Scheduled workflows own the next observations.

## Machine-owned continuation

```text
1. Scheduled validation evaluates current main.
2. The authorized deployment platform synchronizes the declared topology.
3. Hourly verification tests provider response, custody, identity preservation, and reconstruction.
4. Pending results remain artifacts.
5. The first verified result is committed automatically at the immutable path.
6. Site imports and validates it automatically.
7. Publisher and both wiki consumers ingest the verified projection automatically.
8. Release readiness remains fail-closed until live and downstream evidence exists.
```

No user confirmation, workflow dispatch, file movement, artifact download, or manual receipt construction is required.

## Canonical downstream destinations

```text
master-records/orchestration
StegVerse-org/StegVerse-SDK
StegVerse-Labs/Site
GCAT-BCAT-Engine/Publisher
StegVerse-Labs/admissibility-wiki
StegVerse-002/stegguardian-wiki
```

`StegVerse-Labs/Sit` and `StegVerse-Labs/stegguardian-wiki` do not exist and are not destinations.

## Authority boundary

```text
provider output != authority
usage measurement != admissibility
local persistence != custody
submission != custody
custody receipt != execution authority
reconstruction PASS != execution authority
workflow artifact != live evidence
pending result != activation
verified receipt != release authority
```

## Release posture

Implementation, topology, scheduled validation, immutable receipt retention, Site consumption, Publisher import, and wiki consumers are installed. Current-main evidence, authorized deployment, live provider use, custody, reconstruction, Site completion, and downstream public observation remain pending. No release tag is authorized.

## Archive readiness

This handoff, repository history, machine-owned state files, scheduled workflows, tests, and the eventual immutable verified receipt preserve all continuation state. Earlier conversation context is not required.
