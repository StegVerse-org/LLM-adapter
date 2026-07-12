# LLM Adapter Mirror Handoff

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat plus External Chat compatibility, review, publication, and bounded mutation services
Phase: external-chat-commit-time-repository-mutation-adapter-installed
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
-> delegated reviewer correction
-> independently delegated publication candidate
-> separately authorized commit-time repository mutation
-> GitHub-confirmed commit/blob identity
-> HMAC-bound mutation receipt
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
llm_adapter/external_publication_mutation.py
tests/test_external_framework_compatibility.py
tests/test_external_review_api.py
tests/test_external_review_publication.py
tests/test_external_publication_mutation.py
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
GET  /api/external-review/reviewer/packages/{package_id}
POST /api/external-review/corrections
POST /api/external-review/publication-transitions
GET  /api/external-review/repository-mutation/health
POST /api/external-review/repository-mutations
```

## Repository mutation contract

The adapter is disabled by default and accepts only stored `ALLOW_PUBLICATION_CANDIDATE` transitions.

```text
STEGVERSE_EXTERNAL_MUTATION_ENABLED=false
```

A mutation requires:

```text
registered mutator token hash
current mutator delegation window
repository:mutate scope
repository:StegVerse-Labs/admissibility-wiki scope
path:docs/external-frameworks/* scope
framework:<framework_id> scope
matching authority, delegation, and policy references
unexpired request freshness
matching publication/correction/package evidence chain
matching expected main-branch head SHA
matching expected target blob SHA
```

The only permitted destination is:

```text
repository: StegVerse-Labs/admissibility-wiki
branch: main
path prefix: docs/external-frameworks/
```

A GitHub write is attempted only after every predicate passes. A mutation receipt is issued only after GitHub returns both the new commit SHA and new blob SHA.

Required external configuration:

```text
STEGVERSE_EXTERNAL_MUTATORS_JSON
STEGVERSE_EXTERNAL_GITHUB_TOKEN
STEGVERSE_EXTERNAL_MUTATION_RECEIPT_KEY
STEGVERSE_EXTERNAL_MUTATION_POLICY_REF
```

No credential is returned to Site or stored in transition or receipt payloads.

## Receipt and authority separation

```text
compatibility receipt != review intake receipt
review intake receipt != correction receipt
correction receipt != publication authority
publication candidate != repository mutation
mutation request != successful mutation
mutation receipt != certification
mutation receipt != standing
provider output != authority
SQLite persistence != Master-Records custody
```

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

Current fixture values remain `CONFIGURED`, not `MEASURED`.

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

Required invariants remain:

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

No new workflow was created.

## Next task

```text
1. Verify current-main External Chat review, publication, and mutation tests.
2. Verify the Admissibility Wiki mutation-receipt schema through Goal 5 aggregate validation.
3. Add live health checks for compatibility, review, reviewer, publication, and mutation surfaces.
4. Deploy with repository mutation disabled and verify all non-mutating routes.
5. Perform one separately authorized staging mutation against a disposable external-framework path.
6. Inspect commit SHA, blob SHA, content hash, and mutation receipt before any production enablement.
7. Continue provider-usage lifecycle integration and measured trace capture in the parallel workstream.
```

## Archive readiness

This handoff contains the combined gateway, compatibility intake, authenticated review, delegated correction, publication candidacy, commit-time-revalidated repository mutation adapter, provider/custody boundaries, recursive comparison, provider usage events, and continuation order. Production mutation remains disabled and live validation remains pending.
