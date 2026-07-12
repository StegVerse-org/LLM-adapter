# LLM Adapter Mirror Handoff

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat plus External Chat compatibility, review, publication, bounded mutation, and staging verification
Phase: full-external-chat-validation-workflow-installed
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
scripts/verify_external_publication_staging.py
tests/test_external_framework_compatibility.py
tests/test_external_review_api.py
tests/test_external_review_publication.py
tests/test_external_publication_mutation.py
.github/workflows/validate.yml
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

A mutation requires current mutator identity, token hash, delegation window, repository/path/framework/mutation scopes, matching authority/delegation/policy references, unexpired freshness, complete publication/correction/package evidence, matching main-branch head SHA, and matching target blob SHA.

The only permitted destination is:

```text
repository: StegVerse-Labs/admissibility-wiki
branch: main
path prefix: docs/external-frameworks/
```

A GitHub write is attempted only after every predicate passes. A mutation receipt is issued only after GitHub returns both the new commit SHA and new blob SHA.

## Disposable staging verifier

Installed:

```text
scripts/verify_external_publication_staging.py
```

Default mode is non-mutating. It verifies the deployed mutation-health contract and requires `mutation_enabled = false`.

A real staging mutation requires:

```text
STEGVERSE_STAGING_MUTATION_EXECUTE=true
```

plus explicit gateway, publication-transition, mutator, authority, delegation, policy, expected-head, target-path, content, and token values. The target must be under:

```text
docs/external-frameworks/staging/
```

The verifier accepts success only when the response includes a mutation receipt, commit SHA, new blob SHA, and content SHA-256 while preserving no certification or standing.

## Validation workflow integration

The existing `.github/workflows/validate.yml` now installs:

```text
python -m pip install -e '.[dev]'
```

and executes:

```text
python scripts/verify_external_publication_staging.py
python -m pytest tests/test_external_framework_compatibility.py tests/test_external_review_api.py -v
python -m pytest tests/test_external_review_publication.py tests/test_external_publication_mutation.py -v
```

The staging command runs in its default non-mutating mode because no execution flag or mutation credentials are provided to CI.

Existing recursive comparison, provider usage, provider boundary, free-tier, transition-candidate, recovery, authority, receipt, and Goal 4 checks remain present. No new workflow was created.

## Site deployment evidence

`StegVerse-Labs/Site/scripts/check_external_chat_live_routes.py` now writes:

```text
reports/external-chat-live-verification.json
```

The receipt records each public page and gateway-health observation, timestamp, HTTP status, contract result, failure class, required disabled mutation posture, and non-authority boundary. DNS or network resolution failure is recorded separately and is not treated as deployed success or product failure.

## Receipt and authority separation

```text
compatibility receipt != review intake receipt
review intake receipt != correction receipt
correction receipt != publication authority
publication candidate != repository mutation
mutation request != successful mutation
mutation receipt != certification
mutation receipt != standing
live verification receipt != deployment authority
provider output != authority
SQLite persistence != Master-Records custody
```

## Parallel comparison and usage work

The recursive comparison, entry-point role, and provider-usage event work remains installed and unchanged:

```text
llm_adapter/recursive_comparison.py
llm_adapter/entry_point_role.py
llm_adapter/provider_usage.py
scripts/verify_recursive_comparison.py
scripts/verify_provider_usage.py
tests/test_recursive_comparison.py
tests/test_provider_usage.py
```

Configured values remain distinct from measured values, and provider/usage observations remain non-authorizing.

## Latest validation state

The validation workflow now includes all External Chat compatibility, authenticated review, publication, mutation, and non-mutating staging checks. A current-main green run on this workflow revision has not yet been observed. The current execution environment also could not resolve the public Site and gateway hostnames, so no live deployment result is claimed from that attempt.

## Next task

```text
1. Observe and inspect the current-main validate run containing the External Chat test and staging steps.
2. Repair any first failing step without removing existing comparison, provider-usage, authority, receipt, or recovery checks.
3. Verify the Admissibility Wiki mutation-receipt schema through Goal 5 aggregate validation.
4. Deploy with repository mutation disabled.
5. Run Site live-route verification from an environment with public DNS/network access and retain its receipt.
6. Perform one separately authorized staging mutation under docs/external-frameworks/staging/.
7. Inspect commit SHA, blob SHA, content hash, and mutation receipt before production enablement.
8. Continue provider-usage lifecycle integration and measured trace capture in the parallel workstream.
```

## Archive readiness

This handoff contains the combined gateway, compatibility intake, authenticated review, delegated correction, publication candidacy, commit-time-revalidated mutation adapter, full existing-workflow validation registration, evidence-producing live checks, disposable staging verifier, provider/custody boundaries, comparison and usage work, validation state, and continuation order. Production mutation remains disabled and live validation remains pending.
