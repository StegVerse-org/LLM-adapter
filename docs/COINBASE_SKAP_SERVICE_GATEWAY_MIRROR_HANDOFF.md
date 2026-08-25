# Coinbase SKAP Service Gateway Mirror Handoff

Updated: 2026-08-25T12:41:00-05:00
Repository: `StegVerse-org/LLM-adapter`
Upstream architecture owner: `StegVerse-org/LLM-adapter#72`
Downstream credential/custody owner: `StegVerse-Labs/TVC#119`

## Goal

Reuse the existing shared StegVerse Service Gateway for the public HTTPS transport/persistence hop of current-iPhone Coinbase SKAP ingress without granting the Gateway Coinbase credential, private-key, decryption, custody, trading, or execution authority.

## Canonical role

```text
CURRENT_USER_IPHONE
-> local P-256 browser encryption
-> shared Service Gateway HTTPS intake
-> exact ciphertext staging + non-authorizing receipt
-> local TVC staged-packet consumer
-> TVC SKAP ciphertext custody
-> verified Coinbase endpoint/session + current grant
-> transient credential resolution
```

The Service Gateway is transport + durable staging only. It is not SKAP custody and cannot complete TVC admission.

## Implemented source

- `llm_adapter/service_gateway_coinbase_skap.py`
- `llm_adapter/service_gateway_composed.py`
- `llm_adapter/runtime_gateway.py` integration
- `tests/test_service_gateway_coinbase_skap.py`
- `tests/test_service_gateway_coinbase_skap_api.py`
- `.github/workflows/coinbase-skap-service-gateway.yml`

The Coinbase adapter is mounted onto the actual `stegverse-service-gateway` runtime entrypoint, preserving existing HIL, math-solver, and VA gateway adapters. No second service plane was created.

## No-value TVC boundary

Gateway readiness requires a TVC decision receipt with:

```text
role: service_gateway_coinbase_skap_ciphertext_intake
admissible: true
binding_matched: true
allowed_keys: []
denied_keys: []
credential_values_available: false
```

The Gateway therefore has no admitted secret/key names and no credential-value access.

## Public HTTP staging contract

Routes:

```text
GET  /api/coinbase/skap/readiness
POST /api/coinbase/skap/ingress
```

Ingress requires exact StegVerse origin, JSON body, no Authorization header, no Cookie header, bounded body size, current-iPhone/WebAuthn/browser-ciphertext bindings, and TV/TVC credential-authority markers.

The exact request bytes are durably persisted and read back before a receipt is emitted. Replay of an existing ingress ID is denied.

Returned receipt:

```text
schema: stegverse.service_gateway.coinbase_skap_stage_receipt/v1
decision: STAGED_FOR_TVC
gateway_credential_value_access: false
gateway_decryption_authority: false
gateway_execution_authority: NONE
browser_ciphertext_mutated: false
decryption_performed: false
rewrap_performed: false
plaintext_persisted: false
tvc_admission_completed: false
next_required_transition: TVC_SKAP_CIPHERTEXT_CUSTODY_ADMISSION
blind_retry_allowed: false
```

No ciphertext or credential plaintext is returned in the receipt.

## TVC continuation

`StegVerse-Labs/TVC/tools/coinbase_gateway_stage_consumer.py` consumes the staged packet locally from the shared service-plane storage. It verifies stage receipt integrity, path confinement, raw-body hash, browser packet semantics, and all cross-stage bindings before moving the exact bytes into TVC ciphertext custody and emitting the canonical TVC v2 admission transition.

TVC hosted validation run `32879237493` = `SUCCESS`.

## Hosted validation

Initial run exposed an order-dependency in direct `stage_packet()` invocation because staging directories were created only by `load_runtime()`. The implementation was repaired to self-initialize its bounded staging/receipt directories.

`Coinbase SKAP Service Gateway Validation` run `32879101025` = `SUCCESS` after repair.
Global repository `validate` run `32879100937` = `SUCCESS` for the same repaired commit.

## Current state

```text
shared Gateway source integration: HOSTED PASS
Gateway no-value TVC boundary: HOSTED PASS
exact ciphertext staging/readback: HOSTED PASS
Gateway -> TVC local consumer source: HOSTED PASS in TVC
public production Service Gateway route observation: OPEN
production recipient public-key lease: OPEN
real current-iPhone owner credential ingress: OPEN
real TVC ciphertext custody object: OPEN
authentic Coinbase permission/fee observation: OPEN
live order: NOT EXECUTED
```

## Non-claims

Source/hosted validation does not prove that a public production Service Gateway instance is currently serving these routes. It does not provision the browser recipient private key. It does not admit a real Coinbase credential and grants no order authority.

## Next work

1. Observe/deploy the shared Service Gateway runtime with the Coinbase routes and no-value TVC decision boundary.
2. Establish real TVC-controlled P-256 browser-recipient key custody and ACTIVE public-key lease.
3. Project only the public JWK + proven Gateway ingress URL to Site.
4. Perform the first owner-authorized current-iPhone ciphertext staging and TVC custody transition.
5. Continue through provider-session verification and sanitized Coinbase permission/fee observation before any bounded order.
