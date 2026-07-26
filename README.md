# StegVerse LLM Adapter

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

Release: v2.1

## Position in the LLM Communications Stack

- **Stack ID:** `STEGVERSE-LLM-COMMS-STACK-v1`
- **Component ID:** `llm-adapter`
- **Primary bounded role:** SDK-adjacent access bridge that connects an authorized user's external LLM as a user-class participant for Demo test-suite interaction and bounded entity-sandbox submission
- **Consumes:** authenticated user/LLM requests, Demo test-suite operations, test data, provider and model metadata, continuity evidence, policy and delegation references
- **Produces:** manifest-ready test packages, normalized LLM-originated inputs, governed adapter receipts, bounded sandbox submissions, transition candidates, and governed results returned to the originating LLM
- **Does not own:** user identity merely from connection, model hosting, general communications routing, continuity truth, commit-time authority, unrestricted execution, publication authority, internal collaboration policy, or Master Records custody
- **Deployment posture:** StegVerse-org instances remain Demo and conformance surfaces unless a separate accreditation record establishes another posture
- **Canonical reference:** [`docs/LLM_COMMUNICATIONS_STACK.md`](docs/LLM_COMMUNICATIONS_STACK.md)

`LLM-adapter` is the SDK-adjacent access bridge through which a user's external LLM can connect to StegVerse, view and manipulate the bounded Demo test suite, construct test submissions, send data to `StegGhost/entity-sandbox-runner`, and receive governed results through the original user path.

Provider-response normalization and metadata binding are supporting capabilities. They do not redefine the repository as a provider broker or displace its user-LLM access purpose.

The adapter does not execute LLM output directly. It normalizes output, classifies risk, produces a governance decision, and prepares admissible outputs for receipt-bound routing through the StegVerse formal testing path.

---

## Boundary rule

```text
LLM connection is not authority.
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
user / external LLM request
  -> authenticated adapter access
  -> SDK-equivalent Demo/test operation
  -> manifest-ready package
  -> Demo test suite or entity sandbox runner
  -> governed receipt and result
  -> original user / external LLM path
```

Local verification:

```bash
pytest
stegverse-llm-adapter fixtures/governed_response_fixture.json --pretty
python scripts/smoke_governed_session.py
python scripts/verify_goal4.py
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

## AI Entry free-tier trust boundary

Goal 7 adds a bounded free-tier trust layer for the StegVerse governed LLM entry point.

The free tier is designed to prove the core claim through bounded live governed use rather than static demonstration material. The adapter exposes a Site-facing `free_tier_trust` response field with quota, receipt export, replay, reconstruction, retention, upgrade, and non-authority metadata.

```text
public user inquiry
-> bounded free-tier quota envelope
-> governed LLM adapter request
-> Site-visible free-tier trust metadata
-> transition receipt inspection
-> bounded receipt export / replay / reconstruction limits
-> upgrade only for scale, retention, connectors, premium models, or API depth
```

Free-tier policy files:

```text
docs/FREE_TIER_TRUST_POLICY.md
examples/free_tier_trust_policy.json
llm_adapter/free_tier_quota.py
llm_adapter/free_tier_limits.py
```

Verify the free-tier boundary with:

```bash
python scripts/verify_free_tier_quota.py
python scripts/verify_free_tier_limits.py
python scripts/verify_ai_entry_free_tier_metadata.py
pytest tests/test_free_tier_quota.py -v
pytest tests/test_free_tier_limits.py -v
pytest tests/test_ai_entry_free_tier_trust_metadata.py -v
```

The free-tier boundary does not claim that quota availability is admissibility, that replay or reconstruction grants commit-time standing, that receipt export is permanent retention, or that upgrading changes admissibility requirements.

---

## Roles

| Role | Function |
|---|---|
| User-LLM access bridge | Authorized external LLM -> SDK-equivalent Demo/test capability -> governed return |
| SDK-side adapter | User / LLM Adapter submission -> manifest-ready package |
| Demo test-suite interface | View and manipulate bounded Demo test-suite state under authenticated scope |
| Test-route feeder | Route admissible packages into SDK / ingestion / sandbox testing paths |
| Governed runtime boundary | LLM-originated input -> continuity evidence -> receipts -> disabled unrestricted execution handoff |
| Micro-node return-path caller | Adapter fixture -> micro-node-compatible request -> governed return to origin |
| AI Entry free-tier trust boundary | Public inquiry -> bounded quota/receipt/replay metadata -> Site-visible trust envelope |

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
- disabled unrestricted execution gateway by default;
- micro-node-compatible governed return-path fixture verification;
- side-effect-free free-tier quota and receipt/replay limit evaluation.

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
User / external LLM
-> LLM-adapter authenticated user-access boundary
-> StegVerse-SDK-equivalent Demo/test capabilities
-> manifest binding
-> receipt binding
-> StegVerse-org Demo test route
-> StegGhost/entity-sandbox-runner when adversarial or entity-specific testing is requested
-> returned result / reconstruction packet
-> originating user / external LLM
```

For adversarial or entity-specific tests, the bounded downstream route is `StegGhost/entity-sandbox-runner` after adapter/SDK-equivalent intake.

---

## Integration

| System | Role |
|---|---|
| `StegVerse-org/StegVerse-SDK` | Parallel direct public/application entry with the same bounded Demo/test distinction |
| `StegVerse-002/micro-node-runtime` | Portable transition-table-native governed return-path contract |
| `StegVerse-org/core-node-runtime-demo` | Runtime path compatibility comparison |
| `StegVerse-org/demo_ingest_engine` | Demo test-suite orchestration and result-return boundary |
| `StegGhost/entity-sandbox-runner` | Bounded sandbox test path |
| Trust Kernel | Private authority-bearing governance kernel |
| StegVerse Admission | Private admission / threshold layer |

---

## Links

- Repository: https://github.com/StegVerse-org/LLM-adapter
- Issues: https://github.com/StegVerse-org/LLM-adapter/issues
