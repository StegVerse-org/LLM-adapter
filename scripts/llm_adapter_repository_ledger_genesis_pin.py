#!/usr/bin/env python3
"""REPOSITORY_LEDGER_GENESIS_PIN: precompute repository_ledger_location.expected_genesis_receipt_sha256, read it back.

Byte-deterministic genesis (Coordination, StegVerse-org/.github#167 comment 6372442705 item 6). The genesis receipt
takes ``observed_at`` from its own ``hb_reference`` (``SUPPLIED_HB_EPOCH:<epoch>``, the StegVerse-Labs/.github#3263
rule, now in this repository's emit.py), so the same inputs at the same supplied epoch give the same bytes. An
absent epoch is refused before anything is computed (``HB_EPOCH_NOT_SUPPLIED``; a clock-derived or malformed one is
``HB_EPOCH_INVALID``; predicate ``SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH``; StegVerse-Labs/.github#3290 and the
shared supplied-epoch rule below). ``precompute`` therefore gives ``expected_genesis_receipt_sha256`` in advance:

    sha256(canon(receipt_body(transition_id, REPOSITORY_LEDGER_INITIALIZATION, predecessor_state_sha256,
                              successor_state_sha256, evidence, authority_effect, hb_reference(epoch), None)))

with ``canon`` = json.dumps(sort_keys, separators (",", ":"), ensure_ascii False) and ``hb_reference(epoch)`` the
supplied-epoch reference built from .stegverse/heartbeat-awareness.json, exactly as emit.py builds them (a test
proves the bytes equal emit.append's). ``plan`` below is then only the read-back check: it requires the observed
genesis to be supplied-epoch and byte-deterministic, and to equal a precomputed pin (else
EXPECTED_GENESIS_PIN_CONFLICT); while no pin is set it still plans the write from the read-back.

A manifest state transition, not a hand step. Its trigger is the receipted
REPOSITORY_LEDGER_INITIALIZATION genesis on the org ledger at the contract's location (the organization's own
append; StegVerse-org/LLM-adapter#431). `plan` is a pure planner and verifier over a local read-only copy of that
ledger ref. It:

  1. reads the namespace chain from <namespace>/HEAD.json back to its root, and requires every receipt to be sealed;
  2. requires the root to be this repository's REPOSITORY_LEDGER_INITIALIZATION genesis
     (stegverse.repo-transition-receipt/v1, previous_receipt_sha256 null), and, when the triggering record
     names a genesis receipt, requires that receipt to be the root;
  3. authenticates that read-back (LC-KV-19): the genesis, the namespace head and the namespace tree oid at the
     published ref must carry a stegverse.org-ledger-head-attestation/v1 signed by a key published in
     .stegverse/node-ledger/org-ledger-head-signers.v1.json (ORG-LEDGER-HEAD-SIGNER-001, TV/TVC custody; checked by
     llm_adapter.org_ledger_location, a byte copy of #432's module). A caller-built ledger copy that carries its own
     genesis (and its own InTr pair) is therefore never accepted. No attester is published yet, so every plan is
     six-field FAIL_CLOSED MERGE_APPEND_PATH_NOT_ADMITTED until the append route is admitted;
  4. returns the exact contract.json write (bytes, before and after sha256) setting the field to the genesis
     receipt_sha256, plus the consumes receipt: the emit.append arguments of a REPOSITORY_LEDGER_GENESIS_PIN
     repository receipt whose evidence consumes the genesis receipt by its sha256.

It is idempotent: a contract already pinned to the observed genesis plans no write and no receipt, and a contract
pinned to a different value is refused. Every refusal is FAIL_CLOSED with the six fields. Nothing is written,
appended or dispatched here: emit.py appends the consumes receipt only when the admitted transition runs. There is no clock, network, credential or new dependency: stdlib plus local `git`, through the #431 reader; the
signature check is the stdlib Ed25519 verifier (llm_adapter.ed25519_verify, byte copy) and holds no key.
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
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from llm_adapter import org_ledger_location as org_location  # noqa: E402  (byte copy of #432's; LC-KV-19)
from llm_adapter import supplied_epoch  # noqa: E402  (the shared supplied-epoch rule, byte copy)

ROOT = M.ROOT
CONTRACT_PATH = M.CONTRACT_PATH
CONTRACT_REL = ".stegverse/transition-ledger/contract.json"
#: The repo-relative contracts this transition may target (Lane D finding 5): this repository's only. Nothing outside
#: this list is ever read or planned.
CONTRACT_PATHS = (CONTRACT_REL,)
#: Withdrawn targets: continuity-vault-kit#263 @20451a0c's KV and SKAP Vault ledger contracts put those endpoints'
#: ledgers on refs/stegverse/organization-ledger. No endpoint (KV, SKAP Vault, node or gateway, externally or
#: ecosystem maintained) is a GitHub Organization member or a source of org-ledger records (Rigel, relayed on
#: StegVerse-org/.github#160 comment 6372871021), and cvk#263 @706877b6 moved both to STEGVERSE_KV's own recorded
#: receipt chains (_StegVerse/Receipts, _Vault/SKAP/Receipts; KV_RECEIPT_CHAIN_DESIGNATED_ON_ORG_LEDGER there).
#: Naming one here is six-field FAIL_CLOSED ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE; nothing is read or planned.
ENDPOINT_CONTRACT_PATHS = (".stegverse/receipt-ledgers/01_KV_Ledger.contract.json",
                           ".stegverse/receipt-ledgers/02_SKAP_Vault_Ledger.contract.json")
ENDPOINT_REPOSITORY_PREFIXES = ("_StegVerse-org/", "STEGVERSE_KV", "_StegVerse/", "_Vault/")
ENDPOINT_NOT_ORG_SOURCE = "ENDPOINT_NOT_AN_ORG_LEDGER_SOURCE"
ENDPOINT_NOT_ORG_SOURCE_PREDICATE = "NO_ENDPOINT_IS_AN_ORG_MEMBER_OR_A_SOURCE_OF_ORG_LEDGER_RECORDS"
CONTRACT_SCHEMA = "stegverse.repo-transition-ledger-contract/v1"
ORG_LEDGER_REPOSITORY, ORG_LEDGER_REF = "StegVerse-org/.github", "refs/stegverse/organization-ledger"
TRANSITION_CLASS = "REPOSITORY_LEDGER_GENESIS_PIN"
GENESIS_CLASS = "REPOSITORY_LEDGER_INITIALIZATION"
RECEIPT_SCHEMA = "stegverse.repo-transition-receipt/v1"
RESULT_SCHEMA = "stegverse.repository-ledger-genesis-pin-plan/v1"
EVIDENCE_SCHEMA = "stegverse.repository-ledger-genesis-pin-evidence/v1"
FIELD = "expected_genesis_receipt_sha256"
FIELD_POINTER = "/repository_ledger_location/" + FIELD
ALLOW, FAIL_CLOSED = M.ALLOW, M.FAIL_CLOSED
PRECOMPUTE_SCHEMA = "stegverse.repository-ledger-expected-genesis/v1"
AWARENESS_PATH = ROOT / ".stegverse/heartbeat-awareness.json"
EPOCH_PREDICATE = supplied_epoch.EPOCH_PREDICATE
SUPPLIED_EPOCH_FAILURE_SHA256 = supplied_epoch.SUPPLIED_EPOCH_FAILURE_SHA256
supplied_epoch_failure = supplied_epoch.supplied_epoch_failure
observed_at_from_hb_reference = supplied_epoch.observed_at_from_hb_reference
ORDERING = "OSCILLATOR_HEARTBEAT_EPOCH_ONLY"
PRECOMPUTE_ENTRYPOINT = ("scripts/llm_adapter_repository_ledger_genesis_pin.py precompute --hb-epoch <supplied epoch> "
                         "--predecessor-state-sha256 <sha256> --successor-state-sha256 <sha256> "
                         "--evidence-json <json>")
EPOCH_NEXT = ("supply the epoch the genesis append carries (ASCII digits, >= 32, derived_from_clock false) and run "
              "again; nothing was computed or written")
#: the external dependency this alignment records rather than guesses (StegVerse-org/.github#196, InTr consumers
#: lane, session 03dd): the org kernel's hb_reference keeps a clock fallback until #196 lands.
HB_REFERENCE_DEPENDENCY = "StegVerse-org/.github#196 (kernel hb_reference has no clock fallback; draft, not landed)"
SIX_FIELDS = M.SIX_FIELDS
GOAL = "StegVerse-org/LLM-adapter#431 (organization-ledger onboarding; governed element), StegVerse-org/.github#162"
ENTRYPOINT = ("scripts/llm_adapter_repository_ledger_genesis_pin.py plan --org-ledger <read-only copy of "
              "refs/stegverse/organization-ledger> --genesis-receipt <sha256 named by the receipted genesis record> "
              "--head-attestation <stegverse.org-ledger-head-attestation/v1 json>")
HEAD_PREDICATE = "ORG_LEDGER_HEAD_AUTHENTICATED_BY_APPEND_ROUTE"
HEAD_REPAIR = ("the genesis may be authenticated only from the published refs/stegverse/organization-ledger read-back "
               "plus an org-ledger head attestation: a stegverse.org-ledger-head-attestation/v1 over {org_ledger_location, "
               "genesis_receipt_sha256, head_receipt_sha256, namespace_tree_oid, appended_through} signed by a key "
               "published in .stegverse/node-ledger/org-ledger-head-signers.v1.json (ORG-LEDGER-HEAD-SIGNER-001; TV/TVC "
               "custody, StegVerse-org/TVC#542; publication only by an admitted change carrying TV/TVC's publication "
               "receipt). A caller-built ledger copy with its own genesis is never accepted")
HEAD_NEXT = ("event-triggered: when ORG-LEDGER-HEAD-SIGNER-001 is published by its admitted change and the append "
             "route attests the head that holds the receipted genesis; no clock, no polling, no person")
NEXT = ("event-triggered: re-run when the receipted REPOSITORY_LEDGER_INITIALIZATION genesis record is on the org "
        "ledger at the contract's location; no clock, no polling, no person")
PINNED_NOTE = ("Pinned by REPOSITORY_LEDGER_GENESIS_PIN from the receipted REPOSITORY_LEDGER_INITIALIZATION genesis "
               "read back from {location} at organization-ledger tip {tip}; the transition's consumes receipt cites it.")


def supplied_hb_reference(epoch: int) -> dict[str, Any]:
    """emit.py's hb_reference(epoch) for a supplied epoch, from the declared heartbeat. Reads a file, never a clock."""
    p = json.loads(AWARENESS_PATH.read_text(encoding="utf-8"))["heartbeat"]
    if p.get("progression_dependency") != "OSCILLATOR_ONLY":
        raise ValueError("heartbeat progression must be OSCILLATOR_ONLY")
    if epoch < int(p["anchor_epoch"]):
        raise ValueError(f"epoch must be an integer of at least the anchor {p['anchor_epoch']}")
    return {"epoch": epoch, "heartbeat_id": f"HB:{epoch}", "frequency_hz": p["rate_hz"],
            "period_ms": int(p["period_ms"]), "progression_dependency": "OSCILLATOR_ONLY",
            "derived_from_clock": False, "authority_effect": "NONE"}


