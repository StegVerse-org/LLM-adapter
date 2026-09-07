# Issue 288 — install, validate, merge, reconcile

Branch: `feat/anthropic-intr-runtime-fix-288`
Protocol: `stegverse.intr.anthropic.transport.v1`

This branch is the current-main integration branch. The historical `feat/anthropic-intr-transport-288` branch is retained as provenance only and is superseded for merge purposes because it diverged behind current `main`.

## Installed source surfaces

```text
llm_adapter/anthropic_intr_transport.py
llm_adapter/anthropic_intr_executor.py
schemas/stegverse-intr-anthropic-transport-envelope.schema.json
schemas/stegverse-intr-anthropic-evidence.schema.json
schemas/stegverse-intr-anthropic-capability.json
docs/CANONICALIZATION.md
docs/ANTHROPIC_INTR_MIRROR_HANDOFF.md
examples/reference_transaction.py
scripts/validate_anthropic_intr.py
tests/test_anthropic_intr_transport.py
tests/test_anthropic_content_blocks.py
tests/test_anthropic_intr_executor.py
tests/test_anthropic_adversarial.py
tasks/LLMA-ANTHROPIC-INTR-TRANSPORT-288.json
```

`llm_adapter/__init__.py` intentionally remains lightweight on current main; direct implementation-module imports are canonical. No Anthropic-only export list replaces existing package semantics.

Core-Lite constraint: validation is a script invoked by the existing stable validation surface. Do **not** add a dedicated workflow file merely for Anthropic.

## Exact-branch validation

```bash
python3 scripts/validate_anthropic_intr.py --branch feat/anthropic-intr-runtime-fix-288
python3 scripts/validate_anthropic_intr.py --branch feat/anthropic-intr-runtime-fix-288 --json > validation-288.json
```

The gate retains the exact 43-check contract and sets `merge_permitted: true` only on PASS. Its scope is installed-source integrity only and explicitly does not attest live Claude execution, Master Records custody acceptance, egress ALLOW, or product activation.

## README completeness

README must describe Anthropic as optional, non-authoritative interoperability over the native Messages API. It must preserve:

```text
credential_authority: TV/TVC
authority_effect: NONE
egress_intr_required: true
canonical_sovereign_route_replaced: false
hosted_provider_required: false
streaming/batches/files: unsupported in v1
```

Do not add availability or activation language.

## Merge condition

Merge only when all are evidenced on the exact current integration head:

| Condition | Evidence |
|---|---|
| Anthropic source gate PASS / `merge_permitted=true` | validation output |
| branch observed == `feat/anthropic-intr-runtime-fix-288` | same validation output |
| worktree clean at validated commit | same validation output |
| existing repository validation green, including Z.ai regression coverage | GitHub validation run |
| no existing Z.ai/DeepSeek/Kimi source modules modified by the Anthropic diff | main-to-head diff |
| README updated without activation claim | branch diff/review |

A merge is source integration only. It is not a tag, release, live-provider proof, or product activation.

## Runtime binding

The task reuses the existing canonical runtime:

```text
runtime profile: sovereign-runtime-worker-v1
resident substrate: canonical-resident-substrate-v1
executor: WorkerCoordinator
HB: HB32
oscillator: existing independent oscillator
runtime capability: bounded_process_execution
task-routing direction: INTERNAL
credential authority: TV/TVC
provider ingress/egress: external Interlock/InTr
custody/reconstruction: Master Records
```

Runtime-profile discovery must not manufacture a new provider runtime. A current authentic task-executing WorkerCoordinator remains required for a live call even though candidate discovery does not require current observation.

## Handoff / task-state reconciliation

After source validation, record no stronger than:

| Item | Status |
|---|---|
| transport/source/schema/canonicalization | INSTALLED, commit-referenced |
| source gate | PASSING on validated commit |
| live Claude execution | REQUIRES_STEGVERSE_RUNTIME_EVIDENCE |
| Master Records custody acceptance | REQUIRES_STEGVERSE_RUNTIME_EVIDENCE |
| exact-response egress ALLOW | REQUIRES_STEGVERSE_RUNTIME_EVIDENCE |
| product activation / tag / release | NOT CLAIMED |

## Downstream propagation

Source merge permits capability documentation only. Site/Publisher availability claims remain blocked until one authentic governed transaction produces and reconstructs the exact triple:

```text
ingress_receipt_hash
response_hash
egress_receipt_hash
```

StegIndex may index the merged capability as optional/non-authoritative after merge evidence exists. Wiki protocol documentation may describe the protocol after merge, but must not claim activation or availability.