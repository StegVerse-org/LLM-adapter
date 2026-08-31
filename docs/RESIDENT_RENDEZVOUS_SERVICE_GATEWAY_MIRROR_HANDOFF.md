# Resident Rendezvous Service Gateway Mirror Handoff

Updated: 2026-08-30
Repository: StegVerse-org/LLM-adapter
Issue: #240
Merged PR: #241\nMerge: e34d52ec83b83992e3b27b8b28c0fa3ca39829b8
State: SOURCE_MERGED_VALIDATED / RUNTIME_DEPLOYMENT_OPEN
Authority effect: NONE
Runtime activation claimed: false

## Goal

Remove the requirement for a coordinating ChatGPT/browser session to possess SSH, systemd, or direct server-control access to a sovereign resident.

The StegVerse Service Gateway becomes a **non-authorizing rendezvous carrier**:

```text
authorized client / Site
  -> bounded resident task intent
  -> StegVerse Service Gateway durable rendezvous
  -> sovereign resident outbound fetch
  -> exact request digest validation
  -> local resident request materialization
  -> existing resident request consumer
  -> WorkerCoordinator admission / claim / fence
  -> local execution attempt
  -> non-authorizing acknowledgement
```

The Gateway does not become scheduler, WorkerCoordinator, execution authority, credential authority, route authority, or runtime owner.

## Initial admitted request class

Only the existing StegOS/KV chain is admitted in v1:

```text
consumer=stegos_kv_intr_chain
resident_request.schema=stegverse.resident-execution-request/v1
resident_request.task_id=SHWP-STEGOS-KV-INTR-CHAIN-001
resident_request.mode=STEGOS_KV_INTR_CHAIN
```

No shell command, argv, source URL, credential, provider operation, arbitrary path, or arbitrary task may be transported.

## Persistence

A deployment must set a durable `STEGVERSE_RESIDENT_RENDEZVOUS_ROOT`.

Canonical layout:

```text
<root>/
  pending/<request_id>.json
  acknowledged/<request_id>.json
```

Source/CI without a durable production root does not prove activation.

## Request envelope

```text
schema=stegverse.resident-rendezvous.request/v1
request_id=<opaque>
target_node_ref=<opaque non-secret node selector>
consumer=stegos_kv_intr_chain
resident_request=<exact admitted resident request object>
resident_request_sha256=sha256:<64 hex>
submitted_at=<UTC>
expires_at=<UTC>
submitter_authorization_ref=<opaque>
authority_effect=NONE_REQUEST_ONLY
```

The request grants no claim, fence, execution authority, credential authority, or runtime authority.

## Resident fetch

Resident fetch is outbound-only. The Gateway returns at most one live pending request for the exact target node. Fetching does not consume or acknowledge it.

## Acknowledgement

The resident may post a bounded acknowledgement containing:

- request id and exact request digest;
- local resident consumption state;
- opaque local receipt references;
- terminal-chain-observed boolean;
- credential authority = TV/TVC;
- execution authority remains external to the Gateway;
- authority effect = NONE_OBSERVATION_ONLY.

Acknowledgement does not establish truth for the underlying local receipt. Canonical runtime evidence remains the resident receipt itself and downstream custody/reconstruction.

## Fail-closed invariants

- non-allowlisted consumer/task/mode/schema: reject;
- resident request hash mismatch: reject;
- secret-like field names: reject;
- expired request: do not deliver;
- duplicate request id with different bytes: reject;
- acknowledgement hash mismatch: reject;
- no Gateway-generated claim/fence;
- no arbitrary command transport;
- no GitHub token/runtime authority;
- TV/TVC credential authority unchanged.

## Lifecycle

```text
IMPLEMENTED: IN_PROGRESS
VALIDATED: false
MERGED: false
DEPLOYED_DURABLE_GATEWAY: false
ACTIVATED: false
OBSERVED: false
COMPLETE: false
```


## Merge evidence

```text
issue: #240 CLOSED_BY_MERGE
PR: #241 MERGED
merge: e34d52ec83b83992e3b27b8b28c0fa3ca39829b8
validated head: c0a14d692fdb8bdd801cd440b71f96e81e809e14
validate: 33351682618 SUCCESS
Coinbase SKAP Service Gateway Validation: 33351682616 SUCCESS
hil-sovereign-receiver-source: 33351682636 SUCCESS
```

The direct-control dependency is removed at source level: any compatible client may deposit the exact bounded resident intent in the Service Gateway, and a sovereign resident may retrieve it outbound-only. Deployment/public-route observation remains required before claiming live use.


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
resident -> POST /api/resident-rendezvous/v1/advertisements
Gateway  -> short-lived target_node_ref advertisement (max 5 minutes)
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


## 2026-08-31 node capability advertisement propagation — issue #254

`/api/stegverse-node` now advertises the complete resident-rendezvous v1 public capability set:
```text
request endpoint
acknowledgement endpoint
discovery endpoint
resident advertisement endpoint
current request id = RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003
discovery_grants_authority = false
gateway_execution_authority = NONE
```

This is a health-bound endpoint projection only. It does not prove that a resident advertisement is currently fresh, that discovery returns AVAILABLE, or that any request has been consumed.
