# KnowledgeVault Onboarding Service Gateway Mirror Handoff

Updated: 2026-08-27
Repository: `StegVerse-org/LLM-adapter`
Goal ID: `LLMA-KV-ONBOARDING-GATEWAY-001`
Status: IMPLEMENTED_PENDING_HOSTED_VALIDATION / NON_AUTHORIZING_TRANSPORT

## Goal

Provide the existing shared StegVerse Service Gateway with a bounded, non-secret InTr transport/staging surface for the Site KnowledgeVault onboarding successor without granting the Gateway KV ownership, identity, device, installation, SKAP, governance, or execution authority.

## Canonical topology

```text
CURRENT_USER_DEVICE / Site
-> InTr onboarding request
-> shared StegVerse Service Gateway
-> durable non-secret staging receipt
-> STAGED_FOR_CANONICAL_KV_AUTHORITY
-> canonical KV / StegID / Continuity admission
-> only admitted canonical receipts may establish KV_CREATED / OWNER_BOUND / DEVICE_REGISTERED / INSTALLATION_ADMITTED / KV_ACTIVE
```

The Gateway MUST NOT mint or imply any of those canonical lifecycle states.

## Initial request operations

Transport may carry bounded requests for:

```text
CREATE_KV
ATTACH_KV
REGISTER_DEVICE
INSTALL_KV
```

Request records may contain only non-secret references and hashes. Raw passwords, provider credentials, SKAP material, private keys, authentication headers, browser cookies and credential plaintext are prohibited.

## Gateway receipt contract

The Gateway response must remain transport-only:

```text
schema: stegverse.service_gateway.kv_onboarding_stage_receipt/v1
decision: STAGED_FOR_CANONICAL_KV_AUTHORITY
transport_protocol: InTr
completed_boundary: DEVICE_TO_KV_STAGING
kv_ownership_established: false
owner_binding_established: false
device_registration_established: false
installation_admitted: false
kv_active: false
skap_unlocked: false
gateway_identity_authority: false
gateway_kv_authority: false
gateway_device_authority: false
gateway_execution_authority: NONE
authority_transfer: false
secret_plaintext_present: false
next_required_transition: CANONICAL_KV_OWNERSHIP_ADMISSION
```

A 202/receipt is not ownership and must not cause Site to reveal the production KV tree.

## Runtime/storage

Reuse the existing `runtime_gateway` service plane. Do not create another public service.

A dedicated runtime staging root may be configured by `STEGVERSE_KV_ONBOARDING_STORAGE_ROOT`. Production configuration authority remains external to the module. No user/provider credential is required for source/hosted tests.

Replay/idempotency must be fail-closed and durable by request id + canonical request hash.

## Dependencies

Upstream contract:
- `StegVerse-Labs/Site/docs/GENERIC_LOGIN_TEST_MIRROR_HANDOFF.md`
- `StegVerse-Labs/continuity-vault-kit/CONTINUITY_VAULT_KIT_MIRROR_HANDOFF.md`
- `StegVerse-Labs/Continuity/docs/KNOWLEDGEVAULT_CONTINUITY_MIRROR_HANDOFF.md`
- `StegVerse-Labs/StegID/docs/KNOWLEDGEVAULT_CONTINUITY_BINDING_MIRROR_HANDOFF.md`

Adjacent Gateway:
- `docs/COINBASE_SKAP_SERVICE_GATEWAY_MIRROR_HANDOFF.md`

The Coinbase SKAP lane remains separate. This onboarding lane carries no credential material.

## Implemented source

```text
llm_adapter/service_gateway_kv_onboarding.py
llm_adapter/runtime_gateway.py
tests/test_service_gateway_kv_onboarding.py
.github/workflows/validate.yml
```

The route provides:

```text
GET  /api/kv/onboarding/readiness
POST /api/kv/onboarding/transitions
```

The POST path requires the stegverse.org Origin, rejects Authorization/Cookie headers, requires JSON, limits body size, rejects secret/credential fields recursively, enforces operation-specific input ordering, persists canonical non-secret request bytes with exclusive creation, denies request-id replay durably, and returns only a transport-stage receipt.

The shared runtime response cannot mint or imply canonical ownership/device/install states.

## Current state

```text
Site TEST_ONLY onboarding state machine: MERGED
Packageable User KV clean-room file install: HOSTED VALIDATED
production onboarding transport endpoint source: IMPLEMENTED ON feature/kv-onboarding-gateway-001
shared runtime_gateway mount: IMPLEMENTED
durable replay-safe staging: IMPLEMENTED
hosted validation conclusion: PENDING
canonical ownership backend: NOT IMPLEMENTED
production owner/device receipts: NOT OBSERVED
```

## Next executable boundary

1. hosted-validate the implemented shared Gateway route;
2. merge only after the canonical global validate lane passes;
3. bind Site production adapter to consume only the transport receipt;
4. keep Site at NO_KV / pending until a separately authoritative canonical admission receipt exists.

## User action

None for source/hosted transport implementation.
