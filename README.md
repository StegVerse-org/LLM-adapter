# StegVerse LLM Adapter

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/github/license/StegVerse-org/LLM-adapter)

Release: v2.1

The dual-purpose governance bridge between AI-generated content and StegVerse execution. Translates LLM outputs into canonical intents and evaluates them through the full safety stack before any code touches reality.

## Dual Purpose

| Purpose | Function |
|---------|----------|
| **Governance Ingress** | LLM output → canonical intent → safety stack → decision |
| **Ecosystem Optimization** | Ecosystem metrics → LLM analysis → optimization → decision |

## Security Features

- **20 dangerous pattern detectors** — Automatic DENY for `os.system`, `eval`, `pickle`, `socket`, etc.
- **Code complexity scoring** — Penalizes high-risk outputs
- **Test/docs detection** — Rewards observable, documented code
- **GCAT state computation** — Derives governance scores from output characteristics

## Install

```bash
pip install stegverse-llm-adapter
```

## Quick Start

```python
from llm_adapter import StegVerseLLMAdapter, LLMProvider

adapter = StegVerseLLMAdapter()

# Govern LLM-generated code
result = adapter.govern_llm_output(
    provider=LLMProvider.OPENAI,
    model="gpt-4",
    prompt="Write a hello function",
    output=llm_output
)

print(result["decision"])   # ADMIT | DENY | DEFER
print(result["receipt"])    # verifiable hash
print(result["gcat_score"]) # legitimacy surplus
```

### Ecosystem Optimization

```python
result = adapter.optimize_ecosystem(
    ecosystem_metrics={"cpu": 0.85, "memory": 0.90, "cost_ratio": 0.8},
    llm_analysis="System approaching limits",
    proposed_changes={"type": "scale", "cost_increase": 5000}
)
```

## Integration

| System | Role |
|--------|------|
| StegVerse-SDK | Public API surface |
| Trust Kernel | Governance evaluation |
| Safety Stack | Layer 1 (Mathematical) |
| demo_ingest_engine | LLM output ingestion |
| StegDB | Adapter state monitoring |

## Links

- Repository: https://github.com/StegVerse-org/LLM-adapter
- Issues: https://github.com/StegVerse-org/LLM-adapter/issues

---

**StegVerse: Execution is not assumed. Execution is admitted.**
