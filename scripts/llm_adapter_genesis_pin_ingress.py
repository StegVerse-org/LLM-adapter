#!/usr/bin/env python3
"""Pre-pin InTr ingress receiver for the REPOSITORY_LEDGER_GENESIS_PIN trigger (Lane B, StegVerse-org/.github#162).

The genesis pin's trigger reaches LLM-adapter as an InTr ingress signal: the org-side emitter is the existing
path transfer (StegVerse-org/.github .github/workflows/intr-path-transfer.yml), and the carrying pair is the existing
INTR_MESH_PATH_TRANSFER source half retained at <namespace>/source-receipts/<hex>.json plus the
INTR_MESH_PATH_INGRESS (ORGANIZATION_INTR_DESTINATION_INGRESS) destination half on the namespace chain, checked by
llm_adapter.intr_transport_carrier.verify (byte copy of #432/#433's module, unchanged).

No circularity: #433's normal InTr gate (intr_transport_carrier.observe through org_ledger_location.
designated_org_ledger) accepts a store only at the contract's pinned genesis, so it cannot deliver the pin. This
receiver never reads the pin to authenticate anything. While repository_ledger_location.expected_genesis_receipt_sha256
is null it accepts exactly one signal class, REPOSITORY_LEDGER_GENESIS_OBSERVED (the receipted genesis-observed
record), and relies on the genesis-pin planner's own chain-to-sealed-genesis verification over the read-only ledger
copy, which also requires the published head signer's attestation over that genesis, head and namespace tree
(LC-KV-19; org_ledger_location byte copy of #432's), so a caller-built copy with its own genesis and InTr pair is
refused. Every other signal class is refused with six fields. Once the pin is set this exception is closed: every
signal, including a repeated trigger, is refused here and goes to the normal gates.

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

RESULT_SCHEMA = "stegverse.genesis-pin-pre-pin-ingress/v1"
SIGNAL_SCHEMA = "stegverse.repository-ledger-genesis-observed/v1"
SIGNAL_CLASS = "REPOSITORY_LEDGER_GENESIS_OBSERVED"
#: the emitting source named in the carrier path (path_id "<node_ref>->StegVerse-org:intr-destination")
EMITTER_REF = "StegVerse-org/.github"
SIGNAL_KEYS = frozenset({"schema", "signal_class", "repository", "ledger_location", "genesis_receipt_sha256",
                         "transition_class", "node_ref"})
ACCEPTED, FAIL_CLOSED = "ACCEPTED_FOR_GENESIS_PIN", "FAIL_CLOSED"
OWNING_GOAL = ("StegVerse-org/.github#162 (Lane B; GENESIS_PIN trigger over InTr, option (b)); "
               "StegVerse-org/LLM-adapter#431")
ENTRYPOINT = ("scripts/llm_adapter_genesis_pin_ingress.py receive --signal <genesis-observed signal json> "
              "--carrier <{destination_receipt_sha256, org_ledger_head_receipt_sha256, org_ledger_head_attestation} json> "
              "--org-ledger <read-only copy of refs/stegverse/organization-ledger>")
NEXT = ("event-triggered: on the InTr pair the existing org path transfer (intr-path-transfer.yml) appends for the "
        "receipted genesis-observed record; no clock, no polling, no person")


def genesis_signal(genesis_receipt_sha256: str, contract: Mapping[str, Any]) -> dict[str, Any]:
    """The one signal the pre-pin receiver accepts: the receipted genesis-observed record, as an InTr body."""
    loc = contract["repository_ledger_location"]
    return {"schema": SIGNAL_SCHEMA, "signal_class": SIGNAL_CLASS, "repository": contract["repository"],
            "ledger_location": f"{loc['repository']}#{loc['ref']}:{loc['namespace']}",
            "genesis_receipt_sha256": genesis_receipt_sha256, "transition_class": P.TRANSITION_CLASS,
            "node_ref": EMITTER_REF}


def _refuse(code: str, predicate: str, repair: str, *, retry: str = ENTRYPOINT, next_attempt: str = NEXT,
            **extra: Any) -> dict[str, Any]:
    return {"schema": RESULT_SCHEMA, "disposition": FAIL_CLOSED, "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": retry, "owning_existing_goal": OWNING_GOAL,
            "next_attempt": next_attempt, "genesis_pin_plan": None, **extra,
            "ledger_written": False, "contract_written": False, "authority_effect": "NONE_PLAN_ONLY"}


def receive(signal: Any, *, intr_carrier: Any, org_ledger: str | None,
            contract_bytes: bytes | None = None) -> dict[str, Any]:
    before = contract_bytes if contract_bytes is not None else P.CONTRACT_PATH.read_bytes()
    contract = json.loads(before)
    loc = contract["repository_ledger_location"]
    if loc.get(P.FIELD) is not None:
        return _refuse("PRE_PIN_INGRESS_CLOSED", "EXPECTED_GENESIS_PIN_IS_NULL",
                       f"{P.FIELD} is set ({loc[P.FIELD]}); the pre-pin exception is closed and signals take the normal "
                       "InTr gate: the pinned genesis and authenticated head (intr_transport_carrier.observe through "
                       "org_ledger_location.designated_org_ledger, #433)",
                       retry=carrier.RETRY_ENTRYPOINT, next_attempt=carrier.NEXT_ATTEMPT)
    if not isinstance(signal, Mapping) or signal.get("signal_class") != SIGNAL_CLASS \
            or set(signal) != SIGNAL_KEYS or signal != genesis_signal(signal.get("genesis_receipt_sha256"), contract):
        got = signal.get("signal_class") if isinstance(signal, Mapping) else type(signal).__name__
        return _refuse("PRE_PIN_SIGNAL_CLASS_NOT_ACCEPTED", "PRE_PIN_SIGNAL_IS_THE_GENESIS_PIN_TRIGGER",
                       f"while {P.FIELD} is null only one signal is received here: {SIGNAL_CLASS} "
                       f"({SIGNAL_SCHEMA}, exact keys {sorted(SIGNAL_KEYS)}) for {contract['repository']}; got "
                       f"{got!r}. Other signals wait for the pin and then take the normal gates",
                       next_attempt="after REPOSITORY_LEDGER_GENESIS_PIN is admitted, through the normal gates "
                                    "(#433); event-triggered, never on a timer")
    # The planner's own chain-to-sealed-genesis verification, never the pin.
    # LC-KV-19: the read-back must carry a published head signer's attestation (cited with the carrier).
    cited = intr_carrier if isinstance(intr_carrier, Mapping) else {}
    planned = P.plan(org_ledger=org_ledger, genesis_receipt_sha256=signal["genesis_receipt_sha256"],
                     contract_bytes=before, org_ledger_head_attestation=cited.get("org_ledger_head_attestation"))
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
    refused = failure and ("ORG_LEDGER_CHAIN_UNREAD", failure) or carrier.verify(
        signal, destination_receipt_sha256=cited.get("destination_receipt_sha256"),
        org_ledger_head_receipt_sha256=cited.get("org_ledger_head_receipt_sha256"),
        org_chain=chain, retained_source=retained)
    if refused:
        return _refuse(carrier.FAILURE_CODE, carrier.PREDICATE, f"{refused[0]}: {refused[1]}. {carrier.REPAIR}",
                       carrier_reason=refused[0])
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
    return {"schema": RESULT_SCHEMA, "disposition": ACCEPTED, "signal_class": SIGNAL_CLASS,
            "pre_pin_exception": True, "carried_by": carried_by, "genesis_pin_plan": planned,
            "ledger_written": False, "contract_written": False, "authority_effect": "NONE_PLAN_ONLY"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("receive")
    p.add_argument("--signal", required=True)
    p.add_argument("--carrier", required=True)
    p.add_argument("--org-ledger")
    p.add_argument("--out")
    a = ap.parse_args(argv)
    result = receive(json.loads(Path(a.signal).read_text()), intr_carrier=json.loads(Path(a.carrier).read_text()),
                     org_ledger=a.org_ledger)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    sys.stdout.write(text)
    return 0 if result["disposition"] == ACCEPTED else 3


if __name__ == "__main__":
    raise SystemExit(main())
