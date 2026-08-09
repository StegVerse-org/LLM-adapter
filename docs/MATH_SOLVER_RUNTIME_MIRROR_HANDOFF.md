# Math Solver Runtime Mirror Handoff

## Source of truth

Goal ID: `MATH-SOLVER-STEGGATE-RUNTIME-001`

Originating session goal: convert the public StegVerse Math Solver from `RESEARCH_NOTE` into a real deterministic public application whose execution is gated by the canonical StegGate runtime, with inspectable decision and replay evidence.

Repository: `StegVerse-org/LLM-adapter`
Branch: `main`
Canonical application tracker: `StegVerse-Labs/Site#240`
Parent four-app goal: `StegVerse-Labs/Site#239`
Canonical StegGate owner: `StegVerse-Labs/StegCore#68`
Common integration owner: `StegVerse-Labs/StegCore#70`

## Claim

Task ID: `MATH-SOLVER-STEGGATE-RUNTIME-001`
Role: implementation + validation of the non-LLM deterministic runtime adapter.
Claimant: this repository execution lane.
Claim creation: 2026-08-08T21:15:00-05:00.
Release condition: runtime code and tests are committed, hosted route is directly observed, Site surface consumes it, and Site#240 acceptance evidence is complete.
Collision boundary: do not create a parallel StegGate evaluator; use `llm_adapter/steggate_portable_consumer.py` and canonical StegCore.

## Authoritative files

- `llm_adapter/steggate_portable_consumer.py`
- `llm_adapter/math_solver_gateway.py`
- `tests/test_math_solver_gateway.py`
- `.github/workflows/math-solver-governed-runtime.yml`
- `pyproject.toml`
- `Dockerfile.service-gateway`
- this handoff

## Required execution chain

```text
public math expression
-> normalized request hash
-> canonical portable StegGate package
-> canonical StegGate + coherence evaluation
-> deterministic arithmetic executor only after ALLOW
-> execution observation + decision/hash evidence
-> response receipt
-> public Site display
-> deterministic replay/verification
```

## Completion gates

1. safe bounded deterministic arithmetic evaluator exists;
2. canonical StegGate is in the pre-execution path;
3. DENY/REFUSED cannot invoke the evaluator;
4. request/result hashes and StegGate execution evidence are returned;
5. tests prove ALLOW and fail-closed behavior;
6. hosted service route is directly observed;
7. Site public surface calls the hosted route;
8. deployed public request and replay/verification are directly observed.

## Current state

`CLAIMED_FOR_IMPLEMENTATION`.

No completion or activation claim is made by creation of this handoff.

## Cross-repository continuation

MERGED INTO: `StegVerse-Labs/Site#240` for public application activation and `StegVerse-Labs/Site/docs/STEGGATE_FOUR_APP_MIRROR_HANDOFF.md` for four-app status.

## Archive condition

This lane remains active until its unique runtime implementation/evidence is either completed or durably transferred to a verified successor. Product-level archival remains governed by Site#239.
