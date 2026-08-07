# Least-Stable Micro-Node Standards Mirror Handoff

## Scope

Task-specific continuation record for the cross-cutting StegVerse runtime standards introduced on branch `standards/ephemeral-by-default`. This handoff does not replace `LLM_ADAPTER_MIRROR_HANDOFF.md`; it governs only this standards lane.

## Active goal

Establish the **Least-Stable Capability Micro-Node Standard** as the structural precursor to the **Ephemeral-by-Default Runtime Standard**, then validate and propagate the pair across StegVerse runtime/hosting contracts.

## Originating requirement

All aspects of StegVerse MUST be constructed from the least-stable viable micro-node instances. Anything that can subsequently be performed ephemerally SHOULD be performed ephemerally. Persistent or capability-rich constructions are exceptions requiring explicit target semantics and bounded revalidation.

## Authoritative files

- `docs/STEGVERSE_LEAST_STABLE_MICRONODE_STANDARD.md`
- `contracts/least-stable-micronode-policy.v1.json`
- `tests/test_least_stable_micronode_policy.py`
- `docs/STEGVERSE_EPHEMERAL_BY_DEFAULT_STANDARD.md`
- `contracts/ephemeral-execution-policy.v1.json`
- `tests/test_ephemeral_execution_policy.py`
- this handoff

## Canonical ordering

```text
1. least-stable viable micro-node construction
2. capability/authority minimization
3. externalized reconstructable state
4. ephemeral lifecycle by default
5. bounded persistence exception only when target/protocol requires
```

An ephemeral monolith is non-conforming if the same workload can be decomposed into smaller independently reconstructable capability nodes without violating declared safety, atomicity, latency, or target semantics.

## Claim

- owner repository: `StegVerse-org/LLM-adapter`
- branch: `standards/ephemeral-by-default`
- role: cross-cutting standard definition and executable contract validation
- collision boundary: standards files listed above only
- release condition: hosted validation passes and PR is merged, or branch is superseded by a canonical standards owner with an explicit transfer record

## Validation

```bash
pytest tests/test_least_stable_micronode_policy.py -v
pytest tests/test_ephemeral_execution_policy.py -v
pytest tests/ -v
```

Hosted repository workflows are required before merge. Workflow success proves repository validation only; it does not prove ecosystem-wide propagation.

## Current completion

- precursor standard document: IMPLEMENTED
- precursor machine policy: IMPLEMENTED
- precursor tests: IMPLEMENTED
- ephemeral standard dependency ordering: IMPLEMENTED
- ephemeral machine policy dependency: IMPLEMENTED
- hosted validation: PENDING
- merge: PENDING
- ecosystem propagation: PENDING

## Propagation obligations

After merge, the policy must be incorporated into canonical runtime/hosting contracts where applicable without duplicating authority:

- `StegVerse-Labs/Site` — workload admission and hosted/public surfaces;
- `master-records/orchestration` — custody/reconstruction services and connection/state lifetimes;
- `GCAT-BCAT-Engine/Publisher` — publication workers and transport;
- `AdmittedCode` — gate/API/browser/provider adapter decomposition;
- StegVerse-owned hosting/deployment plane — micro-node scheduling, leases, scale-to-zero, secret materialization, endpoint discovery, replacement and teardown.

## Authority boundary

These standards constrain construction and lifecycle. They do not themselves grant execution, publication, custody, deployment, provider, release, or human authority.

## Archive condition

This standards lane may be transferred/archived only after the normative files, machine policies, tests, validation evidence, merge state, and exact propagation obligations are durably recorded in a canonical handoff or successor workstream.
