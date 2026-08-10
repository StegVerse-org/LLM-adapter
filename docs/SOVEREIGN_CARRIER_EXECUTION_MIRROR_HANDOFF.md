# Sovereign Carrier Execution Mirror Handoff

## Authority

This scoped handoff is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md` and is authoritative for `LLMA-SOVEREIGN-CARRIER-EXECUTION-020`. Live repository state, the task record, TVC route receipts, heartbeat receipts, provider-usage evidence, and Master Records reconstruction supersede older descriptions of the canonical local-model binding blocker.

## Active goal

```text
goal_id: LLMA-SOVEREIGN-CARRIER-EXECUTION-020
originating_goal: consume the exact TVC-admitted canonical micro-node endpoint through StegVerseLocalHTTPProviderClient on the sovereign carrier
repository: StegVerse-org/LLM-adapter
branch: feat/canonical-sovereign-route-execution-20260810
canonical_issue: #18
claim: CLAIMED_FOR_VALIDATION
claim_created_at: 2026-08-10T11:46:00Z
claim_release_condition: merged deterministic validation of exact route/proof/endpoint execution adapter
heartbeat_owner: StegVerse-Labs/.github#60
model_owner: StegVerse-002/micro-node-runtime#22
route_owner: StegVerse-Labs/TVC:TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002
credential_owner: StegVerse-Labs/TV
custody_owner: master-records/orchestration
```

## Superseded blocker

The historical statement that canonical binding is blocked because an Actions credential cannot read the micro-node repository is superseded. Cross-repository checkout is not part of the production path.

Current canonical path:

```text
micro-node runtime is materialized locally on the sovereign carrier
-> heartbeat discovers/launches/proves persistent private model endpoint
-> heartbeat invokes locally materialized TVC route authority
-> TVC binds exact runtime proof hash + endpoint and emits ROUTE_ADMITTED
-> credential_requirement NONE / github_token_required false
-> LLM-adapter carrier executor consumes the admitted endpoint
```

Merged upstream evidence:

```text
micro-node persistent endpoint PR #28: e64e1f36a85c0eb23937219118b649b9b18ae390
.github persistent heartbeat lifecycle PR #69: 4479fbb5399ccd1509ec1fdcc95dacfcc173b9b8
.github automatic local TVC invocation PR #70: f25204874189a90bc2bc07f1ac65d060be41e397
TVC canonical route compatibility PR #17: 5fc63c5daa90b02ed2cd0f7eefd833873304ecb8
```

## Installed integration surfaces

```text
scripts/execute_canonical_sovereign_route.py
tests/test_execute_canonical_sovereign_route.py
tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json
docs/SOVEREIGN_CARRIER_EXECUTION_MIRROR_HANDOFF.md
```

The executor:

1. requires TVC `ROUTE_ADMITTED`;
2. requires route authority `StegVerse-Labs/TVC`;
3. verifies the route receipt's `runtime_proof_hash` against the exact canonical proof;
4. requires `canonical_micro_node_proof_consumed=true`;
5. requires `credential_requirement=NONE` and `github_token_required=false`;
6. rejects third-party execution dependency or route/execution authority escalation;
7. derives only the canonical `/v1/chat/completions` transport path from the admitted private base endpoint;
8. calls existing `execute_verified_local_model`, which uses `StegVerseLocalHTTPProviderClient`;
9. preserves request/response hashes and MEASURED prompt/completion/total-token and latency evidence;
10. reuses canonical Master Records provider-usage submission rather than duplicating custody authority;
11. does not claim activation when custody/reconstruction or production-scale predicates remain incomplete.

## Authority boundary

```text
github_token_required: false
github_actions_production_role: false
credential_requirement: NONE
provider_output_authority: false
route_execution_authority: false
binding_receipt_authority: false
master_records_custody_authority_duplicated: false
```

GitHub Actions may validate source only. No source checkout, GitHub token, hosted model provider key, Render service, or other hosted control plane is a production prerequisite for this carrier execution path.

## Remaining activation sequence

```text
heartbeat TVC_LOCAL_MODEL_ROUTE_ADMITTED
-> execute_canonical_sovereign_route.py on same carrier
-> real StegVerseLocalHTTPProviderClient response
-> measured provider usage persisted
-> provider-usage Master Records reconstruction PASS
-> same-execution transition reconstruction PASS
-> immutable zero-blocker ecosystem-chat-live-activation.verified.json
-> Site ACTIVATION_COMPLETE
-> Publisher/admissibility-wiki/stegguardian-wiki verified ingestion
```

The reference model is a real formally developed local model and can prove this sovereign transport/evidence path. It is not represented as a production-scale foundation LLM; any product requirement for production-scale model quality remains a separate explicit predicate.

## Validation commands

```text
python -m unittest -v tests.test_execute_canonical_sovereign_route
python -m unittest -v tests.test_sovereign_local_model_binding
```

## Integration and propagation obligations

After this task merges, `.github#60` should invoke this executor after `TVC_LOCAL_MODEL_ROUTE_ADMITTED`. Master Records owns same-execution custody/reconstruction. Only after immutable activation verification may Site, Publisher, admissibility-wiki, and stegguardian-wiki claim verified ingestion.

## Completion accounting

```text
developed task surfaces: 4/4
scaffolding/stubs: 0
deterministic validation: pending hosted run
same-carrier provider execution: pending direct observation
provider-usage reconstruction: pending
transition reconstruction: pending
integration into heartbeat: pending after merge
goal activation: 70%
```

## Session consolidation

The no-GitHub-token correction, supersession of cross-repository checkout, exact TVC route-binding requirement, and next activation steps are durable here and in task 020. This session retains a distinct implementation/validation role until task 020 is merged and bound into the heartbeat path.
