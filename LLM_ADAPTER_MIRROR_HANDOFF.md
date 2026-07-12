# LLM Adapter Mirror Handoff

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat request-response transport
Phase: bounded-governed-lifecycle-return-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_DEPLOYMENT_VALIDATION_PENDING
```

## Current path

```text
StegVerse-Labs/Site Ecosystem Chat
-> canonical SITE_INPUT transition identity
-> POST /api/ecosystem-chat
-> governed request validation and rate limit
-> bridge/delegation/standing bounded response progression
-> active STEGVERSE_AI_ENTITY response generation
-> final response receipt
-> lifecycle status lookup
-> same transition identity returned to Site
```

## Installed service surfaces

```text
llm_adapter/ecosystem_chat_gateway.py
llm_adapter/governed_chat_pipeline.py
tests/test_ecosystem_chat_gateway.py
tests/test_governed_chat_pipeline.py
render.yaml
pyproject.toml
```

The service exposes:

```text
GET  /health
POST /api/ecosystem-chat
GET  /api/transitions/{transition_id}
```

## Identity invariant

The gateway and pipeline preserve:

```text
transition_id
run_id
event_id
origin_manifest_id
parent_transition_id
previous_receipt_id
```

Any browser response with mismatched identity is rejected and falls closed to local classification.

## Bounded normal-request lifecycle

```text
DECLARED
-> bridge-decision: ALLOW_NEXT_BOUNDARY
-> delegation-decision: ALLOW_DELEGATION
-> standing-decision: ALLOW_BOUNDED_RESPONSE
-> executor: STEGVERSE_AI_ENTITY ACTIVE
-> action: bounded-chat-response-generation
-> lifecycle_state: COMPLETED
-> final-response-receipt:sha256:...
```

Returned fields include:

```text
task_status = completed_bounded_response
lifecycle_state = COMPLETED
admissibility_result = ALLOW
commit_time_validity = VALID
final_receipt_id
master_record_status = NOT_YET_SUBMITTED
reconstruction_status = PARTIAL
```

`PARTIAL` reconstruction means response, transition, receipts, and hashes are reconstructable within the running gateway process, but durable Master-Records custody has not yet occurred.

## Restricted-request lifecycle

```text
restricted administration or credential-shaped input
-> lifecycle_state = VERIFICATION_REQUIRED
-> task_status = pending_authority
-> final_receipt_id = null
-> no execution or mutation
```

## Authority boundary

```text
Gateway intake receipt != final response receipt
Final response receipt authorizes only the completed bounded response record
Final response receipt != repository mutation authority
Final response receipt != publication authority
Final response receipt != Master-Records custody
Native executor ACTIVE != blanket per-transition authority
Gateway does not mutate repositories
Gateway does not claim durable reconstruction success
```

## Deployment blueprint

`render.yaml` defines `stegverse-ecosystem-chat-gateway` with:

```text
uvicorn llm_adapter.ecosystem_chat_gateway:app
health path: /health
allowed origin: https://stegverse-labs.github.io
bounded hourly rate limit
```

Expected URL:

```text
https://stegverse-ecosystem-chat-gateway.onrender.com
```

## Next task

```text
1. Verify current-main gateway and pipeline tests.
2. Deploy the Render blueprint and verify GET /health.
3. Submit a Site request and verify completed lifecycle and final_receipt_id round trip.
4. Add durable Master-Records submission for completed response relationships.
5. Replace in-memory transition lookup with durable custody-backed lookup.
6. Add a live provider adapter only after provider policy, cost, and credential boundaries are installed.
```

## Archive readiness

This handoff contains the complete deployable gateway, bounded lifecycle pipeline, identity rules, authority boundaries, and continuation order. Earlier conversation context is not required.
