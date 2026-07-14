# System-Boundary Fixture Provenance Handoff

## Scope

This bounded handoff records the cross-repository provenance guard for the adapter-produced system-boundary fixture consumed by `StegVerse-org/StegVerse-SDK`.

Repository-wide authority remains `LLM_ADAPTER_MIRROR_HANDOFF.md`.

## Installed files

```text
tests/fixtures/system-boundary-sdk-session-packet.v1.json
tests/fixtures/system-boundary-sdk-session-packet.v1.provenance.json
tests/test_system_boundary_fixture_provenance.py
receipts/system-boundary-fixture-provenance-2026-07-14.json
receipts/system-boundary-provenance-workflow-binding-2026-07-14.json
.github/workflows/validate.yml
iosnoperiod/github/workflows/validate.yml
```

## Protected identities

```text
producer fixture commit: dbd6ca0bde250bdf9865532049f58d523269d305
declaration id: sbd:sha256:9b43cec895a07d51e02c59aa4d2779d50e288bfe635d8017fcfdbdde66b73101
receipt hash: sha256:24b454a3426aecca2ff6f46f70b9694807e89124969ecbdad998e4310011d317
consumer repo: StegVerse-org/StegVerse-SDK
```

The guard validates semantic identity and non-authority fields rather than file formatting. The producer and consumer copies may use different whitespace while preserving the same declaration, receipt, source commit, and claim boundaries.

## Required boundaries

```text
authorizing: false
custody_transferred: false
admissibility_determined: false
production_binding_enabled: false
model_has_execution_authority: false
consciousness_claim: not_evaluated
personhood_claim: not_evaluated
welfare_claim: not_evaluated
```

## Workflow binding

```text
canonical workflow commit: c1c2518a4274a6c488827de1f0e1bdf90f0968ba
ios workflow mirror commit: f11e534fc21ed085cf05699bb940b48e797c2b62
fixture generation test: tests/test_system_boundary_sdk_fixture.py
provenance guard: tests/test_system_boundary_fixture_provenance.py
workflow parity: synchronized identical content
```

## Current state

```text
producer provenance manifest: installed
producer provenance validator: installed
producer installation receipt: installed
consumer mirror manifest: installed
consumer mirror validator: installed
consumer installation receipt: installed
canonical workflow binding: installed
ios workflow mirror binding: installed
workflow observation: pending
combined status observation: no status reported
production binding: disabled
```

## Next event

Observe a canonical `LLM-adapter` validation run containing commit `f11e534fc21ed085cf05699bb940b48e797c2b62` or later. Repair only the first repository-local failure. After success, record the workflow evidence and propagate verified status downstream without enabling production binding.

## Archive readiness

All decisions, identities, boundaries, installed artifacts, ownership, and pending observations for this workstream are durable in this file and the installation receipts. Earlier conversation context is not required.