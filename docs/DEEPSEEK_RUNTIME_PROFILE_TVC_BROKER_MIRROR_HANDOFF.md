# DeepSeek Runtime Profile / TVC Broker Mirror Handoff

Updated: 2026-09-07  
Repository: `StegVerse-org/LLM-adapter`  
Primary source integration: `#290 / PR #291`  
TVC-runtime egress verification: `#300`  
Canonical branch: `main`  
State: `COMPLETE_RELEASED_SOURCE + EGRESS_VERIFIER_VALIDATION_PENDING`  
Authority effect: `NONE_EXECUTION_BRIDGE_ONLY`

## Goal

Bind the already-released DeepSeek InTr lane to the existing canonical resident runtime profile and existing TVC non-exportable provider-operation broker so hosted DeepSeek execution does not depend on another user-operated machine or direct credential delivery into LLM-adapter.

## Completed integration

```text
validated_head: ba4c673d3eda9769b122503425efd6ab66c7545f
merge_commit: ca4bc8a2da706c59f91fb6480d5190561cda0473
DeepSeek validation: 34069735573 SUCCESS
repository validation: 34069735593 SUCCESS
repository validation steps: 71/71 PASS
source state: COMPLETE_RELEASED_SOURCE
```

## Canonical connection contract

```text
current device
-> Universal InTr ingress
-> canonical StegGate/Interlock ALLOW receipt
-> stegverse:runtime-profile:llm-adapter-deepseek:v1
-> base stegverse:runtime-profile:hb-intr-resident:v1 materialization
-> existing WorkerCoordinator resident execution
-> TVC single-use non-exportable DeepSeek provider operation
-> vault://tvc/providers/deepseek/api-key remains inside TV/TVC authority
-> DeepSeek provider result without credential material
-> canonical provider-usage event
-> Master Records custody/reconstruction
-> separate canonical StegGate/Interlock egress evaluation bound to exact response hash
-> TVC-runtime exact-response egress admission verifier
-> current device
```

The StegGate decision receipt is the Interlock decision evidence bound into the InTr transport. InTr transport does not synthesize ALLOW; the portable canonical StegGate micro-node evaluates first and the provider operation occurs only after an actual `ALLOW` disposition is retained.

## Reused surfaces

- `stegverse.intr.deepseek.transport.v1`
- `stegverse:runtime-profile:hb-intr-resident:v1`
- canonical `StegVerse-Labs/StegCore` portable StegGate micro-node
- `StegVerse-Labs/TVC/config/provider_operation_profiles.json::deepseek`
- TVC operation `chat_completion_with_usage`
- TVC secret ref `vault://tvc/providers/deepseek/api-key`
- TVC bounded DeepSeek InTr lease from `StegVerse-Labs/TVC#343 / PR #344`
- canonical provider usage + Master Records submission
- external Interlock decision authority at ingress and egress

## Installed bridge surfaces

```text
config/deepseek-runtime-profile.json
llm_adapter/deepseek_tvc_broker.py
llm_adapter/deepseek_tvc_runtime_executor.py
tests/test_deepseek_tvc_runtime.py
.github/workflows/validate-deepseek-intr.yml
README.md
```

Issue #300 extends `llm_adapter/deepseek_tvc_runtime_executor.py` with the missing TVC-runtime exact-response egress verifier. It requires an externally produced `ALLOW`, an exact lowercase SHA-256 receipt hash, and exact equality with the provider response hash. Local verifier authority remains `NONE_LOCAL`.

## Boundaries

No new heartbeat, oscillator, scheduler, WorkerCoordinator, credential authority, route authority, broker, custody plane, provider adapter, or governance evaluator is introduced. The runtime profile grants no authority. LLM-adapter never receives or persists DeepSeek credential material. Another physical machine, Linux-specific runtime, systemd, or Unix socket path is not a property of the DeepSeek runtime profile.

The existing raw `credential_resolver` DeepSeek transport remains source-compatible for deterministic validation only and is not the production connection contract.

## README impact

`NO_ADDITIONAL_CHANGE_REQUIRED` for issue #300. PR #291 already updated the root README to state the runtime-profile + TVC non-exportable operation and separate exact-response egress InTr requirement. Issue #300 supplies the missing verifier implementation without changing those public semantics.

## Completion predicates

```text
runtime_profile_binding: COMPLETE
tvc_non_exportable_operation_bridge: COMPLETE
TVC bounded production lease: COMPLETE_RELEASED_SOURCE (TVC #343/#344)
provider_usage_master_records_continuation: COMPLETE
egress_handoff: COMPLETE
TVC-runtime egress verifier implementation: COMPLETE
egress verifier validation: PENDING
deterministic tests: PENDING_UPDATED_SUITE
README: COMPLETE / NO_ADDITIONAL_CHANGE_REQUIRED
live DeepSeek execution: NOT CLAIMED
```

## Remaining evidence

After issue #300 validates and merges, source completion leaves only the resident dispatch/consumption path and authentic same-execution evidence. Authentic operational proof requires one cycle producing canonical StegGate ingress ALLOW, TVC lease/provider use, DeepSeek response, Master Records reconstruction, canonical StegGate egress ALLOW, and exact-response egress admission. Absence of that evidence must not be converted into a requirement for another physical machine or a new runtime/profile implementation.
