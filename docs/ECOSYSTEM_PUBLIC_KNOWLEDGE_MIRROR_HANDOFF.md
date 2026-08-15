# Ecosystem Chat Public Knowledge Mirror Handoff

## Goal

```text
goal_id: LLMA-ECOSYSTEM-PUBLIC-KNOWLEDGE-021
originating_goal: Ecosystem Chat can answer public StegVerse details and explain public SDK/governance/integration modes from canonical sources rather than model memory
repository: StegVerse-org/LLM-adapter
branch: main
canonical_issue: #140
```

## Installed source

```text
data/stegverse-public-knowledge.v1.json
llm_adapter/public_knowledge.py
llm_adapter/ai_entry_backend_service.py
tests/test_public_knowledge.py
tasks/LLMA-ECOSYSTEM-PUBLIC-KNOWLEDGE-021.json
```

The public knowledge manifest is local, credential-free, and non-authorizing. Initial coverage includes StegVerse overview, governance modes 000/00/0A/0B/1/2, SDK Connect my LLM, MCP, Ecosystem Chat, and VACC.

The resolver requires every entry to reference a declared public repository/path source. `model_memory_is_source` is false. Unknown/unindexed questions return no grounded answer; the bounded fallback states that it will not invent a StegVerse fact.

`ai_entry_backend_service.py` now consults this resolver before returning its deterministic fallback. Recognized public help questions therefore produce a source-grounded response even when the separately governed provider/model lane is unavailable. Provider execution remains independent and authoritative runtime ownership is unchanged.

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

Public knowledge output is explanation only and grants no execution or publication authority.

## Validation state

```text
source installed on main: YES
automatic repository workflows observed after source commits: YES
focused tests installed: YES
focused test execution result: PENDING INSPECTION
runtime provider activation: OUT OF SCOPE / MACHINE OWNED
```

Do not treat a generic workflow completion as focused validation until the run/jobs/logs show the relevant source/test path or an equivalent full suite.

## Expansion rule

Issue #140 owns future public corpus expansion. Add entries only when a canonical public StegVerse repository/path exists. Do not ingest private project material merely because a model can access it. For changed operational instructions, update the canonical source first, then refresh the public knowledge manifest.

## Collision boundaries

- closed issue #18 / sovereign runtime lanes retain provider/model activation ownership;
- heartbeat and local model lanes are not reopened;
- Site is not mutated without its mandatory orchestrator;
- Master Records remains custody/reconstruction authority.

## Archive / continuation

Source implementation can release after focused validation passes. Live Ecosystem Chat model activation remains separately machine-owned. Issue #140 remains the canonical continuation for public knowledge coverage.
