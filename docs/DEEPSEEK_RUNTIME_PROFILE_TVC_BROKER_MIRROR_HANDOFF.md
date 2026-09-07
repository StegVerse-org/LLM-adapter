# DeepSeek Runtime Profile / TVC Broker Mirror Handoff

Updated: 2026-09-06  
Repository: `StegVerse-org/LLM-adapter`  
Issue: `#290`  
PR: `#291`  
Canonical branch: `main`  
State: `COMPLETE_RELEASED_SOURCE`  
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
-> stegverse:runtime-profile:llm-adapter-deepseek:v1
-> base stegverse:runtime-profile:hb-intr-resident:v1 materialization
-> existing WorkerCoordinator resident execution
-> TVC single-use non-exportable DeepSeek provider operation
-> vault://tvc/providers/deepseek/api-key remains inside TV/TVC authority
-> DeepSeek provider result without credential material
-> canonical provider-usage event
-> Master Records custody/reconstruction
-> separate Universal InTr egress ALLOW bound to exact response hash
-> current device
```

## Reused surfaces

- `stegverse.intr.deepseek.transport.v1`
- `stegverse:runtime-profile:hb-intr-resident:v1`
- `StegVerse-Labs/TVC/config/provider_operation_profiles.json::deepseek`
- TVC operation `chat_completion_with_usage`
- TVC secret ref `vault://tvc/providers/deepseek/api-key`
- canonical provider usage + Master Records submission
- external InTr ingress/egress authority

## Installed bridge surfaces

```text
config/deepseek-runtime-profile.json
llm_adapter/deepseek_tvc_broker.py
llm_adapter/deepseek_tvc_runtime_executor.py
tests/test_deepseek_tvc_runtime.py
.github/workflows/validate-deepseek-intr.yml
README.md
```

## Boundaries

No new heartbeat, oscillator, scheduler, WorkerCoordinator, credential authority, route authority, broker, custody plane, or provider adapter is introduced. The runtime profile grants no authority. LLM-adapter never receives or persists DeepSeek credential material. Another physical machine, Linux-specific runtime, systemd, or Unix socket path is not a property of the DeepSeek runtime profile.

The existing raw `credential_resolver` DeepSeek transport remains source-compatible for deterministic validation only and is not the production connection contract.

## README impact

`REQUIRED_AND_SATISFIED` in the same merge set. Public DeepSeek semantics now identify the runtime-profile + TVC non-exportable operation as the production connection path.

## Completion predicates

```text
runtime_profile_binding: COMPLETE
tvc_non_exportable_operation_bridge: COMPLETE
provider_usage_master_records_continuation: COMPLETE
egress_handoff: COMPLETE
deterministic_tests: PASS
README: COMPLETE
repository_validation: PASS
merge: COMPLETE
live DeepSeek execution: NOT CLAIMED
```

## Remaining evidence

Source completion removes the Linux/another-machine dependency from the declared DeepSeek connection contract. Authentic operational proof still requires one same-execution cycle producing real InTr ingress, TVC broker/provider use, DeepSeek response, Master Records reconstruction, and exact-response InTr egress evidence. Absence of that evidence must not be converted into a requirement for another physical machine or a new runtime/profile implementation.