def genesis_receipt_body(repository: str, *, transition_id: str, predecessor_state_sha256: str,
                         successor_state_sha256: str, evidence: Mapping[str, Any], authority_effect: str,
                         hb: Mapping[str, Any]) -> dict[str, Any]:
    """emit.py receipt_body for the genesis (previous_receipt_sha256 null). Pure."""
    return {"schema": RECEIPT_SCHEMA, "repository": repository, "transition_id": transition_id,
            "transition_class": GENESIS_CLASS, "predecessor_state_sha256": predecessor_state_sha256,
            "successor_state_sha256": successor_state_sha256, "evidence": dict(evidence),
            "authority_effect": authority_effect, "hb_reference": dict(hb), "ordering": ORDERING,
            "observed_at": observed_at_from_hb_reference(hb), "observed_at_is_descriptive_not_ordering": True,
            "previous_receipt_sha256": None}


def _precompute_refuse(code: str, predicate: str, repair: str, **extra: Any) -> dict[str, Any]:
    return {"schema": PRECOMPUTE_SCHEMA, "disposition": FAIL_CLOSED, "failure_code": code,
            "failed_predicate": predicate, "required_evidence_or_repair": repair,
            "retry_entrypoint": PRECOMPUTE_ENTRYPOINT, "owning_existing_goal": GOAL, "next_attempt": EPOCH_NEXT,
            "expected_genesis_receipt_sha256": None, **extra, "ledger_written": False, "contract_written": False,
            "authority_effect": "NONE_PLAN_ONLY"}


