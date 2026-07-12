# LLM Adapter Mirror Handoff

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat with provider-backed responses and durable custody continuity
Phase: governed-provider-broker-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_DEPLOYMENT_VALIDATION_PENDING
```

## Current path

```text
StegVerse-Labs/Site Ecosystem Chat
-> canonical SITE_INPUT transition identity
-> governed validation and rate limit
-> optional governed provider broker
-> deterministic fallback on any provider boundary failure
-> bridge/delegation/standing bounded progression
-> active STEGVERSE_AI_ENTITY response completion
-> final response receipt
-> SQLite persistence
-> Master-Records custody queue and authenticated submission
```

## Installed service surfaces

```text
llm_adapter/ecosystem_chat_gateway.py
llm_adapter/governed_provider.py
llm_adapter/governed_chat_pipeline.py
llm_adapter/transition_store.py
llm_adapter/master_records_client.py
llm_adapter/custody_worker.py
tests/test_ecosystem_chat_gateway.py
tests/test_governed_provider.py
tests/test_governed_chat_pipeline.py
tests/test_transition_store_and_custody.py
tests/test_production_gateway_blueprint.py
render.yaml
render-production.yaml
```

The service exposes:

```text
GET  /health
POST /api/ecosystem-chat
GET  /api/transitions/{transition_id}
```

## Governed provider contract

The provider is vendor-neutral and disabled by default. Activation requires:

```text
STEGVERSE_PROVIDER_ENABLED=true
HTTPS provider endpoint
hostname allowlist match
provider bearer token
provider name and model
bounded timeout
input/output character limits
daily request quota
daily estimated-cost ceiling
per-request estimated-cost ceiling
```

Provider requests carry the existing transition and run identities. Provider responses may return text, usage, request identity, and matching transition metadata.

A successful response creates:

```text
provider status = USED
provider-response-receipt:sha256:...
provider request id
provider/model reference
bounded usage and estimated cost
provider evidence in the canonical transition relationship
```

## Fail-closed provider behavior

Any of the following causes deterministic StegVerse fallback rather than request failure:

```text
provider disabled
configuration incomplete
unapproved hostname
quota exhausted
request or daily cost boundary exceeded
input/output size violation
transport failure
invalid response contract
transition/run identity mismatch
```

Provider credentials are never returned to Site, stored in receipts, or included in transition records.

## Persistence profiles

Validation profile:

```text
render.yaml
plan: free
STEGVERSE_TRANSITION_DB=/tmp/stegverse-ecosystem-chat.db
STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS=false
provider disabled by default
```

Production profile:

```text
render-production.yaml
plan: starter
persistent disk: /var/data
STEGVERSE_TRANSITION_DB=/var/data/stegverse-ecosystem-chat.db
STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS=true
provider disabled until explicit credential and policy configuration
```

## Custody contract

```text
SQLite persistence != Master-Records custody
PENDING/RETRY queue state != RECORDED
RECORDED requires a remote identity-matched custody receipt
```

## Authority boundary

```text
Provider output != authority
Provider receipt != final response receipt
Provider response != admissibility
Provider failure cannot grant fallback authority
Gateway intake receipt != final response receipt
Final response receipt != repository mutation authority
SQLite persistence != Master-Records custody
Native executor ACTIVE != blanket per-transition authority
```

## Latest validation failure and repair

```text
Workflow: validate
Run: 29191217331
Branch: main
Commit: 4896fb08338b5a28cb9afc142ee85e8bbe6a3fa2
Job: validate
First failing step: Check no-manual-task wiring
Failure class: stale handoff-marker assertion
```

All workflow steps through package initialization, micro-node return-path verification, provider-boundary verification, backend-service verification, endpoint verification, and service-wrapper verification passed before the failure.

`scripts/check_ai_entry_no_manual_tasks.py` still required superseded archive-readiness prose from an earlier adapter phase. It now validates the current governed-provider handoff identity, phase, result, authority boundary, and first declared verification task.

Applied repair:

```text
89a55c63522f6366ff744aaacc90f58c9deed725
```

No provider was enabled, no credential was used, no deployment was performed, and no execution, publication, repository-mutation, final-receipt, or custody authority changed.

## Verification required

```text
validate must pass on commit 89a55c63522f6366ff744aaacc90f58c9deed725 or a documented successor
Check no-manual-task wiring must pass
all later aggregate, test, parity, authority, receipt, provider-capture, recovery, and Goal 4 verification steps must complete
passing run ID and commit SHA must be recorded here
```

## Next task

```text
1. Verify the current-main validate run on 89a55c63522f6366ff744aaacc90f58c9deed725 or later.
2. If green, verify gateway, provider, pipeline, storage, custody, and blueprint tests as complete.
3. Deploy gateway and custody production profiles only under separate explicit deployment authority.
4. Configure custody endpoint/token/receipt key/hostname allowlist only when credentials and authority are available.
5. Optionally configure a governed provider broker endpoint and bounded policy values.
6. Verify one public request returns provider USED or explicit deterministic fallback posture.
7. Verify the same transition reaches RECORDED custody without identity drift.
8. Run orchestration live round-trip verification before public activation claims.
```

## Archive readiness

This handoff contains the provider broker, gateway lifecycle, persistent production profile, custody continuity, latest validation failure and bounded repair, authority boundaries, and continuation order. Earlier conversation context is not required.
