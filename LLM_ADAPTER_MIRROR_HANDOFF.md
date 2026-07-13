# LLM Adapter Mirror Handoff

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat plus External Chat compatibility, provider telemetry, authenticated usage retrieval, review, publication, bounded mutation, and staging verification
Phase: authenticated-usage-session-endpoint-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_DEPLOYMENT_VALIDATION_PENDING
```

## Current service paths

```text
Ecosystem Chat
-> canonical transition identity
-> governed validation and optional provider
-> provider-owned usage event
-> authenticated usage-session submission
-> same-origin authenticated usage retrieval
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
llm_adapter/provider_usage.py
llm_adapter/usage_session_api.py
llm_adapter/external_framework_compatibility.py
llm_adapter/external_chat_api.py
llm_adapter/external_review_store.py
llm_adapter/external_review_api.py
llm_adapter/external_publication_mutation.py
scripts/verify_usage_session_api.py
scripts/verify_external_publication_staging.py
tests/test_usage_session_api.py
.github/workflows/validate.yml
render.yaml
render-production.yaml
```

## HTTP routes

```text
GET  /health
POST /api/ecosystem-chat
GET  /api/transitions/{transition_id}
POST /api/usage/sessions
GET  /api/usage/sessions/{session_id}
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

## Authenticated usage-session endpoint

Installed:

```text
llm_adapter/usage_session_api.py
scripts/verify_usage_session_api.py
tests/test_usage_session_api.py
```

Machine submission:

```text
POST /api/usage/sessions
Authorization: Bearer ${STEGVERSE_USAGE_SUBMIT_TOKEN}
```

Submission accepts one session-bound batch of usage events and validates:

```text
session identity
measurement identity
transition identity
entry-point identity
metric owner
MEASURED / CONFIGURED / DERIVED / UNAVAILABLE evidence class
UNAVAILABLE => value is null
event SHA-256 when supplied
metric_owner + measurement_id uniqueness
```

Exact repeated events are idempotent. Reusing one owner/measurement identity with changed session or event content fails with `409 measurement_identity_conflict`.

Browser retrieval:

```text
GET /api/usage/sessions/{session_id}
```

Retrieval requires either:

```text
same-origin cookie: stegverse_session_id == requested session_id
or
X-SteGVerse-Session == requested session_id
```

No Site-configured bearer token, query token, local-storage token, or rendered secret is required. Missing or mismatched session identity fails closed.

Response contract:

```text
schema = stegverse.usage.session.v1
source_class = LIVE_USAGE_API
requested session identity preserved
events = ordered array
retrieval_receipt required
authority_granted = false
custody_recorded = false
```

The route is mounted into `llm_adapter.combined_gateway`.

## Site contract alignment

The installed endpoint matches the prepared Site route and response contract:

```text
GET /api/usage/sessions/{session_id}
same-origin session authentication
stegverse.usage.session.v1
LIVE_USAGE_API
mandatory retrieval receipt
authority_granted=false
custody_recorded=false
```

The implementation does not enable Site live transport, configure browser credentials, claim same-origin deployment, or claim Master-Records custody. Deployment topology must place the endpoint behind the authorized same-origin gateway or proxy before browser credentials can be used safely.

## Usage authority boundary

```text
provider usage event != authority
usage submission != custody
SQLite usage persistence != Master-Records custody
usage retrieval != admissibility
retrieval receipt != final response receipt
retrieval receipt != custody receipt
session identity possession != execution authority
```

## Repository mutation contract

The adapter remains disabled by default and accepts only stored `ALLOW_PUBLICATION_CANDIDATE` transitions.

```text
STEGVERSE_EXTERNAL_MUTATION_ENABLED=false
```

A mutation requires current mutator identity, token hash, delegation window, repository/path/framework/mutation scopes, matching authority/delegation/policy references, unexpired freshness, complete publication/correction/package evidence, matching main-branch head SHA, and matching target blob SHA.

The only permitted destination remains:

```text
repository: StegVerse-Labs/admissibility-wiki
branch: main
path prefix: docs/external-frameworks/
```

A GitHub write is attempted only after every predicate passes. A mutation receipt is issued only after GitHub returns both the new commit SHA and new blob SHA.

## Validation workflow integration

The existing `.github/workflows/validate.yml` includes:

```text
python scripts/verify_usage_session_api.py
python -m pytest tests/test_usage_session_api.py -v
```

Existing recursive comparison, provider usage, provider boundary, External Chat, mutation, free-tier, transition-candidate, recovery, authority, receipt, and Goal 4 checks remain present. No workflow was added.

The usage verifier proves locally:

```text
machine-authenticated submission succeeds
unauthenticated submission fails
unauthenticated retrieval fails
matching session retrieval succeeds
response schema and source class match Site contract
retrieval receipt preserves non-authority and non-custody posture
```

## Latest observed validation progression

```text
Run ID: 29225358446
Commit: 2bf56ba34212df9a19682163cdcb8f72da2e7e2c
Workflow/job: validate / validate
Result: FAILED
First failing step: Check no-manual-task wiring
Earlier steps passed: package init, micro-node return path, provider boundary, backend service, endpoint, service wrapper
Failure class: stale handoff-marker validation
```

The checker still required earlier handoff wording while the current handoff uses the authenticated usage-session authority vocabulary. The bounded repair is installed:

```text
Commit: 3c5eb2cb8d6f8a08b7d1fee9ad974ff506379366
File: scripts/check_ai_entry_no_manual_tasks.py
Repair: align stable handoff markers with provider usage, SQLite usage persistence, and current-main observation language
```

No validation surface was removed or bypassed. A completed successor run containing the repaired guard and usage-session verification has not yet been observed.

## Disposable staging verifier

Installed:

```text
scripts/verify_external_publication_staging.py
```

Default mode remains non-mutating. A real staging mutation still requires `STEGVERSE_STAGING_MUTATION_EXECUTE=true` and explicit authorized inputs under `docs/external-frameworks/staging/`.

## Latest validation state

```text
Usage session API implementation: installed
Combined gateway route mounting: installed
Verifier and tests: installed
Existing workflow integration: installed
First current-main validation blocker: repaired
Successor current-main green validation: not observed
Same-origin deployed topology: not observed
Live provider-owned event submission: not observed
Master-Records usage custody receipt: not observed
```

The absence of visible successor validation or deployment evidence is not treated as success.

## Next task

```text
1. Observe and inspect the successor current-main validate run after commit 3c5eb2cb8d6f8a08b7d1fee9ad974ff506379366.
2. Repair the next first failing step without removing existing validation surfaces.
3. After a green destination run, integrate automatic provider-owned usage submission into the live provider lifecycle.
4. Add Master-Records usage-custody submission after local usage persistence.
5. Deploy the combined gateway with repository mutation disabled only under explicit deployment authority.
6. Establish an authorized same-origin gateway/proxy for Site browser retrieval.
7. Run the Site usage-endpoint conformance suite against the deployed endpoint.
8. Preserve retrieval and custody receipts before enabling Site live transport.
```

## Release posture

No deployment, same-origin proxy activation, credential configuration, Site transport activation, Master-Records custody claim, release, merge, tag, or production mutation is authorized by this handoff.

## Archive readiness

This handoff contains the combined gateway, authenticated usage-session submission and same-origin retrieval contract, provider-usage boundaries, Site contract alignment, External Chat compatibility, review, publication, mutation, workflow registration, observed validation progression, bounded repair, validation state, and continuation order. Earlier conversation context is not required.
