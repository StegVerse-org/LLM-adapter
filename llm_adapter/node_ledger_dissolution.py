"""NODE-LEDGER-DISSOLUTION-DISBURSEMENT-001: no node chain is ever stranded; the Org records it digest-only.

Rigel's rule: temporary node ledgers are viable as long as each is disbursed
back to an Org Ledger at node dissolution. Dissolution is an event (the node's
NODE_DISSOLUTION), never a timer.

Dissolution applies to EPHEMERAL nodes only: a temporary StegApp, StegBrowser
or StegNode generated through StegOS, whose ledger was anchored by StegOS's
NODE_LEDGER_OPENED record. PERMANENT ledgers never dissolve here; KV and
SKAP_VAULT keep their own chains on their KV storage endpoints; and no GATEWAY
chain is on the org ledger (GATEWAY_CARRIER_LEDGER_NOT_DESIGNATED).

No endpoint is a source of org-ledger records (StegVerse-org/.github#160 comment
6372871021), so the ephemeral ledger is disbursed back to an Org Ledger as
digest-only crossing receipts (Rigel's ruling), never as copied receipts:
  1. the endpoint's own side, on the ephemeral ledger: INTR_MESH_PATH_TRANSFER
     whose message body is stegverse.node-ledger-disbursement/v1 naming the full
     chain (every address oldest first, the head, the genesis, the anchor);
  2. the Org's own side at repository-ledger/StegVerse-org/LLM-adapter (#431):
     one INTR_MESH_PATH_INGRESS (ORGANIZATION_INTR_DESTINATION_INGRESS) per
     ephemeral receipt, oldest first, the source record last, each exactly
     endpoint_ledger_anchor.crossing_evidence: the receipt's digest, the path,
     the communication id and endpoint_head_sha256 (the source record), with a
     supplied hb epoch. No body and no copy of an endpoint receipt is on the
     org ledger.
``read_back`` then reads the Org side back: the crossing receipts for this
communication, each digest-only, whose digests are the planned chain in order,
ending at the source record, which the endpoint's own chain holds with this
disbursement body. Only after that read back does ``finalize`` append
NODE_LEDGER_DISSOLVED on the org ledger. Until then the result is six-field
FAIL_CLOSED NODE_LEDGER_DISBURSEMENT_NOT_READ_BACK and nothing is closed.

After NODE_LEDGER_DISSOLVED, llm_adapter.endpoint_ledger_anchor.verify_anchor
refuses the root (EPHEMERAL_NODE_LEDGER_DISSOLVED), so it is no longer admissible.

NODE_LEDGER_DISSOLVED is the one new transition class: REPOSITORY_LEDGER_INITIALIZATION
opens a ledger location and the InTr path classes move receipts, but no
existing class closes a location.

``plan`` and ``read_back`` are pure (files only, no clock, network or
randomness). ``disburse``, ``finalize`` and ``dissolve`` append through
endpoint_ledger_anchor.append_receipt and run on temporary directories only:
the org-ledger append route is not admitted.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from llm_adapter import endpoint_ledger_anchor as anchor
from llm_adapter import healthy_node_evaluator as hne

ALLOW, FAIL_CLOSED = anchor.ALLOW, anchor.FAIL_CLOSED
EVENT = "NODE_DISSOLUTION"
RESULT_SCHEMA = "stegverse.node-ledger-dissolution-result/v1"
DISSOLUTION_SCHEMA = "stegverse.node-ledger-dissolution/v1"
FAILURE_CODE = "NODE_LEDGER_DISBURSEMENT_NOT_READ_BACK"
TASK = "NODE-LEDGER-DISSOLUTION-DISBURSEMENT-001"
OWNING_GOAL = ("STEGVERSE-CANONICAL-WORK-COORDINATION-001 via NODE-LEDGER-DISSOLUTION-DISBURSEMENT-001 "
               "(class B, Lane B, StegVerse-org/.github#162)")
RETRY_ENTRYPOINT = ("llm_adapter.node_ledger_dissolution.dissolve(node_id, endpoint=..., org_ledger_root=..., "
                    "org_ledger_head_receipt_sha256=..., dissolution_event={event: NODE_DISSOLUTION, node_id})")
NEXT_ATTEMPT = ("on the node's next NODE_DISSOLUTION event, or when the disbursement's destination receipt is read "
                "back at the org ledger; never on a timer")

REASONS: dict[str, tuple[str, str]] = {
    "DISSOLUTION_EVENT_INVALID": ("DISSOLUTION_IS_A_NODE_EVENT", "an event {event: NODE_DISSOLUTION, node_id} for this node"),
    "ENDPOINT_NOT_ANCHORED": ("ENDPOINT_LEDGER_ANCHORED_ON_ORG_LEDGER", "an anchored, undissolved endpoint ledger "
                              "(endpoint_ledger_anchor.verify_anchor ALLOW)"),
    "NOT_EPHEMERAL": ("ENDPOINT_KIND_EPHEMERAL", "only an EPHEMERAL ledger dissolves; PERMANENT ledgers stay "
                      "anchored, KV and SKAP_VAULT keep their own chains, and no GATEWAY chain is on the org ledger"),
    "DISBURSEMENT_RECEIPT_NOT_READ_BACK": ("DISBURSEMENT_DESTINATION_RECEIPT_READ_BACK", "the org's own digest-only "
                                           "INTR_MESH_PATH_INGRESS receipts for this disbursement, the last naming the "
                                           "endpoint's own source record that carries the planned body"),
    "DISBURSED_CHAIN_INCOMPLETE": ("FULL_CHAIN_RECORDED_DIGEST_ONLY_AT_DESTINATION", "one digest-only Org crossing "
                                   "receipt per planned endpoint receipt, oldest first, ending at the source record"),
    "ORG_CROSSING_RECEIPT_NOT_DIGEST_ONLY": anchor.REASONS["ORG_CROSSING_RECEIPT_NOT_DIGEST_ONLY"],
    "ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE": anchor.REASONS["ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE"],
    "HB_EPOCH_NOT_SUPPLIED": anchor.REASONS["HB_EPOCH_NOT_SUPPLIED"],
    "HB_EPOCH_INVALID": anchor.REASONS["HB_EPOCH_INVALID"],
}


def _fail(reason: str, detail: str, node_id: Any = None, **extra: Any) -> dict[str, Any]:
    out = anchor.non_allow(reason, detail, node_id=node_id, schema=RESULT_SCHEMA, failure_code=FAILURE_CODE,
                           reasons=REASONS, retry_entrypoint=RETRY_ENTRYPOINT, owning_existing_goal=OWNING_GOAL,
                           next_attempt=NEXT_ATTEMPT, dissolved=False, **extra)
    out.pop("healthy_node_established", None)
    return out


def plan(node_id: Any, *, endpoint: Any, org_ledger_root: Any, org_ledger_head_receipt_sha256: Any,
         dissolution_event: Any) -> dict[str, Any]:
    """What dissolving this node's ledger disburses. Pure."""
    if not isinstance(dissolution_event, Mapping) or dissolution_event.get("event") != EVENT \
            or dissolution_event.get("node_id") != node_id:
        return _fail("DISSOLUTION_EVENT_INVALID", f"event {dissolution_event!r}", node_id)
    if not isinstance(endpoint, Mapping) or endpoint.get("endpoint_kind") != anchor.EPHEMERAL:
        return _fail("NOT_EPHEMERAL", f"endpoint {endpoint!r}", node_id)
    # Provenance is not a precondition: even a ledger holding a foreign receipt is disbursed whole, never stranded.
    anchored = anchor.verify_anchor(node_id, endpoint=endpoint, org_ledger_root=org_ledger_root,
                                    org_ledger_head_receipt_sha256=org_ledger_head_receipt_sha256,
                                    check_provenance=False)
    if anchored["disposition"] != ALLOW:
        return _fail("ENDPOINT_NOT_ANCHORED", f"{anchored['reason']}: {anchored['detail']}", node_id,
                     anchor_result=anchored)
    if anchored["endpoint_kind"] != anchor.EPHEMERAL or anchored["ledger_lifetime"] != anchor.BOUNDED:
        return _fail("NOT_EPHEMERAL", f"endpoint_kind {anchored['endpoint_kind']!r}", node_id)
    chain, _, _ = hne.read_chain(anchored["ledger_root"])
    addresses = [r["receipt_sha256"] for r in reversed(chain)]
    body = {"schema": anchor.DISBURSEMENT_BODY_SCHEMA, "node_id": node_id, "endpoint_kind": anchored["endpoint_kind"],
            "genesis_receipt_sha256": anchored["genesis_receipt_sha256"], "disbursed_head_sha256": addresses[-1],
            "chain_length": len(addresses), "receipt_sha256s": addresses, "chain_sha256": anchor.sha(addresses),
            "anchor_destination_receipt_sha256": anchored.get("anchor_destination_receipt_sha256"),
            "node_kind": anchored.get("node_kind"),
            "node_ledger_opened_generation_receipt_sha256": anchored.get("node_ledger_opened_generation_receipt_sha256"),
            "destination_location": anchor.ORG_LEDGER_LOCATION,
            "provenance_at_dissolution": (anchor.provenance_failure(chain, node_id, anchored["endpoint_kind"])
                                          or ("PINNED_SHAPE_ONLY", ""))[0]}
    return {"schema": RESULT_SCHEMA, "disposition": ALLOW, "node_id": node_id, "task": TASK,
            "endpoint_kind": anchored["endpoint_kind"], "ledger_root": anchored["ledger_root"],
            "communication_id": f"node-ledger-disbursement:{node_id}@{addresses[-1][7:23]}",
            "disbursement_body": body, "anchor": anchored}


