# StegVerse LLM Adapter

The StegVerse LLM Adapter is the machine-readable translation and provider-boundary component between governed StegVerse requests and model/runtime execution.

Its canonical production path is sovereign and credential-neutral at the route boundary: TC/TVC owns credential semantics and route authority, and the canonical local route requires credential class `NONE`.

## Canonical production path

```text
StegVerse request
-> LLM-adapter governed consumer
-> canonical StegGate runtime identity validation
-> governed transition package
-> StegGate + coherence evaluation
-> canonical heartbeat-owned local model process
-> persistent local runtime proof
-> TVC route evaluation
-> ROUTE_ADMITTED / credential_requirement NONE
-> private or loopback StegVerseLocalHTTPProviderClient
-> provider response + measured usage
-> provider-usage persistence
-> Master Records custody/reconstruction
-> same-execution transition reconstruction
```

The adapter does not own the model process, heartbeat, route authority, or Master Records custody.

Canonical ownership:

```text
local model/runtime: StegVerse-002/micro-node-runtime#16/#22
heartbeat/carrier lifecycle: StegVerse-Labs/.github#60 / SHWP-ECOSYSTEM-CHAT-INFERENCE-001
credential semantics: TC/TVC
route authority: StegVerse-Labs/TVC
provider transport/usage evidence: StegVerse-org/LLM-adapter
custody/reconstruction: master-records/orchestration
```

## Ecosystem Chat distributed LLM service

Until a fully realized native Ecosystem Chat LLM exists, the intended LLM capability is a **distributed service across named model sources**. A canonical Ecosystem Chat request may be represented as a deterministic workload that identifies one or more named sources, binds every contribution to the existing `ProviderRequest` / `ProviderResponse` envelopes, retains source-specific provenance and usage evidence, and packages the contribution set for the existing governance path.

```text
canonical Ecosystem Chat request
-> distributed workload descriptor
-> named source selection
-> one or more source-bound ProviderRequest / ProviderResponse pairs
-> normalized contribution envelopes
-> disagreement / refusal / uncertainty retained as evidence
-> reconciliation request for the existing governance path
-> governed disposition + result
-> source-bound provenance / receipt
-> Master Records custody/reconstruction
```

Supported source-level routing declarations are `single`, `parallel`, `sequential`, `challenge`, and `fallback`. These declarations describe workload execution intent only. They do not create truth by voting, grant admission, or make any model the governance authority.

Bounded executor support is layered separately. `single`, `parallel`, and `fallback` can be executed over explicitly injected `ProviderClient` instances. `parallel` means independent fan-out over the same canonical input with deterministic retained result ordering; it does not grant scheduler or concurrency authority. Missing or failing optional sources produce explicit `FAILED` contribution evidence, provider refusal remains `REFUSED`, and fallback proceeds in declared workload order until a source returns. `sequential` and `challenge` fail closed until a separately governed derived-input/prompt-construction contract exists. Fixture-provider execution validates this execution mechanism only; it is not evidence of live external named-source execution.

The canonical sovereign local/private route remains independently sufficient for Ecosystem Chat operation. Optional named external sources may expand capability, comparison, specialization, or fallback behavior, but they must not become mandatory third-party production dependencies. Provider credentials are deployment/runtime configuration and are prohibited from workload, contribution, reconciliation, governed-result, and execution-summary artifacts.

The distributed contract preserves the following distinctions:

```text
model contribution != governed result
model disagreement != failure
model majority != governance authority
provider availability != canonical availability authority
provider credentials != artifact content
source validation != live distributed execution
fixture execution != live external provider execution
parallel fan-out semantics != scheduler authority
```

The unfinished 12-lane analysis may later populate source capability profiles and supply evidence for routing, cost, independence, or comparative behavior. It is useful evidence, not an implementation prerequisite.

The future native Ecosystem Chat LLM is a separate model-development target distinguished by governance that participates in reasoning and generation rather than relying primarily on reactive post-generation barriers:

> **No reactive guardrails. Native governance instead.**

The distributed workload and bounded executor do not claim that native model exists, and they do not create a second governance engine.

Canonical distributed-workload and executor source surfaces:

```text
llm_adapter/distributed_workload.py
llm_adapter/distributed_executor.py
schemas/ecosystem-chat-distributed-llm-workload.schema.json
schemas/ecosystem-chat-llm-contribution.schema.json
schemas/ecosystem-chat-llm-reconciliation-request.schema.json
schemas/ecosystem-chat-governed-result.schema.json
schemas/ecosystem-chat-distributed-llm-execution.schema.json
tests/test_distributed_workload.py
tests/test_distributed_executor.py
scripts/check_distributed_llm_workload.py
scripts/check_distributed_llm_executor.py
docs/DISTRIBUTED_LLM_WORKLOAD_MIRROR_HANDOFF.md
docs/DISTRIBUTED_LLM_EXECUTOR_MIRROR_HANDOFF.md
tasks/LLMA-DISTRIBUTED-LLM-WORKLOAD-272.json
tasks/LLMA-DISTRIBUTED-LLM-EXECUTOR-274.json
```

