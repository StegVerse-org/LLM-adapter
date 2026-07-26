# StegVerse LLM Communications Stack

Stack identifier: `STEGVERSE-LLM-COMMS-STACK-v1`

The StegVerse LLM Communications Stack is a distributed governed communications stack. It operates across multiple repositories and deployment locations. No single repository owns every function, and repository location does not by itself grant production, admissibility, execution, publication, identity, continuity, or custody authority.

## End-to-end stack

```text
user
  -> user's authorized external LLM
  -> LLM-adapter user-access boundary
  -> SDK-equivalent demo/test capabilities
  -> manifest and receipt construction
  -> Demo test suite or bounded entity sandbox runner
  -> governed result returned to the user's LLM
```

Provider inference, collaboration, continuity, admissibility, execution, and custody remain separate bounded functions elsewhere in the stack.

## Component map

| Component | Repository or owner | Bounded function |
|---|---|---|
| Public application entry | StegVerse SDK | Direct public and application entry, manifest-ready package construction, and result return |
| User-LLM access adapter | `StegVerse-org/LLM-adapter` | Connects an authorized user-controlled LLM as a user-class participant with SDK-equivalent demo/test access, package construction, bounded test submission, and governed result return |
| StegVerse inference provider | `StegVerse-Labs/governed-llm` | Local StegVerse-controlled model inference using the governed generation contract |
| Internal collaboration adapter | `StegVerse-Labs/hybrid-collab-bridge` | Multi-provider expert coordination, synthesis, admission, trace creation, and collaboration receipts |
| Communications gateway | `StegVerse-Labs/Comms-Gateway` | Communication-source normalization, routing candidates, and communication receipts |
| Continuity and standing | StegID / Continuity | Continuity evidence, standing, and verification inputs |
| Decision engine | `StegVerse-Labs/StegCore` | Commit-time allow, deny, or defer decisions under policy, consent, and verified continuity |
| Validation and orchestration | `GCAT-BCAT-Engine/workflows` | Deterministic validation, proof pipelines, transition testing, and cross-repository workflow dispatch |
| Demo test suite | StegVerse-org | Isolated public and Demo operational-surface verification |
| Entity sandbox runner | `StegGhost/entity-sandbox-runner` | Bounded adversarial and entity-specific test execution |
| Durable custody | Master Records | Durable record chains, release records, replay, and reconstruction custody |

## Position of this repository

`StegVerse-org/LLM-adapter` is the SDK-adjacent access bridge for a user's external LLM. Its primary purpose is to let that LLM connect as an authorized user-class participant and use the same bounded distinction as the SDK for viewing and manipulating the Demo test suite, constructing test submissions, sending data to `StegGhost/entity-sandbox-runner`, and receiving governed results.

The adapter may normalize model output and bind provider metadata as supporting capabilities, but those functions do not redefine it as a provider broker and do not displace its user-access role.

### This repository owns

- connection of an authorized user-controlled LLM to the StegVerse demo and testing surface;
- SDK-equivalent construction of manifest-ready packages;
- bounded inspection and manipulation requests for the Demo test suite;
- bounded submission of test data to `StegGhost/entity-sandbox-runner`;
- normalization of LLM-originated test inputs and returned results;
- request, response, model, provider, usage, and evidence metadata binding;
- governed adapter receipts and result-return envelopes;
- non-authorizing transition and commitment candidates;
- fail-closed adapter behavior and conformance tests.

### This repository does not own

- the user's identity or authority merely because an LLM is connected;
- model weights or local inference custody;
- general communication-source routing;
- continuity truth;
- commit-time admissibility or authority;
- execution outside the bounded Demo or sandbox test route;
- publication authority;
- Master Record custody;
- internal multi-model consensus policy.

## Connection and authorization rule

Connecting an LLM establishes a governed user-access channel. It does not grant unrestricted authority. Every inspection, manipulation, or submission remains bound to the user's authenticated scope, the SDK-equivalent Demo/test capability contract, applicable policy, and the receiving test surface's own admission rules.

## Deployment declaration requirement

Every deployment or emitted proof should identify:

- `stack_id`;
- `component_id`;
- source repository and revision;
- deployment environment;
- governance profile;
- authority scope;
- whether the evidence is Demo, sandbox, conformance, production-candidate, or externally observed operational evidence.

## Core rule

> The user's LLM is an authorized access participant, not an implicit authority source. SDK-equivalent access does not collapse admission, execution, continuity, publication, or custody boundaries.