# Ephemeral StegBrowser OpenAI TVC integration — canonical owner handoff

Goal: `EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001`
Central source: `StegVerse-Labs/.github/data/ephemeral-external-ai-reusable-component-profile.v1.json`
Existing convergence owner: `StegVerse-org/LLM-adapter#324`
Companion TVC branch: `StegVerse-Labs/TVC:feat/ephemeral-openai-task-bound-lease-20260924`

## Narrow implementation

Extend existing `llm_adapter.external_llm_connection` and `governed_external_provider_client` to route OpenAI through the existing TVC non-exportable broker, not `http_provider_clients.OpenAIHTTPProviderClient` or `OPENAI_API_KEY` from the process environment. The thin provider edge `openai_tvc_runtime_executor.py` projects exact OpenAI Responses semantics, verifies a TVC task-bound lease, sends an exact operation to existing TVC, normalizes a real provider result and measured native usage, and hands local transition evidence to the existing organization-ledger owner before separately required usage custody and external InTr egress. These source functions do not mint claims, leases, credentials, InTr decisions, Master Records confirmations or resident runtime capacity.

## Exact runtime boundaries

Existing WorkerCoordinator must first authentically claim and fence this exact task invocation. Existing StegBrowser must admit a bounded ephemeral lease. Existing Interlock/InTr must return a current exact OpenAI wire-request ingress ALLOW. Existing TVC owner must issue the task-bound `stegverse.tvc.ephemeral-openai-capability-lease/v1` using its authenticated admission verifier; this cannot be a Generation-3 measurement lease. Exact payload hashes in TVC and the LLM Adapter must converge. TVC independently verifies the lease, uses its existing non-exportable local vault operation broker, and returns only normalized non-secret response and usage with its single-use receipt. The organization owner wraps the provider event in the existing canonical state-transition receipt and appends the exact predecessor-linked organization transition, not a new ledger or adapter-owned custody. The selected transition's explicit custody contract decides whether independent Master Records acknowledgement is immediate or via a governed organization batch. Existing InTr must separately ALLOW exact response egress. StegBrowser must observe terminal temporary-session destruction while retaining node/task continuity.

This source change currently requires the org recorder callback and explicit usage custody before external egress. Its usage path follows the existing external LLM contract; org-local replay and conditional batch-custody policy must still be reconciled against the actual resident transition contract. A successful offline test or merge never proves the browser, WorkerCoordinator, provider, credential, org replay, Master Records or InTr runtime path is live.

## Independent lanes and error semantics

Native MyKV and its private AI assistant remain an independent lane. Existing Anthropic/Claude source path remains unchanged and is tested only after a genuinely governed OpenAI invocation. The historical StegBrowser A3 source-refresh requirement is relevant only to that exact A3 invocation. Inaccessible resident receipts remain EVIDENCE_REACHABILITY/UNKNOWN_NOT_FALSE. The first **authentic retained** failed organization transition determines the original component owner of any runtime repair. Terminal worker failure requires WorkerCoordinator expiry, canonical Registry state and an organization worker-expiry receipt, preserving immediate predecessor lineage.

Source checks: `tests/test_ephemeral_openai_governed_integration.py` must be included in existing convergence workflow at the exact PR head. No tokens or credentials in GitHub, workflow arguments, manifests or source fixtures.

## Current-fence authenticity correction

Adversarial exact-head tests showed that a caller could recompute the unkeyed JSON digest after substituting a worker claim or fence. The corrected `GovernedExternalProviderClient` and `openai_tvc_runtime_executor` require a **separate existing-resident `current_admission_verifier` callback**. That callback must read back the exact TVC-issued lease receipt and current WorkerCoordinator claim/fence, confirm the same invocation's active StegBrowser lease and exact InTr ingress, and return all canonical identity/digest fields plus `current_fence_active=true` and `browser_lease_active=true`. The adapter verifies strict exact equality with the proposed lease before invoking the TVC broker. Missing/stale/mismatched verification is a hard stop; the callback is not a new authority plane and cannot be replaced with source fixtures in live execution. The TVC broker independently requires its own authenticated issuance/fence verifier.