## Z.ai Interlock/InTr transport and governed execution

Z.ai is supported as an **optional hosted-provider interoperability transport** through `stegverse.intr.zai.transport.v1`. It does not replace the canonical sovereign local route and does not acquire admission, route, credential, custody, heartbeat, scheduler, worker, publication, or availability authority.

```text
canonical ProviderRequest provenance
-> derive exact outbound Z.ai wire payload: model + messages + temperature
-> canonicalize exact outbound payload and compute request_hash
-> contemporaneous Interlock/InTr ingress evaluation
-> DENY: no credential resolution / no provider call
-> ALLOW: bind exact wire request_hash + transition ID + ingress receipt hash + carrier ref
-> derive transport_id as zait-<sha256(canonical transport basis)>
-> resolve TV/TVC provider credential exactly once at execution/send time
-> approved official Z.ai OpenAI-compatible endpoint selected only from admitted endpoint_profile
-> send the exact canonical bytes whose hash was admitted
-> validate provider response and usage fail-closed
-> reject credential material echoed by provider or present in outgoing evidence
-> provider response with authority_effect NONE
-> provider usage event using the existing adapter schema
-> existing Master Records provider-usage submission path, without authority escalation
-> deterministic pre-egress handoff requests ALLOW but never assumes it
-> separate Interlock/InTr egress evaluation
-> exact egress ALLOW receipt must bind the provider response hash
-> only the externally admitted downstream transition may attach consequence
```

The v1 `transport_id` format is `zait-` followed by a lowercase SHA-256 digest. Its digest basis is the protocol version, transition ID, exact wire request hash, ingress receipt hash, carrier reference, and endpoint profile. The envelope `request_hash` binds the exact outbound Z.ai payload rather than the broader adapter `ProviderRequest` object; the broader `ProviderRequest.request_hash` may be retained separately as provenance but is not substituted for the admitted wire hash.

The implementation allowlists the official global general API base `https://api.z.ai/api/paas/v4` and Coding Plan base `https://api.z.ai/api/coding/paas/v4`. Endpoint profile selection is part of the admitted envelope; a runtime configured for one profile cannot execute an envelope admitted for the other. Credentials remain under TV/TVC authority, are resolved through an external callable at send time, and are prohibited from serialized transport envelopes, response metadata, evidence, task records, handoffs, provider-usage events, and egress-admission records. A provider response that echoes the resolved credential is rejected fail-closed before returned evidence is emitted.

`execute_governed_zai` binds the transport to the existing provider-usage and Master Records submission mechanisms. It accepts a TV/TVC credential resolver rather than persisted credential material, produces non-authoritative provider output, and emits an explicit deterministic pre-egress handoff with `requested_disposition=ALLOW`, `egress_intr_required=true`, and `authority_effect=NONE`; this is a request for external evaluation, not an assumed decision. `admit_zai_egress` does not evaluate or grant governance; it verifies an externally produced Interlock/InTr `ALLOW` receipt, an exact SHA-256 receipt identifier, and an admitted response hash equal to the provider response produced by the execution. Its local authority effect is explicitly `NONE_LOCAL`.

The exact outbound bytes are deterministically serialized from the canonical adapter request fields used by the Z.ai payload. Canonical `ProviderRequest` currently represents `temperature` as a numeric value; source validation therefore binds the bytes actually sent, while any future restricted-string/scaled-integer numeric canonicalization contract must be explicitly reconciled rather than silently changing provider typing.

Canonical source surfaces:

```text
llm_adapter/zai_intr_transport.py
llm_adapter/zai_intr_executor.py
schemas/zai-intr-transport-envelope.schema.json
tests/test_zai_intr_transport.py
tests/test_zai_intr_executor.py
capability/stegverse-intr-zai-transport.capability.json
docs/ZAI_INTR_TRANSPORT_MIRROR_HANDOFF.md
docs/ZAI_INTR_EXECUTOR_MIRROR_HANDOFF.md
docs/ZAI_INTR_TRANSPORT_ID_RECONCILIATION_MIRROR_HANDOFF.md
tasks/LLMA-ZAI-INTR-TRANSPORT-276.json
tasks/LLMA-ZAI-INTR-EXECUTOR-278.json
```

Source validation proves fail-closed transport identity, exact wire-byte/hash binding, execution-time credential resolution, credential-redaction checks, usage-evidence, custody-submission, deterministic egress-handoff, and exact-response egress-binding semantics only. It is not live Z.ai execution, route admission, credential materialization, authentic Master Records custody/reconstruction, live egress ALLOW, Ecosystem Chat activation, or Site activation evidence.

