# LLM Adapter Mirror Handoff

## Source of truth

This file is the current continuation source for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat with provider response, provider telemetry, authenticated usage retrieval, transition custody, provider-usage custody, and reconstructable evidence
Phase: live-activation-automation-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_CURRENT_MAIN_AND_LIVE_EVIDENCE_PENDING
```

## Installed runtime surfaces

```text
llm_adapter/combined_gateway.py
llm_adapter/ecosystem_chat_gateway.py
llm_adapter/provider_usage.py
llm_adapter/provider_usage_submission.py
llm_adapter/master_records_usage_submission.py
llm_adapter/usage_session_api.py
llm_adapter/master_records_client.py
llm_adapter/system_boundary.py
llm_adapter/system_boundary_binding.py
llm_adapter/system_boundary_receipt.py
llm_adapter/system_boundary_lifecycle.py
```

## Provider usage lifecycle

```text
successful provider result
-> canonical provider usage event
-> local usage-session persistence
-> automatic authenticated Master-Records submission
-> identity-bound custody receipt validation
-> custody and reconstruction posture included in gateway response
```

Behavior:

```text
provider used = true -> persist exactly one event
provider disabled, blocked, failed, or fallback -> no provider event
identical replay -> idempotent
changed event under the same measurement identity -> fail closed
local persistence custody -> false
external custody accepted only after exact receipt identity validation
usage authority -> false
repository mutation -> false
```

## Master-Records provider usage contract

Source implementation:

```text
llm_adapter/master_records_usage_submission.py
```

Destination implementation:

```text
master-records/orchestration
services/master_records_custody_api.py
POST /api/custody/provider-usage
GET /api/custody/provider-usage/receipts/{receipt_id}/reconstruction
PROVIDER_USAGE_CUSTODY_MIRROR_HANDOFF.md
```

The adapter resolves the endpoint and bearer credential only in the deployed server environment. Remote transport requires HTTPS. Browser payloads and responses never contain the credential.

The adapter accepts custody only when the destination receipt exactly preserves:

```text
session_id
measurement_id
event_sha256
custody_recorded = true
authority_granted = false
```

## Usage-session contract

```text
POST /api/usage/sessions
GET  /api/usage/sessions/{session_id}
```

The endpoint validates event identity and evidence classes, deduplicates by `metric_owner + measurement_id`, and returns a bounded retrieval receipt. Local persistence and retrieval do not grant custody, authority, standing, or admissibility.

## Production deployment posture

```text
render-production.yaml
Dockerfile
```

The production blueprint now specifies:

```text
Render autoDeploy: true
persistent /var/data disk
persistent transition database
persistent usage-session database
persistent external-review database
governed provider enabled
Master-Records endpoint and token resolved server-side
external mutation disabled
allowed Site origins
```

External provider and custody endpoint credentials remain platform-managed values and are not stored in the repository.

## Autonomous activation evidence

Installed:

```text
scripts/write_ecosystem_chat_destination_activation_state.py
scripts/verify_live_ecosystem_chat_activation.py
.github/workflows/validate.yml
.github/workflows/ecosystem-chat-live-activation.yml
iosnoperiod/github/workflows/validate.yml
tests/test_live_activation_automation_contract.py
```

Automation behavior:

```text
canonical validation runs on pushes, pull requests, dispatch, and schedule
canonical and iOS-safe workflows remain byte-equivalent
repository-local destination state is written and retained as a workflow artifact
live activation verification runs after successful validation and hourly
first existing VERIFIED live receipt is preserved and not replaced
fresh governed transition identity is generated for live verification
real provider use is required
provider usage local persistence must remain non-custodial
provider-usage custody and reconstruction PASS are required
transition custody and reconstruction PASS are required
pending results are retained as artifacts
only the first VERIFIED live result is committed
no browser credential or manual live-verifier command is required
```

## System-boundary posture

```text
runtime declaration builder: INSTALLED
runtime surface inventory: INSTALLED
feedback-path recorder: INSTALLED
claim and authority guards: INSTALLED
optional governed response/session binding: INSTALLED
explicit lifecycle binding: INSTALLED
system_boundary_declaration_ref persistence: INSTALLED
replay and conflict handling: INSTALLED
production binding: DISABLED PENDING SEPARATE AUTHORIZATION
consciousness/personhood/welfare claims: NOT_EVALUATED
```

## Current evidence state

```text
provider usage local persistence: INSTALLED
provider usage automatic custody submission: INSTALLED
provider usage receipt validation: INSTALLED
provider usage destination API: INSTALLED IN master-records/orchestration
provider usage reconstruction API: INSTALLED IN master-records/orchestration
production deployment blueprint: INSTALLED
scheduled live verifier: INSTALLED
canonical/iOS workflow parity: INSTALLED
activation automation contract tests: INSTALLED
current-main validation containing latest automation: NOT YET OBSERVED
production gateway containing latest source: NOT YET OBSERVED
production custody service containing provider-usage route: NOT YET OBSERVED
real provider use: NOT YET OBSERVED
live provider-usage custody receipt: NOT YET OBSERVED
live transition custody receipt: NOT YET OBSERVED
retained VERIFIED activation receipt: NOT YET OBSERVED
Site activation-ledger consumption: NOT YET OBSERVED
```

## Remaining work

```text
1. Observe current-main validation containing fb07017f14710af863de1d52e793a227499192c4 or later.
2. Repair only the first exact failing validation step without removing checks.
3. Allow Render auto-deployment to deploy current main using render-production.yaml.
4. Let .github/workflows/ecosystem-chat-live-activation.yml perform the live check automatically.
5. Preserve the first VERIFIED activation receipt.
6. Propagate that verified receipt into StegVerse-Labs/Site activation state.
7. Enable Site live usage display only when its own handoff gates accept the retained receipt.
8. Propagate verified status to Publisher, admissibility-wiki, stegguardian-wiki, and Sit.
9. Tag or release only after repository validation and retained live evidence are both verified.
```

## Downstream destinations

```text
master-records/orchestration
StegVerse-org/StegVerse-SDK
StegVerse-Labs/Site
GCAT-BCAT-Engine/Publisher
StegVerse-Labs/admissibility-wiki
StegVerse-Labs/stegguardian-wiki
StegVerse-Labs/Sit
```

## Authority boundary

```text
provider output != authority
usage measurement != admissibility
local persistence != custody
submission != custody
custody receipt != execution authority
reconstruction PASS != execution authority
system-boundary binding != authority
workflow artifact != deployment evidence
pending live check != activation
```

## Release posture

Repository-local implementation and autonomous validation are installed. Current-main validation, production deployment, live provider use, live transition and usage custody, reconstructability, and Site consumption remain pending. No release tag is authorized.

## Archive readiness

This handoff, the Master-Records provider-usage handoff, repository history, workflows, tests, deployment blueprints, activation-state artifacts, and the eventual retained VERIFIED receipt preserve all continuation state. Earlier conversation context is not required.
