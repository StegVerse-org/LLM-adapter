# LLM Adapter Mirror Handoff

## Source of truth

Organization: `StegVerse-org`  
Repository: `LLM-adapter`  
Canonical branch: `main`  
Canonical Ecosystem Chat activation owner: `StegVerse-org/LLM-adapter#18`  
Parent four-app goal: `StegVerse-Labs/Site#239`  
Common StegGate runtime binding owner: `StegVerse-Labs/StegCore#70`  
Canonical local-model/runtime owner: `StegVerse-002/micro-node-runtime#16/#22`  
Canonical local-model binding task: `tasks/LLMA-CANONICAL-LOCAL-MODEL-BINDING-018.json`  
Completed transport/evidence adapter: `tasks/LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019.json`  
Completed same-carrier executor implementation: `tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json`  
Scoped handoff: `docs/SOVEREIGN_CARRIER_EXECUTION_MIRROR_HANDOFF.md`  
Declared path: healthy node -> LLM-adapter (transport only) -> SDK (manifest build + submit) -> `StegVerse-org/.github` -> Interlock/InTr => Org Ledger. No machine carrier is awaited; `StegVerse-Labs/.github#60 / SHWP-ECOSYSTEM-CHAT-INFERENCE-001` owns only the optional sovereign local-model route.

Live repository state, task records, scoped handoffs and organization ledger transition receipts supersede older chat summaries.

## Active goal state

```text
Repository-local governed path implementation: COMPLETE
Portable StegGate consumer: COMPLETE + VALIDATED
Canonical StegGate runtime identity binding: COMPLETE + VALIDATED
Canonical local model development/runtime: COMPLETE_RELEASED
Persistent canonical local endpoint proof: COMPLETE_MERGED_VALIDATED
Heartbeat-owned persistent model lifecycle: COMPLETE_MERGED_VALIDATED
Heartbeat -> local TVC route invocation: COMPLETE_MERGED_VALIDATED
TVC credential-free route evaluator: COMPLETE_MERGED_SOURCE / live observation pending
Transport/evidence adapter task 019: COMPLETE_RELEASED
Canonical carrier execution task 020: COMPLETE_RELEASED
Public runtime documentation reconciliation: COMPLETE_MERGED_VALIDATED
Sovereign provider execution transition: FAIL_CLOSED -> LLMA-368-D1
Provider-usage transition: FAIL_CLOSED -> LLMA-368-D2
Same-execution transition receipt chain: FAIL_CLOSED -> LLMA-368-D3
Ecosystem Chat activation transition: FAIL_CLOSED -> LLMA-368-D4
Site activation transition: FAIL_CLOSED -> LLMA-368-D5
Manual user tasks: NONE
Repository implementation claim: RELEASED
Session continuation role: NONE_AWAITED (each remaining item is a manifest-transition disposition)
```

Repository implementation completion does not imply public Ecosystem Chat activation.

### Remaining manifest-transition dispositions

Measured against `StegVerse-org/.github:docs/ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md` (Conformance standard): no external machine, receiver or observer is awaited, every action by manifest is a state transition, and every non-`ALLOW` carries the six fields below. Master Records reconstruction is not a predicate of any of them.

