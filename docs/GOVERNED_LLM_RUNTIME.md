# Governed LLM Runtime

## Purpose

`LLM-adapter` converts candidate model output into StegVerse-governed response artifacts.

It does not make the LLM an authority. It classifies the transition, binds the evidence state, and emits a receipt-ready result that can be routed through SDK intake or downstream commit-time governance.

## Definition of Done

The runtime path is installed when:

1. a user query and candidate output can enter the adapter;
2. the adapter creates a query packet through `stegverse.governed_llm`;
3. the adapter returns `ALLOW`, `DENY`, or `QUARANTINE`;
4. read-only answers receive response receipts;
5. action-bearing outputs are quarantined until commit-time authority is established;
6. the result contains a reconstruction summary for future continuity search.

## Runtime Flow

```text
user query
  -> allowed source map
  -> evidence pointers
  -> SDK governed query packet
  -> candidate model output
  -> adapter decision
  -> SDK governed response receipt
  -> reconstruction summary
  -> user or downstream route
```

## Decision Rules

| Condition | Decision | Meaning |
| --- | --- | --- |
| Empty output | `DENY` | Nothing can be admitted without emitted content. |
| Low-risk read-only candidate | `ALLOW` | The response may be returned with reconstruction receipt. |
| High-risk/action-bearing candidate | `QUARANTINE` | The output needs downstream commit-time standing before consequence attaches. |
| Stale, revoked, or superseded evidence | `QUARANTINE` | History may be reconstructable, but current authority requires fresh retrieval. |

## Usage

```python
from llm_adapter import GovernedLLMAdapter

adapter = GovernedLLMAdapter(default_provider="example", default_model="example-model")

result = adapter.govern_response(
    query="What changed since the last response?",
    candidate_output="The earlier response is reconstructable but requires fresh retrieval before execution.",
    allowed_sources=("receipt_index", "model_knowledge"),
    policy={"policy": "read-only"},
    delegation={"adapter": "read"},
)

print(result.decision)
print(result.response_receipt)
print(result.reconstruction)
```

## Boundary

```text
The adapter governs candidate output.
The SDK provides shared packet and receipt contracts.
Continuity search reconstructs historical state.
Commit-time governance determines whether consequence may attach.
```
