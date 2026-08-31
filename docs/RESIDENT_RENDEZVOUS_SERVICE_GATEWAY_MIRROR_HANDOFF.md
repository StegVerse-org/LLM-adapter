# Resident Rendezvous Service Gateway Mirror Handoff

Updated: 2026-08-30
Repository: StegVerse-org/LLM-adapter
Issue: #240
Branch: feature/resident-rendezvous-240
State: SOURCE_IMPLEMENTATION_IN_PROGRESS
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