def expected_genesis(*, hb_epoch: Any, predecessor_state_sha256: Any, successor_state_sha256: Any,
                     evidence: Any, transition_id: str | None = None, authority_effect: str = "NONE",
                     repository: str | None = None) -> dict[str, Any]:
    """The genesis receipt and its receipt_sha256, computed before it is appended, or six-field FAIL_CLOSED. Pure
    apart from reading the declared heartbeat parameters. Nothing is written."""
    failure = supplied_epoch_failure(hb_epoch)
    if failure:
        return _precompute_refuse(failure[0], EPOCH_PREDICATE, f"{failure[1]}: the genesis is byte-deterministic "
                                  "only at a supplied epoch, so none is precomputed without one")
    repo = repository or json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["repository"]
    problems = [name for name, v in (("predecessor_state_sha256", predecessor_state_sha256),
                                     ("successor_state_sha256", successor_state_sha256))
                if not (isinstance(v, str) and v.startswith("sha256:") and len(v) == 71)]
    if not isinstance(evidence, Mapping):
        problems.append("evidence")
    if problems:
        return _precompute_refuse("REPOSITORY_LEDGER_GENESIS_MISMATCH",
                                  "REPOSITORY_LEDGER_GENESIS_IS_THIS_REPOSITORYS_INITIALIZATION",
                                  f"supply {', '.join(problems)} as the genesis append carries them "
                                  "(sha256:<64 hex> digests and an evidence object)")
    hb = supplied_hb_reference(int(str(hb_epoch)))
    body = genesis_receipt_body(repo, transition_id=transition_id or f"{GENESIS_CLASS}:{repo}",
                                predecessor_state_sha256=predecessor_state_sha256,
                                successor_state_sha256=successor_state_sha256, evidence=evidence,
                                authority_effect=authority_effect, hb=hb)
    digest = M.sha(body)
    return {"schema": PRECOMPUTE_SCHEMA, "disposition": ALLOW, "repository": repo,
            "expected_genesis_receipt_sha256": digest, "genesis_receipt": {**body, "receipt_sha256": digest},
            "computation": "sha256(canon(receipt_body(..., hb_reference(supplied epoch), previous null))); "
                           "observed_at = SUPPLIED_HB_EPOCH:<epoch> (StegVerse-Labs/.github#3263)",
            "read_back_check": ENTRYPOINT, "ledger_written": False, "contract_written": False,
            "authority_effect": "NONE_PLAN_ONLY"}


