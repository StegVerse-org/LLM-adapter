# Ecosystem Chat Public Knowledge Mirror Handoff

## Goal

```text
goal_id: LLMA-ECOSYSTEM-PUBLIC-KNOWLEDGE-021
originating_goal: Ecosystem Chat can answer public StegVerse details and explain public SDK/governance/integration modes from canonical sources rather than model memory
repository: StegVerse-org/LLM-adapter
canonical_issue: #140
state: COMPLETE_VALIDATED_SOURCE
claim_state: RELEASED
```

## Authoritative implementation

```text
data/stegverse-public-knowledge.v1.json
llm_adapter/public_knowledge.py
llm_adapter/ai_entry_backend_service.py
tests/test_public_knowledge.py
tasks/LLMA-ECOSYSTEM-PUBLIC-KNOWLEDGE-021.json
docs/ECOSYSTEM_PUBLIC_KNOWLEDGE_MIRROR_HANDOFF.md
```

The local public-knowledge manifest is credential-free and non-authorizing. Each entry must reference a declared public repository/path source. `model_memory_is_source` is false. Unknown or unindexed questions return no grounded answer rather than inventing a StegVerse fact. `ai_entry_backend_service.py` consults this resolver before deterministic fallback; provider/model execution remains a separate governed lane.

Initial coverage includes the StegVerse overview, governance modes 000/00/0A/0B/1/2, SDK Connect my LLM, MCP, Ecosystem Chat, and VACC.

## Authority and credential boundary

```text
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_required: false
github_token_runtime_authority: NONE
provider/model authority changed: false
StegGate authority changed: false
Master Records authority changed: false
Site activation authority changed: false
```

Public-knowledge output is explanation only and grants no execution, custody, publication, deployment, filing, or activation authority.

## Historical release validation

The original combined source-validation evidence remains immutable historical release evidence:

```text
historical_workflow: .github/workflows/public-knowledge-vacc-source-validation.yml
workflow_run: 31875248198
job: 94989892925
result: SUCCESS
focused tests in combined Ecosystem/VACC run: 11/11 PASS
credential-empty assertions: GITHUB_TOKEN, GH_TOKEN, OPENAI_API_KEY, ANTHROPIC_API_KEY
source materialization: anonymous exact-SHA archive
compile: PASS
marker: PUBLIC_KNOWLEDGE_VACC_SOURCE_VALIDATION_PASS
manual workflow dispatch: NO
```

## Current deterministic validation

Workflow consolidation claim `LLMA-WORKFLOW-CONSOLIDATE-PUBLIC-KNOWLEDGE-VACC-041` transfers continuing source validation into the shared credential-clean dispatcher:

```text
current_workflow: .github/workflows/validate.yml
workflow_credential_authority: NONE
runtime_credential_authority: TV/TVC
checkout/setup/artifact transport: NONE
repository writeback: NONE
activation effect: NONE
```

The dispatcher compiles `public_knowledge.py`, `ai_entry_backend_service.py`, `vacc_public_information.py`, and the focused tests, then runs:

```bash
$PYTHON_BIN -m unittest -q tests.test_public_knowledge tests.test_vacc_public_information
```

It explicitly refuses `GITHUB_TOKEN`, `GH_TOKEN`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, TV/TVC protected values, and other credential-bearing environment values before source acquisition. No provider call occurs.

## Continuation

Issue #140 owns future public corpus expansion. Add entries only when a canonical public StegVerse repository/path exists. Update changed operational instructions at the canonical source before refreshing the public manifest. Sovereign runtime/provider/model activation remains a separate machine-owned lane; heartbeat/local-model work is not reopened; Site requires its own orchestrator; Master Records remains custody/reconstruction authority.

The originating public-knowledge implementation is complete and released. Workflow consolidation is repository maintenance and does not reopen the product implementation.

## Provider / device / platform / access-surface expansion

Task `LLMA-PROVIDER-SURFACE-KNOWLEDGE-057` extends the released public-knowledge substrate without reopening task 021.

Canonical provider facts remain owned by `StegVerse-Labs/continuity-vault-kit#56` and its merged registry:

```text
specs/kv-provider-surface-capability-registry.v1.json
schema: stegverse.kv.provider-surface-capability-registry/v1
fact state at integration start: INSTALLED_UNVERIFIED
```

LLM-adapter adds only a fail-closed consumer. It does not copy provider facts into its local public-knowledge manifest. The runtime may receive the canonical registry through `STEGVERSE_KV_PROVIDER_SURFACE_REGISTRY`; if that source is unavailable or no matching tuple is admitted, Ecosystem Chat reports the state as unknown/unverified rather than inferring behavior from model memory.

The diagnostic dimensions remain distinct:

```text
provider × device × platform × access surface × browser/runtime
```

This expansion changes no provider, credential, execution, StegGate, Master Records, Site, publication, or activation authority.
