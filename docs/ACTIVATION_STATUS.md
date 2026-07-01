# Governed Adapter Activation Status

## Status

`StegVerse-org/LLM-adapter` is adapter-boundary complete.

The repository now contains a complete non-executing governed LLM runtime chain:

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
12. no built-in path performs side effects.

## Capability Manifest

Machine-readable capability status is in:

```text
adapter.capabilities.json
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
an execution handoff executes side effects.
```

## Remaining External Integration Work

The remaining work is outside the adapter boundary:

| Integration | Status | Notes |
| --- | --- | --- |
| Live provider credentials | external | Uses `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. |
| Continuity search service | external | Uses `STEGVERSE_CONTINUITY_SEARCH_URL`. |
| External executor | external | Must be separately governed and reviewed. |
| SDK release alignment | external | Publish compatible SDK package after SDK contract versioning. |

## Activation Conclusion

The adapter can now prove the complete governed path without relying on a live model provider, live continuity service, or execution layer.

That makes it suitable as the runtime adapter boundary for a StegVerse-governed LLM.
