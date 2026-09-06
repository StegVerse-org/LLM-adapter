# Z.ai Interlock/InTr Executor Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-org/LLM-adapter`
Issue: `#278`
Branch: `feat/zai-intr-executor-278`
State: `SOURCE_IMPLEMENTED / VALIDATION_AND_MERGE_PENDING`
Authority effect: `NONE_EXECUTION_WRAPPER_ONLY`

## Source of truth

This is the scoped continuation record for `LLMA-ZAI-INTR-EXECUTOR-278`. It is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md`, the merged transport task `LLMA-ZAI-INTR-TRANSPORT-276`, the organization runtime authority in `StegVerse-Labs/.github`, existing Interlock/InTr transition authority, TV/TVC credential/route authority, and Master Records custody authority.

The canonical sovereign local route remains independently sufficient and unchanged.

## Machine preflight

PASS for bounded execution-wrapper implementation:

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

README changed in the same change set because this adds executable hosted-provider and evidence/custody behavior.

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

The wrapper does not call itself an authority and cannot manufacture either ingress or egress admission.

## Implemented surfaces

```text
llm_adapter/zai_intr_executor.py
tests/test_zai_intr_executor.py
tasks/LLMA-ZAI-INTR-EXECUTOR-278.json
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

Source and CI can prove deterministic binding and fail-closed behavior. They do not prove:

- a live Z.ai provider request;
- current TV/TVC credential materialization;
- production provider route admission;
- real Master Records custody receipt;
- live egress InTr ALLOW;
- canonical resident WorkerCoordinator execution;
- Ecosystem Chat activation;
- Site/publication activation.

## Remaining work

1. run exact-head repository validation;
2. merge only if exact-head validation passes;
3. after merge, the next runtime goal is authentic governed execution under an admitted workload using a TV/TVC-resolved credential and real Master Records custody;
4. downstream Site/Publisher/wiki propagation remains gated on verified activation rather than source completion.

## Completion accounting

```text
executor source: COMPLETE
deterministic tests: IMPLEMENTED / EXECUTION PENDING
provider usage integration: COMPLETE
Master Records submission reuse: COMPLETE
egress exact-response binding: COMPLETE
README: COMPLETE
PR validation: PENDING
merge: PENDING
live Z.ai execution: NOT CLAIMED
live egress admission: NOT CLAIMED
scaffolding/stubs: 0
```
