# KV AI Memory Context Bridge Mirror Handoff

Status: SOURCE_IMPLEMENTED / RESIDENT-MATERIALIZER-VALIDATED / HOSTED_VALIDATION_PASS / LIVE_RUNTIME_PROOF_REQUIRED
Repository: `StegVerse-org/LLM-adapter`
Goal Task ID: `SV-KV-AI-PERSISTENCE-001`
Parent KV handoff: `StegVerse-Labs/continuity-vault-kit/KV_AI_PERSISTENCE_CLASSES_MIRROR_HANDOFF.md`
Resident binding handoff: `StegVerse-Labs/.github/docs/KV_AI_MEMORY_RESIDENT_EXECUTION_MIRROR_HANDOFF.md`
COSV task.v1: `20111110110000`

## Goal

Bind an already-admitted KnowledgeVault AI memory context packet into the existing provider-neutral `ProviderRequest` path without bypassing the existing external-LLM ingress Interlock/InTr gate or granting the model authority over KV.

## Implemented source

- `llm_adapter/kv_memory_context_bridge.py`
- `scripts/materialize_kv_memory_provider_request.py`
- `tests/test_kv_memory_context_bridge.py`
- `tests/test_kv_memory_provider_request_materializer.py`
- `.github/workflows/validate-kv-memory-context-bridge.yml`
- this scoped handoff

## Canonical sequence

```text
PERSONAL_KV context packet
-> exact packet hash
-> externally-produced memory-packet InTr ALLOW
-> ProviderRequest with bounded KV context + provenance metadata
-> existing external-LLM exact-request InTr ALLOW
-> existing TV/TVC provider operation
-> provider response
-> existing exact-response egress InTr ALLOW
```

The bridge requires the first ALLOW receipt to bind both `packet_id` and canonical `packet_sha256`. It independently validates per-entry content hashes, the packet `entries_sha256`, Personal-KV authority profile, and non-authority flags before constructing a provider request.

The resulting request adds `kv_memory_context` to `allowed_sources` and carries exact packet/admission bindings in request metadata. The memory context appears as provenance-bearing system context whose instruction grants no execution, governance, credential, or write authority.

## Resident-local exact materialization

`scripts/materialize_kv_memory_provider_request.py` is the resident application-side materializer used by the existing `.github` WorkerCoordinator binding. It consumes three already-local JSON objects:

```text
context packet
memory-packet admission artifact
provider request input
```

It rejects credential-like fields in request input, requires an explicit `created_at` so the request can be exactly reconstructed, calls the canonical KV memory bridge, and emits one deterministic `ProviderRequest` plus `provider_request_hash`.

The materialization result explicitly fixes all live effects false:

```text
provider_ingress_admission_observed=false
provider_execution_observed=false
provider_egress_admission_observed=false
kv_writeback_observed=false
credential_material_present=false
request_granted_authority=false
authority_effect=NONE_MATERIALIZATION_ONLY
```

The materializer does not perform network I/O, read provider credentials, decide InTr admission, execute a model, or mutate KV.

## Authority invariants

```text
memory packet admission != provider request admission
context != authority
model != KV authority
provider != KV authority
memory packet != write authority
ProviderRequest materialization != provider execution
LLM adapter != Interlock/InTr authority
LLM adapter != TV/TVC credential authority
```

The existing `GovernedExternalProviderClient` remains unchanged and continues to require exact provider-request ingress ALLOW, TV/TVC material, provider execution, Master Records usage continuation, and exact-response egress ALLOW.

## Validation

The bridge suite covers exact memory packet admission and metadata binding, denial rejection, packet tamper rejection after admission, entry-content hash tamper rejection, cross-authority profile rejection, and secret-material flag rejection.

The new resident materializer suite adds:

- deterministic replay with a fixed request timestamp;
- exact packet/admission/hash preservation;
- credential-like input rejection;
- required reconstruction timestamp enforcement;
- tampered admission rejection;
- explicit non-claims for ingress, provider execution, egress, and KV writeback.

Historical bridge repair:

- run `34798513098` failed only because the initial workflow omitted repository-root Python import resolution;
- the workflow was repaired with `PYTHONPATH=${{ github.workspace }}`;
- repair run `34798649357` / job `103836623691` completed SUCCESS.

Current materializer head `920fedd13a182636c80a30fc10d9482ee21de57a` is hosted-validated:

- run `34803228613` / job `103849905207` — SUCCESS;
- run `34803228620` / job `103849906564` — SUCCESS.

Those runs validate source behavior only. They are not evidence that a private KV was read or that an AI provider received memory context.

## Resident integration

The corresponding `.github` resident binding is source-validated and uses `ProcessWorkerAdapter` fenced bound state at `~/.stegverse/state/kv-ai-memory-resident`. Private packet/admission/prompt and materialized ProviderRequest bytes remain outside GitHub repository state. The request consumer only tests input-path presence before asking the existing WorkerCoordinator to execute the task.

Canonical resident source of truth:

`StegVerse-Labs/.github/docs/KV_AI_MEMORY_RESIDENT_EXECUTION_MIRROR_HANDOFF.md`

## README impact

This bridge is additive to the existing provider-neutral external-LLM architecture. The repository README must identify the KV-backed pre-ingress context stage, while preserving the existing distinction that source/CI and ProviderRequest materialization are not live connection evidence.

## Runtime truth

Source and CI cannot establish that a private KV was read, that an Interlock/InTr admission occurred, that a provider received the context, or that Auri/model consumed it. Live completion requires authentic same-execution evidence for both the memory-packet admission and the existing provider request/response admission chain.

## Next executable boundary

Reuse the current resident/WorkerCoordinator external-LLM lane to feed one authentic `PERSONAL_KV` context packet through this bridge and preserve:

1. exact KV packet hash;
2. memory-packet InTr ALLOW receipt;
3. exact ProviderRequest hash;
4. existing external ingress ALLOW receipt;
5. TV/TVC provider-operation evidence;
6. provider response hash;
7. egress ALLOW receipt;
8. Master Records custody/reconstruction evidence.

Then, if a memory write is proposed, route the non-authorizing write proposal through target-KV admission and exact-byte readback before claiming persistent memory.

No runtime receipt may be synthesized from source or CI.
