# Governed LLM Runtime

## Purpose

`LLM-adapter` converts candidate model output into StegVerse-governed response artifacts.

It does not make the LLM an authority. It classifies the transition, binds the evidence state, emits a receipt-ready result, and routes consequence-bearing outputs to commit-time authority without executing them.

## Definition of Done

The runtime path is installed when:

1. a user query and candidate output can enter the adapter;
2. provider request metadata can be normalized before any model call;
3. provider responses can be represented as request-bound output envelopes;
4. retrieval evidence can be represented as pointers and hashes instead of duplicated payloads;
5. continuity-search evidence can be resolved through a deterministic boundary;
6. a one-call governed session can join request, provider response, continuity, receipt, reconstruction, and action routing;
7. the adapter creates a query packet through `stegverse.governed_llm`;
8. the adapter returns `ALLOW`, `DENY`, or `QUARANTINE`;
9. read-only answers receive response receipts;
10. action-bearing outputs become non-executing action candidates;
11. action-bearing outputs are quarantined until commit-time authority is established;
12. stale, revoked, or superseded evidence is quarantined for fresh retrieval;
13. the result contains a reconstruction summary for future continuity search.

## Runtime Flow

```text
provider request envelope
  -> provider client boundary
  -> provider response envelope
  -> request-hash match check
  -> query extraction
  -> allowed source map
  -> continuity search boundary
  -> evidence pointers
  -> SDK governed query packet
  -> adapter decision
  -> SDK governed response receipt
  -> reconstruction summary
  -> action route packet
  -> user or downstream route
```

## Governed Session Runner

`llm_adapter.governed_session` provides a single deterministic runtime surface:

```text
run_governed_session
  -> provider request envelope
  -> fixture provider response
  -> fixture continuity search
  -> governed adapter decision
  -> response receipt
  -> reconstruction summary
  -> action route packet
```

This is the preferred local test and demo path until live provider and service-backed continuity-search integrations are installed.

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

## Provider Client Boundary

`llm_adapter.provider_client` defines the provider output seam.

The provider response records:

```text
provider
model
output
request_hash
metadata
response_hash
```

A provider response must match the request hash before the governed session proceeds. Fixture provider clients are deterministic and local; live provider clients should implement the same boundary and return through adapter governance before any user-visible or downstream effect.

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

## Continuity Search Boundary

`llm_adapter.continuity_search` defines the adapter-facing retrieval boundary for prior receipts, historical answers, freshness state, superseding evidence, and reconstruction notes.

The fixture implementation is intentionally local and deterministic:

```text
FixtureContinuitySearch
  -> query
  -> matching fixture evidence
  -> freshness_status
  -> evidence pointers
  -> reconstruction notes
```

A later service-backed continuity-search engine should preserve the same boundary shape while replacing fixture lookup with indexed receipt and state retrieval.

## Commit-Time Action Route Boundary

`llm_adapter.action_router` turns high-consequence output into non-executing action candidates.

The action route records:

```text
route_status
action_candidates
action_candidate_hashes
adapter_decision
adapter_admissibility_status
```

The action candidate records:

```text
action_type
target
basis_hash
requested_by
status
notes
candidate_hash
```

No commit, send, publish, memory mutation, or execution is performed by this router. It only produces a downstream route packet for authority-bearing governance.

## Decision Rules

| Condition | Decision | Meaning |
| --- | --- | --- |
| Empty output | `DENY` | Nothing can be admitted without emitted content. |
| Provider response request hash mismatch | `ERROR` | The governed session fails before adapter governance. |
| Low-risk read-only candidate | `ALLOW` | The response may be returned with reconstruction receipt. |
| High-risk/action-bearing candidate | `QUARANTINE` | The output needs downstream commit-time standing before consequence attaches. |
| Action-bearing output detected | `route_to_commit_time_authority` | The result contains an action candidate but no side effect occurs. |
| Stale, revoked, or superseded evidence | `QUARANTINE` | History may be reconstructable, but current authority requires fresh retrieval. |

## Usage

```python
from llm_adapter import run_governed_session

result = run_governed_session(
    provider="example",
    model="example-model",
    messages=[{"role": "user", "content": "Commit this governed adapter change."}],
    candidate_output="Prepared a patch candidate. Do not commit until authority passes.",
    purpose="execute",
    allowed_sources=("repo_write",),
    policy={"policy": "commit-gated"},
    delegation={"adapter": "read"},
    action_target="repo://StegVerse-org/LLM-adapter",
).to_dict()

print(result["adapter_result"]["decision"])
print(result["action_route"]["route_status"])
print(result["action_route"]["action_candidates"])
```

## Boundary

```text
The provider request is not execution.
The provider response is not authority.
The governed session is not provider execution.
The adapter governs candidate output.
The action route is not execution.
The SDK provides shared packet and receipt contracts.
Continuity search reconstructs historical state.
Commit-time governance determines whether consequence may attach.
```
