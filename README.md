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

## Roles

| Role | Function |
|---|---|
| Governance ingress | LLM output → canonical intent → safety classification → decision |
| SDK-side adapter | User / LLM Adapter submission → manifest-ready package |
| Test-route feeder | Route admissible packages into SDK / ingestion / sandbox testing paths |

---

## Security features

- dangerous-pattern detection for high-risk generated code;
- code complexity scoring;
- test and documentation signal detection;
- GCAT/BCAT-style governance score computation;
- deterministic decision output: `ADMIT`, `DENY`, or `DEFER`;
- receipt-ready result structure.

---

## Install

```bash
pip install stegverse-llm-adapter
```

---

## Quick start

```python
from llm_adapter import StegVerseLLMAdapter, LLMProvider

adapter = StegVerseLLMAdapter()

result = adapter.govern_llm_output(
    provider=LLMProvider.OPENAI,
    model="gpt-4",
    prompt="Write a hello function",
    output=llm_output,
)

print(result["decision"])   # ADMIT | DENY | DEFER
print(result["receipt"])    # verifiable hash / receipt-ready reference
print(result["gcat_score"]) # governance score
```

---

## Formal route position

```text
User / LLM system
→ LLM-adapter
→ StegVerse-SDK intake
→ manifest binding
→ receipt binding
→ StegVerse-org ingestion
→ bounded test route
→ returned result / reconstruction packet
```

For adversarial or entity-specific tests, the bounded downstream route is `StegGhost/entity-sandbox-runner` after SDK intake.

---

## Integration

| System | Role |
|---|---|
| `StegVerse-org/StegVerse-SDK` | Public SDK intake boundary |
| `StegVerse-org/demo_ingest_engine` | Org-side orchestration / result-return boundary |
| `StegGhost/entity-sandbox-runner` | Bounded sandbox test path |
| Trust Kernel | Private authority-bearing governance kernel |
| StegVerse Admission | Private admission / threshold layer |

---

## Links

- Repository: https://github.com/StegVerse-org/LLM-adapter
- Issues: https://github.com/StegVerse-org/LLM-adapter/issues
