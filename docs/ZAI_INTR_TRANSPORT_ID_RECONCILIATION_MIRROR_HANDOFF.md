# Z.ai InTr Wire Contract Reconciliation Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-org/LLM-adapter`
Origin issue: `#284`
Post-merge reconciliation issue: `#286`
Implementation PR: `#285`
State: `COMPLETE_MERGED_VALIDATED / SOURCE_CLAIM_RELEASED`
Authority effect: `NONE_INTERFACE_CORRECTION_ONLY`

## Source of truth

This is the completion record for reconciliation of the user-supplied Z.ai reference package with canonical `stegverse.intr.zai.transport.v1`. It is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md`, `docs/ZAI_INTR_RELEASE_MIRROR_HANDOFF.md`, existing Interlock/InTr transition authority, TV/TVC credential/route authority, Master Records custody authority, and canonical resident runtime authority.

The reconciliation did not install competing `_ref` runtime modules, create a second Z.ai lane, replace the canonical sovereign route, or create transition/route/credential/custody/runtime/publication authority.

## Completed contract reconciliation

Canonical `main` now enforces:

```text
transport_id: zait-<lowercase sha256>
transport identity: deterministic over protocol/transition/wire-request/ingress/carrier/profile
request_hash: hash of exact outbound Z.ai payload bytes
transmitted bytes: exactly the deterministic bytes whose hash was admitted
ProviderRequest hash: retained separately as adapter provenance
credential authority: TV/TVC
credential lifecycle: external resolver callable at send time
credential persistence/serialization: prohibited
provider credential echo: fail closed
endpoint source: admitted endpoint_profile only
ingress disposition: exact case-sensitive ALLOW only
ingress binding: exact transition/request/receipt binding
egress handoff: deterministic, non-authorizing, requested_disposition=ALLOW only
egress admission: separately supplied exact ALLOW + exact response hash
provider output authority: NONE
Master Records custody reply: cannot grant authority
activation.live: false
```

Adversarial validation covers post-admission request tampering, endpoint drift, malformed provider response/usage, malformed receipt hashes, credential echo, custody authority escalation, and egress response mismatch.

## Machine preflight and README completeness

```text
canonical sovereign route replaced: false
new heartbeat/oscillator: false
new WorkerCoordinator/scheduler: false
new transition authority: false
new route authority: false
new credential authority: false
new custody authority: false
runtime receipt migration required: false
README impact for implementation: REQUIRED_AND_SATISFIED_IN_PR_285
README impact for post-merge reconciliation: NO_CHANGE_REQUIRED
aggregate capability impact: REVIEWED_NO_CHANGE_REQUIRED
root activation/release semantics changed: false
```

The standalone declaration `capability/stegverse-intr-zai-transport.capability.json` is the exact v1 capability contract. `adapter.capabilities.json` remains the aggregate projection and already correctly states that the Z.ai lane is optional, TV/TVC-bound, non-authoritative, non-live, and non-activating.

## Numeric canonicalization determination

The supplied reference canonicalizer rejected floating-point hashed structures and used an exact string temperature fixture. Canonical `ProviderRequest` uses numeric provider temperature.

The controlling canonical invariant is stronger for transport integrity: **the exact admitted deterministic payload bytes are the exact transmitted payload bytes**. No post-admission numeric transformation occurs. A repository-wide change from numeric provider temperature to string/scaled-integer typing would be a separate API contract and is not required by this reconciliation.

Determination: `RESOLVED_BY_EXACT_BYTE_BINDING / NO_GLOBAL_PROVIDERREQUEST_TYPE_CHANGE`.

## Merge and validation evidence

```text
origin issue: #284 CLOSED_COMPLETED
implementation PR: #285 MERGED
validated PR head: 26a1322a7c9121f8bec6ef7963484cc8eeba0e03
merge commit: f5df724385d87ba11205119e6c3fa760c7cbf974
PR-head dedicated Z.ai validation: SUCCESS
PR-head full repository validation: SUCCESS
successor-main dedicated Z.ai run: 34064251514 SUCCESS
successor-main dedicated Z.ai check: 101570125107 SUCCESS
successor-main full repository run: 34064251483 SUCCESS
successor-main full repository check: 101570124994 SUCCESS
canonical main source verification: PASS
```

Duplicate push/PR validation runs do not create additional authority; no contradictory failure was observed when the source merge gate was evaluated.

## Installed canonical surfaces

```text
llm_adapter/zai_intr_transport.py
llm_adapter/zai_intr_executor.py
schemas/zai-intr-transport-envelope.schema.json
tests/test_zai_intr_transport.py
tests/test_zai_intr_executor.py
capability/stegverse-intr-zai-transport.capability.json
.github/workflows/validate-zai-intr.yml
README.md
docs/ZAI_INTR_TRANSPORT_ID_RECONCILIATION_MIRROR_HANDOFF.md
```

Source scaffolding/stubs added by this reconciliation: `0`.

## Release and activation boundary

`SOURCE_CLAIM_RELEASED` means the supplied reference package has been reconciled into canonical source, validated, merged, and successor-main validated. It does **not** mean:

- live Z.ai execution occurred;
- TV/TVC materialized a live Z.ai credential;
- a production workload received Z.ai route admission;
- authentic provider-usage custody/reconstruction occurred;
- live egress InTr ALLOW occurred;
- Ecosystem Chat or Site activated;
- repository version tag/release is authorized.

The root handoff remains controlling. No tag/release or downstream Site/Publisher/wiki mutation is authorized by this source reconciliation alone.

## Next integration goal

The remaining Z.ai goal is authentic governed runtime use of the completed lane:

```text
admitted workload
-> external Interlock/InTr ingress ALLOW bound to exact wire request
-> TV/TVC live provider credential/route materialization
-> canonical Z.ai executor
-> authentic provider response + measured usage
-> Master Records provider-usage custody/reconstruction
-> external egress InTr ALLOW bound to exact response
```

That goal is runtime/authority-owned under existing HB/InTr/TVC/Master Records boundaries. It must not be replaced with fabricated receipts, repository secrets, GitHub Actions runtime substitution, or a session-created monitor.

## Completion accounting

```text
reference-package ingestion: COMPLETE
wire-contract reconciliation: COMPLETE_MERGED_VALIDATED
transport implementation: COMPLETE_MERGED_VALIDATED
executor implementation: COMPLETE_MERGED_VALIDATED
schema: COMPLETE_MERGED_VALIDATED
adversarial tests: COMPLETE_MERGED_VALIDATED
capability declaration: COMPLETE_MERGED_VALIDATED
README completeness: SATISFIED
aggregate capability review: COMPLETE_NO_CHANGE_REQUIRED
numeric compatibility determination: COMPLETE
source scaffolding/stubs: 0
source claim: RELEASED
live Z.ai execution: NOT_CLAIMED
runtime activation: NOT_CLAIMED
repository tag/release authorization: NOT_GRANTED
```

This handoff contains the repository/source information needed for continuation. The completed source-reconciliation thread can be archived once issue #286 is merged/closed; subsequent work should resume from the canonical runtime authorities rather than reopening this source implementation.