```json
[
  {"id": "LLMA-368-D1", "disposition": "FAIL_CLOSED",
   "failure_code": "PROVIDER_EXECUTION_TRANSITION_NOT_RECORDED",
   "failed_predicate": "org_ledger_transition_receipt_present_for_provider_execution_manifest",
   "required_evidence_or_repair": "submit the provider-execution manifest; its organization ledger transition receipt is the evidence",
   "retry_entrypoint": "POST /api/sdk/manifest/submit",
   "owning_existing_goal": "LLMA-DECLARED-PATH-CONFORMANCE-368",
   "next_attempt": "next manifest submission selecting this route"},
  {"id": "LLMA-368-D2", "disposition": "FAIL_CLOSED",
   "failure_code": "PROVIDER_USAGE_TRANSITION_NOT_RECORDED",
   "failed_predicate": "provider_usage_recorded_in_local_ledger_and_transition_receipt",
   "required_evidence_or_repair": "the local provider-usage ledger record and the transition receipt of the same execution",
   "retry_entrypoint": "POST /api/sdk/manifest/submit",
   "owning_existing_goal": "LLMA-DECLARED-PATH-CONFORMANCE-368",
   "next_attempt": "recorded with the next provider-execution transition (D1)"},
  {"id": "LLMA-368-D3", "disposition": "FAIL_CLOSED",
   "failure_code": "SAME_EXECUTION_TRANSITION_CHAIN_NOT_RECORDED",
   "failed_predicate": "ingress_execution_and_egress_receipts_share_one_execution_in_org_ledger",
   "required_evidence_or_repair": "ingress ALLOW, provider execution and exact-response egress ALLOW receipts bound to one execution",
   "retry_entrypoint": "POST /api/sdk/manifest/submit",
   "owning_existing_goal": "LLMA-DECLARED-PATH-CONFORMANCE-368",
   "next_attempt": "with the next provider-execution transition (D1)"},
  {"id": "LLMA-368-D4", "disposition": "FAIL_CLOSED",
   "failure_code": "ECOSYSTEM_CHAT_ACTIVATION_TRANSITION_NOT_RECORDED",
   "failed_predicate": "zero_blocker_activation_manifest_transition_in_org_ledger",
   "required_evidence_or_repair": "an activation manifest whose transition receipt cites D1-D3",
   "retry_entrypoint": "POST /api/sdk/manifest/submit",
   "owning_existing_goal": "LLMA-DECLARED-PATH-CONFORMANCE-368",
   "next_attempt": "after D1-D3 are ALLOW"},
  {"id": "LLMA-368-D5", "disposition": "FAIL_CLOSED",
   "failure_code": "SITE_ACTIVATION_TRANSITION_NOT_RECORDED",
   "failed_predicate": "site_activation_manifest_transition_in_org_ledger",
   "required_evidence_or_repair": "a Site activation manifest whose transition receipt cites D4",
   "retry_entrypoint": "POST /api/sdk/manifest/submit",
   "owning_existing_goal": "LLMA-DECLARED-PATH-CONFORMANCE-368",
   "next_attempt": "after D4 is ALLOW"}
]
```

## Installed governed path

```text
Site request
-> LLM-adapter governed consumer
-> canonical StegGate runtime identity validation
-> governed transition package
-> canonical StegGate + coherence gate
-> provider callback only after ALLOW + coherence ALLOW
-> heartbeat-owned canonical micro-node model process
-> exact persistent local runtime proof
-> canonical TVC route evaluation
-> ROUTE_ADMITTED / credential_requirement NONE
-> StegVerseLocalHTTPProviderClient private/loopback transport
-> provider response + measured usage
-> provider usage persistence
-> authenticated provider-usage custody
-> transition custody
-> reconstruction PASS for both chains
-> immutable zero-blocker activation receipt
-> Site automatic import
-> Publisher/wiki projections
```

## Production topology

`StegVerse-002/micro-node-runtime` owns the model and server. `StegVerse-Labs/.github` owns heartbeat process lifecycle, claims, fences and cycle leases. `TC/TVC` owns credential semantics; this local route requires credential class `NONE`. `StegVerse-Labs/TVC` owns route authority. LLM-adapter owns private provider transport and provider-usage evidence. Master Records is limited to downstream recording of released organization batch receipts for cross-organization reconstruction; the organization ledger holds the record and custody stays with the organization. No application-specific parallel model authority, route authority, heartbeat, scheduler, worker registry, StegGate evaluator, or custody authority is authorized.

## Local model development/runtime — COMPLETE_RELEASED

`SOVEREIGN-LOCAL-MODEL-001` is complete in `StegVerse-002/micro-node-runtime`. The formally developed `stegverse-reference-lm-v1` trains from repository-local corpus data, executes locally without hosted inference or remote weights, and is explicitly bounded as a reference model rather than a production-scale foundation LLM.

The descriptive `select a local model/runtime` boundary is superseded by real discovery, launch, private serving, inference, proof, measured usage, and persistent endpoint behavior.

## Task 019 — COMPLETE_RELEASED

`LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019` merged through PR #134 and released its claim. The existing `execute_verified_local_model` path validates canonical proof identity, uses `StegVerseLocalHTTPProviderClient`, captures MEASURED prompt/completion/total-token and latency evidence, and records provider usage in the local usage ledger, closing on the organization-ledger transition receipt (the Master Records provider-usage submission clients it reused at merge were removed under #368).

