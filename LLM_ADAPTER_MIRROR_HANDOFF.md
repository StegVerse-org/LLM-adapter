# LLM Adapter Mirror Handoff

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: live governed Ecosystem Chat request-response transport with custody continuity
Phase: sqlite-persistence-and-master-records-submission-installed
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
-> authenticated custody submission when configured
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
render.yaml
pyproject.toml
```

The service exposes:

```text
GET  /health
POST /api/ecosystem-chat
GET  /api/transitions/{transition_id}
```

## Persistence contract

Completed and restricted transitions are persisted in SQLite. Completed transitions are placed in a custody queue.

```text
SQLite persistence != Master-Records custody
PENDING/RETRY queue state != RECORDED
RECORDED requires a remote identity-matched custody receipt
```

The deployment blueprint currently uses:

```text
STEGVERSE_TRANSITION_DB=/tmp/stegverse-ecosystem-chat.db
STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS=false
```

Therefore the free Render blueprint provides process-local/restart-limited persistence, not durable cross-redeploy custody. The public health contract reports this explicitly.

## Master-Records client contract

Submission is disabled unless all endpoint requirements are satisfied:

```text
HTTPS endpoint
optional hostname allowlist
bearer token when configured
bounded timeout
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

Any mismatch leaves the record in `RETRY`; no custody receipt is invented.

The startup command runs `llm_adapter.custody_worker` before starting Uvicorn so pending records can resume when the custody endpoint is enabled.

## Identity invariant

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
-> bridge ALLOW_NEXT_BOUNDARY
-> delegation ALLOW_DELEGATION
-> standing ALLOW_BOUNDED_RESPONSE
-> executor STEGVERSE_AI_ENTITY ACTIVE
-> bounded response generation
-> COMPLETED
-> final-response-receipt
-> SQLite persisted
-> custody queue PENDING/RETRY/RECORDED
```

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
1. Verify current-main gateway, pipeline, storage, and custody tests.
2. Deploy the gateway and verify GET /health schema 1.2.0.
3. Deploy master-records/orchestration custody service.
4. Configure STEGVERSE_MASTER_RECORDS_ENDPOINT/TOKEN/ALLOWED_HOSTS.
5. Submit one public chat request and verify PENDING -> RECORDED lifecycle.
6. Move both SQLite stores to persistent disks or managed storage before claiming durability across redeploys.
7. Add governed provider-backed answer generation only after provider policy, cost, and credential boundaries are installed.
```

## Archive readiness

This handoff contains the complete gateway lifecycle, persistence, custody queue, remote submission, recovery, boundaries, and continuation order. Earlier conversation context is not required.
