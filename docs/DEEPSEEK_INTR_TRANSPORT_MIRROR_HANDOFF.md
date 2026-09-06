# DeepSeek Interlock/InTr Transport Mirror Handoff

Updated: 2026-09-06  
Repository: `StegVerse-org/LLM-adapter`  
Issue: `#289`  
Branch: `feat/deepseek-intr-transport-v1`  
State: `SOURCE_IMPLEMENTED / VALIDATION_AND_MERGE_PENDING`  
Authority effect: `NONE_TRANSPORT_ONLY`

## Source of truth

This is the scoped continuation record for `LLMA-DEEPSEEK-INTR-TRANSPORT-289`. It is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md` and the existing canonical runtime/Interlock/InTr authority split.

The canonical sovereign local route remains independently sufficient and unchanged. DeepSeek is optional hosted-provider interoperability only.

## Machine preflight

PASS for bounded source implementation with these constraints:

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
README impact: REQUIRED
```

README change is required because this lane changes provider-interface, transport, failure, credential-boundary, usage-evidence, and egress-governance semantics.

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

Official DeepSeek API documentation observed on 2026-09-06 identifies the OpenAI-format base URL as `https://api.deepseek.com` and current text models as:

```text
deepseek-v4-flash
deepseek-v4-pro
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

## Implemented source

```text
llm_adapter/deepseek_intr_transport.py
llm_adapter/deepseek_intr_executor.py
schemas/deepseek-intr-transport-envelope.schema.json
tests/test_deepseek_intr_transport.py
tests/test_deepseek_intr_executor.py
capability/stegverse-intr-deepseek-transport.capability.json
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
5. endpoint base URL must equal the official DeepSeek OpenAI-format base;
6. exact outbound bytes must hash to the admitted envelope request hash;
7. credential class remains `TV_TVC_PROVIDER_SECRET` under `TV/TVC`;
8. transport envelope retains `authority_effect=NONE` and `egress_intr_required=true`;
9. provider usage token fields, when present, must be integers;
10. credential material cannot appear in envelope, response metadata, usage evidence, custody evidence, or egress handoff;
11. Master Records acknowledgments cannot escalate authority;
12. egress requires exact `ALLOW`, exact receipt hash format, and exact response-hash binding.

## Evidence semantics

Source tests and repository validation can prove deterministic transport binding and fail-closed behavior. They do not prove live DeepSeek execution, valid TV/TVC credential materialization, authentic ingress/egress receipt issuance, Master Records custody/reconstruction, canonical resident execution, Ecosystem Chat activation, or Site activation.

## Remaining work

1. update root README and machine-readable root capability manifest in this same change set;
2. exact-head source validation;
3. merge only on passing validation and preserved authority boundaries;
4. no live-provider or activation claim from merge;
5. downstream projection only after the applicable capability/release gate explicitly requires it.

## Completion accounting

```text
protocol design: COMPLETE
transport source: COMPLETE
executor source: COMPLETE
schema: COMPLETE
deterministic tests: IMPLEMENTED / EXECUTION PENDING
scoped capability declaration: COMPLETE
README/root capability projection: PENDING
exact-head validation: PENDING
merge: PENDING
live DeepSeek execution: NOT CLAIMED
product activation: NOT CLAIMED
scaffolding/stubs in DeepSeek protocol files: 0
```
