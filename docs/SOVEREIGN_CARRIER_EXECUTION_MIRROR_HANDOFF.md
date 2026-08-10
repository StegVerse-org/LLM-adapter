# Sovereign Carrier Execution Mirror Handoff

## Authority

This scoped handoff is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md` and is authoritative for `LLMA-SOVEREIGN-CARRIER-EXECUTION-020`. Live repository state, the task record, TVC route receipts, heartbeat receipts, provider-usage evidence, and Master Records reconstruction supersede older descriptions of the canonical local-model binding blocker.

## Canonical task state

```text
goal_id: LLMA-SOVEREIGN-CARRIER-EXECUTION-020
originating_goal: consume the exact TVC-admitted canonical micro-node endpoint through StegVerseLocalHTTPProviderClient on the sovereign carrier
repository: StegVerse-org/LLM-adapter
canonical_branch: main
canonical_issue: #18
implementation_claim: COMPLETE_RELEASED
implementation_pr: #135
implementation_merge: 72934c7cf135ce2953591a81fe01e16c9719ec2f
validated_head: dbb9558648c9c717d713b941487c48761dd104c6
heartbeat_owner: StegVerse-Labs/.github#60
model_owner: StegVerse-002/micro-node-runtime#22
route_owner: StegVerse-Labs/TVC:TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002
credential_authority_model: TC/TVC
custody_owner: master-records/orchestration
remaining_role: MACHINE_OWNED_SAME_CARRIER_OBSERVATION_AND_RECONSTRUCTION
```

The former `CLAIMED_FOR_VALIDATION` state is released. PR #135 is merged and its validation matrix passed. No session should reimplement this executor merely because live same-carrier evidence remains incomplete.

## Superseded blocker

The historical statement that canonical binding is blocked because an Actions credential cannot read the micro-node repository is superseded. Cross-repository checkout is not part of the production path.

Current canonical path:

```text
micro-node runtime is materialized locally on the sovereign carrier
-> heartbeat discovers/launches/proves persistent private model endpoint
-> heartbeat invokes locally materialized TVC route authority
-> TVC binds exact runtime proof hash + endpoint and emits ROUTE_ADMITTED
-> credential_requirement NONE / github_token_required false
-> released LLM-adapter carrier executor consumes the admitted endpoint
```

Merged upstream evidence:

```text
micro-node persistent endpoint PR #28: e64e1f36a85c0eb23937219118b649b9b18ae390
.github persistent heartbeat lifecycle PR #69: 4479fbb5399ccd1509ec1fdcc95dacfcc173b9b8
.github automatic local TVC invocation PR #70: f25204874189a90bc2bc07f1ac65d060be41e397
TVC canonical route compatibility PR #17: 5fc63c5daa90b02ed2cd0f7eefd833873304ecb8
LLM-adapter exact carrier executor PR #135: 72934c7cf135ce2953591a81fe01e16c9719ec2f
```

## Installed integration surfaces — complete and validated

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

## Validation evidence

PR #135 validated head:

```text
head: dbb9558648c9c717d713b941487c48761dd104c6
merge: 72934c7cf135ce2953591a81fe01e16c9719ec2f
Validate Ecosystem Chat Path: PASS
Validate Structure: PASS
Python 3.9: PASS
Python 3.11: PASS
Python 3.12: PASS
remaining validation checks: PASS
```

Hosted validation proves implementation behavior only. It does not prove a sovereign-carrier execution occurred.

## Authority boundary

```text
github_token_required: false
github_actions_production_role: false
credential_requirement: NONE
credential_authority_model: TC/TVC
provider_output_authority: false
route_execution_authority: false
binding_receipt_authority: false
master_records_custody_authority_duplicated: false
```

Historical committed evidence may contain the older `StegVerse-Labs/TV` credential-policy label. Those references remain historical evidence only. Current credential-authority semantics are TC/TVC; `StegVerse-Labs/TVC` remains the actual canonical route-authority repository.

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

`.github#60` owns invocation of this released executor after `TVC_LOCAL_MODEL_ROUTE_ADMITTED`. Master Records owns same-execution custody/reconstruction. Only after immutable activation verification may Site, Publisher, admissibility-wiki, and stegguardian-wiki claim verified ingestion.

## Completion accounting

```text
developed task surfaces: 4/4
scaffolding/stubs: 0
deterministic/hosted implementation validation: COMPLETE
implementation claim: COMPLETE_RELEASED
same-carrier provider execution observation: 0/1
provider-usage reconstruction: 0/1
transition reconstruction: 0/1
source integration into heartbeat bridge: COMPLETE_MERGED
live same-carrier goal activation: 70%
```

## Session consolidation

MERGED INTO: `StegVerse-Labs/.github#60` + `master-records/orchestration` for live same-carrier execution and reconstruction.

The no-GitHub-token correction, supersession of cross-repository checkout, exact TVC route/proof/endpoint binding, measured-usage adapter, TC/TVC credential semantics, and downstream activation conditions are durable. This repository has no remaining unique implementation work for task 020; only live machine-owned observation/reconstruction remains.