def disburse(planned: Mapping[str, Any], *, org_ledger_root: Any) -> dict[str, Any]:
    """The endpoint's own source record, then the Org's digest-only crossing receipts. Temporary directories only."""
    if planned["disposition"] != ALLOW:
        return dict(planned)
    root, node_id = planned["ledger_root"], planned["node_id"]
    source = anchor.append_source(root, node_id, planned["communication_id"], planned["disbursement_body"])
    chain, failure, detail = hne.read_chain(root)
    if failure:
        return _fail("DISBURSED_CHAIN_INCOMPLETE", f"{failure}: {detail}", node_id)
    last = None
    for receipt in reversed(chain):     # oldest first, the source record last
        org_chain, failure, detail = hne.read_chain(org_ledger_root)
        if failure:
            return _fail("DISBURSEMENT_RECEIPT_NOT_READ_BACK", f"{failure}: {detail}", node_id)
        last = anchor.append_receipt(
            org_ledger_root, anchor.DESTINATION_CLASS,
            f"{anchor.DESTINATION_OPERATION}:{anchor.path_id(node_id)}@{planned['communication_id']}"
            f"#{receipt['receipt_sha256'][7:23]}", org_chain[0]["receipt_sha256"],
            anchor.crossing_evidence(anchor.path_id(node_id), planned["communication_id"], receipt["receipt_sha256"],
                                     source["receipt_sha256"]), anchor.epoch_of(org_chain))
    return {**planned, "outcome": "DISBURSED", "disbursement_source_receipt_sha256": source["receipt_sha256"],
            "disbursement_destination_receipt_sha256": last["receipt_sha256"]}


