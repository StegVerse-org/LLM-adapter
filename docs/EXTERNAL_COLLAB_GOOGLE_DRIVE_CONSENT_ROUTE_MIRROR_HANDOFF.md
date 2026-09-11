# External-Collaboration Google Drive Consent Route Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-org/LLM-adapter`
Parent Service Gateway owner: issue #72
Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
Status: `SOURCE IMPLEMENTED + VALIDATED + MERGED / AUTHENTIC RUNTIME PROOF NEXT`

## Purpose

Implement the exact TVC external-collaboration Google Drive consent public-route contract inside the existing StegVerse Service Gateway. This reuses the existing Gateway/runtime and same-host resident listener and creates no second reverse proxy, hosted fallback, credential path, scheduler, or execution authority.

Canonical TVC contract: `StegVerse-Labs/TVC:contracts/external-collab-google-drive-consent-public-route.v1.json`.

## Exact route contract

```text
GET /tvc/external-collaboration/google-drive/consent/begin
GET /tvc/google-drive/external-collaboration/callback
GET /tvc/external-collaboration/google-drive/consent/health
same-host upstream: http://127.0.0.1:8786
```

## Merged source

PR `#332` merged at `9ab7e019eaf694f20c978ce65ad7a2d5c886010a` from exact validated head `5d199cfc11be410f03c884cd70278d81d956c9f5`.

```text
llm_adapter/service_gateway_external_collab_consent.py
tests/test_service_gateway_external_collab_consent.py
llm_adapter/runtime_gateway.py
.github/workflows/coinbase-skap-service-gateway.yml
receipts/work-safety/SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003-external-collab-routes.json
```

`runtime_gateway.py` composes the route module before wrapping the complete FastAPI application in the existing `QuerySecretSafeAccessLogMiddleware`. Built-in Uvicorn access logging remains disabled by the existing runtime entrypoint.

Implemented rules:

- begin and health reject any query string before contacting the resident listener;
- callback allows only `state`, `code`, `error`, and `error_description`;
- exact admitted callback query bytes are forwarded in memory without persistence;
- method/body surface is GET-only;
- upstream origin is constant `http://127.0.0.1:8786`;
- `requests.Session.trust_env=false` prevents environment HTTP proxies from redirecting the loopback hop;
- redirects are not followed by the Gateway;
- no browser Authorization/Cookie headers are forwarded;
- response forwarding is limited to body/status plus `content-type`, `location`, `cache-control`, `pragma`, `expires`, and `retry-after`;
- `Set-Cookie`, debug headers, and other upstream headers are not propagated;
- upstream connection failure returns `503 external_collaboration_listener_unreachable` and grants no readiness claim.

## Validation evidence

Final PR head `5d199cfc11be410f03c884cd70278d81d956c9f5`:

- Work Mutation Safety - Non-Authorizing run `34563524752` — PASS.
- Coinbase SKAP Service Gateway Validation run `34563524745` — PASS, including compilation and execution of `tests/test_service_gateway_external_collab_consent.py`, mounted HTTP-boundary regressions, and exact source authority/loopback assertions.
- Repository `validate` run `34563524742` — PASS through all 72 observed steps, including canonical Goal 4 verification and validation-only authority-boundary confirmation.

Earlier head `c8dc804ebf07281e01ca30590a993a581568c3ac` also passed Work Mutation Safety `34563415968`, focused Gateway validation `34563415971`, and repository validation `34563415965`; final-head evidence above is authoritative for merge.

These results prove source/test consistency and merge only. They do not establish authentic resident listener health or public route reachability.

## Authority boundary

The Gateway owns only bounded same-host forwarding. TV/TVC remains credential/provider-operation authority. The resident listener owns Google consent semantics. CMC-029/native TLS owns sovereign WebPKI. Source/CI/merge do not prove resident listener health, public HTTPS reachability, owner-present consent, provider execution, or WorkSpace readiness.

## README review

Root `README.md` was reviewed for this source change. No public runtime claim is added because the route remains incomplete until authentic resident listener health and sovereign public HTTPS are independently observed. Existing README authority semantics remain accurate, so no root README wording change is required at this source-only stage.

## Runtime continuation

Runtime completion remains separate and requires:

1. authentic resident receipt proving the consent listener is healthy on `127.0.0.1:8786`;
2. authentic client-secret target custody/readback;
3. sovereign CMC-029/native-TLS adoption for `stegverse.org`;
4. independent HTTPS health-route observation;
5. begin-route redirect observation with the canonical callback;
6. callback request-target logging suppression proof;
7. only then owner-present consent and provider probe.
