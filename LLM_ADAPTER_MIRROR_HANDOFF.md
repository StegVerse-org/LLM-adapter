# LLM Adapter Mirror Handoff

## Source of truth

This file is the current continuation source for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat with provider response, telemetry, authenticated usage retrieval, custody, reconstruction, and automatic downstream propagation
Phase: durable-live-blocker-and-immutable-verification-publication-installed
Result: REPOSITORY_AUTOMATION_COMPLETE_CURRENT_MAIN_AND_LIVE_EVIDENCE_PENDING
Manual user action required: false
```

## Installed governed path

```text
Site request
-> governed provider response
-> provider usage persistence
-> authenticated provider-usage custody
-> transition custody
-> reconstruction PASS for both chains
-> stable semantic live status while pending
-> immutable verified activation receipt after all gates pass
-> Site automatic import
-> Publisher and wiki projections
```

## Production topology

`render-production.yaml` declares the public gateway and private durable Master-Records custody service. The deployment platform generates custody credentials, binds the private host and port, retains both databases on persistent disks, and deploys after checks pass. Browser credentials and repository-exposed custody secrets remain prohibited.

The external model provider remains provider-owned configuration. Missing or invalid provider configuration is reported by scheduled verification as a precise semantic blocker and does not create a manual verification task.

## Autonomous workflows

```text
.github/workflows/validate.yml
.github/workflows/ecosystem-chat-live-activation.yml
iosnoperiod/github/workflows/validate.yml
```

Validation runs on repository events and schedule. Live verification runs hourly and after successful validation.

Pending observations now produce two forms:

```text
receipts/ecosystem-chat-live-activation.latest.json
  full volatile observation retained as a workflow artifact

reports/ecosystem-chat-live-activation-status.json
  stable commit-backed semantic blocker state
```

The stable status omits timestamps and volatile request evidence, so it changes only when the live state, blocker set, or gate posture changes. This prevents hourly commit churn while eliminating manual artifact inspection.

After every gate passes, the first verified observation is copied to and retained at:

```text
receipts/ecosystem-chat-live-activation.verified.json
```

That immutable path is never replaced.

## Installed continuation guards

```text
scripts/verify_live_ecosystem_chat_activation.py
scripts/write_live_activation_status.py
tests/test_live_activation_automation_contract.py
```

The status writer requires:

```text
state = PENDING or VERIFIED
VERIFIED -> blockers = []
manual_user_action_required = false
activation authority = false
deployment authority = false
custody claim = false
release authority = false
stable canonical status hash
```

The live verifier still requires:

```text
gateway health OK
durable storage
governed provider enabled
real provider use
local usage persistence remains non-custodial
provider-usage custody RECORDED
provider-usage reconstructability PASS
transition custody RECORDED
transition reconstructability PASS
all authority flags false
```

## Current evidence state

```text
repository implementation: INSTALLED
self-contained private custody topology: INSTALLED
scheduled validation: INSTALLED
scheduled live verification: INSTALLED
durable semantic blocker publication: INSTALLED
immutable verified receipt publication: INSTALLED AND GUARDED
Site pending-status and verified-receipt import alignment: INSTALLED
latest semantic blocker status: AWAITING FIRST SCHEDULED WRITE
retained immutable verified receipt: NOT YET OBSERVED
Site ACTIVATION_COMPLETE: NOT YET OBSERVED
downstream verified ingestion: NOT YET OBSERVED
```

No combined-status record or absent receipt is treated as success.

## Machine-owned continuation

```text
1. Scheduled validation evaluates current main.
2. The deployment platform synchronizes the declared topology.
3. Hourly verification probes provider, custody, identity, and reconstruction.
4. The semantic blocker set is committed only when it changes.
5. Full observations remain workflow artifacts.
6. The first VERIFIED result is committed at the immutable receipt path.
7. Site imports either the pending semantic status or the verified receipt automatically.
8. Publisher and both wiki consumers ingest the Site projection automatically.
9. Release readiness remains fail-closed until live and downstream evidence exists.
```

No user workflow dispatch, artifact download, file movement, receipt construction, or repeated blocker inspection is required.

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
pending status != activation
verified receipt != release authority
```

## Release posture

Repository implementation, topology, validation, stable blocker publication, immutable receipt retention, Site consumption, Publisher import, and wiki consumers are installed. Current-main workflow observation, authorized deployment, real provider use, live custody, reconstruction, Site completion, and downstream public observation remain pending. No release tag is authorized.

## Archive readiness

This handoff, repository history, machine-owned status files, scheduled workflows, tests, and the eventual immutable verified receipt preserve all continuation state. Earlier conversation context is not required, but this workstream should remain active until the first stable blocker state or immutable verified receipt is observed and any exact repository-owned failure is resolved.
