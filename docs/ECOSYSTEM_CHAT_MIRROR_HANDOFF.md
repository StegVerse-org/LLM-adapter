# Ecosystem Chat Runtime Mirror Handoff

## Active goal and authority

```text
goal_id: ECOSYSTEM-CHAT-SOVEREIGN-ACTIVATION
repository: StegVerse-org/LLM-adapter
branch: main
canonical_runtime_owner: StegVerse-org/LLM-adapter#18
canonical_model_runtime_owner: StegVerse-002/micro-node-runtime#16/#22
canonical_binding_task: tasks/LLMA-CANONICAL-LOCAL-MODEL-BINDING-018.json
canonical_execution_owner: StegVerse-Labs/.github#60 / SHWP-ECOSYSTEM-CHAT-INFERENCE-001
recovery_task: RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
custody_reconstruction_owner: master-records/orchestration
credential_authority: TV/TVC
third_party_deployment_dependency: NONE_ALLOWED
third_party_inference_platform_dependency: NONE_ALLOWED
production_provider_path: STEGVERSE_LOCAL_PRIVATE_ENDPOINT
production_activation_state: ACTIVE_MACHINE_CONTINUATION_PARENT_SAME_EXECUTION_PROOF_PENDING
session_specific_transport_task: LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019 COMPLETE_RELEASED
session_consolidation: MERGED_INTO_CANONICAL_WORKSTREAM
```

GitHub, GitHub Models, Render, Cloudflare, and similar services may remain mirrors, validation surfaces, or optional interoperability paths. None is production model-execution, heartbeat, custody, admissibility, route, or availability authority.

## Formally developed local model — complete and released

The descriptive “select a local model/runtime” step is gone. `StegVerse-002/micro-node-runtime/SOVEREIGN-LOCAL-MODEL-001` contains the repository-developed reference language model, repository corpus/training path, deterministic discovery, launch, OpenAI-compatible private serving, real-process inference proof, token/latency measurement, and validation.

```text
state: COMPLETE_RELEASED
validated_code_commit: 395d4013d1354c07bc3cf66c44f4f26f856c75fc
workflow_run: 31339534741
artifact_id: 9045384610
production_llm_equivalent: false
model_output_grants_authority: false
third_party_inference_required: false
```

`LLMA-LOCAL-RUNTIME-MODEL-017` is superseded as product authority and retained only as a compatibility fixture.

## Sovereign provider and transport/evidence path — complete and released

`StegVerseLocalHTTPProviderClient` accepts loopback/private/link-local/StegVerse-local endpoints in sovereign mode without external provider credentials. Task `LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019` preserves model hash, local-training metadata, measured prompt/completion/total tokens, and measured latency through the provider boundary and into the existing Master Records usage path.

```text
state: COMPLETE_RELEASED
pull_request: 134
merge_commit: 8be63bfd2eddae4092b945032de956e4e9a63576
merged_main_binding_run: 31342485740 SUCCESS
merged_main_binding_job: 93318434329 SUCCESS
merged_main_binding_artifact: 9046241885
artifact_digest: sha256:99216c44a21cafd619d900c8fcb79d73f8fff7dcb9707045e4c0da77fccfc6bc
```

## Superseded blocker — do not restore

The former failure mode in which LLM-adapter Actions attempted to check out the private `StegVerse-002/micro-node-runtime` repository is superseded by task 018. GitHub source-repository credentials do not belong in the production runtime path.

```text
superseded_blocker: LLM-adapter Actions credential cannot read private micro-node-runtime
superseded_workflow: canonical-sovereign-local-model-binding.yml
superseded_workflow_deleted_commit: e0c3c1e5d683d3066f869f205bc9034e630c2efb
github_token_required: false
github_actions_production_role: false
credential_requirement_for_repository_local_model: NONE
```

Do not reintroduce cross-private-repository checkout, PATs, GitHub runtime credentials, or hosted control-plane authority as an Ecosystem Chat activation requirement.

## Current execution state — recovery completed; parent is independently HANDOFF_READY

Current `StegVerse-Labs/.github` machine state supersedes the earlier recovery-pending text. The canonical recovery registry now records:

```text
RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
state: COMPLETED
transition: ORPHAN_LIFECYCLE_RECONSTRUCTED
recovery fencing token: 22
old fencing token: 20
old authority ended: true
old authority reused: false
Master Records custody valid: true
successor authority granted by recovery: false
```

The parent handoff `StegVerse-Labs/.github/handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json` is now independently `HANDOFF_READY`, and `authorizations/SHWP-ECOSYSTEM-CHAT-INFERENCE-001-independent-parent.json` is `AUTHORIZED`. The next legitimate machine transition is a fresh parent fence strictly greater than 22 on an admitted StegVerse task-control execution surface.

Recovery completion does not grant parent inference authority. Neither G18 terminalization nor a WorkerCoordinator-specific promotion cycle is a prerequisite. Heartbeat remains a noncausal reference for this independently admitted task-control execution.

