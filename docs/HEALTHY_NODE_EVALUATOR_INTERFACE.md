# Healthy-node evaluator and ingress admission: consumer interface (LC-KV-13, LC-KV-14)

Owning lane: InTr and Mesh Destinations (Lane B, StegVerse-org/.github#162). Consuming lane: Lane D (KV and WorkSpace), for layer 1, `KV_REACHABLE_ONLY_VIA_INTR_FROM_HEALTHY_NODE`.
Owning goal: KV-SKAP-VAULT-FUNCTIONAL-001 (StegVerse-Labs/.github#3324).
This interface is E0: it is deterministic and uses no clock, no network, no randomness and no LLM. It grants no authority.

## `llm_adapter.healthy_node_evaluator.evaluate`

```python
evaluate(node_id, *, ledger_root, transport_state="INSTALLED",
         report_receipt_sha256=None, require_admission=False,
         repository="StegVerse-org/LLM-adapter") -> dict
```

The evaluator decides `REQUESTER_IS_CURRENTLY_ADMITTED_HEALTHY_NODE` (gate `CURRENT_NODE_HEALTH`) only from receipted health reports. A report counts only when all of these hold:
1. It is a `NODE_HEALTH_REPORTED` receipt whose evidence schema is `stegverse.node-health-report/v1` and whose `node_id` matches.
2. It is read back on the chain walked from `HEAD.json` to genesis.
3. Every receipt on that walk hashes to its address: the file name, `receipt_sha256`, and sha256 of the canonical body without `receipt_sha256` all agree.
4. Every receipt names the expected repository.
5. It is the newest report for the node on the chain. "Currently" means chain position, not a timestamp.

| Field | ALLOW | non-ALLOW |
|---|---|---|
| `disposition` | `ALLOW` | `DENY` (the receipted report is not exactly `HEALTHY`) or `FAIL_CLOSED` (everything else) |
| `healthy_node_established` | `true` | `false` |
| `health_report_receipt_sha256` | the current HEALTHY report | present when a report was read |
| `failure_code` … `next_attempt` | n/a | the six fields; `failure_code` is always `NODE_NOT_CURRENTLY_ADMITTED_HEALTHY` and `failed_predicate` is always `REQUESTER_IS_CURRENTLY_ADMITTED_HEALTHY_NODE` |
| `reason` | n/a | one of `REASONS` (for example `HEALTH_REPORT_MISSING`, `HEALTH_REPORT_NOT_RECEIPTED`, `RECEIPT_HASH_MISMATCH`, `HEALTH_REPORTED_NOT_HEALTHY`, `HEALTH_REPORT_SUPERSEDED`, `TRANSPORT_NOT_INSTALLED`, `NODE_NOT_ADMITTED`) |

- **Admission check (`require_admission=True`).** Layer 1 and later stages should pass this. It also requires the newest `NODE_INGRESS_*` receipt for the node to be `NODE_INGRESS_ADMITTED`, with `healthy_node_established: true`, citing the same current report.
- **Ingress boundary.** The ingress boundary evaluates with `False`, because it is the admission.
- **Layer 1 refusals.** Layer 1 maps any non-ALLOW to its own `KV_ACCESS_LAYER1_REFUSED` and keeps the evaluator's six fields as the cause.

`health_report_authenticated` is `NOT_PROVEN`. A receipt is not an authentication. `AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE` and `NODE_IDENTITY_BINDING` are earlier gates and are not observed here.

## `llm_adapter.node_ingress_boundary.admit`

```python
admit(signal, *, transport="HTTP", health=None, health_report_receipt_sha256=None, hb_epoch=None) -> dict
```

`admit` never raises for a refusal. Every arrival is recorded first: ALLOW under `NODE_INGRESS_ADMITTED`, anything else under `NODE_INGRESS_REFUSED`.

- **ALLOW.** Returned only when standing resolves and `evaluate` returns ALLOW over an INSTALLED transport. The result has:
  - `disposition: "ALLOW"` and `healthy_node_established: true`;
  - `standing`, which is the node-standing disposition that used to be returned as `disposition`;
  - `node_class` and `continuation_profile`;
  - `health_evaluation`;
  - `ingress_record`, `ingress_receipt_sha256`, `ingress_transition_id` and `ingress_ordering`.
- **Non-ALLOW.** The result has:
  - `disposition` (`DENY` or `FAIL_CLOSED`) and `healthy_node_established: false`;
  - the six fields, with `failure_code` `NODE_NOT_CURRENTLY_ADMITTED_HEALTHY`;
  - `failed_stage` (`TRANSPORT`, `NODE_STANDING` or `CURRENT_NODE_HEALTH`) and `reason`;
  - `standing_refusal`, the verbatim node-standing refusal, for a standing failure;
  - `health_evaluation`, for a health failure;
  - the `NODE_INGRESS_REFUSED` receipt reference.
- **`health` callable.** Its result is recorded as `observed_health_unreceipted_status` and decides nothing.

`POST /api/node-standing` reaches `admit` and returns 200 on ALLOW. A non-ALLOW returns 422 for FAIL_CLOSED or 403 for DENY, with the admission's six fields in `detail`. A request may cite `health_report_receipt_sha256`.

## `llm_adapter.node_health_report_producer` (LC-KV-13 producer)

```python
plan(trigger_receipt_sha256, *, ledger_root, repository="StegVerse-org/LLM-adapter") -> dict     # deterministic core, read-only
produce(trigger_receipt_sha256, *, ledger_root, repository="StegVerse-org/LLM-adapter") -> dict  # plan, then append via emit.py
```

**Triggers.** The producer fires on an event, never on a timer, cron or poll. The trigger is a receipt already on the chain:

| trigger event | trigger receipt |
|---|---|
| `NODE_REGISTRATION` | `NODE_INGRESS_REFUSED` with `refusal_stage` CURRENT_NODE_HEALTH and `evaluated_node_id`, or `NODE_INGRESS_ADMITTED`. `admit` fires this itself after recording a health-stage refusal, and returns the result as `health_report_production`. |
| `NODE_IDENTITY_BOUND` | `NODE_IDENTITY_BINDING` |
| `HEALTH_CHECK_RECEIPTED` | `NODE_HEALTH_CHECK_OBSERVED` (schema `stegverse.node-health-check/v1`) |

**Required receipted evidence.** All of it must be on the same chain from `HEAD.json`, with every body hash matching its address:
- `AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE` for the node, with `disposition` ALLOW;
- a newer `NODE_IDENTITY_BINDING` for the node, with `disposition` ALLOW and `existence_receipt_sha256` citing that existence receipt;
- the node's newest `NODE_HEALTH_CHECK_OBSERVED`.

**Emitted receipt.** The receipt has `transition_class` `NODE_HEALTH_REPORTED` and `transition_id` `NODE_HEALTH_REPORTED:<node_id>:<trigger sha>`.
- `predecessor_state_sha256` is the previous report for the node, or sha256 of `{"node_id", "health_report": null}` if there is none.
- `successor_state_sha256` is sha256 of the evidence.
- `hb_reference.epoch` is the trigger's epoch, so it is not derived from a clock.

The evidence fields are:
- `schema` `stegverse.node-health-report/v1`, `node_id`;
- `status`: `HEALTHY` only when the check says exactly HEALTHY, otherwise `UNHEALTHY`;
- `observed_health_check_status`, kept verbatim;
- `trigger` {event, receipt_sha256, transition_class};
- `evidence_receipts` {authenticated_reciprocal_node_existence, node_identity_binding, health_check};
- `previous_health_report_receipt_sha256`;
- `transition_manifest` {schema `stegverse.node-health-report-transition/v1`, intended_action, producer, producer_version};
- `intended_action`, `transition_is_the_disposition_of_the_intended_action`, `disposition` ALLOW;
- `health_report_authenticated` `NOT_PROVEN_BEYOND_RECEIPTED_PREREQUISITES`;
- `authority_effect` NONE.

**Result.** `disposition` is ALLOW, with `outcome` EMITTED or NOOP_ALREADY_CURRENT, `report_status` and `health_report_receipt_sha256`. Otherwise it is FAIL_CLOSED with the six fields: `failure_code` NODE_HEALTH_REPORT_NOT_PRODUCED, a `failed_predicate` naming the missing receipted input, and a `reason`. Nothing is appended on FAIL_CLOSED.

## The three input producers (class B pieces 1-3)

Every producer has the same shape: `plan(...)` is the deterministic, read-only core, with no clock, network or randomness, and `produce(...)` plans and then appends through `emit.py`. Each is triggered by an event, never by a timer. Every refusal is FAIL_CLOSED with the six fields and appends nothing. `hb_reference.epoch` is the HEAD receipt's epoch, or the declared anchor epoch on an empty ledger, so `derived_from_clock` is false.

| producer | trigger / inputs | appends | `failure_code` |
|---|---|---|---|
| `node_existence_readback.produce(broker_receipt, *, ledger_root)` | a StegOS `stegos.node-event-execution-broker.receipt/v3` from capability `observe-reciprocal-node-existence` | `AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE`, evidence `stegverse.node-existence-readback/v1` {node_id = broker `node_ref`, disposition ALLOW, source_broker_receipt, observation} | `NODE_EXISTENCE_NOT_READ_BACK` |
| `node_identity_binding_producer.produce(existence_receipt_sha256, identity_claim, profile, *, ledger_root)` | the node's newest existence ALLOW on the chain, a signed `stegverse.node-identity-claim/v1`, and the observed profile (its StegOS sha256 must equal the receipted `profile_sha256`) | `NODE_IDENTITY_BINDING`, evidence `stegverse.node-identity-binding/v1` {node_id, disposition ALLOW, existence_receipt_sha256, key_ref, public_key_b64, identity_claim_sha256} | `NODE_IDENTITY_NOT_BOUND` |
| `node_health_check_projection.produce(binding_receipt_sha256, observation, attestation, *, ledger_root)` | the node's newest binding ALLOW, a StegHealth `stegverse.steghealth.sovereign-runtime-observation/v1`, and a `stegverse.node-health-attestation/v1` signed by the bound key | `NODE_HEALTH_CHECK_OBSERVED`, evidence `stegverse.node-health-check/v1` {node_id, status HEALTHY or UNHEALTHY, failing_predicates, source, binding_receipt_sha256} | `NODE_HEALTH_CHECK_NOT_OBSERVED` |

**Key reference.** The profile's `node_identity_key` holds {algorithm `Ed25519`, key_id, node_id, public_key_b64, custody `TV/TVC`}. The claim's `key_ref` is {algorithm, key_id, public_key_sha256}.

**Signatures.** The signed bytes are `<schema>\n` followed by the canonical JSON of the object without `signature_b64`. `llm_adapter.ed25519_verify` verifies only; it has no signing function, and any input field named like private key material is refused.

**Requirement on real inputs.** The node's public InTr profile must publish `node_identity_key`. StegOS's profile validator allows the field but doesn't require it.