The source-level integration tests inject an **offline independent issuance snapshot only** and test forged worker/fence, wrong lease, request hash, governance DENY, organization-receipt binding, custody failure and egress failure. Successful fixture validation must not be promoted to authentic runtime proof. The exact existing authenticated resident verifier/readback hookup, original-org predecessor replay and actual StegBrowser session teardown remain runtime integration obligations.


### Independent organization predecessor readback for OpenAI

The ephemeral OpenAI adapter must receive both the existing `org_transition_recorder` and a **separate read-only `org_chain_verifier`** supplied by the original organization ledger owner. The recorder wraps the provider event in the existing canonical-state receipt and appends it to the original organization's hash-linked ledger. The verifier subsequently reads back that exact receipt and its immediate predecessor from the **existing** ledger. It must independently return the exact organization ID, appended receipt SHA-256, previous receipt SHA-256, original provider-event digest, and `predecessor_verified=true`. The adapter fails closed before usage custody or egress if that readback is absent, malformed, contradictory or unreachable. Merely hashing locally supplied receipt JSON does **not** demonstrate independent predecessor continuity. This adds no new store, runtime, scheduler, independent authorization or Master Records prerequisite.

The exact native OpenAI usage assertion now requires measured nonnegative integer input/output/total tokens, positive task input/output and `total=input+output`. Broker-returned provider evidence and use receipts are rejected if they carry protected credential field names or recognizable token prefixes, even when their metadata claims that no secret was exported. The source-only adversarial tests intentionally use fake credentials and fake custody callbacks; they cannot establish that any real provider or existing resident ran. The existing StegBrowser owner remains responsible for authentic ephemeral session destruction and the existing organization owner for worker/lease/transition receipts.


## Independent native vault-broker consumption confirmation

The actual credential-bearing process is the existing
`StegVerse-Labs/stegfin-governance#112` owner, beyond TVC PR #468's
forwarding-client validation. OpenAI's shared LLM Adapter now requires
`TV/TVC+WorkerCoordinator+Interlock/InTr+StegBrowser` readback at its
same-invocation verifier, matching the original TVC and native vault owner.
Provider output cannot be returned without the **native broker's**
`durable_consumption_receipt_ref` and exact task/invocation/wire request
digest/issuer confirmation on its non-secret use receipt. An adapter fixture,
direct OpenAI HTTP client or measurement-only TVC lease cannot replace
this evidence. Even a successful broker response is NOT StegBrowser
terminal-session destruction or complete organization replay; those remain
separate authentic transitions under their existing owners.

## Ecosystem Chat integration repair — 2026-09-25

Continued the existing PR #351 from `ddcaa3e4ad72befef601f2c99df03687e6cc191f` after reading central Registry generation 243 and the canonical external-AI handoff. No new task, claim, fence or runtime is created. The shared ProviderClient returned provider-canonical aliases and wire-request digests, but `distributed_workload.build_contribution` requires the exact declared alias and original envelope digest. An offline full OpenAI adapter-to-distributed-executor test reproduced `provider response identity does not match declared source`; the independent digest mismatch was also established by the existing exact-hash test.

The bridge now checks canonical provider, exact model, wire digest and provider response commitment before egress. After existing egress admission it projects the caller alias and envelope digest while retaining wire request hash, admitted provider response hash, both InTr receipt hashes and measured usage-event references. Both canonical OpenAI and ChatGPT alias compose with the existing executor. Alias tests cover Claude, Z.ai, DeepSeek and Kimi; provider/model/request/response tampering cannot reach egress.

Validation: 115 focused tests passed locally across the existing convergence workflow selection, OpenAI integration, distributed workload and distributed executor. All provider/admission/credential/org/custody fixtures remain OFFLINE TEST DOUBLES. Authentic hosted execution, browser lifecycle destruction, Site routing and organization/Master Records reconstruction remain NOT_OBSERVED. OpenAI companion TVC #468 and native vault-broker consumption remain independent requirements. Grok/Gemini still need provider-specific edge integration at these existing owners; no fake availability is advertised.

Session Prompt Count: 1. Historical Goal Prompt Count was not recorded in the canonical central handoff; this is one additional qualifying prompt, cumulative total UNVERIFIED. Preserve the goal and reconcile history without resetting it.