## Exact production completion sequence

1. Preserve terminal orphan-recovery evidence; do not reacquire or replay recovery authority.
2. Parent `SHWP-ECOSYSTEM-CHAT-INFERENCE-001` independently acquires a fresh authorized fence `>22`.
3. Launch/observe the released canonical micro-node model as a live private process and keep it alive for the whole same-carrier execution.
4. TVC evaluates that exact endpoint and emits `ROUTE_ADMITTED` with `credential_requirement=NONE`, `github_token_required=false`, and no third-party execution dependency.
5. LLM-adapter consumes that exact admitted endpoint through `StegVerseLocalHTTPProviderClient`.
6. Real governed execution traverses E1 → model worker → E2.
7. Provider/model usage is measured and persisted for that execution.
8. `master-records/orchestration` records provider-usage reconstruction `PASS`.
9. `master-records/orchestration` records transition reconstruction `PASS` for the same execution and binds `same_execution=true`.
10. LLM-adapter emits immutable `receipts/ecosystem-chat-live-activation.verified.json` with `state=VERIFIED`, `blockers=[]`, valid result hash, and no authority escalation.
11. `StegVerse-Labs/Site` imports the verified receipt and reaches its Ecosystem Chat activation condition.
12. Publisher, admissibility-wiki, and stegguardian-wiki consume the verified Site propagation under their existing contracts.

No earlier level implies the next.

## Same-carrier runtime seam

`verify_sovereign_model_runtime.py` is proof-oriented and may terminate its probe process. Production activation therefore requires the canonical live model process to remain available across health/model-identity proof → TVC route admission → LLM-adapter request → E1/model/E2 evidence → usage persistence → Master Records custody/reconstruction. The process may be retired only after the bounded same-execution evidence path completes.

## Collision and authority boundaries

- Do not restore GitHub Models, Render, Cloudflare, GitHub Actions, PATs, or private-repository checkout as production blockers or authorities.
- Do not create another local model/runtime authority in LLM-adapter.
- Do not create a second heartbeat, worker registry, TV/TVC route authority, governance engine, or Master Records custody path.
- Recovery authority is continuity-only and may not execute parent inference.
- Provider output, usage measurement, workflow success, recovery completion, custody, or reconstruction alone do not grant activation authority.
- Activation requires the exact same-execution zero-blocker receipt and downstream verified consumption.

## Durable execution inventory

```text
SOVEREIGN-LOCAL-MODEL-001 | micro-node-runtime #16/#22 | COMPLETE_RELEASED
LLMA-LOCAL-RUNTIME-MODEL-017 | LLM-adapter | SUPERSEDED
LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019 | LLM-adapter #18 | COMPLETE_RELEASED
LLMA-CANONICAL-LOCAL-MODEL-BINDING-018 | MERGED_INTO_CANONICAL_WORKSTREAM | next: recovery then exact sovereign endpoint execution
RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28 | COMPLETED | fence 22 / old authority not reused
SHWP-ECOSYSTEM-CHAT-INFERENCE-001 | HANDOFF_READY / AUTHORIZED | next: fresh parent fence >22 and same-carrier execution
Master Records same-execution reconstruction | WAITING_ON_REAL_EXECUTION | provider-usage + transition PASS required
Site activation | WAITING_ON_VERIFIED_RECEIPT
Downstream propagation | WAITING_ON_VERIFIED_SITE_ACTIVATION
```

## Session consolidation

```text
MERGED INTO: StegVerse-org/LLM-adapter/tasks/LLMA-CANONICAL-LOCAL-MODEL-BINDING-018.json
ALSO CONTINUED BY: StegVerse-Labs/.github#60 / SHWP-ECOSYSTEM-CHAT-INFERENCE-001
RECOVERY: StegVerse-Labs/.github/control/worker-registry.d/ecosystem-chat-orphan-recovery-hb28.json
MODEL OWNER: StegVerse-002/micro-node-runtime#16/#22
CUSTODY OWNER: master-records/orchestration
unique_chat_owned_work_remaining: false
product_activation_complete: false
```

## Completion accounting

```text
session-specific developed surfaces: 10/10
session-specific scaffolding/stubs: 0
session-specific implementation claim: RELEASED
canonical local model development/runtime: COMPLETE_RELEASED
canonical provider/transport evidence seam: COMPLETE_RELEASED
recovery registry admission: COMPLETE
fresh recovery execution: COMPLETE / G22
fresh parent sovereign execution: PENDING
same-execution reconstruction: 0/2
immutable verified activation receipt: 0/1
Site activation: 0/1
downstream verified ingestion: 0/3
```


## Destination activation projection correction — issue #7

Direct inspection found that `scripts/write_ecosystem_chat_destination_activation_state.py` still derived its machine-readable destination topology from `render-production.yaml`, even though Render is explicitly superseded as production authority throughout this handoff.