def _disbursement_crossings(org_chain, planned):
    """The Org's crossing receipts for this disbursement, oldest first. Pure."""
    return [r for r in reversed(org_chain) if r.get("transition_class") == anchor.DESTINATION_CLASS
            and anchor._ev(r).get("communication_id") == planned["communication_id"]
            and anchor._ev(r).get("path_id") == anchor.path_id(planned["node_id"])]


def read_back(planned: Mapping[str, Any], *, org_ledger_root: Any) -> dict[str, Any]:
    """Read the disbursement back at the destination. Pure. ALLOW only when the Org recorded the full chain."""
    node_id = planned.get("node_id")
    if planned.get("disposition") != ALLOW:
        return _fail("ENDPOINT_NOT_ANCHORED", "nothing was planned", node_id)
    body = planned["disbursement_body"]
    org_chain, failure, detail = hne.read_chain(org_ledger_root)
    if failure:
        return _fail("DISBURSEMENT_RECEIPT_NOT_READ_BACK", f"{failure}: {detail}", node_id)
    crossings = _disbursement_crossings(org_chain, planned)
    if not crossings:
        return _fail("DISBURSEMENT_RECEIPT_NOT_READ_BACK", f"no crossing for {planned['communication_id']}", node_id)
    for r in crossings:
        failed = anchor.crossing_record_failure(r, node_id)
        if failed:
            return _fail(*failed, node_id)
    heads = {anchor._ev(r)["boundary_evidence"]["endpoint_head_sha256"] for r in crossings}
    digests = [anchor._ev(r)["source_repository_receipt_sha256"] for r in crossings]
    source_sha = digests[-1]
    chain, failure, _ = hne.read_chain(planned["ledger_root"])
    source = next((r for r in chain if r["receipt_sha256"] == source_sha), None) if not failure else None
    if heads != {source_sha} or source is None or source.get("transition_class") != anchor.SOURCE_CLASS \
            or ((anchor._ev(source).get("message") or {}).get("body")) != body:
        return _fail("DISBURSEMENT_RECEIPT_NOT_READ_BACK", f"the Org crossings for {planned['communication_id']} do "
                     "not end at the endpoint's own source record carrying this disbursement", node_id)
    walked = digests[:-1]
    if walked != body["receipt_sha256s"] or anchor.sha(walked) != body["chain_sha256"] \
            or source.get("previous_receipt_sha256") != body["disbursed_head_sha256"]:
        return _fail("DISBURSED_CHAIN_INCOMPLETE", "the Org-recorded digests differ from the planned chain", node_id)
    return {"schema": RESULT_SCHEMA, "disposition": ALLOW, "node_id": node_id,
            "read_back": "FULL_CHAIN_RECORDED_DIGEST_ONLY",
            "disbursement_destination_receipt_sha256": crossings[-1]["receipt_sha256"],
            "disbursement_source_receipt_sha256": source_sha, "recorded_receipts": len(digests),
            "org_side": "DIGEST_ONLY_CROSSING_RECEIPTS"}


