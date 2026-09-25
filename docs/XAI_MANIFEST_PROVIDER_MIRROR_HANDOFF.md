# Manifest-selected xAI/Grok provider — LLM Adapter mirror handoff

Date: 2026-09-25 CDT
Existing canonical coordination task: `EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001`
Canonical coordination handoff: `StegVerse-Labs/.github/docs/EPHEMERAL_STEGBROWSER_EXTERNAL_AI_ACTIVATION_MIRROR_HANDOFF.md`
Task observational COSV: `10100000103000`
Registry read: generation 243; canonical task record coordination_state `PROPOSED`.
Adapter existing owners: `docs/ECOSYSTEM_CHAT_MIRROR_HANDOFF.md`; distributed workload #272 / PR #273 and bounded executor #274 / PR #275 complete source owners. This change does not re-open or replace their ownership.

## Scope and implementation

Add optional provider `xai` / alias `grok` through existing `build_http_provider_client` in `llm_adapter/http_provider_clients.py`. The client implements existing `ProviderClient.complete(ProviderRequest) -> ProviderResponse` and must be explicitly injected under a named `SourceDescriptor`; no second broker, runtime, scheduler, route authority or custody path is introduced. The deployed sovereign local/private provider remains independently sufficient. Chat-completions compatibility is used because current normalized request/response shapes match the xAI documented `/v1/chat/completions` interface. Later adoption of xAI's preferred Responses API is distinct and requires a governed payload/response translation.

The client rejects any endpoint other than HTTPS `api.x.ai` or `mtls.api.x.ai` chat completions, refuses manifest/provider mismatch, accepts only an explicitly injected scoped API key at its call boundary, and never loads `XAI_API_KEY` implicitly. Actual model, response ID, completion reason, measured prompt/completion/total tokens and any native cost tick fields remain response-bound metadata. Absent measured usage or structurally invalid output fails closed with actionable `XAI_RESPONSE_INVALID`. Exceptions enter the already-existing distributed executor as source-scoped `FAILED` contributions. Secrets cannot enter normalized metadata.

## Preservation of both customer and development scopes

Ecosystem Chat accepts user or ecosystem-originated manifests; the manifest declares purpose, named participants, scope, processing path and permitted capabilities. This adapter is one optional provider selected by an already-admitted manifest, not an AI deliberation authority. Parallel contributions are independent; disagreement and uncertainty survive reconciliation. Challenge/sequential tasks still require an independently governed derived-input contract. ChatGPT-assisted development is only one consumer of the same reusable components; ordinary users may request multi-LLM analysis with results returned to Ecosystem Chat.

## Exact authentic execution path and evidence

```text
existing user/ecosystem task -> exact manifest/WorkerCoordinator claim+fence
 -> admitted retained StegBrowser node/ephemeral lease (at most 900s)
 -> exact InTr ingress ALLOW -> TV/TVC+SKAP scoped xAI credential at provider edge
 -> xAI native HTTP response or actionable non-ALLOW provider failure
 -> existing distributed workload contribution with source/model/usage hashes
 -> required InTr egress -> org-local predecessor-linked receipt continuity
 -> observed disposable StegBrowser teardown, retaining non-secret node identity
 -> conditional organization batch / direct Master Records acknowledgement only where required
 -> exact linked Master Records reconstruction and Ecosystem Chat governed return.
```

Historical A3 source-refresh applies only to its exact invocation, not as a universal xAI or external-AI gate. Missing external ledger readback is EVIDENCE_REACHABILITY, not a synthetic DENY or proof of runtime failure. On observed DENY repair under existing owner and proceed to next authentic disposition; terminal FAIL_CLOSED is preserved. Provider output, agreement, runtime code and fixture receipts are not governance or custody proof.

## Evidence posture and next transitions

This branch implements source transport and deterministic unit fixtures only. Tests cover declared xAI selection, unauthorized provider mismatch, explicit scoped credential, endpoint containment, required response/usage, no leaked key, two-source local+xAI contribution, and optional xAI non-ALLOW while local succeeds. **No live xAI call, TVC operation, InTr decision, WorkerCoordinator claim/fence, authentic ephemeral lease, observed teardown, organization receipt, Master Records reconstruction or Site publication is claimed by these source changes.**

The existing external-AI coordination task continues its already-declared first live OpenAI and independent Claude goals. Grok is an optional additional provider whose activation should not displace those proofs. For live Grok verification use a non-private user-facing Ecosystem Chat manifest, exact admitted scoped credential, and actual provider-side measured usage. Return first authentic non-ALLOW disposition or ALLOW with exact organization and Master Records readback. If xAI credentials/provider or resident ledger access are not currently available, preserve non-observation without creating another device or runtime.

## Source surfaces

- `llm_adapter/http_provider_clients.py`
- `tests/test_http_provider_clients.py`
- `tests/test_distributed_executor.py`
- `README.md`
- `docs/XAI_MANIFEST_PROVIDER_MIRROR_HANDOFF.md`

Status: SOURCE_IMPLEMENTED, FIXTURE_VALIDATION_PENDING_CI, LIVE_PROVIDER_NOT_OBSERVED. No release, deployment or propagation claim.
