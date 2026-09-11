# External-Collaboration Google Drive Consent Route Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-org/LLM-adapter`
Parent Service Gateway owner: issue #72
Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
Status: `SOURCE IMPLEMENTATION IN PROGRESS / NO PUBLIC RUNTIME CLAIM`

## Purpose

Implement the exact TVC external-collaboration Google Drive consent public-route contract inside the existing StegVerse Service Gateway. This must reuse the existing Gateway/runtime and same-host resident listener and must not create a second reverse proxy, hosted fallback, credential path, scheduler, or execution authority.

Canonical TVC contract: `StegVerse-Labs/TVC:contracts/external-collab-google-drive-consent-public-route.v1.json`.

## Exact route contract

```text
GET /tvc/external-collaboration/google-drive/consent/begin
GET /tvc/google-drive/external-collaboration/callback
GET /tvc/external-collaboration/google-drive/consent/health
same-host upstream: http://127.0.0.1:8786
```

Rules:

- begin and health reject query strings;
- callback allows only `state`, `code`, `error`, and `error_description`;
- callback query bytes remain in memory only and are never logged or persisted by the Gateway;
- method/body surface is GET-only;
- no Authorization or Cookie forwarding;
- provider/client-secret material is never visible to the Gateway;
- upstream failure is fail-closed and does not imply listener or public-route readiness;
- response forwarding is limited to status/body and a small response-header allowlist required for redirects/content semantics.

## Authority boundary

The Gateway owns only bounded same-host forwarding. TV/TVC remains credential/provider-operation authority. The resident listener owns Google consent semantics. CMC-029/native TLS owns sovereign WebPKI. Source/CI/merge do not prove resident listener health, public HTTPS reachability, owner-present consent, provider execution, or WorkSpace readiness.

## README review

Root `README.md` was reviewed for this source change. No public runtime claim is added because the route remains incomplete until authentic resident listener health and sovereign public HTTPS are independently observed.

## Completion predicate

Source completion requires the module to be composed into `llm_adapter.runtime_gateway`, deterministic tests for exact-route/query/header/failure behavior, and repository validation. Runtime completion remains separate and requires authentic `127.0.0.1:8786` health plus independently observed `https://stegverse.org` route behavior.
