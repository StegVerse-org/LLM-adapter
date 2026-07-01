# Governed LLM Runtime

## Purpose

`LLM-adapter` converts candidate model output into StegVerse-governed response artifacts.

It does not make the LLM an authority. It classifies the transition, binds the evidence state, emits a receipt-ready result, routes consequence-bearing outputs to commit-time authority, builds non-authorizing commitment requests, records non-executing authority decisions, and prepares disabled execution handoffs without executing them.

## Definition of Done

The runtime path is installed when:

1. a user query and candidate output can enter the adapter;
2. provider request metadata can be normalized before any model call;
3. provider responses can be represented as request-bound output envelopes;
4. retrieval evidence can be represented as pointers and hashes instead of duplicated payloads;
5. continuity-search evidence can be resolved through a deterministic boundary;
6. a one-call governed session can join request, provider response, continuity, receipt, reconstruction, action routing, commitment request generation, authority decision capture, and execution handoff generation;
7. the adapter creates a query packet through `stegverse.governed_llm`;
8. the adapter returns `ALLOW`, `DENY`, or `QUARANTINE`;
9. read-only answers receive response receipts;
10. action-bearing outputs become non-executing action candidates;
11. action-bearing outputs create non-authorizing commitment requests;
12. commitment requests receive non-executing authority decisions;
13. authority decisions produce disabled execution handoffs;
14. action-bearing outputs are quarantined until commit-time authority is established;
15. stale, revoked, or superseded evidence is quarantined for fresh retrieval;
16. the result contains a reconstruction summary for future continuity search.

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
  -> commitment request packet
  -> authority decision packet
  -> disabled execution handoff packet
  -> user or external executor boundary
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
  -> commitment request packet
  -> authority decision packet
  -> disabled execution handoff packet
```

This is the preferred local test and demo path until live provider, service-backed continuity-search, and separately reviewed external executor integrations are installed.

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

## Commitment Request Boundary

`llm_adapter.commitment_request` packages routed action candidates into a non-authorizing request for downstream standing checks.

The commitment request records:

```text
status
target
action_route_hash
action_candidates
adapter_reconstruction_hash
provider_request_hash
provider_response_hash
commitment_request_hash
```

A commitment request is not execution authority. It is the handoff object for a downstream governance layer to decide whether the action may attach consequence at commit time.

## Authority Decision Boundary

`llm_adapter.authority_client` evaluates commitment requests without executing them.

The authority decision records:

```text
decision
reason
commitment_request_hash
policy_hash
delegation_hash
authority_decision_hash
```

The default fixture authority client fails closed for action-bearing requests and returns `NOT_REQUIRED` when no commitment request is needed. A configured fixture may return `ALLOW` for tests, but that still does not execute the action.

## Disabled Execution Gateway Boundary

`llm_adapter.execution_gateway` prepares an execution handoff without performing side effects.

The execution handoff records:

```text
status
reason
authority_decision_hash
commitment_request_hash
target
execution_handoff_hash
```

The default gateway never executes. If authority returns `ALLOW`, the handoff status becomes `ready_for_external_executor`; otherwise it remains `not_executable`.

## Decision Rules

| Condition | Decision | Meaning |
| --- | --- | --- |
| Empty output | `DENY` | Nothing can be admitted without emitted content. |
| Provider response request hash mismatch | `ERROR` | The governed session fails before adapter governance. |
| Low-risk read-only candidate | `ALLOW` | The response may be returned with reconstruction receipt. |
| High-risk/action-bearing candidate | `QUARANTINE` | The output needs downstream commit-time standing before consequence attaches. |
| Action-bearing output detected | `route_to_commit_time_authority` | The result contains an action candidate but no side effect occurs. |
| Action route exists | `requires_downstream_commit_time_standing` | A non-authorizing commitment request is emitted. |
| Default action-bearing authority check | `FAIL_CLOSED` | No execution authority is granted by fixture defaults. |
| Read-only authority check | `NOT_REQUIRED` | No commitment request was needed. |
| Authority decision is `ALLOW` | `ready_for_external_executor` | A handoff packet is produced, but the adapter still performs no side effect. |
| Authority decision is not `ALLOW` | `not_executable` | No execution handoff is available beyond a blocked receipt. |
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
print(result["commitment_request"]["status"])
print(result["authority_decision"]["decision"])
print(result["execution_handoff"]["status"])
```

## Boundary

```text
The provider request is not execution.
The provider response is not authority.
The governed session is not provider execution.
The adapter governs candidate output.
The action route is not execution.
The commitment request is not authority.
The authority decision is not side-effect execution.
The execution handoff is not execution.
The SDK provides shared packet and receipt contracts.
Continuity search reconstructs historical state.
Commit-time governance determines whether consequence may attach.
```
