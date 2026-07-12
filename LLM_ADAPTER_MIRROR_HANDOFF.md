# LLM Adapter Mirror Handoff

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat request-response transport with durable custody continuity
Phase: persistent-production-blueprint-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_DEPLOYMENT_VALIDATION_PENDING
```

## Current path

```text
StegVerse-Labs/Site Ecosystem Chat
-> canonical SITE_INPUT transition identity
-> POST /api/ecosystem-chat
-> governed validation and rate limit
-> bridge/delegation/standing bounded progression
-> active STEGVERSE_AI_ENTITY response generation
-> final response receipt
-> SQLite transition persistence
-> Master-Records custody queue
-> authenticated custody submission
-> lifecycle lookup using the same transition identity
```

## Installed service surfaces

```text
llm_adapter/ecosystem_chat_gateway.py
llm_adapter/governed_chat_pipeline.py
llm_adapter/transition_store.py
llm_adapter/master_records_client.py
llm_adapter/custody_worker.py
tests/test_ecosystem_chat_gateway.py
tests/test_governed_chat_pipeline.py
tests/test_transition_store_and_custody.py
tests/test_production_gateway_blueprint.py
render.yaml
render-production.yaml
pyproject.toml
```

The service exposes:

```text
GET  /health
POST /api/ecosystem-chat
GET  /api/transitions/{transition_id}
```

## Persistence profiles

Validation profile:

```text
render.yaml
plan: free
STEGVERSE_TRANSITION_DB=/tmp/stegverse-ecosystem-chat.db
STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS=false
```

Production profile:

```text
render-production.yaml
plan: starter
persistent disk: /var/data
STEGVERSE_TRANSITION_DB=/var/data/stegverse-ecosystem-chat.db
STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS=true
```

The production blueprint retains the custody worker and requires separately configured endpoint, bearer token, and hostname allowlist values.

## Custody contract

```text
SQLite persistence != Master-Records custody
PENDING/RETRY queue state != RECORDED
RECORDED requires a remote identity-matched custody receipt
```

A record is marked `RECORDED` only when the response preserves:

```text
transition_id
run_id
final_receipt_id
custody_status = RECORDED
custody_receipt_id present
master_record_ref present
reconstruction_status = PASS
```

Any mismatch leaves the record in `RETRY`; no custody receipt is invented. The startup worker retries pending records when custody configuration is present.

## Authority boundary

```text
Gateway intake receipt != final response receipt
Final response receipt != repository mutation authority
SQLite persistence != Master-Records custody
Custody submission != custody admission
Custody admission requires remote receipt
Native executor ACTIVE != blanket per-transition authority
Gateway does not mutate repositories
```

## Next task

```text
1. Verify current-main gateway, pipeline, storage, custody, and production-blueprint tests.
2. Deploy render-production.yaml.
3. Deploy master-records/orchestration/render-custody-production.yaml.
4. Configure endpoint, token, receipt key, and hostname allowlist.
5. Run tools/verify_live_ecosystem_chat_custody_roundtrip.py from orchestration.
6. Require one observed transition to reach RECORDED with identity continuity before public activation claims.
7. Add governed provider-backed answer generation only after provider policy, cost, and credential boundaries are installed.
```

## Archive readiness

This handoff contains the gateway lifecycle, persistent production profile, custody queue, remote submission, recovery, boundaries, and continuation order. Earlier conversation context is not required.
