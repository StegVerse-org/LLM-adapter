# Kimi/Moonshot InTr Transport Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-org/LLM-adapter`
Issue: `#292`
Branch: `feat/kimi-intr-runtime-292`

## Authority and scope

This scoped handoff is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md` and the canonical StegVerse Interlock/InTr, TV/TVC, heartbeat/runtime, and Master Records authority boundaries.

```text
provider: kimi / Moonshot AI
protocol: stegverse.intr.kimi.transport.v1
role: OPTIONAL_NON_AUTHORITATIVE_INTEROPERABILITY_TRANSPORT
provider authority effect: NONE
transition authority: external Interlock/InTr
credential/provider-operation authority: TV/TVC
custody/reconstruction authority: Master Records
heartbeat/scheduler/worker authority: NONE
canonical sovereign local route replaced: false
```

## Preflight and collision resolution

The repository already contains the canonical optional-provider pattern implemented for DeepSeek:

```text
llm_adapter/deepseek_intr_transport.py
llm_adapter/deepseek_intr_executor.py
llm_adapter/deepseek_tvc_broker.py
llm_adapter/deepseek_tvc_runtime_executor.py
config/deepseek-runtime-profile.json
```

The Kimi implementation reuses that established pattern and existing shared surfaces rather than installing the standalone-package `shared/` abstraction layer.

Existing shared components reused:

```text
llm_adapter.provider_request.ProviderRequest
llm_adapter.provider_client.ProviderResponse
llm_adapter.provider_usage.build_provider_usage_event
llm_adapter.master_records_usage_submission.submit_provider_usage_to_master_records
StegVerse-Labs/TVC provider profile `kimi`
StegVerse-Labs/TVC secret ref `vault://tvc/providers/kimi/api-key`
StegVerse-Labs/TVC non-exportable provider-operation broker
```

TVC's active credential-model consistency freeze prohibits inventing a new credential wrapper/provider-secret architecture. This lane therefore consumes only the already-existing Kimi provider-operation semantics and never transfers the Kimi credential into LLM-adapter in the production runtime profile.

## Installed source surfaces

```text
llm_adapter/kimi_intr_transport.py
llm_adapter/kimi_intr_executor.py
llm_adapter/kimi_tvc_broker.py
llm_adapter/kimi_tvc_runtime_executor.py
config/kimi-runtime-profile.json
schemas/kimi-intr-transport-envelope.schema.json
capability/stegverse-intr-kimi-transport.capability.json
tests/test_kimi_intr_transport.py
tests/test_kimi_intr_executor.py
tests/test_kimi_tvc_runtime.py
```

The direct credential-resolver transport/executor exists only for compatibility and deterministic isolated testing. It is not the production runtime contract.

## Production runtime composition

```text
external InTr ingress ALLOW bound to exact Kimi request
-> Kimi runtime-profile materialization
-> separately admitted TVC single-use capability lease
-> TVC non-exportable provider-operation request
-> TVC vault broker resolves Kimi credential only at provider-use boundary
-> https://api.moonshot.ai/v1/chat/completions / kimi-k3
-> sanitized provider result + TVC use receipt
-> canonical LLM-adapter provider usage event
-> canonical Master Records provider-usage submission/reconstruction
-> exact response hash handed to external InTr egress
-> external InTr egress ALLOW
-> response may return to StegVerse
```

No ingress ALLOW is synthesized by this transport. No TVC lease is synthesized by this transport. No provider credential is read or persisted by the production LLM-adapter path. No provider output is authoritative.

## README impact

README update is REQUIRED because this change adds an optional hosted-provider runtime profile, endpoint/model semantics, credential-delivery semantics, evidence sequence, and failure behavior. The current README must be patched, not replaced.

## Validation predicates

Source integration is not live activation. Merge readiness requires exact-head CI validating:

- Kimi wire canonicalization and deterministic transport identity;
- exact ingress ALLOW and request-hash binding;
- official endpoint/model locking;
- compatibility-path credential leak guard;
- TVC non-exportable Kimi operation construction;
- lease provider/model/authority boundary validation;
- sanitized TVC result normalization;
- canonical provider-usage/Master Records continuation;
- exact egress response-hash binding;
- capability/schema/runtime-profile consistency;
- validation-only GitHub Actions authority.

## Activation predicates

Status remains `IMPLEMENTED_PENDING_RUNTIME_PROOF` until one authentic same-execution chain proves all of:

1. authentic external InTr ingress receipt;
2. authentic TV/TVC Kimi capability lease and non-exportable operation;
3. authentic Moonshot/Kimi provider response for the bound request;
4. Kimi request/response deterministic hash bindings;
5. authentic TVC use receipt with no credential export;
6. authentic Master Records provider-usage custody/reconstruction;
7. authentic external InTr egress receipt bound to the exact response;
8. common session/transition/transport identifiers across the retained evidence.

Mocks, fixtures, CI success, source merge, runtime-profile presence, and TVC source readiness do not satisfy these predicates.

## Remaining installation / execution ownership

```text
StegVerse-org/LLM-adapter:
  README + adapter capability projection
  exact-head validation / PR integration

StegVerse-Labs/.github runtime owner:
  materialize existing hb-intr-resident runtime profile
  invoke the already-authorized TVC provider-operation path when a valid Kimi lease exists
  retain authentic same-execution runtime receipts

StegVerse-Labs/TVC:
  existing Kimi profile / capsule / lease / non-exportable provider operation only
  no new credential semantics authorized by this task

master-records/orchestration:
  authentic provider-usage custody/reconstruction

Post-activation projections:
  StegIndex
  StegVerse-Labs/Site
  GCAT-BCAT-Engine/Publisher
  StegVerse-Labs/admissibility-wiki
  StegVerse-002/stegguardian-wiki
```

## Current state

```text
issue: OPEN (#292)
source implementation: IN_PROGRESS_BRANCH
credential architecture duplication: NONE
production credential plaintext in LLM-adapter: PROHIBITED
canonical sovereign route replacement: FALSE
live Kimi connector: NOT_YET_PROVEN
release/tag authority: NOT_INFERRED
```
