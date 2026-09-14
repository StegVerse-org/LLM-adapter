# KV AI Memory Context Bridge Mirror Handoff

Status: SOURCE_IMPLEMENTED / HOSTED_VALIDATION_PASS / LIVE_RUNTIME_PROOF_REQUIRED
Repository: `StegVerse-org/LLM-adapter`
Goal Task ID: `SV-KV-AI-PERSISTENCE-001`
Parent KV handoff: `StegVerse-Labs/continuity-vault-kit/KV_AI_PERSISTENCE_CLASSES_MIRROR_HANDOFF.md`
COSV task.v1: `20111110110000`

## Goal

Bind an already-admitted KnowledgeVault AI memory context packet into the existing provider-neutral `ProviderRequest` path without bypassing the existing external-LLM ingress Interlock/InTr gate or granting the model authority over KV.

## Implemented source

- `llm_adapter/kv_memory_context_bridge.py`
- `tests/test_kv_memory_context_bridge.py`
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

The bridge requires the first ALLOW receipt to bind both `packet_id` and canonical `packet_sha256`. It independently validates per-entry content hashes, the packet `entries_sha256`, byte count, Personal-KV authority profile, and non-authority flags before constructing a provider request.

The resulting request adds `kv_memory_context` to `allowed_sources` and carries the exact packet/admission bindings in request metadata. The memory context appears as a provenance-bearing system message whose instruction explicitly grants no execution, governance, credential, or write authority.

## Authority invariants

```text
memory packet admission != provider request admission
context != authority
model != KV authority
provider != KV authority
memory packet != write authority
LLM adapter != Interlock/InTr authority
LLM adapter != TV/TVC credential authority
```

The existing `GovernedExternalProviderClient` remains unchanged and continues to require exact provider-request ingress ALLOW, TV/TVC material, provider execution, Master Records usage continuation, and exact-response egress ALLOW.

## Validation

The dedicated test suite covers exact memory packet admission and metadata binding, denial rejection, packet tamper rejection after admission, entry-content hash tamper rejection, cross-authority profile rejection, and secret-material flag rejection.

Initial dedicated run `34798513098` failed only because the new workflow omitted the repository root from Python import resolution (`ModuleNotFoundError: llm_adapter`). The workflow was repaired by binding `PYTHONPATH=${{ github.workspace }}`. On repair head `ccaf6671289d96bcd535a88cae345f8ef92fa260`, dedicated run `34798649357` / job `103836623691` completed SUCCESS, including `pytest -q tests/test_kv_memory_context_bridge.py`.

A second repository validation job on the same repair head remains independent of this dedicated bridge test and must not be represented as complete until its own conclusion is observed.

## README impact

This scoped bridge does not replace the existing provider-neutral external-LLM architecture documented by the repository README. The canonical README remains correct about `ProviderRequest`, external ingress/egress InTr, TV/TVC, and source-vs-runtime proof. A focused README insertion for KV memory context remains documentation follow-through; this handoff is the current scoped source of truth for the bridge until that insertion is safely applied without truncating the large existing README.

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

No runtime receipt may be synthesized from source or CI.