def genesis_determinism_failure(genesis: Mapping[str, Any]) -> tuple[str, str] | None:
    """Why an observed genesis is not a supplied-epoch, byte-deterministic receipt, or None. Pure."""
    hb = genesis.get("hb_reference")
    failure = supplied_epoch_failure(hb.get("epoch") if isinstance(hb, dict) else None, hb)
    if failure:
        return failure
    if genesis.get("observed_at") != observed_at_from_hb_reference(hb):
        return "HB_EPOCH_INVALID", (f"observed_at {genesis.get('observed_at')!r} is not "
                                    f"{observed_at_from_hb_reference(hb)!r}; a clock-stamped genesis is not "
                                    "byte-deterministic")
    return None


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


def namespace_tree_oid(git_dir: str, tip: str, namespace: str) -> str:
    """The namespace's tree oid at `tip` of the ledger copy ('' when absent). Read-only, local objects only."""
    raw = M._git(git_dir, "rev-parse", "--verify", "--quiet", f"{tip}:{namespace}")
    return raw.decode().strip() if raw else ""


def contract_path_failure(contract_path: Any) -> str | None:
    """Why `contract_path` is not an allowlisted repo-relative contract path, or None. Pure."""
    if not isinstance(contract_path, str) or not contract_path:
        return "the contract path is not a non-empty string"
    parts = contract_path.split("/")
    if contract_path.startswith("/") or "\\" in contract_path or ":" in contract_path or ".." in parts \
            or "." in parts or "" in parts:
        return f"{contract_path!r} is not a plain repo-relative path (absolute, traversal, empty or drive segment)"
    if contract_path not in CONTRACT_PATHS:
        return f"{contract_path!r} is not on the allowlist {list(CONTRACT_PATHS)}"
    return None


