# Service Gateway Query-Secret-Safe Ingress Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-org/LLM-adapter`
Issue: #271
State: SOURCE_MERGED_VALIDATED / DEPLOYED_INGRESS_EVIDENCE_PENDING
Authority effect: NONE

## Goal

Harden the existing sovereign Service Gateway logging boundary so secret-bearing callback query material cannot be persisted by request-target access logs, while retaining non-secret request observability and without creating a new callback, OAuth, credential, ingress, scheduler, carrier, or authority surface.

## Canonical dependency

This is the existing owner for the query-secret-safe ingress prerequisite referenced by:

- `StegVerse-Labs/TVC#328`;
- `StegVerse-Labs/TVC#317`;
- `StegVerse-Labs/TVC/docs/GOOGLE_DRIVE_PERSONAL_KV_OWNER_CONSENT_CALLBACK_INGRESS_MIRROR_HANDOFF.md`;
- root Goal `KV-CONNECTION-REVALIDATION-WORKER-001` / COSV `50000000102000`.

The intended TVC callback remains exactly:

`https://stegverse.org/tvc/google-drive/callback`

TVC retains provider callback and credential authority. This repository owns only the existing Service Gateway logging/runtime boundary.

## Source state

PR #328 merged at `05140d58613cffcfd08f164ff5459c36870a60ee` from exact head `cb8e581f3e5025c2a507970e1784ca9668468aa5` after hosted validation passed.

Current source now:

1. disables Uvicorn built-in request-target access logging in `llm_adapter.runtime_gateway:main()`;
2. wraps the completely composed Gateway application in `QuerySecretSafeAccessLogMiddleware`;
3. logs only method, canonical path, and response status;
4. intentionally does not read or serialize ASGI `query_string`, raw request target, headers, cookies, body, OAuth authorization code, state, or provider credential material;
5. preserves application routing, TVC callback ownership, Interlock/InTr semantics, provider execution ownership, credential custody, and authority boundaries.

README documentation and adversarial source validation were included in the merged change. Source implementation is no longer pending.

## Evidence boundary

Merged source and CI prove the implementation contract only. They do not prove the currently active `stegverse.org -> TVC` public path is running this source.

TVC #328 remains pending until authentic deployed-ingress evidence demonstrates the active public gateway cannot persist harmless synthetic callback query material.

The required runtime observation must use a non-secret synthetic query value and retain enough gateway log evidence to show:

```text
request reached active public Service Gateway
logged fields = method + canonical path + status
synthetic query value absent
raw request target absent
query string absent
credential/provider secret material absent
```

A public HTTP response alone is insufficient because it does not prove what the active gateway persisted in access logs.

## Remaining sequence

1. Identify the active canonical Service Gateway runtime/log source without introducing a second runtime owner or third-party fallback.
2. Send one harmless synthetic query-bearing request to a non-credential route through that exact public gateway.
3. Inspect the corresponding active gateway logs and retain exact observation evidence proving the synthetic query value and raw request target were not persisted while method/path/status were retained.
4. Reconcile issue #271 and TVC #328/#317 only after that deployed observation.
5. Re-run TVC callback preflight; only then implement/activate the exact `/tvc/google-drive/callback` route using the already-merged #302 refresh custody, #315 vault-session consumer, #327 SKAP client-secret protected-use adapter, existing Interlock/InTr boundaries, and canonical carrier.
6. Do not initiate Google consent or provider authorization until the TVC callback preflight passes.

## Manual work

None at this checkpoint. Do not initiate Google consent, expose provider credentials, or treat source/CI/merge as deployed ingress proof.