## No GitHub-token production dependency

GitHub repository access is not part of the production inference path.

```text
github_token_required_for_production: false
github_actions_production_role: false
credential_authority_model: TC/TVC
canonical_local_route_credential_requirement: NONE
```

GitHub Actions, Render, Cloudflare, Vercel, GitHub Models, OpenAI, Anthropic, and Z.ai are not canonical production heartbeat, inference, route, custody, or availability authorities. Optional hosted-provider interoperability lanes are separate from the canonical sovereign local route.

## Local model/runtime

The descriptive "select a local model/runtime" step has been superseded by an executable local-runtime path owned by `StegVerse-002/micro-node-runtime`.

The canonical implementation includes runtime discovery, local model selection, real process launch, loopback/private serving, health proof, real generation, measured token/latency usage, hash-bound runtime proof, and clean termination/recovery behavior.

The repository-local fallback model is `stegverse-reference-lm-v1`, a formally developed local order-2 token-transition language model trained from repository-local corpus data. It guarantees a zero-external-dependency development/inference path and is explicitly not represented as a production-scale foundation LLM.

Runtime discovery prefers a qualifying local `llama.cpp`/GGUF or Ollama model when present and otherwise uses the reference model.

Canonical local-model evidence is recorded in `StegVerse-002/micro-node-runtime/MICRO_NODE_RUNTIME_MIRROR_HANDOFF.md` and `docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md` in that repository.

## LLM-adapter carrier execution

The LLM-adapter's same-carrier executor implementation is complete and released.

Canonical surfaces:

```text
scripts/execute_canonical_sovereign_route.py
tests/test_execute_canonical_sovereign_route.py
tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json
docs/SOVEREIGN_CARRIER_EXECUTION_MIRROR_HANDOFF.md
```

The executor requires an admitted TVC route, binds the exact canonical runtime proof and private endpoint, requires credential class `NONE`, rejects route/execution authority escalation, executes through `StegVerseLocalHTTPProviderClient`, persists request/response hashes and measured usage, and advances into Master Records reconstruction.

## What remains incomplete

Repository implementation completion is not product activation.

The remaining canonical gap is runtime observation of the complete same-carrier sequence:

```text
heartbeat recovery / current fence
-> local model process
-> TVC route admission
-> LLM-adapter carrier execution
-> provider usage persistence
-> provider-usage custody/reconstruction PASS
-> transition custody/reconstruction PASS
-> immutable zero-blocker activation receipt
-> Site activation
-> required Publisher/wiki propagation
```

The distributed named-source workload, bounded executor, Z.ai transport, and governed Z.ai execution wrapper are additive capability implementations. Their source/fixture validation does not satisfy this sovereign activation sequence and does not prove live multi-provider or Z.ai execution.

This continuation is machine-owned. It is not a reason to re-open the completed local-model or carrier-executor implementation tasks.

## Boundary rules

```text
provider output != authority
route admission != execution authority
runtime proof != product activation
usage measurement != admissibility
local persistence != custody
custody receipt != execution authority
reconstruction PASS != execution authority
ingress ALLOW != egress ALLOW
egress receipt verification != local authority grant
session archival != activation
```

The adapter must fail closed rather than silently substitute hosted inference, missing credential authority, unverified runtime identity, incomplete custody evidence, unknown distributed sources, broken hash binding, missing provenance, unsupported derived-input semantics, endpoint-profile drift, missing egress governance, or provider authority escalation into the canonical sovereign route or distributed workload.

## Development and verification

Repository verification remains available through the existing test and verification surfaces, including:

```bash
pytest
python scripts/smoke_governed_session.py
python scripts/verify_goal4.py
pytest tests/test_execute_canonical_sovereign_route.py -v
pytest tests/test_distributed_workload.py -q
python scripts/check_distributed_llm_workload.py
pytest tests/test_distributed_executor.py -q
python scripts/check_distributed_llm_executor.py
pytest tests/test_zai_intr_transport.py -q
pytest tests/test_zai_intr_executor.py -q
```

The authoritative current task and release state is `LLM_ADAPTER_MIRROR_HANDOFF.md`. `adapter.capabilities.json` is the machine-readable capability posture.

## Optional interoperability lanes

The repository can still contain hosted-provider clients, fixture providers, Demo/conformance paths, SDK-adjacent integration, free-tier metadata, system-boundary tooling, named-source distributed LLM contribution lanes, the Z.ai InTr transport, and the governed Z.ai execution wrapper. Those are optional or bounded interoperability surfaces and must not be mistaken for the canonical production local-model authority path.

## Repository

https://github.com/StegVerse-org/LLM-adapter
