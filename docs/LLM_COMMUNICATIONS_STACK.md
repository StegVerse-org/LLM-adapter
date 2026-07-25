# StegVerse LLM Communications Stack

Stack identifier: `STEGVERSE-LLM-COMMS-STACK-v1`

The StegVerse LLM Communications Stack is a distributed governed communications stack. It operates across multiple repositories and deployment locations. No single repository owns every function, and repository location does not by itself grant production, admissibility, execution, publication, identity, continuity, or custody authority.

## End-to-end stack

```text
user, agent, application, or communication source
  -> entry and transport adapters
  -> LLM/provider brokerage and inference
  -> response normalization and transition construction
  -> collaboration, synthesis, and communication routing
  -> continuity and evidence binding
  -> admissibility and authority evaluation
  -> execution, refusal, publication, or governed return
  -> receipts, custody, replay, and reconstruction
```

## Component map

| Component | Repository or owner | Bounded function |
|---|---|---|
| User-facing entry adapter | StegVerse SDK | Public and application entry, manifest-ready package construction, and result return |
| Governed LLM broker | `StegVerse-org/LLM-adapter` | Provider-neutral requests, provider-response normalization, LLM transition candidates, usage envelopes, and adapter receipts |
| StegVerse inference provider | `StegVerse-Labs/governed-llm` | Local StegVerse-controlled model inference using the governed generation contract |
| Internal collaboration adapter | `StegVerse-Labs/hybrid-collab-bridge` | Multi-provider expert coordination, synthesis, admission, trace creation, and collaboration receipts |
| Communications gateway | `StegVerse-Labs/Comms-Gateway` | Communication-source normalization, routing candidates, and communication receipts |
| Continuity and standing | StegID / Continuity | Continuity evidence, standing, and verification inputs |
| Decision engine | `StegVerse-Labs/StegCore` | Commit-time allow, deny, or defer decisions under policy, consent, and verified continuity |
| Validation and orchestration | `GCAT-BCAT-Engine/workflows` | Deterministic validation, proof pipelines, transition testing, and cross-repository workflow dispatch |
| Durable custody | Master Records | Durable record chains, release records, replay, and reconstruction custody |
| Demo and conformance deployment | StegVerse-org | Isolated public and Demo operational-surface verification |
| Adversarial and entity testing | StegGhost | Isolated sandbox, adversarial, and entity-specific verification |

## Position of this repository

`StegVerse-org/LLM-adapter` is the common governed LLM broker and reference adapter implementation for the stack. StegVerse-org deployments of the component remain Demo and conformance surfaces unless a separate deployment record establishes another posture.

### This repository owns

- provider-neutral LLM request envelopes;
- hosted, local, fixture, and StegVerse-provider client contracts;
- provider-response normalization;
- request, response, model, provider, usage, and evidence metadata binding;
- governed adapter receipts;
- non-authorizing commitment candidates;
- LLM-specific transition candidates and governed return envelopes;
- adapter conformance tests and fail-closed provider behavior.

### This repository does not own

- model weights or local inference custody;
- general communication-source normalization;
- continuity truth or identity;
- commit-time admissibility or authority;
- execution;
- publication authority;
- Master Record custody;
- internal multi-model consensus policy.

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

> Distributed operation does not imply duplicated ownership. Each repository owns a bounded function of the same governed LLM communications stack.