def finalize(planned: Mapping[str, Any], *, org_ledger_root: Any) -> dict[str, Any]:
    """NODE_LEDGER_DISSOLVED on the org ledger, only after the disbursement is read back."""
    node_id = planned.get("node_id")
    readback = read_back(planned, org_ledger_root=org_ledger_root)
    if readback["disposition"] != ALLOW:
        return readback
    chain, _, _ = hne.read_chain(org_ledger_root)
    body = planned["disbursement_body"]
    evidence = {"schema": DISSOLUTION_SCHEMA, "task": TASK, "node_id": node_id, "endpoint_kind": planned["endpoint_kind"],
                "node_kind": body.get("node_kind"), "genesis_receipt_sha256": body["genesis_receipt_sha256"],
                "disbursement_destination_receipt_sha256": readback["disbursement_destination_receipt_sha256"],
                "endpoint_final_head_sha256": readback["disbursement_source_receipt_sha256"],
                "recorded_receipts": readback["recorded_receipts"], "root_admissible_after": False,
                "trigger": {"event": EVENT, "node_id": node_id}, "authority_effect": "NONE"}
    receipt = anchor.append_receipt(org_ledger_root, anchor.DISSOLVED_CLASS,
                                    f"{anchor.DISSOLVED_CLASS}:{node_id}:{body['genesis_receipt_sha256']}",
                                    chain[0]["receipt_sha256"], evidence, anchor.epoch_of(chain))
    return {**readback, "outcome": "DISSOLVED", "dissolved": True, "dissolution_receipt_sha256": receipt["receipt_sha256"]}


def dissolve(node_id: Any, *, endpoint: Any, org_ledger_root: Any, org_ledger_head_receipt_sha256: Any,
             dissolution_event: Any) -> dict[str, Any]:
    planned = plan(node_id, endpoint=endpoint, org_ledger_root=org_ledger_root,
                   org_ledger_head_receipt_sha256=org_ledger_head_receipt_sha256, dissolution_event=dissolution_event)
    if planned["disposition"] != ALLOW:
        return planned
    disbursed = disburse(planned, org_ledger_root=org_ledger_root)
    if disbursed["disposition"] != ALLOW:
        return disbursed
    return finalize(planned, org_ledger_root=org_ledger_root)


__all__ = ["EVENT", "FAILURE_CODE", "REASONS", "TASK", "disburse", "dissolve", "finalize", "plan", "read_back"]
