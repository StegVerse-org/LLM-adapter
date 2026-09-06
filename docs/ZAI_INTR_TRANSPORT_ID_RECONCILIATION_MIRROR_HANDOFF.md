# Z.ai InTr Wire Contract Reconciliation Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-org/LLM-adapter`
Issue: `#284`
Branch: `fix/zai-transport-id-284`
State: `SOURCE_RECONCILIATION_IN_PROGRESS`
Authority effect: `NONE_INTERFACE_CORRECTION_ONLY`

## Source of truth

This scoped handoff records newly supplied Z.ai reference-package evidence discovered after the prior Z.ai source claim was released. It is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md`, `docs/ZAI_INTR_RELEASE_MIRROR_HANDOFF.md`, existing Interlock/InTr transition authority, TV/TVC credential/route authority, Master Records custody authority, and canonical resident runtime authority.

The prior Z.ai transport/executor implementation remains complete at its recorded scope. This task does not duplicate `_ref` modules or create a second runtime lane. It reconciles the canonical v1 wire contract before any live Z.ai activation has been claimed.

## Newly observed contract requirements

```text
transport_id pattern: ^zait-[0-9a-f]{64}$
transport_id derivation: "zait-" + sha256(canonical transport basis)
request_hash: exact outbound Z.ai request payload hash
credential resolution: external TV/TVC resolver callable, exactly once at send time
credential persistence: prohibited
provider credential echo: fail closed
provider response hashing: deterministic exact response evidence
pre-egress handoff: explicit, non-authorizing, requested_disposition=ALLOW only
ingress ALLOW: exact/case-sensitive and request-hash-bound
egress ALLOW: exact/case-sensitive and response-hash-bound
custody reply: cannot grant authority
```

The supplied adversarial tests additionally require post-admission request tamper detection, endpoint-profile drift rejection, malformed provider-response rejection, malformed usage rejection, malformed receipt rejection, and secret-material sweeps over structures leaving the executor.

## Machine preflight

```text
canonical sovereign route replaced: false
new heartbeat/oscillator: false
new WorkerCoordinator/scheduler: false
new transition authority: false
new route authority: false
new credential authority: false
new custody authority: false
provider output authority: NONE
live Z.ai execution already observed: false
runtime receipt migration required: false
interface behavior change: true
wire-contract behavior change: true
credential handling change: true
schema change required: true
deterministic/adversarial test change required: true
README impact: REQUIRED
root handoff activation/release semantics: unchanged
```

README impact is required because the externally visible v1 request-identity, transport-identity, credential-lifecycle, and egress-handoff semantics change. No runtime migration is required because canonical handoffs explicitly state that live Z.ai execution has not been claimed.

## Implemented on branch

```text
llm_adapter/zai_intr_transport.py
- namespaced `zait-<sha256>` transport IDs
- exact outbound wire payload/hash helpers
- admission bound to exact wire hash
- exact-once execution-time credential resolver path
- canonical outbound bytes
- provider-output/evidence secret-material guard
- provider response shape/usage validation
- broader ProviderRequest hash retained separately for adapter provenance

llm_adapter/zai_intr_executor.py
- credential resolver passed through to transport
- stronger Master Records authority-escalation rejection
- deterministic pre-egress handoff evidence
- wire request hash and ProviderRequest provenance both retained

schemas/zai-intr-transport-envelope.schema.json
- `transport_id` pattern updated to `^zait-[0-9a-f]{64}$`

tests/test_zai_intr_transport.py
- exact ALLOW
- namespaced deterministic transport identity
- exact wire hash/bytes
- post-admission tamper fail-closed before credential resolution
- endpoint drift
- exact-once credential resolution
- provider credential echo rejection
- malformed usage rejection

tests/test_zai_intr_executor.py
- resolver requirement
- usage/custody/egress handoff evidence
- custody authority non-escalation variants
- exact egress ALLOW + receipt/hash binding

capability/stegverse-intr-zai-transport.capability.json
- subordinate capability declaration
- optional/non-authoritative/fail-closed
- activation.live=false
```

## Known compatibility point still under validation

The supplied reference canonicalizer rejects floating-point values and its fixture represents temperature as an exact string (`"0.2"`). Canonical `ProviderRequest` currently models temperature as a float. This branch does **not** silently alter the repository-wide ProviderRequest API or Z.ai provider typing. The exact canonical bytes actually sent are hash-bound, but numeric canonicalization remains a validation/reconciliation point that must be explicitly resolved or documented before merge if the acceptance contract requires restricted string/scaled-integer numerics.

## README completeness

`README.md` must be updated in this same change set before the preflight can be considered complete. It must state:

- `transport_id` uses `zait-<sha256>`;
- ingress binds the exact outbound Z.ai wire payload hash, while broader ProviderRequest identity can be retained separately as provenance;
- credential material is resolved at execution time through TV/TVC and is not retained in returned artifacts;
- provider credential echo fails closed;
- a deterministic pre-egress handoff requests but never assumes `ALLOW`;
- source validation is not live activation evidence.

## Excluded work

- no `_ref` module duplication into canonical runtime surfaces;
- no hosted-provider activation claim;
- no credential materialization in repository/session artifacts;
- no route or transition authority changes;
- no heartbeat/oscillator changes;
- no Site/Publisher/wiki activation or release claim from source validation alone.

## Completion accounting

```text
bounded mismatches identified: COMPLETE
handoff created/updated: COMPLETE
canonical transport source correction: IMPLEMENTED_ON_BRANCH
canonical executor source correction: IMPLEMENTED_ON_BRANCH
schema correction: IMPLEMENTED_ON_BRANCH
adversarial tests: IMPLEMENTED_ON_BRANCH
subordinate capability declaration: IMPLEMENTED_ON_BRANCH
README: PENDING
numeric canonicalization compatibility: PENDING_VALIDATION_OR_EXPLICIT_DECISION
PR validation: PENDING
merge: PENDING
live Z.ai execution: NOT CLAIMED
runtime activation: NOT CLAIMED
```

This handoff is the current scoped source of truth for issue #284 until merged, superseded, or explicitly released.
