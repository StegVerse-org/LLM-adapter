# LLM Adapter Mirror Handoff

## Source of truth

This file is the current continuation source for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: governed Ecosystem Chat and External Chat with provider telemetry, authenticated usage retrieval, bounded review, publication, and mutation
Phase: external-review-focused-test-isolation-repair-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_CURRENT_MAIN_GREEN_VALIDATION_PENDING
```

## Installed core surfaces

```text
llm_adapter/combined_gateway.py
llm_adapter/ecosystem_chat_gateway.py
llm_adapter/provider_usage.py
llm_adapter/usage_session_api.py
llm_adapter/external_framework_compatibility.py
llm_adapter/external_review_api.py
llm_adapter/external_review_store.py
llm_adapter/external_publication_mutation.py
scripts/verify_usage_session_api.py
scripts/verify_external_publication_staging.py
tests/test_usage_session_api.py
tests/test_external_review_api.py
.github/workflows/validate.yml
```

## Usage-session contract

```text
POST /api/usage/sessions
GET  /api/usage/sessions/{session_id}
```

The endpoint preserves session identity, validates evidence classes and event hashes, deduplicates by `metric_owner + measurement_id`, and returns a bounded retrieval receipt. Local persistence is not Master-Records custody, and retrieval grants no authority or admissibility.

## Observed current-main progression

Workflow run `29228025977` on commit `2498e2daef88d935b3dc7bc3aa846d16cf6c385b` established:

```text
Steps through authenticated usage-session verification and tests: PASS
No-manual-task guard: PASS
External Chat staging posture: PASS
First failing step: Test External Chat compatibility and review
Later steps: SKIPPED
```

The earlier no-manual-task blocker is therefore resolved by observed workflow evidence.

## Latest bounded repair

```text
Commit: bc635306988daad4bbf314774791278103d16ac0
File: tests/test_external_review_api.py
```

The focused External Review tests now mount only the External Review router in an isolated FastAPI application. Production remains mounted through `combined_gateway.app`.

This prevents unrelated gateway routers, middleware, import-time stores, and environment state from changing focused review-contract outcomes. Authentication, delegation, evidence, publication, mutation, and fail-closed behavior remain unchanged.

A successor workflow result after this repair has not yet been observed.

## Current evidence state

```text
Usage-session implementation: INSTALLED
Usage-session current-main focused checks: OBSERVED PASS
External Review focused-test repair: INSTALLED
Successor green current-main validation: NOT OBSERVED
Same-origin deployment: NOT OBSERVED
Live provider usage submission: NOT OBSERVED
Master-Records usage custody: NOT OBSERVED
```

## Next task

```text
1. Observe the validate run on bc635306988daad4bbf314774791278103d16ac0 or successor.
2. Inspect and repair only the next first failing step.
3. Preserve all existing validation surfaces.
4. After green current-main evidence, integrate provider-owned usage submission into the live provider lifecycle.
5. Add Master-Records usage-custody submission after local persistence.
6. Keep production mutation disabled until separately authorized.
7. Establish the authorized same-origin Site retrieval path before enabling live transport.
```

## Release posture

No deployment, live transport activation, Master-Records custody claim, release, tag, or production mutation is authorized by this handoff.

## Archive readiness

This handoff preserves the usage-session contract, observed workflow progression, focused External Review repair, authority boundaries, remaining evidence gates, and continuation order. Earlier conversation context is not required.
