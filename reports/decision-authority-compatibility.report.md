# Decision Authority Compatibility Report

## Repository

`StegVerse-org/LLM-adapter`

## Canonical Source

`StegVerse-Labs/repo-standards/schemas/decision-authority.schema.json`

## Observed Local Decision Values

The README currently documents deterministic decision output as:

```text
ADMIT
DENY
DEFER
```

## Mapping

| LLM-adapter value | ST-004 authority value |
| --- | --- |
| `ADMIT` | `allowed` |
| `DENY` | `denied` |
| `DEFER` | `requires-human-review` |
| `FAIL_CLOSED` | `fail-closed` reserved |
| `ADVISORY_ONLY` | `advisory-only` reserved |

## Compatibility Posture

```text
local_decision_enum_detected: true
compatibility_status: MAPPING_INSTALLED
```

## Boundary

LLM-adapter deterministic decisions are not ST-004 transition authority unless explicitly mapped to the canonical authority vocabulary and supported by policy, delegation, evidence, and validation.
