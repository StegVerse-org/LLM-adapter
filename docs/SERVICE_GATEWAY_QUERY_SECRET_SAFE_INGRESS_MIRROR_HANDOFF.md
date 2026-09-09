# Service Gateway Query-Secret-Safe Ingress Mirror Handoff

Updated: 2026-09-08
Repository: `StegVerse-org/LLM-adapter`
Issue: #271
State: SOURCE_IMPLEMENTATION_IN_PROGRESS / DEPLOYED_INGRESS_EVIDENCE_PENDING
Authority effect: NONE

## Goal

Harden the existing sovereign Service Gateway logging boundary so secret-bearing callback query material cannot be persisted by request-target access logs, while retaining non-secret request observability and without creating a new callback, OAuth, credential, ingress, scheduler, carrier, or authority surface.

## Canonical dependency

This is the existing owner for the query-secret-safe ingress prerequisite referenced by:

- `StegVerse-Labs/TVC#328`;
- `StegVerse-Labs/TVC#317`;
- `StegVerse-Labs/TVC/docs/GOOGLE_DRIVE_PERSONAL_KV_OWNER_CONSENT_CALLBACK_INGRESS_MIRROR_HANDOFF.md`.

The intended TVC callback remains exactly:

`https://stegverse.org/tvc/google-drive/callback`

TVC retains provider callback and credential authority. This repository owns only the existing Service Gateway logging/runtime boundary.

## Source change target

Current `llm_adapter.runtime_gateway:main()` starts Uvicorn with default request-target access logging behavior. The source change will:

1. disable Uvicorn's built-in access log for the Service Gateway runtime;
2. install a Gateway-owned ASGI middleware that logs only method, canonical path, and response status;
3. never log `query_string`, raw request target, Authorization header, cookie material, request body, or provider callback code/state values;
4. preserve ordinary non-secret request observability;
5. leave application routing, TVC callback ownership, InTr semantics, provider execution, credentials, and authority unchanged.

## README completeness

README update required: **YES**.

Changing runtime request logging materially changes Service Gateway observability and the security prerequisite for secret-bearing callback ingress. The same functional change set must document the path-only logging boundary and distinguish source/CI proof from deployed-ingress evidence.

## Evidence boundary

Source tests/CI/merge may prove only that:

- built-in Uvicorn request-target access logging is disabled;
- the replacement middleware never serializes query strings or protected callback values;
- method/path/status observability is retained.

They do not prove the currently deployed `stegverse.org -> TVC` path is running this source. TVC #328 remains pending until authentic deployed ingress evidence demonstrates the active public path cannot persist authorization-code query material.

## Remaining sequence

1. Implement middleware and Uvicorn configuration.
2. Add adversarial tests containing OAuth-like `code`, `state`, bearer-like, and arbitrary query values and prove none appear in logs.
3. Update README in the same functional change set.
4. Validate under repository checks and merge only when green.
5. Deploy through the existing Service Gateway owner path.
6. Produce authentic deployed-ingress observation without using a real provider authorization code.
7. Reconcile TVC #328/#317 only after that deployed observation.

## Manual work

None during source implementation/validation. Do not initiate Google consent or provider authorization from this task.