def endpoint_contract_failure(contract_path: Any, contract: Any = None) -> str | None:
    """Why the target is an endpoint's ledger on the org ledger (never planned), or None. Pure."""
    if contract_path in ENDPOINT_CONTRACT_PATHS:
        return (f"{contract_path} designates an endpoint's ledger on {ORG_LEDGER_REF} (continuity-vault-kit#263 "
                "@20451a0c, superseded at @706877b6 by STEGVERSE_KV's own recorded receipt chains)")
    repository = contract.get("repository") if isinstance(contract, Mapping) else None
    if isinstance(repository, str) and repository.startswith(ENDPOINT_REPOSITORY_PREFIXES):
        return f"the contract names endpoint {repository!r}, whose ledger is never on {ORG_LEDGER_REF}"
    return None


def endpoint_contract_refusal(why: str, refuse: Any) -> dict[str, Any]:
    return refuse(ENDPOINT_NOT_ORG_SOURCE, ENDPOINT_NOT_ORG_SOURCE_PREDICATE,
                  f"{why}. No endpoint (KV, SKAP Vault, node or gateway, externally or ecosystem maintained) is a "
                  "GitHub Organization member or a source of org-ledger records (StegVerse-org/.github#160 comment "
                  "6372871021): its genesis is pinned on its own recorded receipt chain, and its data crosses only "
                  "through InTr, recorded at both ends (the Org side a digest-only crossing receipt). Name "
                  f"{CONTRACT_REL}")


def contract_shape_failure(contract: Any) -> str | None:
    """Why `contract` does not have the #431 repository_ledger_location shape, or None. Pure."""
    if not isinstance(contract, Mapping) or contract.get("schema") != CONTRACT_SCHEMA \
            or not isinstance(contract.get("repository"), str):
        return f"not a {CONTRACT_SCHEMA} contract naming its repository"
    loc = contract.get("repository_ledger_location")
    if not isinstance(loc, Mapping) or loc.get("repository") != ORG_LEDGER_REPOSITORY \
            or loc.get("ref") != ORG_LEDGER_REF or loc.get("namespace") != "repository-ledger/" + contract["repository"] \
            or FIELD not in loc:
        return (f"repository_ledger_location must designate {ORG_LEDGER_REPOSITORY} {ORG_LEDGER_REF} "
                f"repository-ledger/<repository> and carry {FIELD} (the #431 shape)")
    return None


def head_attestation_failure(attestation: Any, ledger_location: str, genesis_sha: str, head_sha: str,
                             tree_oid: str) -> tuple[str, str] | None:
    """LC-KV-19 head check for the contract's location. For this repository's location it is #432's
    org_ledger_location.head_attestation_failure itself; for an allowlisted cvk location it is the same check over
    the same published signers, message and verifier, with only org_ledger_location naming that location. Pure."""
    if ledger_location == org_location.ORG_LEDGER_LOCATION:
        return org_location.head_attestation_failure(attestation, genesis_sha, head_sha, tree_oid)
    signers = org_location.load_head_signers()
    if not signers:
        return org_location.head_attestation_failure(attestation, genesis_sha, head_sha, tree_oid)
    if not isinstance(attestation, Mapping):
        return "ORG_LEDGER_HEAD_NOT_AUTHENTICATED", "no stegverse.org-ledger-head-attestation/v1 for this head"
    body = {k: attestation.get(k) for k in org_location.HEAD_ATTESTATION_FIELDS}
    want = {**org_location.head_attestation_body(genesis_sha, head_sha, tree_oid), "org_ledger_location": ledger_location}
    if body != want:
        return ("ORG_LEDGER_HEAD_NOT_AUTHENTICATED", "the attestation names another location, genesis, head or "
                f"namespace tree than the store holds (head {head_sha}, tree {tree_oid})")
    key = next((k for k in signers if k.get("key_id") == attestation.get("key_id")), None)
    public = org_location._b64(key.get("public_key_b64")) if key else None
    signature = org_location._b64(attestation.get("signature_b64"))
    if key is None or public is None or len(public) != 32 or signature is None or len(signature) != 64 \
            or not org_location.ed25519_verify.verify(public, org_location.head_attestation_message(body), signature):
        return "ORG_LEDGER_HEAD_NOT_AUTHENTICATED", "the attestation is not by a published key or does not verify"
    return None


