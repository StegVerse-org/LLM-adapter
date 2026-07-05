# Governed Adapter Activation Status

## Status

`StegVerse-org/LLM-adapter` is adapter-boundary complete for the non-executing governed runtime path and now includes a bounded free-tier trust response boundary for the StegVerse governed LLM entry point.

The repository contains a complete non-executing governed LLM runtime chain:

```text
provider request
  -> provider response
  -> continuity evidence
  -> governed adapter receipt
  -> action route
  -> commitment request
  -> authority decision
  -> disabled execution handoff
```

The repository also contains a public-entry trust chain:

```text
public user inquiry
  -> bounded free-tier quota envelope
  -> governed LLM adapter request
  -> Site-visible free-tier trust metadata
  -> transition receipt inspection metadata
  -> bounded receipt export / replay / reconstruction limits
  -> upgrade trigger metadata for scale, retention, connectors, premium models, or API depth
```

## Done Definition

This activation layer is considered done when:

1. provider requests are normalized and hashable;
2. provider responses are request-hash bound;
3. fixture providers can run locally;
4. optional HTTP providers fail closed without credentials;
5. fixture continuity search can provide evidence pointers;
6. optional service continuity search fails closed without endpoint configuration;
7. stale evidence produces `QUARANTINE`;
8. action-bearing output produces an action route;
9. action routes produce non-authorizing commitment requests;
10. commitment requests produce non-executing authority decisions;
11. authority decisions produce disabled execution handoffs;
12. no built-in path performs side effects;
13. free-tier quota checks are deterministic and side-effect free;
14. receipt export, replay, reconstruction, retention, and audit-packet limits are deterministic and side-effect free;
15. AI Entry responses expose Site-facing `free_tier_trust` metadata;
16. quota and limit allow states remain non-authorizing and non-admissibility claims.

## Capability Manifest

Machine-readable capability status is in:

```text
adapter.capabilities.json
```

Free-tier trust policy and manifest files are in:

```text
docs/FREE_TIER_TRUST_POLICY.md
examples/free_tier_trust_policy.json
```

## Local Verification

Run unit tests:

```bash
pytest
```

Run fixture CLI:

```bash
stegverse-llm-adapter fixtures/governed_response_fixture.json --pretty
```

Run smoke script:

```bash
python scripts/smoke_governed_session.py
```

Run aggregate adapter checks:

```bash
python scripts/verify_goal4.py
```

Run free-tier checks directly:

```bash
python scripts/verify_free_tier_quota.py
python scripts/verify_free_tier_limits.py
python scripts/verify_ai_entry_free_tier_metadata.py
python -m pytest tests/test_free_tier_quota.py -v
python -m pytest tests/test_free_tier_limits.py -v
python -m pytest tests/test_ai_entry_free_tier_trust_metadata.py -v
```

Expected smoke result:

```json
{
  "status": "PASS",
  "actual": {
    "adapter_decision": "QUARANTINE",
    "authority_decision": "FAIL_CLOSED",
    "commitment_status": "requires_downstream_commit_time_standing",
    "execution_status": "not_executable"
  }
}
```

## Explicit Non-Claims

The adapter does not claim that:

```text
provider output is authority;
service continuity output is authority;
a commitment request grants authority;
an authority decision executes side effects;
an execution handoff executes side effects;
quota availability is admissibility;
receipt export is permanent retention;
replay grants commit-time standing;
reconstruction grants commit-time standing;
upgrading changes admissibility requirements.
```

## Remaining External Integration Work

The remaining work is outside the adapter boundary:

| Integration | Status | Notes |
| --- | --- | --- |
| Live provider credentials | external | Uses `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. |
| Continuity search service | external | Uses `STEGVERSE_CONTINUITY_SEARCH_URL`. |
| External executor | external | Must be separately governed and reviewed. |
| SDK release alignment | external | Publish compatible SDK package after SDK contract versioning. |
| Site display | external | Site may consume AI Entry `free_tier_trust` metadata after mirror validation. |
| SDK quota metadata ingestion | external | SDK may ingest quota/receipt/replay policy metadata after contract alignment. |

## Activation Conclusion

The adapter can now prove the complete governed path without relying on a live model provider, live continuity service, or execution layer.

It can also expose a bounded, Site-facing free-tier trust contract without creating execution authority, provider authority, permanent receipt retention, or commit-time standing.
