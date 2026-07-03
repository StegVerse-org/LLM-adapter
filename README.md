# StegVerse LLM Adapter

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

Release: v2.1

`LLM-adapter` is the SDK-adjacent intake bridge for converting LLM outputs into StegVerse route-ready governance artifacts.

The adapter does not execute LLM output directly. It normalizes output, classifies risk, produces a governance decision, and prepares admissible outputs for receipt-bound routing through the StegVerse formal testing path.

---

## Boundary rule

```text
LLM output is not execution.
Execution is not authority.
Authority is not admissibility.
Admissibility must be tested before consequence attaches.
```

The adapter must not create endorsement, validation, compatibility recognition, provenance recognition, collaboration, or public attribution from private review or external discussion.

---

## Governed runtime activation

The governed runtime boundary is documented in:

```text
docs/GOVERNED_LLM_RUNTIME.md
```

The activation status is documented in:

```text
docs/ACTIVATION_STATUS.md
```

The machine-readable capability manifest is:

```text
adapter.capabilities.json
```

Current governed chain:

```text
provider request
  -> provider response
  -> continuity evidence
  -> governed adapter receipt
  -> action route
  -> commitment request
  -> authority decision
  -> disabled execution handoff
```

Local verification:

```bash
pytest
stegverse-llm-adapter fixtures/governed_response_fixture.json --pretty
python scripts/smoke_governed_session.py
```

---

## Micro-node return-path proof

Goal 4 adds a fixture-bound proof that `LLM-adapter` can preserve the portable micro-node governed return-path contract.

```text
external LLM / UI
-> LLM-adapter
-> micro-node-compatible transition request
-> transition-table role evaluation contract
-> terminal decision + receipt reference
-> governed return payload
-> original customer path
```

Verify it with:

```bash
python scripts/verify_micro_node_return_path.py
pytest tests/test_micro_node_return_path.py -v
```

This proof does not call a live provider, call a live continuity service, mutate a repository, post publicly, send email, or grant execution authority.

---

## Roles

| Role | Function |
|---|---|
| Governance ingress | LLM output -> canonical intent -> safety classification -> decision |
| SDK-side adapter | User / LLM Adapter submission -> manifest-ready package |
| Test-route feeder | Route admissible packages into SDK / ingestion / sandbox testing paths |
| Governed runtime boundary | Provider output -> continuity evidence -> receipts -> disabled execution handoff |
| Micro-node return-path caller | Adapter fixture -> micro-node-compatible request -> governed return to origin |

---

## Security features

- dangerous-pattern detection for high-risk generated code;
- code complexity scoring;
- test and documentation signal detection;
- GCAT/BCAT-style governance score computation;
- deterministic decision output: `ADMIT`, `DENY`, or `DEFER`;
- receipt-ready result structure;
- request-hash-bound provider responses;
- optional HTTP provider clients that fail closed without credentials;
- optional continuity service client that fails closed without endpoint configuration;
- non-authorizing commitment requests;
- disabled execution gateway by default;
- micro-node-compatible governed return-path fixture verification.

---

## Install

```bash
pip install stegverse-llm-adapter
```

---

## Quick start

```python
from llm_adapter import run_governed_session

result = run_governed_session(
    provider="fixture-provider",
    model="fixture-model",
    messages=[{"role": "user", "content": "Can the prior answer be reused?"}],
    candidate_output="The prior answer is reconstructable but requires fresh retrieval.",
    allowed_sources=("receipt_index",),
    evidence_fixtures=[
        {
            "source_type": "receipt",
            "pointer": "master-records://fixture/prior-answer",
            "payload": {"standing": "historical_only"},
            "freshness": "stale",
            "retrieved_at": "2026-07-01T00:00:00+00:00",
        }
    ],
    policy={"policy": "freshness-required"},
    delegation={"adapter": "read"},
).to_dict()

print(result["adapter_result"]["decision"])
print(result["commitment_request"]["status"])
print(result["execution_handoff"]["status"])
```

---

## Formal route position

```text
User / LLM system
-> LLM-adapter
-> StegVerse-SDK intake
-> manifest binding
-> receipt binding
-> StegVerse-org ingestion
-> bounded test route
-> returned result / reconstruction packet
```

For adversarial or entity-specific tests, the bounded downstream route is `StegGhost/entity-sandbox-runner` after SDK intake.

---

## Integration

| System | Role |
|---|---|
| `StegVerse-org/StegVerse-SDK` | Public SDK intake boundary |
| `StegVerse-002/micro-node-runtime` | Portable transition-table-native governed return-path contract |
| `StegVerse-org/core-node-runtime-demo` | Runtime path compatibility comparison |
| `StegVerse-org/demo_ingest_engine` | Org-side orchestration / result-return boundary |
| `StegGhost/entity-sandbox-runner` | Bounded sandbox test path |
| Trust Kernel | Private authority-bearing governance kernel |
| StegVerse Admission | Private admission / threshold layer |

---

## Links

- Repository: https://github.com/StegVerse-org/LLM-adapter
- Issues: https://github.com/StegVerse-org/LLM-adapter/issues
