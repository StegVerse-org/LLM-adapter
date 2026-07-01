# Governed LLM Runtime

## Purpose

`LLM-adapter` converts candidate model output into StegVerse-governed response artifacts.

It does not make the LLM an authority. It classifies the transition, binds the evidence state, and emits a receipt-ready result that can be routed through SDK intake or downstream commit-time governance.

## Definition of Done

The runtime path is installed when:

1. a user query and candidate output can enter the adapter;
2. provider request metadata can be normalized before any model call;
3. retrieval evidence can be represented as pointers and hashes instead of duplicated payloads;
4. the adapter creates a query packet through `stegverse.governed_llm`;
5. the adapter returns `ALLOW`, `DENY`, or `QUARANTINE`;
6. read-only answers receive response receipts;
7. action-bearing outputs are quarantined until commit-time authority is established;
8. stale, revoked, or superseded evidence is quarantined for fresh retrieval;
9. the result contains a reconstruction summary for future continuity search.

## Runtime Flow

```text
provider request envelope
  -> query extraction
  -> allowed source map
  -> evidence pointers
  -> SDK governed query packet
  -> candidate model output
  -> adapter decision
  -> SDK governed response receipt
  -> reconstruction summary
  -> user or downstream route
```

## Provider Request Boundary

`llm_adapter.provider_request` creates a hashable provider request envelope.

The envelope records:

```text
provider
model
messages
purpose
allowed_sources
temperature
metadata
request_hash
```

It does not execute the provider call and does not store credentials.

## Retrieval Evidence Boundary

`llm_adapter.retrieval_evidence` creates evidence pointers from fixture data or future retrieval layers.

The evidence pointer records:

```text
source_type
pointer
content_hash
retrieved_at
freshness
authority_scope
notes
```

It does not require copying full source payloads into the response receipt.

## Decision Rules

| Condition | Decision | Meaning |
| --- | --- | --- |
| Empty output | `DENY` | Nothing can be admitted without emitted content. |
| Low-risk read-only candidate | `ALLOW` | The response may be returned with reconstruction receipt. |
| High-risk/action-bearing candidate | `QUARANTINE` | The output needs downstream commit-time standing before consequence attaches. |
| Stale, revoked, or superseded evidence | `QUARANTINE` | History may be reconstructable, but current authority requires fresh retrieval. |

## Usage

```python
from llm_adapter import (
    GovernedLLMAdapter,
    build_provider_request,
    evidence_from_payload,
)

request = build_provider_request(
    provider="example",
    model="example-model",
    messages=[{"role": "user", "content": "What changed since the last response?"}],
    allowed_sources=("receipt_index", "model_knowledge"),
)

evidence = evidence_from_payload(
    source_type="receipt",
    pointer="master-records://example/receipt/1",
    payload={"state": "current"},
)

adapter = GovernedLLMAdapter(default_provider=request.provider, default_model=request.model)

result = adapter.govern_response(
    query=request.user_query,
    candidate_output="The earlier response is reconstructable but requires fresh retrieval before execution.",
    allowed_sources=request.allowed_sources,
    evidence=(evidence,),
    policy={"policy": "read-only"},
    delegation={"adapter": "read"},
)

print(result.decision)
print(result.response_receipt)
print(result.reconstruction)
```

## Boundary

```text
The provider request is not execution.
The adapter governs candidate output.
The SDK provides shared packet and receipt contracts.
Continuity search reconstructs historical state.
Commit-time governance determines whether consequence may attach.
```
