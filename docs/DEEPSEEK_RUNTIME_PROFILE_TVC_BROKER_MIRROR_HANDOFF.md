# DeepSeek Runtime Profile / TVC Broker Mirror Handoff

Updated: 2026-09-06  
Repository: `StegVerse-org/LLM-adapter`  
Issue: `#290`  
Branch: `feat/deepseek-runtime-profile-tvc-broker-290`  
State: `SOURCE_IMPLEMENTED / VALIDATION_PENDING`  
Authority effect: `NONE_EXECUTION_BRIDGE_ONLY`

## Goal

Bind the already-released DeepSeek InTr lane to the existing canonical resident runtime profile and existing TVC non-exportable provider-operation broker so hosted DeepSeek execution does not depend on another user-operated machine or direct credential delivery into LLM-adapter.

## Canonical connection contract

```text
current device
-> Universal InTr ingress
-> stegverse:runtime-profile:hb-intr-resident:v1 materialization
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

## New local bridge surfaces

```text
config/deepseek-runtime-profile.json
llm_adapter/deepseek_tvc_broker.py
llm_adapter/deepseek_tvc_runtime_executor.py
tests/test_deepseek_tvc_runtime.py
```

## Boundaries

No new heartbeat, oscillator, scheduler, WorkerCoordinator, credential authority, route authority, broker, custody plane, or provider adapter is introduced. The runtime profile grants no authority. LLM-adapter never receives or persists DeepSeek credential material. Another physical machine, Linux-specific runtime, systemd, or Unix socket path is not a property of the DeepSeek runtime profile.

The existing raw `credential_resolver` DeepSeek transport remains source-compatible for deterministic validation only and is not the production connection contract after this lane merges.

## README impact

REQUIRED because the public DeepSeek credential/execution semantics change from direct execution-time credential resolution to the canonical runtime-profile + TVC non-exportable provider operation. README update must be in the same merge set.

## Current predicates

```text
runtime_profile_binding: COMPLETE
tvc_non_exportable_operation_bridge: COMPLETE
provider_usage_master_records_continuation: COMPLETE
egress_handoff: COMPLETE
deterministic_tests: IMPLEMENTED / EXECUTION PENDING
README: PENDING
repository_validation: PENDING
merge: PENDING
live DeepSeek execution: NOT CLAIMED
```
