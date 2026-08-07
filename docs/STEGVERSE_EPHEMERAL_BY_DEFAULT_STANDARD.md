# StegVerse Ephemeral-by-Default Runtime Standard

## Status

Normative cross-cutting runtime standard for StegVerse-owned and StegVerse-integrated services.

## Core rule

**Anything that can be performed ephemerally SHOULD be performed ephemerally.**

A persistent process, connection, credential, cache, lock, session, tunnel, worker, or replicated channel MUST NOT exist merely for convenience. Persistence requires an explicit target or protocol requirement that cannot be satisfied safely by bounded, reconstructable, on-demand execution.

A service may remain discoverable or able to accept work without maintaining a permanently live data connection. Service availability and connection persistence are distinct concepts.

## Default posture

The default StegVerse execution pattern is:

```text
DISCOVER
-> ADMIT
-> CONNECT / START
-> PERFORM BOUNDED WORK
-> VERIFY
-> PERSIST ONLY REQUIRED DURABLE EVIDENCE OR STATE
-> TEARDOWN
-> RECONSTRUCT ON DEMAND
```

The default connection lifetime is one bounded operation or the shortest safe transaction window.

## Persistent connection exception

A persistent or long-lived connection is permitted only when the internal or external data target, protocol, or governed workload materially requires it. Examples include:

- target-originated streaming where polling or bounded reconnect cannot preserve semantics;
- subscriptions whose source protocol requires an open channel;
- interactive bidirectional sessions whose state cannot be safely externalized between turns;
- low-latency control loops whose bounded reconnect would violate declared safety or timing requirements;
- externally imposed protocols that require long-lived transport continuity.

Convenience, lower implementation effort, vendor defaults, connection pooling alone, or historical architecture are not sufficient justification.

## Required persistent-connection controls

Every persistent connection MUST declare and enforce:

1. `persistence_reason` — exact target/protocol requirement;
2. `target_identity` — the bound internal or external data target;
3. `lease_duration_seconds` — finite lease, even if renewable;
4. `renewal_condition` — machine-verifiable reason renewal remains necessary;
5. `idle_timeout_seconds` — teardown after bounded inactivity unless protocol forbids it;
6. `credential_scope` — least privilege for that connection only;
7. `reconnect_policy` — bounded reconnect with backoff and fail-closed exhaustion;
8. `state_externalization` — what state must survive connection loss and where it is durably retained;
9. `teardown_receipt` — evidence of termination or lease expiry when material;
10. `authority_effect` — persistence itself grants no execution, publication, custody, or release authority.

Indefinite unleased connections are non-conforming unless a protocol cannot operate otherwise and that exception is explicitly documented.

## Ephemeral requirements by layer

### Compute

Workers, task runners, inference jobs, build jobs, validators, transformations, renderers, and one-shot automation SHOULD start on demand and terminate after bounded completion.

Persistent daemons are reserved for capabilities that must continuously accept inbound work, coordinate leases, or maintain a protocol-required control plane. Even then, individual jobs SHOULD remain ephemeral.

### Network

Outbound connections SHOULD be created after admission and torn down immediately after the bounded exchange.

Internal service-to-service channels SHOULD prefer discover-on-demand, connect, exchange, verify, teardown.

A public ingress listener may remain available while request and upstream data connections remain ephemeral.

### Credentials

Credentials SHOULD be materialized only after the governed path is admitted, scoped to the smallest target/purpose/time window, and revoked or discarded after use.

Long-lived static secrets are a compatibility fallback, not the StegVerse target state.

### Storage

Temporary working data SHOULD use ephemeral storage and be destroyed after the bounded operation.

Only state required for continuity, custody, reconstruction, audit, replay, user intent, or declared product behavior SHOULD be persisted.

Durable evidence SHOULD contain hashes, receipts, provenance, pointers, and required reconstructable state rather than unnecessary raw transient content.

### Caches

Caches SHOULD be disposable and reconstructable. Cache loss MUST NOT become authority loss or correctness loss.

Governed replay caches MUST re-evaluate current governance where required and MUST NOT allow stale ALLOW state to bypass current policy or consent.

### Sessions

Logical user or workflow continuity SHOULD be externalized into reconstructable state rather than depending on one continuously live transport session.

Session identifiers do not justify keeping a connection open.

### Locks and claims

Locks and work claims MUST be leased, expire, and be reclaimable. Permanent ownership markers are prohibited for active execution claims.

### Observability

Telemetry collectors SHOULD batch and flush bounded observations rather than require continuous external SaaS connections.

Critical receipts and evidence are durable records; telemetry transport is not.

## Hosting implication

StegVerse hosting MUST support cold or on-demand activation of workloads wherever the workload does not require continuous execution.

A hosting substrate is non-conforming if an application must maintain a permanently live process or connection solely because the platform requires it.

Provider adapters such as Render, Cloudflare, Vercel, AWS, GitHub Actions, or other hosting/CI systems may be used, but their always-on defaults do not override this standard.

The StegVerse-owned hosting plane SHOULD support:

- on-demand workload activation;
- short-lived workers;
- bounded network leases;
- ephemeral credential materialization;
- durable externalized state;
- health-bound discovery without permanent upstream sessions;
- restart/reconstruction from retained evidence;
- scale-to-zero where target semantics permit it.

## HIL application

For HIL, the public receiver may remain addressable because the participant-facing target requires an HTTPS endpoint. That does **not** imply a permanently live connection from Site, the browser, the receiver, review services, publication services, provider adapters, or Master-Records.

A normal HIL transaction SHOULD be:

```text
browser discovers verified receiver
-> opens HTTPS request
-> submits bounded artifact
-> receiver verifies and processes
-> receiver returns receipt
-> required durable state/evidence is persisted
-> request connection closes
```

Downstream review, publication, custody, and reconstruction SHOULD likewise be invoked on demand unless their target protocol explicitly requires a persistent channel.

## Provider/model application

Provider or model connectivity MUST remain downstream of admission.

The preferred pattern is:

```text
admit request
-> materialize scoped credential
-> connect to selected model/provider target
-> perform bounded request/stream
-> collect usage/result evidence
-> close connection
-> discard credential material
```

Streaming responses may keep the connection open only for the duration of the active stream. The stream ending terminates the connection unless another governed operation explicitly reuses a still-valid leased channel.

## Database application

Database persistence and database connection persistence are different requirements.

Durable databases may be continuously available while application database connections are acquired on demand and returned/closed after bounded use. Connection pools MUST have finite idle lifetimes and must not create implicit authority or indefinite credentials.

## Standard decision test

Before approving a persistent resource, ask:

> If this resource were torn down immediately after the current bounded operation, could StegVerse reconstruct the next required state from durable evidence without violating the target protocol, safety requirement, user intent, or declared latency contract?

If **yes**, the resource SHOULD be ephemeral.

If **no**, the persistent exception MUST identify the exact requirement and finite lease/revalidation policy.

## Portability requirement

No canonical StegVerse capability may depend on a vendor-specific requirement for an always-live connection when the workload itself does not require one.

This standard applies equally on StegVerse-owned infrastructure and third-party adapters.

## Authority boundary

```text
connection persistence != authority
service availability != execution authority
credential possession != execution authority
cached session state != current consent
live health != admissibility
persistent storage != custody
reconstruction PASS != release authority
```
