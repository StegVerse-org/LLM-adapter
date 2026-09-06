# Issue 288 — install, validate, merge, reconcile

Branch: `feat/anthropic-intr-transport-288`
Protocol: `stegverse.intr.anthropic.transport.v1`

This runbook is executed **by the repo operator**. Nothing in this package
performs a checkout, a merge, a tag, a release, or a provider call.

---

## 1. Install onto the branch

```
git checkout -b feat/anthropic-intr-transport-288 origin/main
# copy from the package:
#   llm_adapter/anthropic_intr_transport.py
#   llm_adapter/anthropic_intr_executor.py
#   schemas/stegverse-intr-anthropic-transport-envelope.schema.json
#   schemas/stegverse-intr-anthropic-evidence.schema.json
#   schemas/stegverse-intr-anthropic-capability.json
#   docs/CANONICALIZATION.md
#   docs/BRANCH_288_INSTALL.md
#   examples/reference_transaction.py
#   scripts/validate_anthropic_intr.py
#   tests/test_anthropic_intr_transport.py
#   tests/test_anthropic_content_blocks.py
#   tests/test_anthropic_intr_executor.py
#   tests/test_anthropic_adversarial.py
```

`llm_adapter/__init__.py` in this package exports only the Anthropic surface.
If the repo's `__init__.py` already exports the Z.ai surface, **merge the export
lists** rather than overwriting the file.

Core-Lite constraint: validation is a script invoked by the existing stable
dispatcher. Do **not** add a workflow file for it.

## 2. Exact-branch validation

```
python3 scripts/validate_anthropic_intr.py --branch feat/anthropic-intr-transport-288
python3 scripts/validate_anthropic_intr.py --json > validation-288.json
```

43 checks across eight groups: exact-branch identity and clean worktree,
install completeness, authority-boundary preservation, schema/code agreement,
hash determinism (including stability across `PYTHONHASHSEED`), fail-closed
spot checks independent of the test suite, credential hygiene of the installed
source, and the full test suite.

Exit 0 sets `merge_permitted: true`. Exit 1 blocks the merge.

**Gate scope.** The report explicitly carries:

```
attests_live_claude_execution: false
attests_custody_acceptance:    false
attests_egress_allow:          false
attests_product_activation:    false
scope: "installed-source integrity only"
```

A green gate authorizes a merge of source. It authorizes nothing downstream.

## 3. README changes required on the branch

Add to the adapter README, under the provider list:

> **Anthropic (`stegverse.intr.anthropic.transport.v1`)** — optional,
> non-authoritative provider transport over the native Messages API
> (`POST https://api.anthropic.com/v1/messages`). Credential authority remains
> TV/TVC; no credential material enters any envelope, evidence, usage record,
> custody handoff or log. Every result carries `authority_effect = "NONE"` and
> `egress_intr_required = true`. Ingress and egress dispositions remain external
> Interlock/InTr decisions; the adapter verifies them and never generates one.
> `canonical_sovereign_route_replaced = false`,
> `hosted_provider_required = false`. Streaming, Batches and Files are
> UNSUPPORTED in v1 and require separately admitted endpoint profiles.
> Hashing and normalization are specified in `docs/CANONICALIZATION.md`.
> Validation: `python3 scripts/validate_anthropic_intr.py`.

Do not add release, availability, or activation language.

## 4. Merge condition

Merge **only** if all of the following hold, each with an artifact:

| Condition | Evidence artifact |
|---|---|
| Gate outcome `PASS`, `merge_permitted: true` | `validation-288.json` |
| Branch observed == branch expected | same file, `branch_observed` |
| Worktree clean at validated commit | same file, `head_commit` |
| Z.ai transport tests still green | existing suite run on the branch |
| No change to Z.ai modules in the diff | `git diff --stat origin/main` |
| README carries no activation claim | review |

If any row lacks its artifact, the merge does not proceed. A merge is a merge of
source only; it is not a tag, a release, or an activation.

## 5. Handoff / task-state reconciliation

Reconcile `docs/ANTHROPIC_INTR_MIRROR_HANDOFF.md` and the #288 task state to
exactly these statuses, and no stronger:

| Item | Status |
|---|---|
| Transport source, schemas, canonicalization spec, capability declaration | INSTALLED (commit-referenced) |
| Test suite + validation gate | PASSING on the validated commit |
| Requirement classification | per README table |
| Live Claude execution | REQUIRES_STEGVERSE_RUNTIME_EVIDENCE |
| Master Records custody acceptance | REQUIRES_STEGVERSE_RUNTIME_EVIDENCE |
| Egress ALLOW against a real response hash | REQUIRES_STEGVERSE_RUNTIME_EVIDENCE |
| Product activation / tag / release | NOT CLAIMED |

Every status line should cite the validated commit SHA. A status without a
commit SHA or a receipt hash is not evidence.

## 6. Downstream propagation determination

**NOT AUTHORIZED at merge.** A source merge is not an activation event, and
StegIndex / Site / Publisher / wiki surfaces are public-facing: propagating on a
green gate would publish an availability claim the evidence does not support.

Propagation becomes authorized per surface when its own predicate is met:

| Surface | Predicate |
|---|---|
| StegIndex | Merge commit SHA + `validation-288.json` recorded; index entry states capability, not availability, and mirrors `optional_interoperability: true` / `authoritative: false` |
| Site | Requires at least one authentic governed transaction: real ingress receipt hash, real `response_hash`, real egress ALLOW receipt hash. Absent that, site copy may describe the interop capability only, with no execution claim |
| Publisher | Same predicate as Site, plus a reconstruction check (`docs/CANONICALIZATION.md` §9) reproducing `envelope_hash` and `response_hash` from the archived bundle |
| Wiki | Authorized at merge for protocol documentation (envelope fields, hash bases, normalization, fail-closed list). Not authorized for any activation, availability, or endorsement statement |

Blocking gap for Site and Publisher: no authentic runtime evidence exists yet.
The smallest step that closes it is one real transaction through the external
Interlock/InTr path producing a triple of `{ingress_receipt_hash,
response_hash, egress_receipt_hash}` that survives the §9 reconstruction check.
Until that triple exists and reconstructs, those two surfaces stay blocked.
