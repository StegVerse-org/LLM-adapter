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
