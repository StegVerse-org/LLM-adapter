# Z.ai Interlock/InTr Executor Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-org/LLM-adapter`
Issue: `#278`
State: `COMPLETE_MERGED_VALIDATED / SOURCE_CLAIM_RELEASED`
Authority effect: `NONE_EXECUTION_WRAPPER_ONLY`

## Source of truth

This is the scoped completion record for `LLMA-ZAI-INTR-EXECUTOR-278`. It is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md`, the merged transport task `LLMA-ZAI-INTR-TRANSPORT-276`, the organization runtime authority in `StegVerse-Labs/.github`, existing Interlock/InTr transition authority, TV/TVC credential/route authority, and Master Records custody authority.

The canonical sovereign local route remains independently sufficient and unchanged.

## Validated merge evidence

```text
transport PR: #277
transport merge: 8a763e1257df17403381f5f4c408273d896c3283
executor PR: #279
validated executor head: eee7ef03bc32d5240928c44e8492197103643d52
executor merge: a982236b24182e77e407a02581b176509ebc367d
dedicated Z.ai validation run: 34054884017 SUCCESS
transport tests: 7/7 PASS
executor/egress tests: 6/6 PASS
repository validation run: 34054885878 SUCCESS
repository validation steps: 71/71 PASS
```

## Machine preflight

PASS for the bounded execution-wrapper implementation:

```text
new heartbeat/oscillator: false
new WorkerCoordinator/scheduler: false
new transition authority: false
new credential authority: false
new route authority: false
new custody authority: false
provider output authority: NONE
canonical sovereign route replaced: false
README impact: REQUIRED / SATISFIED
```

README changed in PR #279 because the lane added executable hosted-provider and evidence/custody semantics.

## Installed execution chain

```text
exact ProviderRequest
-> externally observed ingress Interlock/InTr ALLOW
-> `build_zai_intr_envelope` exact request-hash binding
-> ephemeral TV/TVC-resolved provider credential passed only to ZAIHTTPTransport
-> Z.ai provider execution
-> non-authoritative provider response
-> provider usage event using existing provider_usage schema
-> existing Master Records provider-usage submission path
-> execution evidence with egress_intr_required=true
-> external egress Interlock/InTr evaluation
-> `admit_zai_egress` verifies ALLOW + exact response hash + receipt hash
-> downstream consequence may proceed only under the external InTr authority
```

The wrapper does not evaluate governance itself and cannot manufacture either ingress or egress admission.

## Installed surfaces

```text
llm_adapter/zai_intr_transport.py
llm_adapter/zai_intr_executor.py
schemas/zai-intr-transport-envelope.schema.json
tests/test_zai_intr_transport.py
tests/test_zai_intr_executor.py
.github/workflows/validate-zai-intr.yml
tasks/LLMA-ZAI-INTR-TRANSPORT-276.json
tasks/LLMA-ZAI-INTR-EXECUTOR-278.json
docs/ZAI_INTR_TRANSPORT_MIRROR_HANDOFF.md
docs/ZAI_INTR_EXECUTOR_MIRROR_HANDOFF.md
README.md
```

## Fail-closed predicates

1. session, transition, and measurement identifiers must be present;
2. ingress disposition must be exact `ALLOW`;
3. ingress receipt and request hash constraints remain enforced by the merged transport;
4. provider credential is passed only at transport construction and never serialized;
5. provider output remains `authority_effect=NONE`;
6. provider usage uses the existing adapter-owned usage event schema;
7. Master Records response may not grant authority;
8. egress disposition must be exact `ALLOW`;
9. egress receipt hash must be an exact lowercase SHA-256;
10. egress admitted response hash must exactly match the response hash produced by the execution;
11. local egress verification reports `authority_effect=NONE_LOCAL` and identifies Interlock/InTr as the transition authority.

## Evidence semantics

Source and CI prove deterministic binding and fail-closed behavior. They do not prove:

- a live Z.ai provider request;
- current TV/TVC credential materialization;
- production provider route admission;
- authentic Master Records custody/reconstruction;
- live egress InTr ALLOW;
- canonical resident WorkerCoordinator execution;
- Ecosystem Chat activation;
- Site/publication activation.

## Continuation ownership

No source implementation claim remains active for this executor lane. The next candidate is authentic governed runtime execution under the existing authorities:

```text
admitted workload
-> Interlock/InTr ingress ALLOW
-> TV/TVC provider credential/route authority
-> merged Z.ai executor
-> authentic provider-usage custody/reconstruction in master-records/orchestration
-> external egress InTr ALLOW bound to exact response
```

That runtime sequence must not be fabricated or replaced by CI. It remains subject to current machine/authority ownership and credential availability.

## Release boundary

The Z.ai source lane is complete/released at implementation scope. Repository version tagging/release is **not** authorized by this completion because the root handoff still requires directly observed canonical activation evidence before release/tag.

Downstream Site/Publisher/wiki propagation remains gated on immutable verified activation rather than this source merge.

## Completion accounting

```text
transport source: COMPLETE_MERGED_VALIDATED
executor source: COMPLETE_MERGED_VALIDATED
dedicated Z.ai validation: PASS
repository validation: PASS
provider usage integration: COMPLETE
Master Records submission reuse: COMPLETE
egress exact-response binding: COMPLETE
README: COMPLETE
source claim: RELEASED
live Z.ai execution: NOT CLAIMED
live egress admission: NOT CLAIMED
release/tag authorization: NOT_GRANTED
scaffolding/stubs: 0
```