## Task 020 — COMPLETE_RELEASED

Canonical source of truth: `tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json`.

```text
PR: #135
head: dbb9558648c9c717d713b941487c48761dd104c6
merge: 72934c7cf135ce2953591a81fe01e16c9719ec2f
validation_matrix: PASS
claim_state: COMPLETE_RELEASED
github_token_required_for_production: false
github_actions_production_role: false
credential_authority_model: TC/TVC
credential_requirement: NONE
```

Installed executor behavior:

```text
TVC ROUTE_ADMITTED receipt
-> exact canonical runtime_proof_hash binding
-> exact private endpoint binding
-> credential_requirement NONE
-> github_token_required false
-> reject route/execution authority escalation
-> execute exact endpoint through StegVerseLocalHTTPProviderClient
-> persist request/response hashes + MEASURED usage
-> local usage ledger + organization-ledger transition receipt
   (downstream, non-gating: Master Records may record the released organization batch)
-> advance to same-execution transition reconstruction
```

Implementation surfaces:

```text
scripts/execute_canonical_sovereign_route.py
tests/test_execute_canonical_sovereign_route.py
tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json
docs/SOVEREIGN_CARRIER_EXECUTION_MIRROR_HANDOFF.md
```

No LLM-adapter implementation claim remains active for this lane.

## No-GitHub-token production boundary

GitHub repository access is not part of the production model/runtime path and no GitHub token is a release or activation condition.

Current upstream sequence includes:

```text
micro-node persistent endpoint: COMPLETE_MERGED_VALIDATED
heartbeat persistent lifecycle: COMPLETE_MERGED_VALIDATED
heartbeat automatic TVC invocation: COMPLETE_MERGED_VALIDATED
TVC canonical proof compatibility: COMPLETE_MERGED_SOURCE
orphan recovery: StegVerse-Labs/.github#78 COMPLETE_RELEASED
G20 lifecycle downstream record (non-gating): master-records/orchestration#27 COMPLETE_RELEASED
hosted GitHub activation/persistence retirement: StegVerse-Labs/.github#79 COMPLETE_RELEASED
```

GitHub Actions, Render, Cloudflare, Vercel, GitHub Models, OpenAI and Anthropic are not canonical production heartbeat, inference, credential, route, custody, or availability authorities. Optional hosted-provider interoperability lanes remain separate.

## Public documentation reconciliation — COMPLETE_MERGED_VALIDATED

```text
goal_id: LLMA-PUBLIC-RUNTIME-DOCS-001
originating_session_goal: publicly distributed adapter documentation must match the canonical sovereign runtime and TV/TVC authority model
superseded_pr: #137 CLOSED
authoritative_pr: #138 MERGED
merge_commit: 982114d3c5965a62ffff74195969bcf9db7cc55d
pr_head: f34955699c2a4e1ea1835f834b508d0e76869f6e
pr_validate_run: 31524832518 SUCCESS
pr_architecture_guard_run: 31524832495 SUCCESS
pr_provider_usage_run: 31524832524 SUCCESS
successor_main_validate_run: 31524940882 SUCCESS
claim_state: COMPLETE_RELEASED
collision_boundary: documentation/capability projection only; local-model/runtime, task 019, task 020, heartbeat, TVC, and Master Records implementation remain canonical elsewhere
```

Public truth now installed on canonical `main` in:

```text
README.md
adapter.capabilities.json
LLM_ADAPTER_MIRROR_HANDOFF.md
```

The public documentation now states that the canonical production route is sovereign local runtime; TC/TVC owns credential semantics and route authority; the local route credential class is `NONE`; GitHub tokens and GitHub Actions are not production inference prerequisites; local runtime discovery/launch/proof and the formally developed local reference model are already complete/released; task 020 is complete/released; and the remaining activation gap is machine-owned runtime observation, custody/reconstruction, Site activation, and downstream propagation.

## Current evidence posture

