#!/usr/bin/env python3
"""REPOSITORY_LEDGER_GENESIS_PIN: pin repository_ledger_location.expected_genesis_receipt_sha256 after genesis.

A manifest state transition, not a hand step. Its trigger is the receipted
REPOSITORY_LEDGER_INITIALIZATION genesis on the org ledger at the contract's location (the organization's own
append; StegVerse-org/LLM-adapter#431). `plan` is a pure planner and verifier over a local read-only copy of that
ledger ref. It:

  1. reads the namespace chain from <namespace>/HEAD.json back to its root, and requires every receipt to be sealed;
  2. requires the root to be this repository's REPOSITORY_LEDGER_INITIALIZATION genesis
     (stegverse.repo-transition-receipt/v1, previous_receipt_sha256 null), and, when the triggering record
     names a genesis receipt, requires that receipt to be the root;
  3. returns the exact contract.json write (bytes, before and after sha256) setting the field to the genesis
     receipt_sha256, plus the consumes receipt: the emit.append arguments of a REPOSITORY_LEDGER_GENESIS_PIN
     repository receipt whose evidence consumes the genesis receipt by its sha256.

It is idempotent: a contract already pinned to the observed genesis plans no write and no receipt, and a contract
pinned to a different value is refused. Every refusal is FAIL_CLOSED with the six fields. Nothing is written,
appended or dispatched here: emit.py is unchanged and appends the consumes receipt only when the admitted transition
runs. There is no clock, network, credential or new dependency: stdlib plus local `git`, through the #431 reader.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm_adapter_ledger_merge_transfer as M  # noqa: E402  (#431's reader: sha, sealed, _git, read_org_ledger)

ROOT = M.ROOT
CONTRACT_PATH = M.CONTRACT_PATH
CONTRACT_REL = ".stegverse/transition-ledger/contract.json"
TRANSITION_CLASS = "REPOSITORY_LEDGER_GENESIS_PIN"
GENESIS_CLASS = "REPOSITORY_LEDGER_INITIALIZATION"
RECEIPT_SCHEMA = "stegverse.repo-transition-receipt/v1"
RESULT_SCHEMA = "stegverse.repository-ledger-genesis-pin-plan/v1"
EVIDENCE_SCHEMA = "stegverse.repository-ledger-genesis-pin-evidence/v1"
FIELD = "expected_genesis_receipt_sha256"
FIELD_POINTER = "/repository_ledger_location/" + FIELD
ALLOW, FAIL_CLOSED = M.ALLOW, M.FAIL_CLOSED
SIX_FIELDS = M.SIX_FIELDS
GOAL = "StegVerse-org/LLM-adapter#431 (organization-ledger onboarding; governed element), StegVerse-org/.github#162"
ENTRYPOINT = ("scripts/llm_adapter_repository_ledger_genesis_pin.py plan --org-ledger <read-only copy of "
              "refs/stegverse/organization-ledger> --genesis-receipt <sha256 named by the receipted genesis record>")
NEXT = ("event-triggered: re-run when the receipted REPOSITORY_LEDGER_INITIALIZATION genesis record is on the org "
        "ledger at the contract's location; no clock, no polling, no person")
PINNED_NOTE = ("Pinned by REPOSITORY_LEDGER_GENESIS_PIN from the receipted REPOSITORY_LEDGER_INITIALIZATION genesis "
               "read back from {location} at organization-ledger tip {tip}; the transition's consumes receipt cites it.")


def _sha_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _refuse(code: str, predicate: str, repair: str, **extra: Any) -> dict[str, Any]:
    return {"schema": RESULT_SCHEMA, "transition_class": TRANSITION_CLASS, "disposition": FAIL_CLOSED,
            "failure_code": code, "failed_predicate": predicate, "required_evidence_or_repair": repair,
            "retry_entrypoint": ENTRYPOINT, "owning_existing_goal": GOAL, "next_attempt": NEXT,
            "contract_write": None, "consumes_receipt": None, **extra,
            "ledger_written": False, "contract_written": False, "authority_effect": "NONE_PLAN_ONLY"}


def read_genesis(git_dir: str | None, namespace: str) -> tuple[dict[str, Any] | None, dict[str, Any], str | None]:
    """(root receipt, observation, failure detail) for the namespace chain on the ledger copy. Read-only."""
    chain, obs, failure = read_chain(git_dir, namespace)
    return (chain[-1] if chain and not failure else None), obs, failure


def ledger_file(git_dir: str, tip: str, path: str) -> Any:
    """One JSON file at `tip` of the ledger copy, or None. Read-only."""
    raw = M._git(git_dir, "show", f"{tip}:{path}")
    try:
        return json.loads(raw) if raw is not None else None
    except ValueError:
        return None


def read_chain(git_dir: str | None, namespace: str) -> tuple[list[dict[str, Any]], dict[str, Any], str | None]:
    """(sealed chain newest first, observation, failure detail) from <namespace>/HEAD.json to its root. Read-only."""
    obs: dict[str, Any] = {"tip": None, "namespace": namespace, "namespace_head": None, "chain_length": 0}
    chain: list[dict[str, Any]] = []
    if not git_dir:
        return chain, obs, "no copy"
    tip = M._git(git_dir, "rev-parse", "--verify", M.LEDGER_REF + "^{commit}")
    if tip is None:
        return chain, obs, "no copy"
    obs["tip"] = tip.decode().strip()
    head = ledger_file(git_dir, obs["tip"], namespace + "/HEAD.json")
    if not isinstance(head, Mapping) or not isinstance(head.get("receipt_sha256"), str):
        return chain, obs, "absent"
    obs["namespace_head"] = head["receipt_sha256"]
    cursor, seen = head["receipt_sha256"], set()
    while isinstance(cursor, str):
        if cursor in seen:
            return chain, obs, f"chain cycles at {cursor}"
        seen.add(cursor)
        r = ledger_file(git_dir, obs["tip"], f"{namespace}/receipts/{cursor.split(':')[-1]}.json")
        if not M.sealed(r) or r.get("receipt_sha256") != cursor:
            return chain, obs, f"receipt {cursor} is absent or does not hash to its receipt_sha256"
        obs["chain_length"] += 1
        chain.append(r)
        cursor = r.get("previous_receipt_sha256")
    if cursor is not None or not chain:
        return chain, obs, "the chain does not end at previous_receipt_sha256 null"
    return chain, obs, None


def plan(*, org_ledger: str | None, genesis_receipt_sha256: str | None = None,
         contract_bytes: bytes | None = None) -> dict[str, Any]:
    """The exact contract write and consumes receipt for REPOSITORY_LEDGER_GENESIS_PIN, or six-field FAIL_CLOSED."""
    before = contract_bytes if contract_bytes is not None else CONTRACT_PATH.read_bytes()
    contract = json.loads(before)
    repo, loc = contract["repository"], contract["repository_ledger_location"]
    location = f"{loc['repository']}#{loc['ref']}:{loc['namespace']}"
    genesis, obs, failure = read_genesis(org_ledger, loc["namespace"])
    common = {"repository": repo, "ledger_location": location, "observation": obs}
    if failure == "no copy":
        return _refuse("ORGANIZATION_LEDGER_COPY_UNAVAILABLE", "ORGANIZATION_LEDGER_COPY_READ",
                       f"a local read-only copy of {loc['repository']} {loc['ref']}", **common)
    if failure == "absent":
        return _refuse("REPOSITORY_LEDGER_GENESIS_UNOBSERVED", "REPOSITORY_LEDGER_GENESIS_RECEIPTED_ON_ORG_LEDGER",
                       f"{loc['namespace']}/HEAD.json on {loc['repository']} {loc['ref']}, naming a sealed chain whose "
                       f"root is this repository's {GENESIS_CLASS} receipt (the organization's own append; #431)",
                       **common)
    if failure:
        return _refuse("REPOSITORY_LEDGER_GENESIS_NOT_ON_CHAIN", "REPOSITORY_LEDGER_GENESIS_ON_SEALED_CHAIN",
                       f"an intact sealed chain from {loc['namespace']}/HEAD.json to its genesis ({failure})", **common)
    wrong = [k for k, want in (("schema", RECEIPT_SCHEMA), ("transition_class", GENESIS_CLASS),
                               ("repository", repo)) if genesis.get(k) != want]
    if wrong:
        return _refuse("REPOSITORY_LEDGER_GENESIS_MISMATCH", "REPOSITORY_LEDGER_GENESIS_IS_THIS_REPOSITORYS_INITIALIZATION",
                       f"the chain root {genesis['receipt_sha256']} must be a {RECEIPT_SCHEMA} {GENESIS_CLASS} receipt "
                       f"for {repo}; it differs in {', '.join(wrong)}", **common)
    digest = genesis["receipt_sha256"]
    if genesis_receipt_sha256 is not None and genesis_receipt_sha256 != digest:
        return _refuse("REPOSITORY_LEDGER_GENESIS_NOT_ON_CHAIN", "REPOSITORY_LEDGER_GENESIS_ON_SEALED_CHAIN",
                       f"the triggering record names {genesis_receipt_sha256!r}, but the chain from "
                       f"{loc['namespace']}/HEAD.json is rooted at {digest}", **common)
    current = loc.get(FIELD)
    if current is not None and current != digest:
        return _refuse("EXPECTED_GENESIS_PIN_CONFLICT", "EXPECTED_GENESIS_PIN_UNSET_OR_EQUAL",
                       f"{CONTRACT_REL} {FIELD_POINTER} is {current!r}, not the observed genesis {digest}; a pin is "
                       "never overwritten by this transition, so the conflict needs its own admitted change",
                       **common, observed_genesis_receipt_sha256=digest)
    result = {"schema": RESULT_SCHEMA, "transition_class": TRANSITION_CLASS, "disposition": ALLOW, **common,
              "genesis_receipt_sha256": digest, "already_pinned": current == digest,
              "contract_write": None, "consumes_receipt": None,
              "ledger_written": False, "contract_written": False, "authority_effect": "NONE_PLAN_ONLY"}
    if current == digest:
        return result      # idempotent: the pin and its consumes receipt already exist
    after_contract = json.loads(before)
    after_contract["repository_ledger_location"][FIELD] = digest
    after_contract["repository_ledger_location"]["expected_genesis_note"] = PINNED_NOTE.format(
        location=location, tip=obs["tip"])
    after = (json.dumps(after_contract, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    result["contract_write"] = {"path": CONTRACT_REL, "json_pointer": FIELD_POINTER, "value": digest,
                                "before_sha256": _sha_bytes(before), "after_sha256": _sha_bytes(after),
                                "after_text": after.decode("utf-8")}
    epoch = (genesis.get("hb_reference") or {}).get("epoch")
    supplied = (genesis.get("hb_reference") or {}).get("derived_from_clock") is False and type(epoch) is int
    result["consumes_receipt"] = {
        "emit_append": {
            "transition_id": f"{TRANSITION_CLASS}:{repo}:{digest.split(':')[1]}",
            "transition_class": TRANSITION_CLASS,
            "predecessor_state_sha256": _sha_bytes(before),
            "successor_state_sha256": _sha_bytes(after),
            "evidence": {"schema": EVIDENCE_SCHEMA, "consumes_receipt_sha256": digest,
                         "consumes": [{"receipt_sha256": digest, "transition_class": GENESIS_CLASS,
                                       "ledger_location": location}],
                         "organization_ledger_tip": obs["tip"],
                         "namespace_head_receipt_sha256": obs["namespace_head"],
                         "contract_path": CONTRACT_REL, "json_pointer": FIELD_POINTER, "value": digest},
            "authority_effect": "NONE",
            # the genesis's own supplied epoch orders the pin after it; None means emit.py would sample a clock,
            # so the admitted run must then supply the epoch of the triggering record
            "hb_epoch": epoch if supplied else None},
        "appended_by": ".stegverse/transition-ledger/emit.py append (unchanged), when the admitted transition runs"}
    return result


def apply_write(planned: Mapping[str, Any], contract_bytes: bytes) -> bytes:
    """The bytes the admitted transition writes, checked against the plan's before digest. Pure."""
    write = planned.get("contract_write")
    if planned.get("disposition") != ALLOW or write is None:
        return contract_bytes
    if _sha_bytes(contract_bytes) != write["before_sha256"]:
        raise ValueError("contract.json changed since the plan; re-plan")
    return write["after_text"].encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--org-ledger", help="local bare copy holding " + M.LEDGER_REF)
    p.add_argument("--genesis-receipt", help="the genesis receipt_sha256 named by the triggering record")
    p.add_argument("--out")
    a = ap.parse_args(argv)
    result = plan(org_ledger=a.org_ledger, genesis_receipt_sha256=a.genesis_receipt)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    sys.stdout.write(text)
    return 0 if result["disposition"] == ALLOW else 3


if __name__ == "__main__":
    raise SystemExit(main())
