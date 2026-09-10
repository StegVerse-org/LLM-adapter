# Device KV SKAP Roundtrip Mirror Handoff

Updated: 2026-09-10T15:05:00-05:00
Repository: `StegVerse-org/LLM-adapter`
Parent goal: `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001`
Parent canonical owner: `StegVerse-Labs/.github`
PR: `#331`
Status: SOURCE_IMPLEMENTED / VALIDATION_IN_PROGRESS / RUNTIME_NOT_PROVEN
Authority effect: NONE

## Purpose

Extend the existing Coinbase SKAP Service Gateway so the boundary that actually accepts the current-iPhone browser request emits a canonical Universal-InTr `DEVICE_SYSTEM -> KV` first-hop projection in addition to the preserved legacy TVC double-Interlock stage receipt.

## Ownership and compatibility

The Gateway owns only the first-hop transport/staging evidence. TV/TVC remains credential and custody authority. Interlock/InTr remains transition authority. The legacy `stegverse.service_gateway.coinbase_skap_stage_receipt/v1` and embedded `stegverse.intr.boundary_transition_receipt/v1` remain unchanged for TVC compatibility.

The additive canonical sidecar is:

```text
schema: stegverse.service-gateway.device-kv-canonical-stage/v1
payload_schema: kv.interlock.request.v1
boundary: DEVICE_SYSTEM -> KV
receipt_schema: stegverse.intr.hop_receipt/v1
prior_receipt_hash: null
credential_material_present: false
authority_effect: NONE_EVIDENCE_ONLY
```

The canonical payload contains only request/reference/hash metadata. It does not contain browser ciphertext, credential plaintext, private keys, provider tokens, execution authority, or governance authority.

## Durable first-hop evidence

`llm_adapter/service_gateway_composed.py` writes the canonical first-hop projection beside the legacy stage receipt under:

```text
<gateway-storage-root>/coinbase-skap-stage-canonical/<ingress_id>.json
```

The write is exact-readback checked and collision-fail-closed. The live HTTP response may also carry this projection, but downstream custody must use the durable sidecar so the canonical first hop is not lost after request completion.

## Source surfaces

- `llm_adapter/canonical_device_kv_stage.py`
- `llm_adapter/service_gateway_composed.py`
- `tests/test_canonical_device_kv_stage.py`
- `llm_adapter/README.md`
- this handoff

## Downstream continuation

The canonical continuation is owned by `StegVerse-Labs/.github` goal `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001`:

```text
current iPhone
-> Service Gateway canonical DEVICE_SYSTEM -> KV receipt
-> TVC legacy double-Interlock custody admission (preserved)
-> exact SKAP ciphertext persistence/readback
-> canonical KV -> SKAP_VAULT receipt
-> canonical SKAP_VAULT -> KV receipt
-> exact KV return readback
-> canonical KV -> DEVICE_SYSTEM receipt
-> fail-closed four-leg verifier
```

The TVC custody writer must remain single-owner. Downstream canonical transport continuation must consume the authentic custody/readback result rather than create a second independent SKAP custody mutation.

## Completion predicate

This repository portion is source-complete only after #331 validation passes and merges. The end-to-end parent remains ACTIVE until an authentic current-iPhone execution yields the four canonical hop receipts in one hash chain plus receipt-bound exact SKAP and KV readbacks.

## Non-claims

Source, CI, PR merge, Gateway staging, or durable sidecar presence is not authentic current-device roundtrip proof. The Gateway does not gain credential, decryption, SKAP custody, provider-operation, execution, governance, or transition authority.
