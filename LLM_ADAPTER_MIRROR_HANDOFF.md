# LLM Adapter Mirror Handoff

## Source of truth

This file is the current continuation source for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: governed Ecosystem Chat and External Chat with provider telemetry, authenticated usage retrieval, bounded review, publication, and mutation
Phase: stable-no-manual-handoff-invariants-installed
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
scripts/check_ai_entry_no_manual_tasks.py
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

Workflow run `29228291304` on commit `14ad96565085b52a920d2403a6ff14132140f4e1` established:

```text
Package and gateway checks before no-manual guard: PASS
First failing step: Check no-manual-task wiring
Authenticated usage and External Review steps: SKIPPED
```

The second failure was caused by the checker requiring superseded handoff sentences after the handoff was rewritten around current evidence and continuation language.

## Repairs installed

### External Review focused-test isolation

```text
Commit: bc635306988daad4bbf314774791278103d16ac0
File: tests/test_external_review_api.py
```

The focused External Review tests mount only the External Review router in an isolated FastAPI application. Production remains mounted through `combined_gateway.app`.

### Stable no-manual handoff verification

```text
Commit: 7573f717a3bd4de8945560f31c71926eb5efa463
File: scripts/check_ai_entry_no_manual_tasks.py
```

The guard now validates stable handoff structure and invariants rather than exact transient phase sentences. It requires:

```text
source-of-truth and active-goal sections
combined gateway and usage endpoint surfaces
External Review focused test registration
usage-session contract
non-custody and non-authority boundaries
current evidence state
explicit unobserved green-current-main posture
continuation task list
release boundary
```

No workflow, test, authority, receipt, recovery, provider, usage, review, publication, or mutation validation surface was removed.

A successor workflow result after commit `7573f717a3bd4de8945560f31c71926eb5efa463` has not yet been observed.

## Current evidence state

```text
Usage-session implementation: INSTALLED
Usage-session current-main focused checks: OBSERVED PASS in run 29228025977
External Review focused-test isolation repair: INSTALLED
Stable no-manual guard repair: INSTALLED
Successor green current-main validation: NOT OBSERVED
Same-origin deployment: NOT OBSERVED
Live provider usage submission: NOT OBSERVED
Master-Records usage custody: NOT OBSERVED
```

## Next task

```text
1. Observe the validate run on 7573f717a3bd4de8945560f31c71926eb5efa463 or successor.
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

This handoff preserves the usage-session contract, two observed workflow progressions, External Review test isolation, stable no-manual validation, authority boundaries, remaining evidence gates, and continuation order. Earlier conversation context is not required.
