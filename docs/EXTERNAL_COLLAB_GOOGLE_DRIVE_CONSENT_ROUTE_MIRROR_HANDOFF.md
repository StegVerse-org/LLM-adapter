# External-Collaboration Google Drive Consent Route Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-org/LLM-adapter`
Parent Service Gateway owner: issue #72
Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
Status: `SOURCE IMPLEMENTED / VALIDATION PENDING / NO PUBLIC RUNTIME CLAIM`

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

## Implemented source

```text
llm_adapter/service_gateway_external_collab_consent.py
tests/test_service_gateway_external_collab_consent.py
llm_adapter/runtime_gateway.py
```

`runtime_gateway.py` composes the new route module before wrapping the complete FastAPI application in the existing `QuerySecretSafeAccessLogMiddleware`. Built-in Uvicorn access logging remains disabled by the existing runtime entrypoint.

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

## Authority boundary

The Gateway owns only bounded same-host forwarding. TV/TVC remains credential/provider-operation authority. The resident listener owns Google consent semantics. CMC-029/native TLS owns sovereign WebPKI. Source/CI/merge do not prove resident listener health, public HTTPS reachability, owner-present consent, provider execution, or WorkSpace readiness.

## README review

Root `README.md` was reviewed for this source change. No public runtime claim is added because the route remains incomplete until authentic resident listener health and sovereign public HTTPS are independently observed. Existing README authority semantics remain accurate, so no root README wording change is required at this source-only stage.

## Validation boundary

Deterministic tests cover:

- forbidden query handling for begin/health;
- exact callback raw-query preservation;
- callback query-key allowlisting;
- fail-closed unreachable-listener behavior;
- redirect/status/header forwarding without `Set-Cookie` or debug leakage;
- direct loopback transport with environment proxy use disabled.

Validation and merge evidence must be added here after the PR exact-head checks complete. Passing source validation will not establish authentic resident listener health or public route reachability.

## Runtime continuation

Runtime completion remains separate and requires:

1. authentic resident receipt proving the consent listener is healthy on `127.0.0.1:8786`;
2. authentic client-secret target custody/readback;
3. sovereign CMC-029/native-TLS adoption for `stegverse.org`;
4. independent HTTPS health-route observation;
5. begin-route redirect observation with the canonical callback;
6. callback request-target logging suppression proof;
7. only then owner-present consent and provider probe.
