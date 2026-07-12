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

## Review authentication and delegation

Submitter intake requires explicit opt-in, a package-only payload, non-empty review scope, the canonical non-authority boundary, and an authenticated request.

Reviewer correction requires a registered reviewer reference, a matching token hash, a current validity window, a delegation reference, field scopes for every reviewed field, and publication-review scope when publication review was requested.

Credentials are not stored in packages, receipts, transition records, or Site state.

## Append-only review behavior

```text
package identity = compatibility receipt + submission SHA-256
same identity / same content = idempotent
same identity / different content = conflict
same challenged receipt / same correction = idempotent
same challenged receipt / different correction = conflict
receipt or submission identity drift = fail closed
expired or out-of-scope delegation = fail closed
```

The service stores only the explicit cooperative-review package. Raw framework artifacts remain excluded by contract.

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

## Deployment profiles

Validation uses temporary SQLite paths for chat and review storage. Production uses persistent paths under `/var/data`.

Both profiles require externally configured submitter authentication, receipt signing, and reviewer registry values.

## Parallel comparison telemetry build

This work supports the Ecosystem Chat governed-vs-recursive comparison test bed without displacing the active review-services goal.

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

Required invariants:

```text
provider_output_is_authority == false
adapter_observation_is_admissibility == false
returned_to_sdk == true
configured_values_are_measured == false
```

Canonical verification:

```bash
python scripts/verify_recursive_comparison.py
python -m pytest tests/test_recursive_comparison.py -v
```

## Observed validation failures and repairs

```text
Workflow: validate
Run: 29191217331
Commit: 4896fb08338b5a28cb9afc142ee85e8bbe6a3fa2
First failing step: Check no-manual-task wiring
Failure class: stale handoff-marker assertion
Repair commit: 89a55c63522f6366ff744aaacc90f58c9deed725

Workflow: validate
Run: 29191480720
Commit: de4f6a31d6a53dd56747fb5bac7bac199749486a
First failing step: Check no-manual-task wiring
Failure class: phase-specific handoff-marker assertion after handoff advancement
Repair commit: 1d924a411a88ef22d1709eca5066b2ce78d1b11f
```

The no-manual-task checker validates stable source-of-truth and authority markers instead of one exact phase label. A green run on the current successor remains required.

## Next task

```text
1. Verify current-main validate, provider, custody, compatibility, external-review, and recursive-comparison tests.
2. Add live provider trace capture behind explicit provider configuration.
3. Add the paired SDK orchestration path consuming governed and recursive results.
4. Add a reviewer-facing console for package lookup and scoped correction requests.
5. Add a separately authorized wiki-publication transition consuming reviewed receipts.
6. Deploy production profiles only under explicit deployment authority.
7. Record live endpoint and CI evidence before public activation claims.
```

## Remaining cross-repository integrations

```text
StegVerse-org/StegVerse-SDK
-> combine governed and recursive route results
-> issue final delta receipt

StegVerse-org/core-node-runtime-demo
-> provide governed route measured telemetry

StegVerse-Labs/Site
-> render route outputs, operation bars, DeltaCost, DeltaLatency, and receipts

master-records
-> retain paired trace hashes, receipts, and reconstruction pointers
```

## Archive readiness

This handoff contains the combined gateway, provider, custody, compatibility, authenticated review, delegation, append-only storage, recursive comparison telemetry contract, latest validation evidence, authority boundaries, and continuation order. Earlier conversation context is not required. Live CI and provider-backed measurement remain pending.
