# DeepSeek Runtime Profile / TVC Broker Mirror Handoff

Updated: 2026-09-07  
Repository: `StegVerse-org/LLM-adapter`  
Primary source integration: `#290 / PR #291`  
TVC-runtime egress verification: `#300 / PR #301`  
Exact TVC lease binding: `#304`  
Canonical branch: `main`  
State: `COMPLETE_RELEASED_SOURCE + EXACT_LEASE_BINDING_VALIDATION_PENDING`  
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
-> provider-usage event + Master Records custody/reconstruction
-> separate canonical StegGate/Interlock egress ALLOW bound to exact response hash
-> TVC-runtime exact-response egress verifier
-> current device
```

The canonical portable StegGate micro-node creates decision evidence; InTr transports the bound request/response and does not synthesize ALLOW. The provider operation occurs only after ingress `ALLOW`, and provider output cannot pass egress without a separate exact-response `ALLOW`.

## Completed source evidence

```text
#291 merge: ca4bc8a2da706c59f91fb6480d5190561cda0473
#291 DeepSeek validation: 34069735573 SUCCESS
#291 repository validation: 34069735593 SUCCESS / 71 of 71
TVC bounded DeepSeek InTr lease: TVC #343 / PR #344 / merge 7e9f73e8faace8dd2c8c8fc373fa8ac0433760c1
#301 merge: f962d75456d217a4dd6f60508b8d63f8ee5f8181
#301 DeepSeek validation: 34071584140 SUCCESS
#301 repository validation: 34071584305 SUCCESS / 71 of 71
```

## Exact lease-binding correction — #304

The TVC lease already binds `model`, `transition_id`, `request_hash`, `ingress_receipt_hash`, `carrier_ref`, and `runtime_profile_id`. Issue #304 makes `llm_adapter/deepseek_tvc_broker.py` verify every one of those fields against the exact admitted `DeepSeekInTrEnvelope` before any broker call. It also requires `credential_authority=TV/TVC`, `credential_material_present=false`, and `second_machine_required=false`.

This closes a lease replay/detachment gap. A valid DeepSeek lease for one admitted transition cannot be reused for another request, ingress receipt, carrier, model, or runtime profile.

## Boundaries

No new heartbeat, oscillator, scheduler, WorkerCoordinator, credential authority, route authority, broker, custody plane, provider adapter, or governance evaluator is introduced. LLM-adapter receives no provider credential material. Another physical machine is not a prerequisite.

## README impact

`NO_ADDITIONAL_CHANGE_REQUIRED` for #300/#304. PR #291 already describes the runtime-profile + TVC non-exportable provider operation and separate exact-response egress requirement. These changes complete and harden that implementation without changing the public architecture.

## Completion predicates

```text
runtime_profile_binding: COMPLETE
TVC non-exportable operation bridge: COMPLETE
TVC bounded production lease: COMPLETE_RELEASED_SOURCE
exact lease-to-envelope binding implementation: COMPLETE
exact lease binding validation: PENDING
provider usage/Master Records continuation: COMPLETE_SOURCE
egress handoff: COMPLETE
TVC-runtime exact-response egress verifier: COMPLETE_MERGED_VALIDATED
resident dispatch/consumption: ACTIVE_IN_.github#1122
live DeepSeek execution: NOT CLAIMED
```

Authentic operational proof still requires one same-execution cycle producing StegGate ingress ALLOW, exact-bound TVC lease/provider use, DeepSeek response, Master Records reconstruction, StegGate egress ALLOW, and exact-response egress admission. Missing runtime evidence must not be converted into a second-machine or new-runtime requirement.