```text
repository implementation: COMPLETE
local model/runtime implementation: COMPLETE_RELEASED
same-carrier executor: COMPLETE_RELEASED
public runtime documentation: COMPLETE_MERGED_VALIDATED
provider execution transition: FAIL_CLOSED -> LLMA-368-D1
provider-usage transition: FAIL_CLOSED -> LLMA-368-D2
same-execution transition receipt chain: FAIL_CLOSED -> LLMA-368-D3
activation transition: FAIL_CLOSED -> LLMA-368-D4
Site activation transition: FAIL_CLOSED -> LLMA-368-D5
```

## Machine-owned continuation

```text
model/runtime: StegVerse-002/micro-node-runtime#16/#22
heartbeat process lifecycle and carrier: StegVerse-Labs/.github#60 / SHWP-ECOSYSTEM-CHAT-INFERENCE-001
orphan recovery: StegVerse-Labs/.github / RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
credential authority: TC/TVC / credential class NONE
route authority: StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
provider transport/usage: StegVerse-org/LLM-adapter#18 + task 020 COMPLETE_RELEASED
organization record: organization ledger (custody stays with the organization)
downstream recorder of released batch receipts (non-gating): master-records/orchestration
site activation: StegVerse-Labs/Site#239/#242
required downstream ingestion after immutable verified activation: GCAT-BCAT-Engine/Publisher, StegVerse-Labs/admissibility-wiki, StegVerse-002/stegguardian-wiki
```

No carrier, receiver or observer is awaited. Each remaining item is a manifest-transition disposition (LLMA-368-D1..D5 below) whose next attempt is a manifest submission; it is not a runtime observation gap.

No workflow dispatch, artifact download, file movement, screenshot confirmation, receipt construction, blocker transcription, credential copying, or manual publication task is required.

## Downstream destinations

Only after the activation manifest transition (LLMA-368-D4) is recorded in the organization ledger; Master Records receives released organization batches:

```text
master-records/orchestration (optional non-gating downstream recording; not a release condition)
StegVerse-Labs/Site
GCAT-BCAT-Engine/Publisher
StegVerse-Labs/admissibility-wiki
StegVerse-002/stegguardian-wiki
```

No downstream activation is claimed from repository completion, CI success, local-model proof, route validation, transport validation, or session archival.

## Authority boundary

```text
provider output != authority
usage measurement != admissibility
local persistence != custody
custody receipt != execution authority
reconstruction PASS != execution authority
workflow artifact != live evidence
runtime identity validation != public provider execution
local model proof != product activation
TVC route admission != execution authority
transport/evidence adapter success != canonical carrier activation
verified receipt != release authority
session archival != activation
```

## Release posture

No release or tag is authorized while dispositions LLMA-368-D1..D5 remain non-ALLOW or required downstream ingestion is incomplete.

Task 019, task 020, local-model/runtime implementation, and public-runtime-doc reconciliation claims are released. No session should reopen their implementation unless directly observed evidence creates a new bounded task.

MERGED INTO canonical runtime continuation: `StegVerse-Labs/.github#60 / SHWP-ECOSYSTEM-CHAT-INFERENCE-001` + `StegVerse-Labs/.github/handoffs/generated/RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28.json` + `StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json`; `master-records/orchestration` receives released organization batches downstream and is not part of the runtime continuation.

## Session consolidation

The following requirements from the current session are durable in repository state rather than remaining only in chat:

1. no GitHub token in the canonical production SDK/LLM runtime path;
2. TV/TVC owns credential semantics and route authority;
3. generic SDK users do not receive person-specific evaluator routes;
4. local-model selection is executable, not descriptive;
5. a local model is formally developed;
6. the local reference model is not misrepresented as production-scale;
7. completed local-model/runtime and carrier-executor implementation is not duplicated by another session;
8. public README and capability manifest reflect the canonical sovereign route;
9. product activation remains distinct from repository implementation, CI success, and session archival.

Requirements 1–9 are transferred or complete. Product activation is disposition LLMA-368-D4, retried by manifest submission; nothing is awaited from a machine owner, and no unique implementation, validation, integration, or propagation role from this session remains in LLM-adapter.

## Completion accounting

