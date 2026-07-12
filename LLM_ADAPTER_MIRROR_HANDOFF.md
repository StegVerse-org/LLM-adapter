# LLM Adapter Mirror Handoff

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat plus External Chat compatibility and delegated review services
Phase: authenticated-external-review-transport-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_DEPLOYMENT_VALIDATION_PENDING
```

## Current service paths

```text
Ecosystem Chat
-> canonical transition identity
-> governed validation and optional provider
-> deterministic fallback
-> bounded response lifecycle
-> SQLite persistence
-> Master-Records custody queue

External Chat
-> bounded compatibility evaluation
-> explicit cooperative-review opt-in
-> authenticated package-only intake
-> append-only review storage
-> delegated reviewer correction
-> HMAC-bound intake and correction receipts
```

## Installed service surfaces

```text
llm_adapter/combined_gateway.py
llm_adapter/ecosystem_chat_gateway.py
llm_adapter/governed_provider.py
llm_adapter/governed_chat_pipeline.py
llm_adapter/transition_store.py
llm_adapter/master_records_client.py
llm_adapter/custody_worker.py
llm_adapter/external_framework_compatibility.py
llm_adapter/external_chat_api.py
llm_adapter/external_review_store.py
llm_adapter/external_review_api.py
tests/test_external_framework_compatibility.py
tests/test_external_review_api.py
render.yaml
render-production.yaml
```

## HTTP routes

```text
GET  /health
POST /api/ecosystem-chat
GET  /api/transitions/{transition_id}
POST /api/external-framework-compatibility
GET  /api/external-review/health
POST /api/external-review/packages
GET  /api/external-review/packages/{package_id}
POST /api/external-review/corrections
```

## Receipt and authority separation

```text
compatibility receipt != review intake receipt
review intake receipt != correction receipt
correction receipt != publication authority
correction receipt != certification
reviewer delegation != standing
provider output != authority
SQLite persistence != Master-Records custody
```

Review intake returns `AWAITING_DELEGATED_REVIEW` and no wiki record, publication authority, certification, or standing.

## Parallel comparison telemetry build

Installed:

```text
llm_adapter/recursive_comparison.py
examples/llm_route_comparison/external_recursive_fixture.json
scripts/verify_recursive_comparison.py
tests/test_recursive_comparison.py
.github/workflows/validate.yml comparison verification steps
```

Proof path:

```text
SDK comparison package
-> package SHA-256 verification
-> select exactly one EXTERNAL_RECURSIVE route
-> validate provider-neutral telemetry
-> preserve comparison and task identity
-> emit external recursive route result
-> return deterministic result hash to SDK
```

Current fixture values are classified `CONFIGURED`, not `MEASURED`. Live provider traces must supply actual call, token, latency, cost, retry, tool, and output evidence before public delta claims are allowed.

## Parallel cross-entry role and usage build

Installed:

```text
llm_adapter/entry_point_role.py
llm_adapter/provider_usage.py
scripts/verify_provider_usage.py
tests/test_provider_usage.py
docs/ENTRY_POINT_ROLE.md
.github/workflows/validate.yml role and usage verification steps
```

The adapter now publishes a machine-readable role declaration and emits provider-owned `TRANSITION_USAGE_RECORDED` events compatible with the SDK usage ledger.

Proof path:

```text
provider/model interaction
-> preserve session_id and transition lineage
-> classify interaction_type
-> record provider-owned metrics only
-> preserve MEASURED / CONFIGURED / DERIVED / UNAVAILABLE
-> emit stable measurement_id and event SHA-256
-> return receipt references and origin entry point
-> shared cross-entry usage ledger
```

Required invariants:

```text
provider_output_is_authority == false
adapter_observation_is_admissibility == false
usage_event_is_authority == false
usage_event_is_admissibility == false
metric_owner == llm_adapter
session_identity_preserved == true
transition_lineage_preserved == true
configured_values_are_measured == false
```

Canonical verification:

```bash
python scripts/verify_recursive_comparison.py
python scripts/verify_provider_usage.py
python -m pytest tests/test_recursive_comparison.py tests/test_provider_usage.py -v
```

No new workflow was created.

## Next task

```text
1. Verify current-main validation after role and provider-usage installation.
2. Wire provider usage emission into the governed provider call lifecycle.
3. Add live provider trace capture behind explicit provider configuration.
4. Add a callable comparison HTTP route returning recursive route results.
5. Add Master-Records custody queue support for provider usage events.
6. Add a reviewer-facing console and separately authorized publication transition.
7. Record live endpoint and CI evidence before public activation claims.
```

## Remaining cross-repository integrations

```text
StegVerse-org/StegVerse-SDK
-> paired comparison orchestration and shared usage aggregation installed
-> consume adapter provider-usage events in integrated sessions

StegVerse-org/core-node-runtime-demo
-> provide governed measured telemetry
-> emit runtime/node/closure usage events

StegVerse-Labs/Site
-> render entry-point role, transition prepend, session ledger, comparison outputs, and receipts

master-records
-> retain usage events, paired trace hashes, receipts, and reconstruction pointers
```

## Archive readiness

This handoff contains the combined gateway, provider, custody, compatibility, authenticated review, delegation, recursive comparison contract, machine-readable adapter role, provider usage-event emitter, validation wiring, authority boundaries, and continuation order. Earlier conversation context is not required. Live CI, provider lifecycle integration, and provider-backed measurement remain pending.