def read_contract(contract_path: str = CONTRACT_REL, checkout: Any = None) -> bytes:
    """The allowlisted contract's bytes from `checkout` (default: this repository). Raises on a refused path."""
    failure = contract_path_failure(contract_path)
    if failure:
        raise ValueError(failure)
    return (Path(checkout) if checkout is not None else ROOT).joinpath(*contract_path.split("/")).read_bytes()


def plan(*, org_ledger: str | None, genesis_receipt_sha256: str | None = None,
         contract_bytes: bytes | None = None, org_ledger_head_attestation: Any = None,
         contract_path: str = CONTRACT_REL, checkout: Any = None) -> dict[str, Any]:
    """The exact contract write and consumes receipt for REPOSITORY_LEDGER_GENESIS_PIN, or six-field FAIL_CLOSED."""
    endpoint = endpoint_contract_failure(contract_path)
    if endpoint:
        return {**endpoint_contract_refusal(endpoint, _refuse), "contract_path": repr(contract_path)}
    bad_path = contract_path_failure(contract_path)
    if bad_path:
        return _refuse("CONTRACT_PATH_NOT_ALLOWLISTED", "CONTRACT_PATH_IS_AN_ALLOWLISTED_REPO_RELATIVE_431_CONTRACT",
                       f"name one of {list(CONTRACT_PATHS)} ({bad_path})", contract_path=repr(contract_path))
    try:
        before = contract_bytes if contract_bytes is not None else read_contract(contract_path, checkout)
        contract = json.loads(before)
    except (OSError, ValueError) as exc:
        contract, before = None, b""
        unreadable = type(exc).__name__
    endpoint = endpoint_contract_failure(contract_path, contract)
    if endpoint:
        return endpoint_contract_refusal(endpoint, _refuse)
    bad_shape = contract_shape_failure(contract) if contract is not None else f"unreadable ({unreadable})"
    if bad_shape:
        return _refuse("CONTRACT_NOT_431_SHAPE", "CONTRACT_HAS_THE_431_REPOSITORY_LEDGER_LOCATION_SHAPE",
                       f"{contract_path}: {bad_shape}", contract_path=contract_path)
    repo, loc = contract["repository"], contract["repository_ledger_location"]
    location = f"{loc['repository']}#{loc['ref']}:{loc['namespace']}"
    genesis, obs, failure = read_genesis(org_ledger, loc["namespace"])
    common = {"repository": repo, "ledger_location": location, "observation": obs, "contract_path": contract_path}
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
    undetermined = genesis_determinism_failure(genesis)
    if undetermined:
        return _refuse(undetermined[0], EPOCH_PREDICATE, f"the chain root {digest}: {undetermined[1]}. The genesis "
                       "must carry a supplied hb_epoch (derived_from_clock false) and observed_at "
                       "SUPPLIED_HB_EPOCH:<epoch>, so its digest is the precomputed one", **common,
                       observed_genesis_receipt_sha256=digest)
    if genesis_receipt_sha256 is not None and genesis_receipt_sha256 != digest:
        return _refuse("REPOSITORY_LEDGER_GENESIS_NOT_ON_CHAIN", "REPOSITORY_LEDGER_GENESIS_ON_SEALED_CHAIN",
                       f"the triggering record names {genesis_receipt_sha256!r}, but the chain from "
                       f"{loc['namespace']}/HEAD.json is rooted at {digest}", **common)
    # LC-KV-19: the read-back decides nothing by itself. Its genesis, head and namespace tree must be attested by
    # a published org-ledger head signer, or a caller-built copy could carry its own genesis and InTr pair.
    tree_oid = namespace_tree_oid(org_ledger, obs["tip"], loc["namespace"])
    unauthenticated = head_attestation_failure(org_ledger_head_attestation, f"{loc['ref']}:{loc['namespace']}",
                                               digest, obs["namespace_head"], tree_oid)
    if unauthenticated:
        return _refuse(unauthenticated[0], HEAD_PREDICATE,
                       f"{unauthenticated[1]}. {HEAD_REPAIR}", **common, observed_genesis_receipt_sha256=digest,
                       namespace_tree_oid=tree_oid, next_attempt=HEAD_NEXT)
    current = loc.get(FIELD)
    if current is not None and current != digest:
        return _refuse("EXPECTED_GENESIS_PIN_CONFLICT", "EXPECTED_GENESIS_PIN_UNSET_OR_EQUAL",
                       f"{contract_path} {FIELD_POINTER} is {current!r}, not the observed genesis {digest}; the "
                       "read-back does not match the pin (precomputed or earlier), and a pin is never overwritten by "
                       "this transition, so the conflict needs its own admitted change",
                       **common, observed_genesis_receipt_sha256=digest)
    result = {"schema": RESULT_SCHEMA, "transition_class": TRANSITION_CLASS, "disposition": ALLOW, **common,
              "genesis_receipt_sha256": digest, "already_pinned": current == digest,
              "read_back_check": "MATCHES_PIN" if current == digest else "PIN_UNSET_PLANNED_FROM_READ_BACK",
              "org_ledger_head_authenticated": True, "namespace_tree_oid": tree_oid,
              "contract_write": None, "consumes_receipt": None,
              "ledger_written": False, "contract_written": False, "authority_effect": "NONE_PLAN_ONLY"}
    if current == digest:
        return result      # read-back check only: the pin (precomputed or earlier) equals the observed genesis
    after_contract = json.loads(before)
    after_contract["repository_ledger_location"][FIELD] = digest
    after_contract["repository_ledger_location"]["expected_genesis_note"] = PINNED_NOTE.format(
        location=location, tip=obs["tip"])
    after = (json.dumps(after_contract, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    result["contract_write"] = {"path": contract_path, "json_pointer": FIELD_POINTER, "value": digest,
                                "before_sha256": _sha_bytes(before), "after_sha256": _sha_bytes(after),
                                "after_text": after.decode("utf-8")}
    epoch = int(str(genesis["hb_reference"]["epoch"]))      # supplied: checked by genesis_determinism_failure above
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
                         "namespace_tree_oid": tree_oid,
                         "org_ledger_head_attestation_key_id": org_ledger_head_attestation.get("key_id"),
                         "contract_path": contract_path, "json_pointer": FIELD_POINTER, "value": digest},
            "authority_effect": "NONE",
            # the genesis's own supplied epoch orders the pin after it
            "hb_epoch": epoch},
        "appended_by": ".stegverse/transition-ledger/emit.py append, when the admitted transition runs"}
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
    p.add_argument("--head-attestation", help="stegverse.org-ledger-head-attestation/v1 json file")
    p.add_argument("--contract-path", default=CONTRACT_REL, choices=CONTRACT_PATHS,
                   help="allowlisted repo-relative contract (default: this repository's)")
    p.add_argument("--checkout", help="checkout holding --contract-path (default: this repository)")
    p.add_argument("--out")
    c = sub.add_parser("precompute", help="expected_genesis_receipt_sha256 from the supplied genesis inputs")
    c.add_argument("--hb-epoch", type=str, default=None)
    c.add_argument("--predecessor-state-sha256", required=True)
    c.add_argument("--successor-state-sha256", required=True)
    c.add_argument("--evidence-json", default="{}")
    c.add_argument("--transition-id")
    c.add_argument("--authority-effect", default="NONE")
    c.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "precompute":
        result = expected_genesis(hb_epoch=a.hb_epoch, predecessor_state_sha256=a.predecessor_state_sha256,
                                  successor_state_sha256=a.successor_state_sha256,
                                  evidence=json.loads(a.evidence_json), transition_id=a.transition_id,
                                  authority_effect=a.authority_effect)
        text = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if a.out:
            Path(a.out).write_text(text)
        sys.stdout.write(text)
        return 0 if result["disposition"] == ALLOW else 3
    attestation = json.loads(Path(a.head_attestation).read_text()) if a.head_attestation else None
    result = plan(org_ledger=a.org_ledger, genesis_receipt_sha256=a.genesis_receipt,
                  org_ledger_head_attestation=attestation, contract_path=a.contract_path, checkout=a.checkout)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    sys.stdout.write(text)
    return 0 if result["disposition"] == ALLOW else 3


if __name__ == "__main__":
    raise SystemExit(main())
