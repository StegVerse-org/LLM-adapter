# Service Gateway HTTP-01 Challenge Projection Mirror Handoff

Updated: 2026-08-28
Repository: `StegVerse-org/LLM-adapter`
Issue: #210
Branch: `feat/tvc-http01-challenge-projection`
Upstream: `StegVerse-Labs/TVC` CMC-029 / PR #214
State: CLAIMED_FOR_IMPLEMENTATION

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

Implement the bounded public challenge reader/route, validate exact head, merge only after green evidence, then let the TVC resident CMC-029 adapter project challenge files into the same runtime root.
