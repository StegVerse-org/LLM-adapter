# LLM Adapter Mirror Handoff

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat request-response transport
Phase: deployable-gateway-service-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_DEPLOYMENT_VALIDATION_PENDING
```

## Current path

```text
StegVerse-Labs/Site Ecosystem Chat
-> canonical SITE_INPUT transition identity
-> POST /api/ecosystem-chat
-> governed gateway validation and rate limit
-> bounded response + gateway intake receipt
-> hybrid-collab-bridge target candidate
-> Ecosystem-Delegation / SPE / orchestration
```

## Installed deployable gateway

```text
llm_adapter/ecosystem_chat_gateway.py
tests/test_ecosystem_chat_gateway.py
render.yaml
pyproject.toml
```

The service exposes:

```text
GET /health
POST /api/ecosystem-chat
```

The request contract requires:

```text
text-only message
session_id
requested route and transition intent
raw_shell_allowed = false
authority_required = true
rate_limit_required = true
receipt_required_for_execution = true
canonical transition_identity
```

The gateway preserves:

```text
transition_id
run_id
event_id
origin_manifest_id
parent_transition_id
previous_receipt_id
```

## Bounded live behavior

```text
normal request
-> bounded gateway response
-> task_status = preview_only
-> GATEWAY_INTAKE_RECEIPT
-> candidate target = hybrid-collab-bridge

restricted administration or credential-shaped input
-> no execution
-> task_status = pending_authority
-> route = Restricted admin

rate limit exceeded
-> HTTP 429
-> Retry-After response
```

## Authority boundary

```text
Gateway receipt != final transition receipt
Gateway response != admissibility
Gateway route != execution authority
Gateway does not mutate repositories
Gateway does not install Master-Records records
Gateway does not claim reconstruction success
```

## Deployment blueprint

`render.yaml` defines the `stegverse-ecosystem-chat-gateway` web service with:

```text
uvicorn llm_adapter.ecosystem_chat_gateway:app
health path: /health
allowed origin: https://stegverse-labs.github.io
bounded hourly rate limit
```

Expected service URL used by Site configuration:

```text
https://stegverse-ecosystem-chat-gateway.onrender.com
```

The repository implementation is deployment-ready. Successful Render creation, health verification, and current-main test evidence remain required before declaring the gateway live.

## Existing supporting surfaces

```text
llm_adapter/transition_candidate.py
llm_adapter/ai_entry_backend_service.py
llm_adapter/free_tier_quota.py
llm_adapter/free_tier_limits.py
scripts/verify_goal4_full.py
```

## Next task

```text
1. Verify current-main tests including tests/test_ecosystem_chat_gateway.py.
2. Deploy the Render blueprint and verify GET /health.
3. Submit a Site request and verify transition_id/run_id round trip.
4. Connect accepted candidates to hybrid-collab-bridge normalization transport.
5. Return orchestration status and final receipt updates to the same chat transition.
```

## Archive readiness

This handoff contains the complete deployable gateway implementation, boundaries, and activation sequence. Earlier conversation context is not required.
