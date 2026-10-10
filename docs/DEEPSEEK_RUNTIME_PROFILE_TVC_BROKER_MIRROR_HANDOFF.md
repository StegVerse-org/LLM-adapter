# DeepSeek Runtime Profile / TVC Broker Mirror Handoff

Updated: 2026-09-07  
Repository: `StegVerse-org/LLM-adapter`  
Primary source integration: `#290 / PR #291`  
TVC-runtime egress verification: `#300 / PR #301`  
Exact TVC lease binding: `#304 / PR #305`  
Local Master Records usage client: `#310` (removed under #368; usage closes on the local usage ledger + organization-ledger transition receipt)  
Canonical branch: `main`  
State: `COMPLETE_RELEASED_SOURCE` (former `LOCAL_MASTER_RECORDS_ORGANIZATION_RECORD_CLIENT_VALIDATION_PENDING` qualifier retired under #368)  
Authority effect: `NONE_EXECUTION_BRIDGE_ONLY`

## Canonical connection contract

```text
current device
-> Universal InTr ingress
-> canonical StegGate/Interlock ALLOW receipt
-> stegverse:runtime-profile:llm-adapter-deepseek:v1
-> base stegverse:runtime-profile:hb-intr-resident:v1
-> existing WorkerCoordinator
-> TVC single-use DeepSeek lease bound to exact model/transition/request/ingress/carrier/runtime-profile
-> existing TVC non-exportable DeepSeek provider operation
-> vault://tvc/providers/deepseek/api-key remains inside TV/TVC authority
-> DeepSeek result without credential material
-> canonical provider-usage event
-> local usage ledger + organization-ledger transition receipt (usage recording is non-gating)
-> separate canonical StegGate/Interlock egress ALLOW bound to exact response hash
-> TVC-runtime exact-response egress verifier
-> current device
```

The canonical portable StegGate micro-node creates decision evidence; InTr transports the bound request/response and does not synthesize ALLOW. The provider operation occurs only after ingress `ALLOW`, and provider output cannot pass egress without a separate exact-response `ALLOW`.

Provider usage closes on the local usage ledger and the organization-ledger transition receipt. The former LLM-adapter Unix-socket client for `master-records/orchestration/services/master_records_local_provider_usage_broker.py` was removed under #368; Master Records may record the released organization batch downstream, is never in this sequence, and nothing waits on it. LLM-adapter never receives the Master Records bearer or receipt key.

## Completed source evidence

```text
#291 merge: ca4bc8a2da706c59f91fb6480d5190561cda0473
#291 DeepSeek validation: 34069735573 SUCCESS
#291 repository validation: 34069735593 SUCCESS / 71 of 71
TVC bounded DeepSeek InTr lease: TVC #343 / PR #344 / merge 7e9f73e8faace8dd2c8c8fc373fa8ac0433760c1
#301 merge: f962d75456d217a4dd6f60508b8d63f8ee5f8181
#301 DeepSeek validation: 34071584140 SUCCESS
#301 repository validation: 34071584305 SUCCESS / 71 of 71
#305 merge: 57975dd16546e1be2895ab331876c89fbdec6b97
#305 DeepSeek validation: 34071884772 SUCCESS
#305 repository validation: 34071884797 SUCCESS
Master Records local provider-usage broker (downstream recorder, non-gating): merged on master-records/orchestration main under issue #82
```

## Exact lease-binding correction

The TVC lease binds `model`, `transition_id`, `request_hash`, `ingress_receipt_hash`, `carrier_ref`, and `runtime_profile_id`. `llm_adapter/deepseek_tvc_broker.py` verifies every field against the exact admitted `DeepSeekInTrEnvelope` before any broker call. It also requires `credential_authority=TV/TVC`, `credential_material_present=false`, and `second_machine_required=false`.

## Local Master Records usage client — #310 (removed under #368)

Formerly installed source (removed under #368; usage now closes on the local usage ledger + organization-ledger transition receipt):

```text
llm_adapter/master_records_local_usage_record.py     (removed under #368)
tests/test_master_records_local_usage_record.py       (removed under #368)
```

Former success predicates (retired under #368; usage recording never gates execution or egress):

```text
decision = ALLOW_CUSTODY_RESULT
status = CUSTODY_RECORDED
custody_recorded = true
reconstructability = PASS
session_id = exact event session_id
measurement_id = exact event measurement_id
event_sha256 = exact event_sha256
authority_granted = false
admissibility_determined = false
execution_authority = false
publication_authority = false
secret_material_returned = false
credential_material_returned = false
credential_authority = TV/TVC
authority_effect = NONE
```

## Boundaries

No new heartbeat, oscillator, scheduler, WorkerCoordinator, credential authority, route authority, custody authority, provider adapter, or governance evaluator is introduced. LLM-adapter receives no provider or Master Records credential material. Another physical machine is not a prerequisite.

## README impact

`NO_ADDITIONAL_CHANGE_REQUIRED` for #310. The change supplies a local transport adapter for the already-documented provider-usage custody capability; custody semantics, authority, record identity, and public API behavior are unchanged.

## Completion predicates

```text
runtime_profile_binding: COMPLETE
TVC non-exportable operation bridge: COMPLETE
TVC bounded production lease: COMPLETE_RELEASED_SOURCE
exact lease-to-envelope binding: COMPLETE_MERGED_VALIDATED
provider usage event generation: COMPLETE
Master Records local provider-usage broker (downstream, non-gating; not a completion predicate): COMPLETE_SOURCE_MERGED
LLM-adapter local Master Records client: REMOVED under #368 (formerly COMPLETE / validation PENDING)
egress handoff: COMPLETE
TVC-runtime exact-response egress verifier: COMPLETE_MERGED_VALIDATED
resident dispatch/consumption: ACTIVE_IN_.github#1122
live DeepSeek execution: NOT CLAIMED
```

Authentic operational proof still requires one same-execution cycle producing StegGate ingress ALLOW, exact-bound TVC lease/provider use, DeepSeek response, local usage-ledger record and organization-ledger transition receipt, StegGate egress ALLOW, and exact-response egress admission. Missing runtime evidence must not be converted into a second-machine or new-runtime requirement.
