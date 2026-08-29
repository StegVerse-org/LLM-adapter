# Service Gateway HTTP-01 Challenge Projection Mirror Handoff

Updated: 2026-08-28
Repository: `StegVerse-org/LLM-adapter`
Issue: #210
Branch: `main`
Upstream: `StegVerse-Labs/TVC` CMC-029 / PR #214
State: MERGED_VALIDATED_PUBLIC_CHALLENGE_ROUTE_RUNTIME_UNOBSERVED

## Goal

Serve one exact TVC-projected ACME HTTP-01 public key-authorization value through the existing sovereign Service Gateway.

## Authority boundary

```text
credential authority: TV/TVC
ACME account-key authority: TV/TVC
leaf private-key authority: TV/TVC
Gateway signing authority: NONE
Gateway CA credential authority: NONE
Gateway issuance authority: NONE
Gateway provider-operation authority: NONE
challenge material classification: PUBLIC_HTTP01_KEY_AUTHORIZATION
challenge root: runtime-local confined directory
directory listing: false
mutation API: false
generalized ACME manager: false
authority_effect: NONE
```

The Gateway may read only a validated token filename beneath the configured challenge root and return its bounded public text value. It must reject traversal, symlinks, oversized files, invalid tokens, or non-regular files.

## Planned source

- `llm_adapter/service_gateway_http01.py`
- `llm_adapter/deployed_gateway.py`
- `tests/test_service_gateway_http01.py`
- existing repository validation surface
- this handoff
- `docs/COINBASE_SKAP_SERVICE_GATEWAY_MIRROR_HANDOFF.md`

## Non-claims

No live ACME account, leaf key, issuance, public HTTPS reachability, DNS ownership, provider authority, or READY_FOR_OWNER_INGRESS is created here.

## Next executable boundary

Run exact-head Coinbase SKAP/Gateway validation for the bounded challenge reader/route. Merge only after green evidence, then bind the TVC resident CMC-029 adapter to project/remove public challenge files beneath the same runtime root.


## Merge and validation evidence

```text
issue: #210
PR: #211
validated head: b6897f060e09600d7d5a05e77d78ce40c918b31a
Coinbase SKAP Service Gateway Validation (push): 33226168732 SUCCESS
Coinbase SKAP Service Gateway Validation (PR): 33226178414 SUCCESS
global validate (PR): 33226178477 SUCCESS
merge: cbfb3b2b33931d6867d2e6b58437b57a191d8a67
```

The deployed Gateway now contains exactly one GET-only TVC public challenge route. No challenge material, live runtime, external reachability, public certificate, or issuance is claimed by the merge.

## Current next boundary

The TVC resident CMC-029 adapter may project/remove public key-authorization files beneath the shared challenge root. Actual CA retrieval of that route and successful issuance remain non-hosted runtime evidence.
