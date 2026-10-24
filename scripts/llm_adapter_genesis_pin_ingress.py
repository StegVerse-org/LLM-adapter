#!/usr/bin/env python3
"""Pre-pin InTr ingress receiver for the REPOSITORY_LEDGER_GENESIS_PIN trigger (Lane B, StegVerse-org/.github#162).

The genesis pin's trigger reaches LLM-adapter as an InTr ingress signal: the org-side emitter is the existing
path transfer (StegVerse-org/.github .github/workflows/intr-path-transfer.yml), and the carrying pair is the existing
INTR_MESH_PATH_TRANSFER source half kept at <namespace>/source-receipts/<hex>.json plus the Org's digest-only
INTR_MESH_PATH_INGRESS (ORGANIZATION_INTR_DESTINATION_INGRESS) destination half on the namespace chain, checked by
llm_adapter.intr_transport_carrier.verify (byte copy of #432/#433's module). The source half here is the Org's own
record (emitter StegVerse-org/.github, node_ref = the org), so keeping it on the Org ledger is ORG-kind under
Q-PERMANENT-REPOSITORY-LEDGER (StegVerse-org/.github#167 comment 6374130335); a node's own source half never is.

No circularity: #433's normal InTr gate (intr_transport_carrier.observe through org_ledger_location.
designated_org_ledger) accepts a store only at the contract's pinned genesis, so it cannot deliver the pin. This
receiver never reads the pin to authenticate anything. While repository_ledger_location.expected_genesis_receipt_sha256
is null it accepts exactly one signal class, REPOSITORY_LEDGER_GENESIS_OBSERVED (the receipted genesis-observed
record), and relies on the genesis-pin planner's own chain-to-sealed-genesis verification over the read-only ledger
copy, which also requires the published head signer's attestation over that genesis, head and namespace tree
(LC-KV-19; org_ledger_location byte copy of #432's), so a caller-built copy with its own genesis and InTr pair is
refused. Every other signal class is refused with six fields.

Byte-deterministic genesis (StegVerse-org/.github#167 comment 6372442705 item 6): the pin can be precomputed
(planner ``precompute``), so pin-after-observe is only the read-back check. Once the pin is set the pre-pin exception
is closed -- every other signal is refused here and goes to the normal gates -- and a genesis pointer is checked
only as that read-back: the same planner and carrier checks, the observed genesis must equal the pin
(EXPECTED_GENESIS_PIN_CONFLICT otherwise), and nothing is planned for writing (READ_BACK_MATCHES_PIN).

The InTr body is a pointer, not a description (Labs docs/WORKSPACE_KV_DESIGN_SESSION_CAPTURE.md): the genesis
receipt digest and its recorded receipt chain location under its schema. What it means here (signal class
REPOSITORY_LEDGER_GENESIS_OBSERVED, the REPOSITORY_LEDGER_GENESIS_PIN transition) is this receiver's own
description, added on this side.

Both sides record the crossing (Rigel, StegVerse-org/.github#162 comment 6372641743): the egress record on the
source side (the retained INTR_MESH_PATH_TRANSFER) and the ingress record on the destination side (the
INTR_MESH_PATH_INGRESS on this namespace's chain). Each points at the other by digest or location -- the ingress names
the egress's receipt_sha256, the egress names the destination location and communication_id -- and each carries a
supplied epoch. A one-sided crossing is six-field FAIL_CLOSED INTR_CROSSING_NOT_RECORDED_BY_BOTH_SIDES; a crossing
record without a supplied epoch is HB_EPOCH_NOT_SUPPLIED / HB_EPOCH_INVALID. ``plan_destination_half`` gives the
exact emit.py append for the destination's own ingress record (plan only; no transition is wired to it here).

Pure apart from reading the local ledger copy through the planner (local `git`; no clock, network, credential or
dispatch). It writes nothing and appends nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import llm_adapter_repository_ledger_genesis_pin as P  # noqa: E402
from llm_adapter import intr_transport_carrier as carrier  # noqa: E402
from llm_adapter import supplied_epoch  # noqa: E402

RESULT_SCHEMA = "stegverse.genesis-pin-pre-pin-ingress/v1"
SIGNAL_SCHEMA = "stegverse.repository-ledger-genesis-pointer/v1"
SIGNAL_CLASS = "REPOSITORY_LEDGER_GENESIS_OBSERVED"
#: the emitting source named in the carrier path (path_id "<node_ref>->StegVerse-org:intr-destination")
EMITTER_REF = "StegVerse-org/.github"
SIGNAL_KEYS = frozenset({"schema", "ledger_location", "genesis_receipt_sha256", "node_ref"})
#: No endpoint (KV, SKAP Vault, node or gateway, externally or ecosystem maintained) is a GitHub Organization member
#: or a source of org-ledger records (Rigel, relayed on StegVerse-org/.github#160 comment 6372871021): the genesis
#: pointer is originated only by the org's own path (EMITTER_REF).
ENDPOINT_NOT_ORG_SOURCE = P.ENDPOINT_NOT_ORG_SOURCE
ENDPOINT_NOT_ORG_SOURCE_PREDICATE = P.ENDPOINT_NOT_ORG_SOURCE_PREDICATE
ACCEPTED, FAIL_CLOSED = "ACCEPTED_FOR_GENESIS_PIN", "FAIL_CLOSED"
READ_BACK = "READ_BACK_MATCHES_PIN"
OWNING_GOAL = ("StegVerse-org/.github#162 (Lane B; GENESIS_PIN trigger over InTr, option (b)); "
               "StegVerse-org/LLM-adapter#431")
ENTRYPOINT = ("scripts/llm_adapter_genesis_pin_ingress.py receive --signal <genesis-observed signal json> "
              "--carrier <{destination_receipt_sha256, org_ledger_head_receipt_sha256, org_ledger_head_attestation} json> "
              "--org-ledger <read-only copy of refs/stegverse/organization-ledger>")
CROSSING_CODE = "INTR_CROSSING_NOT_RECORDED_BY_BOTH_SIDES"
CROSSING_PREDICATE = "EACH_CROSSING_RECORDED_BY_BOTH_ENDPOINTS"
DESTINATION_PLAN_SCHEMA = "stegverse.intr-destination-half-plan/v1"
DESTINATION_ENTRYPOINT = ("scripts/llm_adapter_genesis_pin_ingress.py plan-destination --source <retained "
                          "INTR_MESH_PATH_TRANSFER receipt json> --hb-epoch <supplied epoch> "
                          "--namespace-head <sha256 of this namespace's head receipt>")
NEXT = ("event-triggered: on the InTr pair the existing org path transfer (intr-path-transfer.yml) appends for the "
        "receipted genesis-observed record; no clock, no polling, no person")


def genesis_signal(genesis_receipt_sha256: str, contract: Mapping[str, Any]) -> dict[str, Any]:
    """The one signal this receiver takes: a pointer to the receipted genesis on its recorded receipt chain."""
    loc = contract["repository_ledger_location"]
    return {"schema": SIGNAL_SCHEMA, "ledger_location": f"{loc['repository']}#{loc['ref']}:{loc['namespace']}",
            "genesis_receipt_sha256": genesis_receipt_sha256, "node_ref": EMITTER_REF}


def crossing_pair_failure(source: Any, destination: Any) -> tuple[str, str, str] | None:
    """(code, predicate, detail) unless both sides recorded the crossing, pointing at each other, each with a
    supplied epoch. Pure."""
    has_source, has_destination = isinstance(source, Mapping) and bool(source), \
        isinstance(destination, Mapping) and bool(destination)
    if not (has_source and has_destination):
        side = "SOURCE_ONLY" if has_source else "DESTINATION_ONLY" if has_destination else "NEITHER"
        return CROSSING_CODE, CROSSING_PREDICATE, (f"{side}: the crossing needs the source's "
                                                   f"{carrier.SOURCE_CLASS} egress record and this namespace's "
                                                   f"{carrier.DESTINATION_CLASS} ingress record")
    sev = source.get("evidence") if isinstance(source.get("evidence"), Mapping) else {}
    dev = destination.get("evidence") if isinstance(destination.get("evidence"), Mapping) else {}
    if dev.get("source_repository_receipt_sha256") != source.get("receipt_sha256") \
            or sev.get("destination_location") != dev.get("destination_location") \
            or sev.get("communication_id") != dev.get("communication_id"):
        return CROSSING_CODE, CROSSING_PREDICATE, ("the two records do not point at each other (ingress -> egress "
                                                   "digest, egress -> destination location and communication_id)")
    for name, record in (("egress", source), ("ingress", destination)):
        failed = supplied_epoch.record_epoch_failure(record)
        if failed:
            return failed[0], supplied_epoch.EPOCH_PREDICATE, f"the {name} record: {failed[1]}"
    return None


def _refuse(code: str, predicate: str, repair: str, *, retry: str = ENTRYPOINT, next_attempt: str = NEXT,
            **extra: Any) -> dict[str, Any]:
    return {"schema": RESULT_SCHEMA, "disposition": FAIL_CLOSED, "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": retry, "owning_existing_goal": OWNING_GOAL,
            "next_attempt": next_attempt, "genesis_pin_plan": None, **extra,
            "ledger_written": False, "contract_written": False, "authority_effect": "NONE_PLAN_ONLY"}


def receive(signal: Any, *, intr_carrier: Any, org_ledger: str | None,
            contract_bytes: bytes | None = None, contract_path: str = P.CONTRACT_REL,
            checkout: Any = None) -> dict[str, Any]:
    endpoint = P.endpoint_contract_failure(contract_path)
    if endpoint:
        return P.endpoint_contract_refusal(endpoint, _refuse)
    bad = P.contract_path_failure(contract_path)
    if bad:
        return _refuse("CONTRACT_PATH_NOT_ALLOWLISTED", "CONTRACT_PATH_IS_AN_ALLOWLISTED_REPO_RELATIVE_431_CONTRACT",
                       f"name one of {list(P.CONTRACT_PATHS)} ({bad})")
    try:
        before = contract_bytes if contract_bytes is not None else P.read_contract(contract_path, checkout)
        contract = json.loads(before)
        shape = P.contract_shape_failure(contract)
    except (OSError, ValueError) as exc:
        shape = f"unreadable ({type(exc).__name__})"
    endpoint = None if shape else P.endpoint_contract_failure(contract_path, contract)
    if endpoint:
        return P.endpoint_contract_refusal(endpoint, _refuse)
    if shape:
        return _refuse("CONTRACT_NOT_431_SHAPE", "CONTRACT_HAS_THE_431_REPOSITORY_LEDGER_LOCATION_SHAPE",
                       f"{contract_path}: {shape}")
    loc = contract["repository_ledger_location"]
    pinned = loc.get(P.FIELD)
    is_pointer = isinstance(signal, Mapping) and signal.get("schema") == SIGNAL_SCHEMA
    if pinned is not None and not is_pointer:
        return _refuse("PRE_PIN_INGRESS_CLOSED", "EXPECTED_GENESIS_PIN_IS_NULL",
                       f"{P.FIELD} is set ({pinned}); the pre-pin exception is closed and signals take the normal "
                       "InTr gate: the pinned genesis and authenticated head (intr_transport_carrier.observe through "
                       "org_ledger_location.designated_org_ledger, #433). Only the genesis pointer is still taken "
                       "here, as the read-back check against the pin",
                       retry=carrier.RETRY_ENTRYPOINT, next_attempt=carrier.NEXT_ATTEMPT)
    if is_pointer and "node_ref" in signal and signal.get("node_ref") != EMITTER_REF:
        return _refuse(ENDPOINT_NOT_ORG_SOURCE, ENDPOINT_NOT_ORG_SOURCE_PREDICATE,
                       f"the genesis pointer names node_ref {signal.get('node_ref')!r}; only the org's own path "
                       f"({EMITTER_REF}) originates a record on refs/stegverse/organization-ledger. No endpoint is an "
                       "Organization member or a source of org-ledger records (StegVerse-org/.github#160 comment "
                       "6372871021): endpoint data crosses only through InTr and is recorded at both ends, the Org "
                       "side as the org's own digest-only crossing receipt",
                       next_attempt="on a pointer emitted by the org's own path transfer (event-triggered)")
    if not is_pointer or set(signal) != SIGNAL_KEYS \
            or signal != genesis_signal(signal.get("genesis_receipt_sha256"), contract):
        got = signal.get("schema") if isinstance(signal, Mapping) else type(signal).__name__
        return _refuse("PRE_PIN_SIGNAL_CLASS_NOT_ACCEPTED", "PRE_PIN_SIGNAL_IS_THE_GENESIS_PIN_TRIGGER",
                       f"only one signal is received here: the {SIGNAL_CLASS} pointer "
                       f"({SIGNAL_SCHEMA}, exact keys {sorted(SIGNAL_KEYS)}) to {contract['repository']}'s genesis; "
                       f"got {got!r}. Other signals wait for the pin and then take the normal gates",
                       next_attempt="after REPOSITORY_LEDGER_GENESIS_PIN is admitted, through the normal gates "
                                    "(#433); event-triggered, never on a timer")
    # The planner's own chain-to-sealed-genesis verification, never the pin.
    # LC-KV-19: the read-back must carry a published head signer's attestation (cited with the carrier).
    cited = intr_carrier if isinstance(intr_carrier, Mapping) else {}
    planned = P.plan(org_ledger=org_ledger, genesis_receipt_sha256=signal["genesis_receipt_sha256"],
                     contract_bytes=before, org_ledger_head_attestation=cited.get("org_ledger_head_attestation"),
                     contract_path=contract_path, checkout=checkout)
    if planned["disposition"] != P.ALLOW:
        return _refuse(planned["failure_code"], planned["failed_predicate"], planned["required_evidence_or_repair"],
                       observation=planned.get("observation"),
                       **({"next_attempt": planned["next_attempt"]} if planned["failed_predicate"] == P.HEAD_PREDICATE
                          else {}))
    chain, _, failure = P.read_chain(org_ledger, loc["namespace"])
    destination = next((r for r in chain if r.get("receipt_sha256") == cited.get("destination_receipt_sha256")), {})
    dev = destination.get("evidence") if isinstance(destination.get("evidence"), Mapping) else {}
    source_sha = dev.get("source_repository_receipt_sha256")
    retained = None
    if isinstance(source_sha, str) and source_sha.startswith("sha256:") and "/" not in source_sha:
        retained = P.ledger_file(org_ledger, planned["observation"]["tip"],
                                 f"{loc['namespace']}/source-receipts/{source_sha[7:]}.json")
    if not destination and isinstance(cited.get("source_receipt_sha256"), str) and not retained:
        named = cited["source_receipt_sha256"]
        if named.startswith("sha256:") and "/" not in named:
            retained = P.ledger_file(org_ledger, planned["observation"]["tip"],
                                     f"{loc['namespace']}/source-receipts/{named[7:]}.json")
    if not failure and (not destination or not retained):
        code, predicate, detail = crossing_pair_failure(retained, destination)
        return _refuse(code, predicate, f"{detail}. Each side records the crossing and points at the other's "
                       "record by digest (StegVerse-org/.github#162 comment 6372641743)",
                       next_attempt="event-triggered: on the read-back of the missing side's record",
                       one_sided=detail.split(":", 1)[0])
    refused = failure and ("ORG_LEDGER_CHAIN_UNREAD", failure) or carrier.verify(
        signal, destination_receipt_sha256=cited.get("destination_receipt_sha256"),
        org_ledger_head_receipt_sha256=cited.get("org_ledger_head_receipt_sha256"),
        org_chain=chain, source_record=retained)
    if refused:
        return _refuse(carrier.FAILURE_CODE, carrier.PREDICATE, f"{refused[0]}: {refused[1]}. {carrier.REPAIR}",
                       carrier_reason=refused[0])
    paired = crossing_pair_failure(retained, destination)
    if paired:
        return _refuse(paired[0], paired[1], f"{paired[2]} (StegVerse-org/.github#162 comment 6372641743)")
    carried_by = {"destination_receipt_sha256": cited["destination_receipt_sha256"],
                  "source_receipt_sha256": source_sha,
                  "org_ledger_head_receipt_sha256": cited["org_ledger_head_receipt_sha256"],
                  "org_ledger_head_authenticated": True,
                  "carrier_classes": [carrier.SOURCE_CLASS, carrier.DESTINATION_CLASS]}
    if planned["consumes_receipt"] is not None:
        evidence = planned["consumes_receipt"]["emit_append"]["evidence"]
        evidence["carried_by"] = carried_by
        evidence["consumes"].append({"receipt_sha256": cited["destination_receipt_sha256"],
                                     "transition_class": carrier.DESTINATION_CLASS,
                                     "ledger_location": planned["ledger_location"]})
    return {"schema": RESULT_SCHEMA, "disposition": ACCEPTED if pinned is None else READ_BACK,
            "signal_class": SIGNAL_CLASS, "pre_pin_exception": pinned is None, "read_back_check": planned["read_back_check"],
            "carried_by": carried_by, "genesis_pin_plan": planned,
            "ledger_written": False, "contract_written": False, "authority_effect": "NONE_PLAN_ONLY"}


def plan_destination_half(source: Any, *, hb_epoch: Any, namespace_head_receipt_sha256: Any) -> dict[str, Any]:
    """The exact emit.py append for the destination's own ingress record of a sealed egress record, or six-field
    FAIL_CLOSED. Plan only: nothing is appended, and no transition is wired to it here. Validates the egress record
    before calling carrier.destination_evidence, so a malformed source refuses instead of raising. Pure."""
    def refuse(code: str, predicate: str, repair: str) -> dict[str, Any]:
        return {"schema": DESTINATION_PLAN_SCHEMA, "disposition": FAIL_CLOSED, "failure_code": code,
                "failed_predicate": predicate, "required_evidence_or_repair": repair,
                "retry_entrypoint": DESTINATION_ENTRYPOINT, "owning_existing_goal": OWNING_GOAL,
                "next_attempt": "event-triggered: on the read-back of a sealed egress record with a supplied epoch",
                "emit_append": None, "ledger_written": False, "authority_effect": "NONE_PLAN_ONLY"}
    failed = supplied_epoch.supplied_epoch_failure(hb_epoch)
    if failed:
        return refuse(failed[0], supplied_epoch.EPOCH_PREDICATE, failed[1])
    ev = source.get("evidence") if isinstance(source, Mapping) else None
    sealed = isinstance(source, Mapping) and carrier.sha({k: v for k, v in source.items()
                                                          if k != "receipt_sha256"}) == source.get("receipt_sha256")
    missing = [k for k in ("path_id", "message", "message_sha256", "endpoint_kind", "communication_id",
                           "destination_location") if not isinstance(ev, Mapping) or k not in ev]
    if not sealed or source.get("transition_class") != carrier.SOURCE_CLASS or missing \
            or not isinstance(source.get("repository"), str) or not carrier.payload_ok(ev):
        return refuse(CROSSING_CODE, CROSSING_PREDICATE,
                      f"a sealed {carrier.SOURCE_CLASS} egress record with its evidence"
                      + (f" (missing {missing})" if missing else ""))
    if ev["destination_location"] != carrier.ORG_LEDGER_LOCATION:
        return refuse(CROSSING_CODE, CROSSING_PREDICATE, f"the egress record points at {ev['destination_location']!r}, "
                      f"not this namespace ({carrier.ORG_LEDGER_LOCATION})")
    failed = supplied_epoch.record_epoch_failure(source)
    if failed:
        return refuse(failed[0], supplied_epoch.EPOCH_PREDICATE, f"the egress record: {failed[1]}")
    if not (isinstance(namespace_head_receipt_sha256, str) and namespace_head_receipt_sha256.startswith("sha256:")
            and len(namespace_head_receipt_sha256) == 71):
        return refuse(CROSSING_CODE, CROSSING_PREDICATE, "the namespace head receipt_sha256 the ingress follows")
    return {"schema": DESTINATION_PLAN_SCHEMA, "disposition": "ALLOW",
            "emit_append": {"transition_id": f"{carrier.DESTINATION_CLASS}:{ev['communication_id']}",
                            "transition_class": carrier.DESTINATION_CLASS,
                            "predecessor_state_sha256": namespace_head_receipt_sha256,
                            "successor_state_sha256": source["receipt_sha256"],
                            "evidence": carrier.destination_evidence(source), "authority_effect": "NONE",
                            "hb_epoch": int(str(hb_epoch))},
            "appended_by": ".stegverse/transition-ledger/emit.py append, when an admitted transition runs it",
            "wired_to_transition": False, "ledger_written": False, "authority_effect": "NONE_PLAN_ONLY"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("receive")
    p.add_argument("--signal", required=True)
    p.add_argument("--carrier", required=True)
    p.add_argument("--org-ledger")
    p.add_argument("--contract-path", default=P.CONTRACT_REL, choices=P.CONTRACT_PATHS)
    p.add_argument("--checkout")
    p.add_argument("--out")
    a = ap.parse_args(argv)
    result = receive(json.loads(Path(a.signal).read_text()), intr_carrier=json.loads(Path(a.carrier).read_text()),
                     org_ledger=a.org_ledger, contract_path=a.contract_path, checkout=a.checkout)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    sys.stdout.write(text)
    return 0 if result["disposition"] in (ACCEPTED, READ_BACK) else 3


if __name__ == "__main__":
    raise SystemExit(main())
