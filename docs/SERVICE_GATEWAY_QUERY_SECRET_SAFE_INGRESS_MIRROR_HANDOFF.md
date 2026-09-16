# Service Gateway Query-Secret-Safe Ingress Mirror Handoff

Updated: 2026-09-16
Repository: `StegVerse-org/LLM-adapter`
Issue: #271
Goal: `KV-CONNECTION-REVALIDATION-WORKER-001`
COSV: `50000000102000`
State: SOVEREIGN_DEPLOYMENT_ENTRYPOINT_PARITY_REPAIR_IN_REVIEW / DEPLOYED_INGRESS_EVIDENCE_PENDING
Authority effect: NONE

## Goal

Harden the existing sovereign Service Gateway logging boundary so secret-bearing callback query material cannot be persisted by request-target access logs, while retaining non-secret request observability and without creating a new callback, OAuth, credential, ingress, scheduler, carrier, or authority surface.

## Canonical dependency

This is the existing owner for the query-secret-safe ingress prerequisite referenced by `StegVerse-Labs/TVC#328`, `StegVerse-Labs/TVC#317`, the TVC Google Drive owner-consent callback handoff, and root Goal `KV-CONNECTION-REVALIDATION-WORKER-001` / COSV `50000000102000`.

The intended TVC callback remains exactly:

`https://stegverse.org/tvc/google-drive/callback`

TVC retains provider callback and credential authority. This repository owns only the existing Service Gateway logging/runtime boundary.

## Prior source hardening

PR #328 merged at `05140d58613cffcfd08f164ff5459c36870a60ee` from exact head `cb8e581f3e5025c2a507970e1784ca9668468aa5` after hosted validation passed.

That change hardened `llm_adapter.runtime_gateway` by disabling Uvicorn built-in request-target access logging and wrapping the composed application in `QuerySecretSafeAccessLogMiddleware`, which logs only method, canonical path, and status and intentionally does not read query strings, raw request targets, headers, cookies, bodies, OAuth authorization codes, state, or provider credential material.

## Sovereign entrypoint parity defect discovered

Subsequent reconciliation established that canonical StegDeploy does not launch `llm_adapter.runtime_gateway`; the sovereign production entrypoint is `llm_adapter.deployed_gateway:app`.

Therefore PR #328 source validation did not prove parity for the actual sovereign StegDeploy entrypoint. Before the parity repair:

- `llm_adapter.deployed_gateway:app` did not bind `QuerySecretSafeAccessLogMiddleware`;
- `scripts/container-entrypoint.sh` launched Uvicorn without explicitly disabling access logging;
- `compose.stegdeploy.tls.yaml` launched the deployed gateway without explicitly disabling access logging.

This is a source/runtime-entrypoint coverage defect only. It does not prove any secret was persisted and does not change TVC, Interlock/InTr, provider, credential, callback, or execution authority.

## Active parity repair

Branch: `fix/sovereign-query-safe-gateway-271`
PR: #343
Verified branch head before PR creation: `7ef63da212eabe623f24a3f08b1529a5e3f02542`
Base at PR creation: `368a1ac9c64dfa8083a280c0a1fb63a7b4c7cabf`

The repair is intentionally bounded to:

1. bind `QuerySecretSafeAccessLogMiddleware` to the actual `llm_adapter.deployed_gateway:app` entrypoint;
2. add `--no-access-log` to the non-TLS StegDeploy container entrypoint;
3. add `--no-access-log` to the TLS StegDeploy compose launch path;
4. extend deterministic tests to require middleware parity and Uvicorn request-target logging suppression for both sovereign launch paths;
5. preserve the existing runtime_gateway hardening and all existing authority boundaries.

Current repair files are:

```text
llm_adapter/deployed_gateway.py
scripts/container-entrypoint.sh
compose.stegdeploy.tls.yaml
tests/test_service_gateway_query_safe_logging.py
tasks/LLMA-SERVICE-GATEWAY-QUERY-SECRET-SAFE-271.json
docs/SERVICE_GATEWAY_QUERY_SECRET_SAFE_INGRESS_MIRROR_HANDOFF.md
```

No source, CI, PR, or merge event counts as deployed-ingress evidence.

## Required validation boundary

PR #343 may merge only after exact-head CI is green and the expected head SHA is re-read immediately before merge. If the head moves, validation must be repeated for the new exact head.

After merge, the deployed predicate remains fail-closed until authentic observation proves the active sovereign public ingress is actually running the hardened boundary.

The required runtime observation must use one harmless synthetic query-bearing request to a non-credential route through the canonical public gateway and retain enough active gateway log evidence to prove:

```text
request reached active public Service Gateway
logged fields = method + canonical path + status
synthetic query value absent
raw request target absent
query string absent
credential/provider secret material absent
```

A public HTTP response alone is insufficient because it does not prove what the active gateway persisted in logs.

## Remaining sequence

1. Obtain exact-head green CI for PR #343 and merge only with expected-head protection.
2. Bind the existing resident observation carrier to the merged canonical sovereign Service Gateway runtime; do not create a second runtime owner or third-party fallback.
3. Send one harmless synthetic query-bearing request to a non-credential route through that exact active public gateway.
4. Inspect the corresponding active gateway logs and retain exact observation evidence proving method/path/status are present while the synthetic query value, raw request target, and query string are absent.
5. Reconcile issue #271 and TVC #328/#317 only from that authentic deployed observation.
6. Re-run TVC callback preflight; only then implement/activate the exact `/tvc/google-drive/callback` route using the already-merged TVC refresh custody, vault-session consumer, SKAP client-secret protected-use adapter, Interlock/InTr boundaries, and canonical carrier.
7. Do not initiate Google consent or provider authorization until the TVC callback preflight passes.

## Manual work

None at this checkpoint. Do not initiate Google consent, expose provider credentials, treat source/CI/merge as deployed ingress proof, reopen TVC provider execution, re-emit the Google Drive KV request, or materialize KV #2 before authentic deployed query-secret-safe ingress evidence is retained.
