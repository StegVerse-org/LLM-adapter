#!/usr/bin/env python3
"""LLM-adapter organization-ledger onboarding: main-merge transfer receipts for StegVerse-org/LLM-adapter.

G-8 DRAFT. Plan only, and FAIL_CLOSED until every prerequisite is observed.

StegVerse-org/.github records each merge on main as ORGANIZATION_MAIN_MERGE_TRANSFER
(.github/workflows/organization-ledger-merge-transfer.yml over
resident-runtime/merge_transfer.py). This repository's chain is designated as the
subtree repository-ledger/StegVerse-org/LLM-adapter of StegVerse-org/.github
refs/stegverse/organization-ledger (.stegverse/transition-ledger/contract.json,
new_ledger_root false), and publishing to that ref is the organization's own
append. There is no LLM-adapter ledger ref, and this draft never creates one.

For each pushed commit, `plan` builds the repository-receipt evidence the pinned
org writer would bind, using commit_facts / facts_failure / merge_evidence / sealed
copied verbatim from merge_transfer.py at the pin in
.stegverse/transition-ledger/merge-transfer-writer-pin.v1.json. It then checks
these predicates in order against a local read-only copy of the org ledger:

  WRITER_PIN_VERIFIED                      the pinned writer checkout matches its sha256 pins
  ORGANIZATION_LEDGER_COPY_READ            a local copy of the org ledger ref was supplied
  ORGANIZATION_HEAD_SUPPLIED_EPOCH         the org head is sealed and carries a supplied epoch (int >= 32, not from a clock)
  REPOSITORY_CHAIN_GENESIS_OBSERVED        <namespace>/HEAD.json points at a sealed receipt on an intact chain
  MERGE_APPEND_PATH_ADMITTED               an admitted publisher exists; never true in this draft

Every result is FAIL_CLOSED with the six fields plus unmet_predicates. Nothing
is written, minted or dispatched. No clock, network, credential or new
dependency: stdlib plus local `git` only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = ROOT / ".stegverse/transition-ledger/merge-transfer-writer-pin.v1.json"
CONTRACT_PATH = ROOT / ".stegverse/transition-ledger/contract.json"
LEDGER_REF = "refs/stegverse/organization-ledger"

OPERATION = "ORGANIZATION_MAIN_MERGE_TRANSFER"
PROFILE_ID = "main-merge-transfer"
EVIDENCE_SCHEMA = "stegverse.main-merge-transfer-evidence/v1"
RESULT_SCHEMA = "stegverse.llm-adapter-merge-transfer-onboarding-plan/v1"
MAIN_REF = "refs/heads/main"
ALLOW, FAIL_CLOSED = "ALLOW", "FAIL_CLOSED"
GOAL = ("StegVerse-org/.github#162 (INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001); "
        "class B item on StegVerse-org/.github#160 owned by Lane B")
ENTRYPOINT = (".github/workflows/llm-adapter-organization-ledger-merge-transfer.yml (push to main) -> "
              "scripts/llm_adapter_ledger_merge_transfer.py plan")
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
SHA40 = re.compile(r"[0-9a-f]{40}")
PR_SUBJECT = re.compile(r"Merge pull request #([0-9]+) from \S+")
COPIED_BLOCKS = ("commit_facts", "facts_failure", "merge_evidence", "sealed")


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


# -- copied verbatim from StegVerse-org/.github resident-runtime/merge_transfer.py at the pin ----------
def commit_facts(commit: str, git_dir: Path | str = ROOT) -> dict[str, Any]:
    """tree, parents and subject of one commit, read from the object itself (git cat-file)."""
    raw = subprocess.run(["git", "-C", str(git_dir), "cat-file", "commit", commit],
                         check=True, capture_output=True, text=True).stdout
    header, _, message = raw.partition("\n\n")
    tree, parents = None, []
    for line in header.splitlines():
        key, _, value = line.partition(" ")
        if key == "tree":
            tree = value
        elif key == "parent":
            parents.append(value)
    full = subprocess.run(["git", "-C", str(git_dir), "rev-parse", "--verify", commit + "^{commit}"],
                          check=True, capture_output=True, text=True).stdout.strip()
    return {"merge_commit": full, "tree": tree, "parents": parents,
            "subject": message.splitlines()[0] if message else ""}


def facts_failure(facts: Any) -> str | None:
    if not isinstance(facts, Mapping):
        return "commit facts are not an object"
    if not isinstance(facts.get("merge_commit"), str) or not SHA40.fullmatch(facts["merge_commit"]):
        return "merge_commit is not 40 lowercase hex"
    if not isinstance(facts.get("tree"), str) or not SHA40.fullmatch(facts["tree"]):
        return "tree is not 40 lowercase hex"
    parents = facts.get("parents")
    if not isinstance(parents, list) or not parents or not all(isinstance(p, str) and SHA40.fullmatch(p) for p in parents):
        return "parents is not a non-empty list of 40 lowercase hex"
    if not isinstance(facts.get("subject"), str):
        return "subject is not text"
    return None


def merge_evidence(repo: str, facts: Mapping[str, Any]) -> dict[str, Any]:
    """The repository receipt's evidence: the merge commit, bound to this repository and main."""
    match = PR_SUBJECT.fullmatch(facts["subject"]) if len(facts["parents"]) == 2 else None
    core = {"schema": EVIDENCE_SCHEMA, "repository": repo, "ref": MAIN_REF,
            "merge_commit": facts["merge_commit"], "tree": facts["tree"],
            "parents": list(facts["parents"]),
            "merge_kind": "MERGE_COMMIT" if len(facts["parents"]) == 2 else "FIRST_PARENT_COMMIT",
            # Declared by the merge commit's own subject; the verifier binds on merge_commit and repository only.
            "pull_request": int(match.group(1)) if match else None,
            "pull_request_source": "MERGE_COMMIT_SUBJECT" if match else None}
    return {**core, "payload_sha256": sha(core), "disposition": ALLOW,
            "communication_id": PROFILE_ID + ":" + repo + "@" + facts["merge_commit"]}