```text
LLM-adapter developed carrier surfaces: 4/4
scaffolding/stubs in canonical local execution path: 0
carrier executor deterministic validation: PASS
implementation claim: RELEASED
public runtime docs required files: 3
public runtime docs developed: 3/3
public runtime docs hosted validation: COMPLETE
public runtime docs main integration: COMPLETE
public runtime docs claim: RELEASED
provider execution transition: FAIL_CLOSED (LLMA-368-D1)
provider-usage transition: FAIL_CLOSED (LLMA-368-D2)
same-execution transition receipt chain: FAIL_CLOSED (LLMA-368-D3)
Site/downstream propagation: PENDING_ACTIVATION
repository implementation completeness: 100%
product activation completeness: not 100%
session-specific requirements transferred-or-complete: 9/9
```

## Execution ownership and collision partition

Standard: `StegVerse-Labs/Continuity/docs/REPOSITORY_HANDOFF_STANDARD.md` / `stegverse.handoff-execution-ownership/v1`.

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: LLMA-HANDOFF-OWNERSHIP-ADOPTION-214
  execution_owner: repo-standards #37 integration lane + LLM-adapter repository owner
  claim_state: CLAIMED_FOR_INTEGRATION
  worker_registry_ref: StegVerse-Labs/repo-standards#37 + StegVerse-org/LLM-adapter#214 + branch docs/handoff-ownership-adoption-214
  manual_execution_allowed: true
  manual_allowed_role: integration
  collision_scope: execution-ownership metadata in LLM_ADAPTER_MIRROR_HANDOFF.md only; excludes specialized handoffs/tasks, Ecosystem Chat product/runtime work, provider execution, runtime observation, custody/reconstruction, Site activation, credentials, claims/fences/leases, release, and cross-repository propagation
  release_condition: this textual root-handoff migration is validated, merged, issue #214 is reconciled, and repo-standards adoption state is updated
  next_executable_action: validate and merge ownership metadata only; do not execute the canonical carrier/runtime/activation chain manually
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: LLMA-ACTIVE-WORK-AGGREGATE
  execution_owner: current per-task machine/repository owner named by data/llm-adapter-orchestration-state.json, scoped handoffs/tasks, issues/claims/fences/leases, and canonical upstream/downstream handoffs
  claim_state: MACHINE_OWNED
  worker_registry_ref: data/llm-adapter-orchestration-state.json + tasks/LLMA-*.json + current docs/*_MIRROR_HANDOFF.md + StegVerse-org/LLM-adapter#18 + StegVerse-Labs/.github#60 + StegVerse-Labs/TVC route task + master-records/orchestration + StegVerse-Labs/Site#239/#242
  manual_execution_allowed: false
  manual_allowed_role: observation
  collision_scope: real same-carrier provider execution, runtime observation, provider-usage persistence/custody, transition reconstruction, immutable activation receipt, Site activation, downstream ingestion, service gateways, HIL runtime, Ecosystem Chat, public knowledge, VACC/governed retrieval, and any specialized task with a current owner
  release_condition: newest valid scoped handoff/task/claim/fence/lease/receipt explicitly releases or supersedes the exact collision scope
  next_executable_action: submit the next manifest through POST /api/sdk/manifest/submit; every non-ALLOW carries the six standard fields; do not duplicate completed task 019/020 or upstream model/TVC/heartbeat authority
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: LLMA-AUTHORITY-BOUNDARY-AGGREGATE
  execution_owner: applicable model/route/credential/custody/activation/release authority -> ecosystem governance
  claim_state: ESCALATED
  worker_registry_ref: LLM_ADAPTER_MIRROR_HANDOFF.md + current upstream/downstream authority handoffs + TV/TVC credential authority records
  manual_execution_allowed: false
  manual_allowed_role: reconciliation
  collision_scope: model/runtime authority, TV/TVC credential and route authority, provider authorization, custody authority, Site activation, publication/release authority, admissibility/certification authority, deployment authority, and cross-repository mutation authority
  release_condition: exact bounded authority is explicitly granted through its canonical mechanism
  next_executable_action: fail closed; repository completion, CI PASS, local-model proof, route validation, transport validation, handoff assignment, or migration metadata do not create activation/release/execution authority
```

### COMPLETED / SUPERSEDED

- Tasks 019 and 020, local-model/runtime implementation, and public-runtime documentation remain complete/released at their recorded scopes and are not reopened by this migration.
- Any inference that pending runtime observation, custody/reconstruction, Site activation, or downstream propagation is manually startable is superseded by the machine-owned aggregate above.
- Any inference that repository implementation completeness or this metadata migration proves product activation, release, provider execution, custody, or downstream activation is superseded/prohibited.


## Resident execution rendezvous — issue #240

A new non-authorizing StegVerse Service Gateway rendezvous is being added to eliminate the need for coordinating ChatGPT/browser sessions to possess SSH/systemd/server-control access to a sovereign resident.

Canonical handoff: `docs/RESIDENT_RENDEZVOUS_SERVICE_GATEWAY_MIRROR_HANDOFF.md`.

The Gateway admits only the exact existing `stegos_kv_intr_chain` resident request in v1, stores it durably, serves it to the exact target node via outbound resident fetch, and records a bounded acknowledgement. It cannot transport arbitrary commands, mint WorkerCoordinator claims/fences, grant execution authority, access credentials, or substitute its acknowledgement for authentic resident evidence.

Canonical native/StegDeploy gateway profiles now provision the rendezvous on the existing durable Service Gateway state volume. Runtime deployment/public observation remain separate from source merge.


## 2026-08-31 canonical Device-KV request 003 propagation — issue #249

The current Service Gateway resident request identity is:
```text
RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003
```

The v1 rendezvous remains bounded to the StegOS/KV chain only. Resident request IDs are now explicitly allowlisted rather than accepting arbitrary non-empty values:
- `...-001` — historical legacy generation; legacy/current exact step vectors only;
- `...-002` — superseded HB-carrier generation; current three-step vector only;
- `...-003` — current shared-HB-signal terminal generation; current three-step vector only.

The Gateway does not infer freshness, execution, claim/fence, HB progression, credential, route, transition, receiving, repository, or deployment authority from the request generation. The current fixture and downstream handoff use request 003.


## 2026-08-31 resident discovery lease — issue #251

The rendezvous now has a non-authorizing resident advertisement/discovery seam so Site does not hard-code a resident selector.

```text
resident -> bound GET /api/resident-rendezvous/v1/requests?target_node_ref=SV-NODE-...
Gateway  -> refresh the existing short-lived advertisement from that genuine poll
Site     -> GET /api/resident-rendezvous/v1/discovery
```

Only the exact current lane is admitted:
- consumer `stegos_kv_intr_chain`;
- current request `RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003`;
- credential authority `TV/TVC`;
- Gateway execution authority `NONE`;
- advertisement/discovery authority effect `NONE_DISCOVERY_ONLY`.

Discovery returns:
- `AVAILABLE` only for exactly one fresh compatible resident;
- `UNAVAILABLE` for none;
- `AMBIGUOUS` for more than one.

No advertisement or discovery result grants claim, fence, execution, credential, route, transition, receiving, HB progression, KV mutation, deployment, or release authority.


## 2026-08-31 canonical target + submitter provenance discovery — issue #253

The existing advertisement/discovery seam is now tied directly to authentic resident polling rather than requiring a separate advertisement action.

A bound resident poll:
```text
GET /api/resident-rendezvous/v1/requests?target_node_ref=SV-NODE-<24 hex>
X-StegVerse-Node-Ref: same exact SV-NODE-<24 hex>
```
refreshes the existing short-lived `stegverse.resident-rendezvous.advertisement/v1` record for request 003. Noncanonical selectors are rejected for the current discovery contract.

`GET /api/resident-rendezvous/v1/discovery` remains the single public discovery surface. It returns `AVAILABLE` only for exactly one fresh canonical sovereign resident, `UNAVAILABLE` for none, and `AMBIGUOUS` for more than one.

For current request 003, the wire-compatible fields:
```text
submitter_authorization_ref
X-StegVerse-Authorization-Id
```
must contain:
```text
node-receipt-1-sha256:<64 lowercase hex>
```
which is a non-secret provenance reference to the browser's already-validated Node Receipt #1. The Gateway checks body/header identity and format only. It does **not** interpret that reference as credential, execution, route, transition, receiving, or publication authority.

Legacy 001/002 request generations retain compatibility semantics; the stricter Receipt #1 provenance requirement applies to current request 003.

Source merge does not prove a production resident is polling, that discovery returns AVAILABLE publicly, or that a request is stored/consumed.


## 2026-09-03 StegIndex resident-root binding receipt

Issue #267 source seam is complete.

```text
PR: #268
head: 73b677883534fa812b57b2262d6bd57c83472478
merge: 6ea118da2e6c6890a1787dc09b8a74b70be94446
validate run: 33765715563 SUCCESS
Coinbase SKAP validation run: 33765715717 SUCCESS
```

Installed StegDeploy behavior:
- a local `vendor/StegIndex` tree is bound only when the complete canonical preflight dependency set is present;
- `STEGVERSE_STEGINDEX_SOURCE_ROOT` points to that exact verified local root;
- `STEGVERSE_REPO_ROOTS_JSON["StegVerse-Labs/StegIndex"]` points to the same exact root;
- incomplete vendored StegIndex source is omitted fail-closed.

This closes only the downstream StegDeploy source-locator/materialization seam. It does not prove authentic resident StegIndex materialization, blocker-derived preflight invocation, runtime activation, or any authority promotion. TV/TVC remains credential authority; GitHub-token runtime authority remains NONE.


## StegBrowser Master Records relay intake

Canonical Goal `StegVerse-Labs/.github:MASTER-RECORDS-STEGBROWSER-ENDPOINT-BINDING-001` reuses the existing Service Gateway and TV/TVC `service_gateway_master_records` credential role as a non-authorizing transport that hands already-closed, released state-transition receipts downstream to the Master Records recorder in `master-records/orchestration` (not custody; custody stays with the organization).

Source surfaces:
- `llm_adapter/stegbrowser_master_records_state_transition_relay.py`;
- `tests/test_stegbrowser_master_records_state_transition_relay.py`;
- `docs/STEGBROWSER_MASTER_RECORDS_STATE_TRANSITION_RELAY_MIRROR_HANDOFF.md`;
- `llm_adapter/combined_gateway.py` advertisement plus bounded relay route.

The relay accepts only the immutable StegBrowser nonce/count-1 custody receipt and complete exact tuple, keeps credential material server-side, and requires authoritative `RECORDED + reconstruction_status=PASS` with exact digest equality. It grants no custody, execution, transition, publication, provider, route, or governance authority. It is optional transport toward a downstream record: its reply is not a predicate of any declared-path transition, and no transition waits on it.


## 2026-10-04 Ecosystem Chat capability-addressed route mapping

Canonical hybrid-collab PR #35 supplies provider-neutral capability, media and entitlement metadata. LLM-adapter reuses the existing recorded SDK manifest-build crossing rather than adding an ingress or broker. An AVAILABLE external text/reasoning descriptor constrained to an ephemeral surface selects only the existing StegBrowser manifest processing pair `stegbrowser / stegverse.route.stegbrowser.v1`; provider/model mismatch is DENY and no substitution is permitted. `llm_adapter.external_llm_connection` remains the text/reasoning execution primitive.

Requested-but-unentitled `UPGRADE_REQUIRED` and `PURCHASE_REQUIRED` outcomes terminate before manifest construction/provider invocation and are recorded by the existing SDK transition ledger as denied intended-action crossings. They remain semantically distinct from `PROVIDER_UNAVAILABLE`. Image/video/audio/code/science/research/data/other classes remain independently extensible and currently return an explicit no-compatible-adapter non-ALLOW rather than falling back to text.

Historical LLM-adapter PR #351 is design evidence only and remains closed/unmerged; no code or authority is imported from that branch. This mapping adds no broker, runtime, SDK ingress, credential authority, device prerequisite, authority plane or external-AI Node identity. Source/CI does not claim live specialized-provider execution.


## 2026-10-04 StegBrowser execution-owner correction

Re-reading current StegVerse-SDK main demonstrated that the installed Ecosystem Chat governed-ask and `stegbrowser` execution path resolves `stegbrowser.llm_browser_execution.execute_manifested_llm_browser_operation` through the StegBrowser owner. It does not traverse `llm_adapter.external_llm_connection`. The earlier capability-selection metadata from PR #361 named external_llm_connection as the execution primitive too strongly. The mapping now names StegBrowser as the execution owner and explicitly records external_llm_connection as a separate provider-neutral text/reasoning primitive not selected by this route. No new bridge, route, broker or authority is introduced merely to make the two implementations look contiguous.
