# Service Gateway Query-Secret-Safe Ingress Mirror Handoff

Updated: 2026-09-16
Repository: `StegVerse-org/LLM-adapter`
Issue: #271
Goal: `KV-CONNECTION-REVALIDATION-WORKER-001`
COSV: `50000000102000`
State: SOVEREIGN_DEPLOYMENT_ENTRYPOINT_PARITY_SOURCE_MERGED_VALIDATED / DEPLOYED_INGRESS_EVIDENCE_PENDING
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

## Sovereign entrypoint parity defect and repair

Subsequent reconciliation established that canonical StegDeploy does not launch `llm_adapter.runtime_gateway`; the sovereign production entrypoint is `llm_adapter.deployed_gateway:app`.

Before the parity repair:

- `llm_adapter.deployed_gateway:app` did not bind `QuerySecretSafeAccessLogMiddleware`;
- `scripts/container-entrypoint.sh` launched Uvicorn without explicitly disabling access logging;
- `compose.stegdeploy.tls.yaml` launched the deployed gateway without explicitly disabling access logging.

This was a source/runtime-entrypoint coverage defect only. It did not prove any secret was persisted and did not change TVC, Interlock/InTr, provider, credential, callback, or execution authority.

PR #343 repaired that parity gap by:

1. binding `QuerySecretSafeAccessLogMiddleware` to the actual `llm_adapter.deployed_gateway:app` entrypoint;
2. adding `--no-access-log` to the non-TLS StegDeploy container entrypoint;
3. adding `--no-access-log` to the TLS StegDeploy compose launch path;
4. extending deterministic tests to require middleware parity and Uvicorn request-target logging suppression for both sovereign launch paths;
5. preserving the existing runtime_gateway hardening and all existing authority boundaries.

PR #343 exact validated head: `cae48e9e24d763cbbecf667e374fdb322b60180e`

Exact-head PR validation:

- `validate` run `35092908169`: SUCCESS;
- `Work Mutation Safety - Non-Authorizing` run `35092908274`: SUCCESS;
- `Coinbase SKAP Service Gateway Validation` run `35092908240`: SUCCESS.

PR #343 merged with expected-head protection as merge commit `6e6a3ac8eb30ce8a2092c6ac0397b80380a9cd33`.

README.md already states the sovereign Service Gateway contract as Uvicorn request-target logging disabled plus method/canonical-path/status-only `QuerySecretSafeAccessLogMiddleware`; the repair made the actual StegDeploy entrypoint conform to that existing documented contract rather than changing the contract.

No source, CI, PR, or merge event counts as deployed-ingress evidence.

## Authentic deployed observation boundary

The deployed predicate remains fail-closed until authentic observation proves the active sovereign public ingress is actually running the hardened boundary.

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

At the 2026-09-16 post-merge checkpoint, the authorized resident-command surface reported no connected runtime device. Therefore no authentic active-gateway log observation could be collected in this session. This is a runtime-observation availability condition, not evidence that the deployed predicate passed or failed. No substitute GitHub Actions runtime, second runtime owner, or third-party fallback was introduced.

## Remaining sequence

1. Re-establish access to the existing authorized resident runtime/observation surface without creating a second runtime owner.
2. Verify that the observed active sovereign Service Gateway is running the merged canonical source lineage containing merge commit `6e6a3ac8eb30ce8a2092c6ac0397b80380a9cd33` or a descendant carrying the same repair.
3. Send one harmless synthetic query-bearing request to a non-credential route through that exact active public gateway.
4. Inspect the corresponding active gateway logs and retain exact observation evidence proving method/path/status are present while the synthetic query value, raw request target, and query string are absent.
5. Reconcile issue #271 and TVC #328/#317 only from that authentic deployed observation.
6. Re-run TVC callback preflight; only then implement/activate the exact `/tvc/google-drive/callback` route using the already-merged TVC refresh custody, vault-session consumer, SKAP client-secret protected-use adapter, Interlock/InTr boundaries, and canonical carrier.
7. Do not initiate Google consent or provider authorization until the TVC callback preflight passes.
8. After successful provider authorization, perform CONNECT/VERIFY and only then materialize Google Drive KV #2 and complete the required roundtrip/terminal-readback evidence.

## Manual work

Reconnect the already-authorized resident runtime device to the existing resident-command surface so authentic active-gateway logs can be observed. Do not initiate Google consent, expose provider credentials, treat source/CI/merge as deployed ingress proof, reopen TVC provider execution, re-emit the Google Drive KV request, or materialize KV #2 before the deployed query-secret-safe ingress observation passes.
