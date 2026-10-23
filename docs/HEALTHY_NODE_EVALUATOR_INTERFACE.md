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
