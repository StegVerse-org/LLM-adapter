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
production_activation_state: ACTIVE_MACHINE_CONTINUATION_RECOVERY_THEN_SAME_EXECUTION_PROOF
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

## Current execution state — recovery is already HANDOFF_READY

The canonical recovery registry in `StegVerse-Labs/.github/control/worker-registry.d/ecosystem-chat-orphan-recovery-hb28.json` records:

```text
state: HANDOFF_READY
executor_binding: AUTHORIZED
required_capability: orphan_lifecycle_reconstruction
fresh_fence_required: true
minimum_fencing_token_exclusive: 20
g18_terminalization_required: false
worker_registry_cleanup_required: false
github_token_required: false
human_action_required: false
```

The recovery-only worker cannot execute parent inference authority. Any compliant StegVerse task-control executor advertising `orphan_lifecycle_reconstruction` may atomically acquire the recovery task under a fresh fencing token strictly greater than 20 and execute the bounded reconstruction.

Neither G18 terminalization nor a WorkerCoordinator-specific promotion cycle is a prerequisite. HB31 `RELEASE_COMPLETE` is sufficient as the released heartbeat reference for this activation chain; heartbeat reference state does not itself grant execution authority.

## Exact production completion sequence

1. Acquire the already `HANDOFF_READY` recovery task under a fresh authorized fence `>20`.
2. Execute `ecosystem-chat-orphan-recovery-worker` against the ended HB25/G20 checkpoint and canonical Master Records lifecycle custody.
3. Persist recovery `PASS`; old G20 claim/fence remain unusable and no parent inference authority is inherited.
4. Parent `SHWP-ECOSYSTEM-CHAT-INFERENCE-001` independently acquires another fresh authorized fence `>20`.
5. Launch/observe the released canonical micro-node model as a live private process and keep it alive for the whole same-carrier execution.
6. TVC evaluates that exact endpoint and emits `ROUTE_ADMITTED` with `credential_requirement=NONE`, `github_token_required=false`, and no third-party execution dependency.
7. LLM-adapter consumes that exact admitted endpoint through `StegVerseLocalHTTPProviderClient`.
8. Real governed execution traverses E1 → model worker → E2.
9. Provider/model usage is measured and persisted for that execution.
10. `master-records/orchestration` records provider-usage reconstruction `PASS`.
11. `master-records/orchestration` records transition reconstruction `PASS` for the same execution and binds `same_execution=true`.
12. LLM-adapter emits immutable `receipts/ecosystem-chat-live-activation.verified.json` with `state=VERIFIED`, `blockers=[]`, valid result hash, and no authority escalation.
13. `StegVerse-Labs/Site` imports the verified receipt and reaches its Ecosystem Chat activation condition.
14. Publisher, admissibility-wiki, and stegguardian-wiki consume the verified Site propagation under their existing contracts.

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
RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28 | HANDOFF_READY | next: fresh fence >20 and reconstruction now
SHWP-ECOSYSTEM-CHAT-INFERENCE-001 | ACTIVE_MACHINE_CONTINUATION | next after recovery: fresh parent fence >20 and same-carrier execution
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
recovery registry admission: HANDOFF_READY
fresh recovery execution: PENDING
fresh parent sovereign execution: PENDING
same-execution reconstruction: 0/2
immutable verified activation receipt: 0/1
Site activation: 0/1
downstream verified ingestion: 0/3
```
