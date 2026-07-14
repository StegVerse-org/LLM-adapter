# Adapter System-Boundary Declaration

## Purpose

`StegVerse-org/LLM-adapter` can generate a machine-readable declaration describing where operational state, persistence, feedback, evidence, and authority exist in a composed LLM system.

This is an architectural and governance artifact. It is not a consciousness, personhood, welfare, autonomy, or execution-authority determination.

## Source contract

The public doctrine and canonical schema originate from:

```text
StegVerse-Labs/admissibility-wiki
- docs/governance/llm-consciousness-model-system-boundary.md
- static/governance/system-boundary-declaration.schema.v0.1.json
```

The SDK ingestion boundary is:

```text
StegVerse-org/StegVerse-SDK
- schemas/system-boundary-declaration.schema.v0.1.json
- stegverse/system_boundary.py
```

## Adapter implementation

```text
llm_adapter/system_boundary.py
```

The module exposes:

```python
from llm_adapter.system_boundary import (
    build_system_boundary_declaration,
    default_adapter_system_boundary,
)

config = default_adapter_system_boundary(
    session_ref="session://example/001",
    receipt_refs=("receipt://adapter/001",),
)

declaration = build_system_boundary_declaration(
    config,
    declaration_id="sbd-adapter-001",
)
```

## Declared surfaces

The declaration keeps these surfaces separate:

```text
model
orchestration
session
memory
environment
```

The default adapter inventory records the model as transient and invocation-scoped. Orchestration and session state may change across calls. Durable memory and environmental observations remain separately identified.

## Continuity rules

Trajectory dependence is accepted only when explicit feedback paths exist.

Reconstructability is accepted only when evidence references exist.

The default paths are:

```text
model-output -> orchestration-state
orchestration-state -> future-model-input
environment-observation -> session-continuity
```

These paths describe causal system behavior. They do not establish subjective experience.

## Authority and claim boundaries

Every generated declaration fixes:

```text
model_has_execution_authority: false
consciousness_claim: not_evaluated
personhood_claim: not_evaluated
welfare_claim: not_evaluated
```

The declaration identifies a commit boundary and decision source, but does not perform commitment or execution.

## Verification

Run:

```bash
pytest tests/test_system_boundary.py
```

The tests cover:

- valid declaration generation;
- model self-modification claim rejection;
- false trajectory-dependence rejection;
- reconstructability-without-evidence rejection;
- non-authorizing and non-consciousness output invariants.

## Downstream path

```text
LLM-adapter runtime inventory
-> system-boundary declaration
-> governed session manifest field
-> StegVerse-SDK validation
-> declaration receipt reference
-> later Site bounded status display
```

No step grants execution, custody, admissibility, consciousness status, or personhood by itself.