def sealed(receipt: Any) -> bool:
    return (isinstance(receipt, Mapping) and isinstance(receipt.get("receipt_sha256"), str)
            and sha({k: v for k, v in receipt.items() if k != "receipt_sha256"}) == receipt["receipt_sha256"])
# -- end of copied blocks -------------------------------------------------------------------------------


def copied_block_digests(source: str) -> dict[str, str]:
    """sha256 of each copied function's text, to compare with the pin's digests of the org originals."""
    out = {}
    for name in COPIED_BLOCKS:
        i = source.index(f"def {name}(")
        ends = [j for j in (source.find("\ndef ", i + 1), source.find("\n# --", i + 1)) if j != -1]
        out[name] = "sha256:" + hashlib.sha256((source[i:min(ends)].rstrip() + "\n").encode()).hexdigest()
    return out


def load_json(path: Path | str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _git(git_dir: str, *args: str) -> bytes | None:
    r = subprocess.run(["git", "--git-dir", git_dir, *args], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def read_org_ledger(git_dir: str | None, namespace: str) -> dict[str, Any]:
    """Read-only observation of a local copy of the org ledger ref."""
    obs: dict[str, Any] = {"copy_supplied": bool(git_dir), "tip": None, "head_epoch": None,
                           "head_epoch_detail": None, "namespace": namespace, "namespace_head": None,
                           "namespace_chain_length": 0, "namespace_detail": None}
    if not git_dir:
        return obs
    tip = _git(git_dir, "rev-parse", "--verify", LEDGER_REF + "^{commit}")
    if tip is None:
        obs["copy_supplied"] = False
        obs["head_epoch_detail"] = "the copy has no " + LEDGER_REF
        return obs
    tip = tip.decode().strip()
    obs["tip"] = tip

    def get(path: str) -> Any:
        raw = _git(git_dir, "show", f"{tip}:{path}")
        try:
            return json.loads(raw) if raw is not None else None
        except ValueError:
            return None

    head = get("HEAD.json")
    receipt = get("receipts/" + str((head or {}).get("receipt_sha256", "")).split(":")[-1] + ".json") \
        if isinstance(head, Mapping) else None
    if not sealed(receipt) or receipt.get("receipt_sha256") != head.get("receipt_sha256"):
        obs["head_epoch_detail"] = "the organization ledger head receipt is absent or unsealed"
    else:
        ref = receipt.get("hb_reference")
        epoch = ref.get("epoch") if isinstance(ref, Mapping) else None
        if type(epoch) is int and epoch >= 32 and ref.get("derived_from_clock") is False:
            obs["head_epoch"] = epoch
        else:
            obs["head_epoch_detail"] = "head hb_reference " + repr(ref) + " is not a supplied epoch"

    nhead = get(namespace + "/HEAD.json")
    if not isinstance(nhead, Mapping):
        obs["namespace_detail"] = namespace + "/HEAD.json is absent on the ledger copy"
        return obs
    cursor, seen, n = nhead.get("receipt_sha256"), set(), 0
    while isinstance(cursor, str) and cursor not in seen:
        seen.add(cursor)
        r = get(f"{namespace}/receipts/{cursor.split(':')[-1]}.json")
        if not sealed(r) or r.get("receipt_sha256") != cursor:
            obs["namespace_detail"] = "namespace chain receipt absent or unsealed: " + cursor
            return obs
        n += 1
        cursor = r.get("previous_receipt_sha256")
    if cursor is not None or n == 0:
        obs["namespace_detail"] = "namespace chain does not end at a genesis receipt (previous_receipt_sha256 null)"
        return obs
    obs["namespace_head"], obs["namespace_chain_length"] = nhead["receipt_sha256"], n
    return obs


def verify_writer(pin: Mapping[str, Any], writer_dir: str | None) -> tuple[bool | None, list[str]]:
    if not writer_dir:
        return None, ["no pinned writer checkout supplied"]
    bad = []
    for f in pin["files"]:
        p = Path(writer_dir) / f["path"]
        got = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        if got != f["sha256"]:
            bad.append(f"{f['path']}: {got} != {f['sha256']}")
    return not bad, bad


def plan(commits: list[str], *, git_dir: Path | str = ROOT, org_ledger: str | None = None,
         writer_dir: str | None = None, pin: Mapping[str, Any] | None = None,
         contract: Mapping[str, Any] | None = None) -> dict[str, Any]:
    pin = pin if pin is not None else load_json(PIN_PATH)
    contract = contract if contract is not None else load_json(CONTRACT_PATH)
    repo = contract["repository"]
    loc = contract["repository_ledger_location"]
    namespace = loc["namespace"]
    if pin.get("pin_sha256") != sha({k: v for k, v in pin.items() if k != "pin_sha256"}):
        raise SystemExit("writer pin does not hash to its pin_sha256")

    planned = []
    for c in commits:
        facts = commit_facts(c, git_dir)
        why = facts_failure(facts)
        planned.append({"commit": facts.get("merge_commit", c), "facts_failure": why,
                        "evidence": None if why else merge_evidence(repo, facts),
                        "evidence_note": "the evidence's own disposition is the copied org evidence shape; "
                                         "nothing is receipted and the plan disposition governs"})

    writer_ok, writer_detail = verify_writer(pin, writer_dir)
    obs = read_org_ledger(org_ledger, namespace)
    org = f"{loc['repository']} {loc['ref']}"
    unmet: list[tuple[str, str, str, str]] = []
    if writer_ok is not True:
        unmet.append(("WRITER_PIN_UNVERIFIED", "WRITER_PIN_VERIFIED",
                      f"a checkout of {pin['source_repository']}@{pin['source_commit']} whose files match the sha256 pins "
                      f"({'; '.join(writer_detail)})",
                      "the workflow checks out the pinned commit; re-run on the next push"))
    if not obs["copy_supplied"]:
        unmet.append(("ORGANIZATION_LEDGER_COPY_UNAVAILABLE", "ORGANIZATION_LEDGER_COPY_READ",
                      f"a local read-only copy of {org} (anonymous fetch of the public ref)",
                      "re-run once the ref is readable; nothing was written"))
    elif obs["head_epoch"] is None:
        unmet.append(("HB_EPOCH_SOURCE_UNOBSERVED", "ORGANIZATION_HEAD_SUPPLIED_EPOCH",
                      "the organization ledger head receipt sealed and carrying hb_reference.epoch, an int >= 32 with "
                      f"derived_from_clock exactly false ({obs['head_epoch_detail']}); no clock is read",
                      "re-run once the organization head carries a supplied epoch"))
    if obs["namespace_head"] is None:
        unmet.append(("REPOSITORY_LEDGER_GENESIS_UNOBSERVED", "REPOSITORY_CHAIN_GENESIS_OBSERVED",
                      f"{namespace}/HEAD.json on {org}, naming a sealed chain that ends at a genesis receipt "
                      f"({obs['namespace_detail'] or 'no ledger copy read'}). Genesis is the REPOSITORY_LEDGER_INITIALIZATION "
                      "transition for this repository (an initialization manifest of the same form as "
                      "StegVerse-org/StegVerse-SDK .stegverse/transition-ledger/initialization-manifest.v1.json), observed at the "
                      "current organization ledger head, with the epoch supplied at execution, and published only by the organization's own append "
                      "(StegVerse-org/.github organization-ledger-transition.yml under ORGANIZATION_LEDGER_LOCK). That is an "
                      "admission transition in StegVerse-org/.github and is not performed here",
                      "re-run plan on the next push to main once the namespace HEAD is readable on the published ref"))
    unmet.append(("MERGE_APPEND_PATH_NOT_ADMITTED", "MERGE_APPEND_PATH_ADMITTED",
                  f"a publisher admitted to append {OPERATION} receipts for {repo} to {namespace}. Either (a) an "
                  "organization-side writer in StegVerse-org/.github, admitted by an admission transition, reads LLM-adapter main "
                  "anonymously on its own trigger and appends under ORGANIZATION_LEDGER_LOCK; or (b) TV/TVC least-privilege "
                  "issuance (TVC custody) of a contents:write credential scoped to StegVerse-org/.github "
                  f"{LEDGER_REF}, which this workflow would use but never mint or hold. In both cases the pinned "
                  "merge_transfer.py needs a repository parameter, because it binds repository() to its own checkout's "
                  "contract. This workflow has contents: read and never writes",
                  "Coordination picks (a) or (b) and the named transition is performed outside this lane; then re-run"))
    primary = unmet[0]
    return {"schema": RESULT_SCHEMA, "repository": repo, "operation": OPERATION,
            "ledger_location": {"repository": loc["repository"], "ref": loc["ref"], "namespace": namespace,
                                "new_ledger_root": loc.get("new_ledger_root")},
            "writer_pin": {"source_repository": pin["source_repository"], "source_commit": pin["source_commit"],
                           "pin_sha256": pin["pin_sha256"], "verified": writer_ok},
            "observation": obs, "planned": planned,
            "disposition": FAIL_CLOSED, "failure_code": primary[0], "failed_predicate": primary[1],
            "required_evidence_or_repair": primary[2], "retry_entrypoint": ENTRYPOINT,
            "owning_existing_goal": GOAL, "next_attempt": primary[3],
            "unmet_predicates": [{"failure_code": u[0], "failed_predicate": u[1], "required_evidence_or_repair": u[2]}
                                 for u in unmet],
            "consequence_committed": False, "ledger_written": False, "credential_used": False,
            "authority_effect": "NONE_PLAN_ONLY_G8_DRAFT"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--commits-file")
    p.add_argument("--commit", action="append", default=[])
    p.add_argument("--git-dir", default=str(ROOT))
    p.add_argument("--org-ledger", help="local bare copy holding " + LEDGER_REF)
    p.add_argument("--writer-checkout")
    p.add_argument("--out")
    a = ap.parse_args(argv)
    commits = list(a.commit)
    if a.commits_file:
        commits += [ln.strip() for ln in Path(a.commits_file).read_text().splitlines() if ln.strip()]
    result = plan(commits, git_dir=a.git_dir, org_ledger=a.org_ledger, writer_dir=a.writer_checkout)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    sys.stdout.write(text)
    return 0 if result["disposition"] == ALLOW else 3


if __name__ == "__main__":
    raise SystemExit(main())
