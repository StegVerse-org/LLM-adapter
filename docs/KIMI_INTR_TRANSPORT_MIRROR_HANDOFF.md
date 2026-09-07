# Kimi/Moonshot InTr Transport Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-org/LLM-adapter`
Primary issue: `#292`
Boundary-correction issue: `#302`
Exact-provider-wire issue: `#307`

## Authority and scope

This scoped handoff is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md` and the canonical StegVerse Universal InTr, Governance/StegCore, TV/TVC, heartbeat/runtime, and Master Records authority boundaries.

```text
provider: kimi / Moonshot AI
protocol: stegverse.intr.kimi.transport.v1
role: OPTIONAL_NON_AUTHORITATIVE_INTEROPERABILITY_TRANSPORT
provider authority effect: NONE
exact-packet transport evidence: Universal InTr / TRANSPORT_COMPLETE
governance disposition: StegCore / ALLOW | DENY | FAIL-CLOSED
credential/provider-operation authority: TV/TVC
custody/reconstruction authority: Master Records
heartbeat/scheduler/worker authority: NONE
canonical sovereign local route replaced: false
```

Universal InTr transport completion is not an ALLOW decision. Governance ALLOW is a separate decision and grants neither execution nor credential authority. A separately valid TVC lease remains required before the provider consequence.

## Existing shared components reused

```text
llm_adapter.provider_request.ProviderRequest
llm_adapter.provider_client.ProviderResponse
llm_adapter.provider_usage.build_provider_usage_event
llm_adapter.master_records_usage_submission.submit_provider_usage_to_master_records
StegVerse-Labs/StegOS external-provider-operation Universal InTr profile
StegVerse-Labs/Governance hosted-llm-provider-operation.v1 profile
StegCore canonical three-layer evaluator
StegVerse-Labs/TVC provider profile `kimi`
StegVerse-Labs/TVC secret ref `vault://tvc/providers/kimi/api-key`
StegVerse-Labs/TVC non-exportable provider-operation broker
```

TVC's credential-model consistency boundary prohibits inventing a second provider-secret architecture. The production lane consumes only the existing Kimi provider-operation semantics and never transfers the Kimi credential into LLM-adapter.

## Installed source surfaces

```text
llm_adapter/kimi_intr_transport.py                    legacy/compat transport primitive
llm_adapter/kimi_intr_executor.py                     compatibility executor
llm_adapter/kimi_governed_admission.py                canonical transport/governance separation
llm_adapter/kimi_tvc_provider_wire.py                  exact TVC->Moonshot provider payload identity
llm_adapter/kimi_tvc_broker.py                         TVC non-exportable provider bridge
llm_adapter/kimi_tvc_runtime_executor.py               compatibility runtime + admitted-envelope execution
llm_adapter/kimi_canonical_runtime.py                  canonical production composition
config/kimi-runtime-profile.json
schemas/kimi-intr-transport-envelope.schema.json
capability/stegverse-intr-kimi-transport.capability.json
tests/test_kimi_intr_transport.py
tests/test_kimi_intr_executor.py
tests/test_kimi_tvc_runtime.py
tests/test_kimi_canonical_runtime.py
tests/test_kimi_tvc_provider_wire.py
```

The older `build_kimi_intr_envelope(... ingress_disposition=...)` and `kimi_wire_*` interfaces are retained only for source compatibility/direct-client tests. Canonical production composition must use `build_governed_kimi_admission` / `execute_canonical_kimi_via_tvc_runtime`, which bind distinct transport and Governance evidence to the exact non-secret JSON payload TVC will serialize to Moonshot.

## Canonical production sequence

```text
exact TVC/Moonshot provider payload bytes
  {model,messages,max_tokens,stream[,response_format]}
