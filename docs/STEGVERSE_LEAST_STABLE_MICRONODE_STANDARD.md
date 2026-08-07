# StegVerse Least-Stable Capability Micro-Node Standard

## Status

Normative precursor standard for all StegVerse runtime, hosting, execution, routing, storage, review, and automation capabilities.

## Governing rule

**All StegVerse capabilities MUST be constructed from the least-stable viable micro-node instances capable of performing the bounded purpose.**

"Least-stable" is a deliberate StegVerse construction term. It does **not** mean unreliable, fragile, or low-integrity. It means the implementation MUST retain process lifetime, connection lifetime, credential lifetime, mutable state, authority, ownership, placement, and instance identity coupling no longer than the bounded capability actually requires.

A least-stable micro-node may be highly reliable and strongly verified while still being short-lived, replaceable, and reconstructable.

"Micro-node" means the smallest independently addressable, replaceable, reconstructable, attestable capability instance that can perform one declared responsibility without inheriting unrelated authority or state.

This standard is structurally prior to the StegVerse Ephemeral-by-Default Runtime Standard. Ephemeral execution is the normal lifecycle consequence of constructing capabilities as least-stable micro-nodes.

## Required construction properties

Every micro-node MUST:

1. declare exactly one primary capability responsibility;
2. request only the minimum capabilities required for that responsibility;
3. carry no implicit execution, publication, custody, release, or delegation authority;
4. bind mutable state outside the node whenever reconstruction is possible;
5. use immutable or content-addressed inputs wherever practical;
6. expose a machine-verifiable identity for the instance and the artifact/configuration that created it;
7. be replaceable without requiring preservation of its process identity;
8. be reconstructable from declared artifacts, configuration, retained evidence, and authorized durable state;
9. accept bounded leases for connections, credentials, claims, locks, and placement;
10. fail closed if the required capability, evidence, authority, or reconstruction input is absent;
11. emit completion, teardown, or replacement evidence when material;
12. avoid coupling unrelated workloads merely to preserve convenience or an always-live topology.

## Least-stability ordering

When multiple constructions can satisfy the same declared purpose, StegVerse MUST prefer the construction with the least retained stability, in this order unless a stricter target requirement applies:

```text
one-shot function / operation
-> short-lived worker micro-node
-> bounded session micro-node
-> leased service micro-node
-> continuously addressable but reconstructable service micro-node
-> persistent stateful micro-node
-> permanent process or permanently coupled service
```

Movement downward in this list requires explicit justification showing why every less-stable construction cannot safely satisfy the target semantics.

## Capability minimization

A micro-node MUST NOT receive a capability merely because another colocated service needs it.

Examples:

- a receipt verifier does not inherit provider-call capability;
- a model adapter does not inherit publication authority;
- an ingress micro-node does not inherit durable custody authority;
- a custody writer does not inherit release authority;
- a Site renderer does not inherit execution authority;
- a telemetry micro-node does not inherit user-content access unless the declared telemetry purpose requires the exact field.

Capability aggregation is permitted only when splitting would violate a declared safety, atomicity, latency, or target-protocol requirement and that exception is machine-readable.

## State rule

The preferred micro-node state model is:

```text
immutable artifact + declared configuration + bounded input
-> perform capability
-> emit output/evidence
-> externalize only required durable state
-> terminate or release lease
```

Local mutable state is disposable by default.

Durable state belongs to a declared storage/custody/reconstruction surface, not to the lifetime of a process.

A micro-node's destruction MUST NOT destroy authority records, required custody evidence, reconstruction inputs, or continuity state that the declared workload requires to survive.

## Identity rule

Service identity and instance identity are distinct.

A durable logical service MAY retain a stable service identifier while individual micro-node instances are created, replaced, moved, reconstructed, or destroyed.

No consumer may require a particular process instance, host PID, container ID, IP address, provider-specific service identifier, or machine placement when a service identity plus verified endpoint/instance receipt can satisfy the same requirement.

## Connection rule

Connections belong to the bounded capability invocation, not to the service identity.

A micro-node SHOULD acquire a connection only after admission and release it as soon as the declared exchange is complete.

Persistent connections require the Ephemeral-by-Default exception controls and do not change the micro-node's authority.

## Credential rule

Credentials SHOULD be materialized to the specific micro-node after its identity, artifact, capability declaration, target, and authority have been verified.

Credentials SHOULD be scoped to:

- one capability;
- one target or target class;
- one bounded lifetime;
- the minimum permitted operations.

A replacement micro-node MUST re-establish entitlement rather than inherit secret material merely because it replaces a previous instance.

## Placement rule

Placement is replaceable metadata, not application identity.

A conforming micro-node may execute on:

- a StegVerse-owned host;
- a sovereign/private deployment;
- a compatible local device;
- a third-party hosting adapter;
- an ephemeral CI worker;
- a future execution substrate;

provided the same capability, identity, evidence, and authority contracts are satisfied.

The hosting substrate MUST NOT expand the node's capability or authority.

## Composition rule

Complex StegVerse services SHOULD be compositions of micro-nodes rather than monolithic persistent processes.

Example:

```text
request ingress micro-node
-> admissibility micro-node
-> provider/model execution micro-node
-> usage evidence micro-node
-> custody submission micro-node
-> receipt verification micro-node
-> projection micro-node
```

Each transition MUST have explicit inputs/outputs and no stage may infer authority merely because the previous stage completed.

## Hosting implication

The StegVerse-owned hosting plane MUST be capable of constructing, addressing, leasing, supervising, replacing, and tearing down micro-node instances independently.

The hosting plane SHOULD support:

- content-addressed artifacts;
- capability-scoped manifests;
- on-demand instance creation;
- scale-to-zero;
- finite leases;
- health-bound service discovery;
- instance replacement without service identity loss;
- externalized durable state;
- reconstruction receipts;
- capability-scoped secret release;
- default-deny ingress and egress;
- per-node resource bounds;
- teardown receipts where material.

A hosting system that requires unrelated capabilities to share one permanently live process is non-conforming when those capabilities can safely be separated.

## HIL application

HIL SHOULD NOT be modeled as one permanently live receiver process containing every responsibility.

The preferred construction separates, where practical:

```text
public ingress / artifact acceptance
-> validation
-> bounded processing
-> receipt generation
-> private review write
-> publication write
-> custody/reconstruction submission
```

The public service identity may remain discoverable while individual processing, review, publication, and custody micro-nodes are started only when required.

## AdmittedCode application

AdmittedCode SHOULD preserve the canonical gate as a minimal capability node.

Browser, API, CLI, provider adapter, receipt storage, receipt verification, and deployment functions SHOULD be separate replaceable micro-node capabilities when they do not require shared atomic state.

The governance gate MUST NOT inherit provider credentials, deployment authority, or publication authority merely because those capabilities are adjacent in a product deployment.

## Exception record

Any construction more stable or more capability-rich than necessary MUST declare:

- `exception_reason`;
- `required_target_semantics`;
- `capabilities_that_cannot_be_split`;
- `state_that_cannot_be_externalized`;
- `minimum_required_lifetime`;
- `revalidation_condition`;
- `teardown_or_split_condition`;
- `authority_effect`.

The default decision for an undocumented exception is `DENY`.

## Decision test

Before constructing a node, ask:

> What is the smallest independently reconstructable capability instance, with the shortest safe lifetime and least retained state/authority, that can complete this declared purpose?

That construction is the StegVerse default.

## Authority boundary

```text
micro-node existence != authority
service identity != instance authority
placement != authority
health != admissibility
capability availability != permission to invoke
shared host != shared authority
completion != downstream authority
persistence != legitimacy
```
