# DeepSeek Interlock/InTr Transport Mirror Handoff

Updated: 2026-09-06  
Repository: `StegVerse-org/LLM-adapter`  
Issue / PR: `#289`  
Canonical branch: `main`  
State: `COMPLETE_RELEASED_SOURCE`  
Authority effect: `NONE_TRANSPORT_ONLY`

## Source of truth

This is the scoped continuation record for `LLMA-DEEPSEEK-INTR-TRANSPORT-289`. It is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md` and the existing canonical runtime/Interlock/InTr authority split.

The canonical sovereign local route remains independently sufficient and unchanged. DeepSeek is optional hosted-provider interoperability only.

## Completed integration

```text
PR: #289
validated_head: 3811b9d47e8eb90818ca6f5ce32a25473ff1dd5a
merge_commit: 6eb6603c8a31c0efb46ab58fed47ce304b5733cd
dedicated_validation_run: 34066526167 SUCCESS
repository_validation_run: 34066526101 SUCCESS
DeepSeek transport tests: 8/8 PASS
DeepSeek executor/egress tests: 6/6 PASS
repository validation steps: 71/71 PASS
source claim: COMPLETE_RELEASED_SOURCE
```

The source implementation claim is released because exact-head validation and merge are complete. This does **not** release runtime, provider credential, activation, publication, tag, or product-release authority.

## Machine preflight

PASS with these constraints preserved:

```text
canonical sovereign route replaced: false
new heartbeat/oscillator: false
new WorkerCoordinator/scheduler: false
new route authority: false
new transition authority: false
new credential authority: false
new custody authority: false
GitHub token runtime authority: false
provider output authority: NONE
README impact: REQUIRED_AND_SATISFIED
scoped capability declaration: COMPLETE
root capability projection: COMPLETE_RECONCILED
```

## Protocol

Protocol identifier: `stegverse.intr.deepseek.transport.v1`

```text
canonical ProviderRequest provenance
-> derive exact outbound DeepSeek payload
-> canonicalize exact outbound bytes and hash them
-> contemporaneous Interlock/InTr ingress evaluation
-> DENY: no credential resolution and no provider call
-> ALLOW: bind exact wire request hash + transition ID + ingress receipt + carrier ref
-> resolve TV/TVC provider credential exactly once at send time
-> call only https://api.deepseek.com/chat/completions
-> validate response and usage fail closed
-> reject any credential echo in provider body or emitted evidence
-> provider output authority_effect NONE
-> canonical provider-usage event
-> existing Master Records provider-usage submission
-> deterministic egress handoff requests ALLOW but assumes none
-> separate Interlock/InTr egress evaluation
-> exact egress ALLOW receipt binds exact provider response hash
```

Ingress ALLOW is not standing authority and cannot be reused as egress authority.

## Provider surface

Provider surface verified during source implementation on 2026-09-06:

```text
base: https://api.deepseek.com
chat: https://api.deepseek.com/chat/completions
models:
  - deepseek-v4-flash
  - deepseek-v4-pro
```

The v1 transport allowlists only that base URL and `/chat/completions`. Legacy aliases are not silently substituted.

## Credential boundary

```text
credential_authority: TV/TVC
credential_class: TV_TVC_PROVIDER_SECRET
credential serialized in envelope: false
credential serialized in provider-usage evidence: false
credential serialized in Master Records event: false
credential serialized in response metadata: false
```

Credential material is accepted only from an externally supplied callable at execution time.

## Installed source

```text
llm_adapter/deepseek_intr_transport.py
llm_adapter/deepseek_intr_executor.py
schemas/deepseek-intr-transport-envelope.schema.json
tests/test_deepseek_intr_transport.py
tests/test_deepseek_intr_executor.py
capability/stegverse-intr-deepseek-transport.capability.json
.github/workflows/validate-deepseek-intr.yml
tasks/LLMA-DEEPSEEK-INTR-TRANSPORT-289.json
docs/DEEPSEEK_INTR_TRANSPORT_MIRROR_HANDOFF.md
README.md
adapter.capabilities.json
```

## Fail-closed predicates

1. ingress disposition must equal exact `ALLOW`;
2. ingress receipt must be exact lowercase SHA-256;
3. provider must explicitly identify DeepSeek;
4. model must be one of the explicitly supported current DeepSeek model IDs;
5. endpoint base URL must equal the approved DeepSeek OpenAI-format base;
6. exact outbound bytes must hash to the admitted envelope request hash;
7. credential class remains `TV_TVC_PROVIDER_SECRET` under `TV/TVC`;
8. transport envelope retains `authority_effect=NONE` and `egress_intr_required=true`;
9. provider usage token fields, when present, must be integers;
10. credential material cannot appear in envelope, response metadata, usage evidence, custody evidence, or egress handoff;
11. Master Records acknowledgments cannot escalate authority;
12. egress requires exact `ALLOW`, exact receipt hash format, and exact response-hash binding.

## Evidence semantics

The merged source and exact-head validation prove deterministic transport binding, fail-closed behavior, credential non-persistence, provider-usage construction, Master Records reuse semantics, and exact-response egress verification.

They do **not** prove:

- live DeepSeek execution;
- valid/current TV/TVC credential materialization;
- authentic ingress InTr receipt issuance;
- authentic provider-usage custody/reconstruction;
- authentic egress InTr ALLOW;
- canonical resident runtime execution;
- Ecosystem Chat activation;
- Site activation or downstream publication.

## Release posture

No repository tag or product release is created by this source integration. The root LLM-adapter handoff still prohibits release/tag claims while canonical same-carrier provider execution, custody/reconstruction, immutable activation evidence, Site activation, and required downstream propagation remain incomplete.

## Remaining work

No implementation, schema, test, README, capability-projection, validation, or merge work remains for the DeepSeek source lane.

Separately governed future work may include:

1. optional authentic runtime exercise only when a current task admits DeepSeek and TV/TVC resolves the credential;
2. authentic provider usage through the existing Master Records custody/reconstruction lane;
3. downstream Site/Publisher/wiki projection only when an activation/release gate explicitly requires it.

## Completion accounting

```text
protocol design: COMPLETE
transport source: COMPLETE
executor source: COMPLETE
schema: COMPLETE
deterministic DeepSeek tests: 14/14 PASS
repository validation: 71/71 PASS
scoped capability declaration: COMPLETE
root capability projection: COMPLETE
README: COMPLETE
merge: COMPLETE
source claim: COMPLETE_RELEASED_SOURCE
live DeepSeek execution: NOT CLAIMED
product activation: NOT CLAIMED
scaffolding/stubs in DeepSeek protocol files: 0
```