-> StegOS Universal InTr external-provider-operation
-> TRANSPORT_COMPLETE + exact terminal transport receipt
-> Governance hosted-llm-provider-operation.v1
-> canonical StegCore ALLOW / DENY / FAIL-CLOSED decision receipt
-> only ALLOW is eligible to continue
-> separately issued TVC single-use capability lease
-> TVC non-exportable provider-operation request
-> TVC vault broker resolves Kimi credential only inside provider-use boundary
-> https://api.moonshot.ai/v1/chat/completions / kimi-k3
-> sanitized provider result + TVC use receipt
-> canonical LLM-adapter provider usage event
-> canonical Master Records provider-usage custody/reconstruction
-> exact response bytes through Universal InTr response transport
-> response may return only after the complete retained evidence chain
```

Neither `TRANSPORT_COMPLETE` nor Governance `ALLOW` is provider execution authority. TV/TVC remains the separate consequence/credential authority.

## Exact request constraint

The current TVC Kimi operation accepts a single prompt string and materializes it as exactly one user message. To preserve exact admitted semantics, Kimi v1 production execution accepts exactly one `user` message and sends that content unchanged. Multi-message or non-user-role chat requests fail closed until TVC exposes a message-preserving chat operation contract. `max_output_tokens` and `response_format` are part of the admitted provider-wire hash; legacy request temperature is not, because TVC does not put temperature on the Moonshot wire.

## Validation predicates

Source integration is not live activation. Merge readiness requires exact-head CI validating:

- legacy Kimi wire compatibility remains isolated from canonical provider-wire identity;
- canonical provider-wire bytes exactly match TVC's `openai_chat_completions` Moonshot payload shape;
- `max_tokens` and JSON response mode change the admitted request hash;
- legacy temperature cannot change the canonical TVC provider-wire hash;
- unsupported message shapes fail closed;
- Universal InTr `TRANSPORT_COMPLETE` required separately from Governance ALLOW;
- Governance DENY/FAIL-CLOSED cannot be replaced by transport success;
- Governance ALLOW cannot replace missing transport completion;
- canonical admission envelope is preserved unchanged through TVC execution;
- exact terminal InTr receipt and Governance decision receipt hashes;
- official endpoint/model locking;
- TVC non-exportable Kimi operation construction;
- lease provider/model/authority boundary validation;
- sanitized TVC result normalization;
- canonical provider-usage/Master Records continuation;
- Master Records custody required before canonical egress;
- exact egress response-hash binding;
- validation-only GitHub Actions authority.

## Activation predicates

Status remains `IMPLEMENTED_PENDING_RUNTIME_PROOF` until one authentic same-execution chain proves all of:

1. authentic Universal InTr ingress `TRANSPORT_COMPLETE` receipt bound to exact TVC/Moonshot provider payload bytes;
2. authentic StegCore Governance decision receipt with `decision=ALLOW`;
3. authentic TV/TVC Kimi capability lease and non-exportable operation;
4. authentic Moonshot/Kimi provider response for the bound request;
5. authentic TVC use receipt with no credential export/log/retention;
6. authentic Master Records provider-usage custody and reconstruction PASS;
7. authentic Universal InTr egress transport completion bound to the exact response;
8. common session/transition/request identifiers across retained evidence.

Mocks, fixtures, CI success, source merge, runtime-profile presence, transport completion alone, Governance ALLOW alone, and TVC source readiness do not satisfy these predicates.

## Remaining execution ownership

```text
StegVerse-Labs/.github:
  existing WorkerCoordinator resident lane
  current claim/fence observation
  consume llm_adapter.kimi_tvc_provider_wire exact bytes/hash
  compose exact InTr -> Governance -> TVC -> Master Records -> InTr execution
  retain authentic same-execution receipts

StegVerse-Labs/TVC:
  existing Kimi capsule/lease/non-exportable provider operation only
  no new credential semantics

master-records/orchestration:
  authentic provider-usage custody/reconstruction

Post-activation projections:
  StegIndex
  StegVerse-Labs/Site
  GCAT-BCAT-Engine/Publisher
  admissibility-wiki
  stegguardian-wiki
```

## Current state

```text
source implementation: EXACT_PROVIDER_WIRE_CORRECTION_COMPLETE_PENDING_CI_MERGE
credential architecture duplication: NONE
production credential plaintext in LLM-adapter: PROHIBITED
transport grants execution authority: FALSE
governance grants execution authority: FALSE
governance grants credential authority: FALSE
canonical sovereign route replacement: FALSE
live Kimi connector: NOT_YET_PROVEN
release/tag authority: NOT_INFERRED
```