The bounded issue #7 repair now uses the canonical sovereign source surfaces instead:

```text
data/ecosystem-chat-sovereign-orchestration-state.json
tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json
receipts/ecosystem-chat-live-activation.verified.json
```

The projection separates:

```text
released source/runtime contract
!=
observed live sovereign execution
!=
Master Records custody/reconstruction
!=
Site activation
```

The historical Site compatibility gate names are preserved so existing importers do not fork, but `same_origin_authenticated_deployment` now means a canonical sovereign runtime service was actually observed in verified live evidence. It no longer means a Render topology declaration.

Source completeness alone leaves live gates false. A valid live receipt must be `VERIFIED`, have `blockers=[]`, pass its canonical result hash, preserve all non-authority flags, and contain real provider usage plus provider-usage/transition custody and reconstruction evidence.

Task: `tasks/LLMA-ECOSYSTEM-CHAT-DESTINATION-PROJECTION-007.json`.

Machine-readable COSV notation is explicit on that task:

```text
task.v1 = L R U I V G O C M T B E A P
width = 14
concrete vector = null until canonical COSV projection emits it
```

This repair does not execute the sovereign parent task and does not fabricate `ecosystem-chat-live-activation.verified.json`. The actual next product transition remains the independently authorized fresh parent fence `>22` on an admitted StegVerse task-control execution surface.


## Independent-parent activation projection seam

A distinct post-parent evidence seam is now implemented under the existing issue #7 lane. It does **not** create a second inference/runtime owner.

`scripts/project_independent_parent_activation.py` consumes only the terminal machine records emitted by the already-authorized `StegVerse-Labs/.github#60` parent execution:

```text
receipts/ecosystem-chat-sovereign-inference/independent_parent_activation.latest.json
receipts/ecosystem-chat-sovereign-inference/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json
receipts/ecosystem-chat-sovereign-inference/tvc_local_model_route.json
receipts/ecosystem-chat-sovereign-inference/llm_adapter_sovereign_execution.json
receipts/ecosystem-chat-sovereign-inference/master_records_same_execution_reconstruction.json
```

The projection requires all terminal parent predicates, a fresh parent fencing token strictly greater than 22, exact parent activation hash verification, TVC route receipt hash binding, provider-usage event hash binding, Master Records reconstruction hash binding, `same_execution=true`, persistent conversational runtime readiness, `credential_authority=TV/TVC`, `credential_requirement=NONE`, no GitHub activation role, and no third-party inference dependency.

On success it writes the immutable local evidence surface:

```text
receipts/ecosystem-chat-sovereign-activation.verified.json
schema: stegverse.ecosystem_chat.sovereign_activation_projection.v1
state: VERIFIED
authority_effect: NONE
```

The destination-state writer accepts this sovereign projection as the preferred current evidence mode. The historical `stegverse.ecosystem_chat.live_activation.v1` receipt remains a compatibility input only; no hosted-gateway evidence is fabricated from the parent receipt.

The projection itself grants no activation, execution, route, custody, publication, release, or repository-mutation authority. Actual parent execution remains owned by `StegVerse-Labs/.github#60`; route authority remains TV/TVC; reconstruction remains Master Records.

### TVC persistence boundary — source merged, runtime observation pending

A successful local projection is still not equivalent to durable cross-repository/public evidence propagation, but the previously missing TV/TVC persistence source seam is now implemented, validated, and merged in `StegVerse-Labs/TVC`.

Canonical TVC continuation:

```text
task: TVC-ECOSYSTEM-CHAT-ACTIVATION-EVIDENCE-001
handoff: docs/ECOSYSTEM_CHAT_ACTIVATION_EVIDENCE_TRANSPORT_MIRROR_HANDOFF.md
adapter: tvc_ecosystem_chat_activation_evidence.py
validated head: 7af83362d3314105831b50240a23cf8e9079cb47
validation run: 33135951150 SUCCESS
merge: 4c8d3440fde168414c700f7e54909e81b2f27e1e
output: receipts/ecosystem-chat-activation-evidence/transport.latest.json
output state when genuinely executed: READY_FOR_SITE_IMPORT
credential authority: TV/TVC
GitHub runtime authority: NONE
Site mutation authority: NONE
publication authority: NONE
```

The TVC runtime persistence receipt is **not observed yet** because no terminal sovereign parent activation projection exists. After a genuine `ecosystem-chat-sovereign-activation.verified.json` is produced on the resident surface, an admitted TVC execution must verify it and persist the hash-bound packet. Site consumption remains separately owned by its current activation-retention lane (currently Site PR #474 / claim `SITE-ECOSYSTEM-CHAT-ACTIVATION-RETENTION-CREDENTIAL-CLEAN-471-20260823` or its reconciled successor). GitHub Actions and third-party platforms remain non-authorizing validation/transport surfaces only.
