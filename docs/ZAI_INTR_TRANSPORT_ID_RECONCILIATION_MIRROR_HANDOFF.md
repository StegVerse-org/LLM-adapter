# Z.ai InTr Wire Contract Reconciliation Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-org/LLM-adapter`
Issue: `#284`
Branch: `fix/zai-transport-id-284`
PR: `#285`
State: `SOURCE_IMPLEMENTED / EXACT_HEAD_VALIDATION_PENDING`
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
README impact: REQUIRED_AND_SATISFIED
aggregate capability impact: REVIEWED_NO_CHANGE_REQUIRED
root handoff activation/release semantics: unchanged
```

README impact is satisfied in PR #285 because the externally visible v1 request-identity, transport-identity, credential-lifecycle, and egress-handoff semantics are now documented in the same change set. `adapter.capabilities.json` was reviewed and requires no mutation because its Z.ai projection is intentionally aggregate-level and already states optional, TV/TVC-bound, non-authoritative, non-live, non-activating semantics; the exact v1 wire contract now resides in the subordinate `capability/stegverse-intr-zai-transport.capability.json` declaration. No runtime migration is required because canonical handoffs explicitly state that live Z.ai execution has not been claimed.

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
- subordinate exact-v1 capability declaration
- optional/non-authoritative/fail-closed
- execution-time TV/TVC resolution
- activation.live=false

.github/workflows/validate-zai-intr.yml
- exact Z.ai tests
- subordinate capability/schema invariant validation
- permissions: {}
- credential-bearing environment refusal
- validation authority NONE

README.md
- exact wire request-hash semantics
- zait transport identifier format
- exact-byte send semantics
- execution-time credential resolver
- credential echo failure behavior
- deterministic non-authorizing egress handoff
- numeric compatibility boundary
```

## Numeric canonicalization compatibility determination

The supplied reference implementation rejects floating-point values in its restricted canonicalizer and its fixture represents temperature as an exact string (`"0.2"`). Canonical `ProviderRequest` models temperature as a numeric value and the provider-facing Z.ai API expects a numeric temperature.

For this repository reconciliation, the controlling invariant is **exact admitted bytes equal exact transmitted bytes**. PR #285 computes the wire hash from the same deterministic payload serialization whose bytes are sent to Z.ai. Therefore no post-admission numeric transformation occurs and no hash/transport ambiguity remains.

Changing the repository-wide `ProviderRequest.temperature` type to string/scaled integer would be a broader API change not required to satisfy the Z.ai transport security invariant and is outside #284. The reference package's restricted numeric representation is retained as reference-design evidence, not silently imposed on canonical provider typing.

Determination: `RESOLVED_BY_EXACT_BYTE_BINDING / NO_GLOBAL_PROVIDERREQUEST_TYPE_CHANGE`.

## Excluded work

- no `_ref` module duplication into canonical runtime surfaces;
- no hosted-provider activation claim;
- no credential materialization in repository/session artifacts;
- no route or transition authority changes;
- no heartbeat/oscillator changes;
- no Site/Publisher/wiki activation or release claim from source validation alone.

## Validation posture

An earlier exact implementation head passed the dedicated Z.ai validation, but subsequent capability/workflow reconciliation changed the PR head. Only validation against the newest PR head may authorize merge of this bounded source correction.

Current merge gate:

```text
dedicated Z.ai validation on newest PR head: REQUIRED
full repository validation on newest PR head: REQUIRED
mergeability/conflict check: REQUIRED
runtime activation evidence: NOT A SOURCE-MERGE PREDICATE
```

## Completion accounting

```text
bounded mismatches identified: COMPLETE
handoff created/updated: COMPLETE
canonical transport source correction: IMPLEMENTED_ON_BRANCH
canonical executor source correction: IMPLEMENTED_ON_BRANCH
schema correction: IMPLEMENTED_ON_BRANCH
adversarial tests: IMPLEMENTED_ON_BRANCH
subordinate capability declaration: IMPLEMENTED_ON_BRANCH
capability validation: IMPLEMENTED_ON_BRANCH
README: COMPLETE_ON_BRANCH
aggregate capability review: COMPLETE_NO_CHANGE_REQUIRED
numeric canonicalization compatibility: RESOLVED_BY_EXACT_BYTE_BINDING
PR: #285 OPEN
PR validation: PENDING_EXACT_HEAD
merge: PENDING_VALIDATION
live Z.ai execution: NOT CLAIMED
runtime activation: NOT CLAIMED
source scaffolding/stubs added by reconciliation: 0
```

This handoff is the current scoped source of truth for issue #284 until merged, superseded, or explicitly released.
