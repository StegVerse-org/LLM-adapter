# Ecosystem Chat and VA Claims Chat LLM Session Archive Mirror Handoff

## Active goal and identity

```yaml
goal_id: LLMA-ECOSYSTEM-VA-CHAT-CONSOLIDATION-011
active_goal: durably consolidate the session that established both Chat products as full-function governed LLMs
originating_session_goal: Ecosystem Chat contains StegVerse Chat with the complete LLM surface; VA Claims Chat has the same LLM surface while external factual grounding is restricted to admitted official VA sources
repository: StegVerse-org/LLM-adapter
branch: goal/ecosystem-va-chat-session-consolidation
canonical_issue: StegVerse-org/LLM-adapter#107
canonical_task: tasks/LLMA-ECOSYSTEM-VA-CHAT-CONSOLIDATION-011.json
claim_state: CLAIMED_FOR_IMPLEMENTATION
claim_created_at: 2026-08-04T18:00:34Z
claim_expires_at: 2026-08-05T18:00:34Z
release_condition: hosted validation PASS, receipt retained, task released, handoff finalized, issue closed
manual_user_action_required: false
```

This handoff is a session-level index and archive proof. It does not replace the repository-wide `docs/LLM_ADAPTER_MIRROR_HANDOFF.md` or any capability-specific handoff.

## Mandatory continuation order

1. Read `docs/LLM_ADAPTER_MIRROR_HANDOFF.md` and `data/llm-adapter-orchestration-state.json`.
2. Read this handoff and `data/ecosystem-va-chat-session-consolidation.json`.
3. Follow the exact canonical owner listed for the target capability.
4. Do not create a competing provider, deployment, custody, Site, TVC, or filing lane.
5. Treat blocked tasks as machine-observable states rather than chat-owned work.

## Authoritative files

```text
data/ecosystem-va-chat-session-consolidation.json
scripts/validate_ecosystem_va_chat_session_consolidation.py
.github/workflows/ecosystem-va-chat-session-consolidation.yml
tasks/LLMA-ECOSYSTEM-VA-CHAT-CONSOLIDATION-011.json
receipts/ecosystem-va-chat-session-consolidation-validation.json
```

Capability sources of truth:

```text
docs/CHAT_LLM_PROFILES_MIRROR_HANDOFF.md
docs/CHAT_LLM_SESSION_BINDING_MIRROR_HANDOFF.md
docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md
docs/VA_CLAIM_ASSISTANT_PRIVACY_RUNTIME_MIRROR_HANDOFF.md
docs/VA_CLAIM_ASSISTANT_PROVIDER_PREFLIGHT_MIRROR_HANDOFF.md
docs/VA_CLAIM_ASSISTANT_SESSION_ARCHIVE_MIRROR_HANDOFF.md
```

## Governing product decision

```text
Ecosystem Chat contains StegVerse Chat.
Ecosystem Chat is a full-function LLM product surface.
VA Claims Chat is a full-function LLM product surface.
The products differ by purpose and factual-source policy, not by model capability.
Governance constrains consequence and authority; it does not silently remove reasoning, conversation, retrieval, multimodal, structured-output, planning, or candidate-tool capability.
```

## Completed work

### Full LLM profiles

```text
task: LLMA-CHAT-LLM-PROFILES-009
state: RELEASED_COMPLETE
PR: #103
merge: 18a49b8856a34d03d94955637adb4a53c9ccfe81
workflow run: 30928497409
Python: 3.9 PASS, 3.11 PASS, 3.12 PASS
policy tests: 16 per runtime
artifact: 8900112614
artifact digest: sha256:5c289bdd81df013d1e33dff0563a78641f689328a1fee8a9db25348eeb217d90
receipt: receipts/chat-llm-profiles-validation.json
receipt hash: 85a98e57b3a8e50fa13de3d24e2fcd39aaff99ea7071f3318719519f78275287
```

Both profiles declare 19/19 canonical LLM capabilities. Ecosystem Chat uses `GENERAL_ADMITTED`. VA Claims Chat uses `OFFICIAL_VA_ONLY`; official `va.gov` and genuine subdomains may ground Claims facts when admitted. General web, model memory, and VA lookalike hosts fail closed. Privacy-approved user records remain `user_record_fact` and never become VA authority.

### Provider-neutral session binding

```text
task: LLMA-CHAT-SESSION-BINDING-010
state: RELEASED_COMPLETE
PR: #106
merge: 5ee90dd1f1cc3d6b20ecb3bce3991d8b59d869e5
workflow run: 30929473927
Python: 3.9 PASS, 3.11 PASS, 3.12 PASS
session tests: 17 per runtime
artifact: 8900506930
artifact digest: sha256:5458d91baf79c4287b25034f58e6f174f27e64032837483229cb9597cbc307b3
receipt: receipts/chat-llm-session-binding-validation.json
receipt hash: b1f9f56e8dc087ee04c49a011d351855a762030e2886d484def025a29e2e09b0
```

The binding creates deterministic multi-turn provider-neutral envelopes. Required denied VA grounding blocks before an envelope exists. Candidate responses reject unknown citations, incorrect fact labels, undeclared or executed-tool claims, side effects, authority, publication, and custody claims.

### VA route and privacy implementation

```text
route task: VACP-ADAPTER-ROUTES-002 — RELEASED_COMPLETE
public-source answer-ready routes: 11
document_organization: sanitized derived context only
urgent_safety: AUTHORITY_RESOLUTION_REQUIRED until an official source is admitted
route receipt: 641c76f9e88c26d88aa0d0b600d158f9b053c05d1875ca4da1a59c160ce77919
dispatch receipt: 562e5528dd44a11a9b6c3f8b965d6449c258f6942f997939f916925a61be7f02

privacy task: VACP-ADAPTER-PII-RUNTIME-006 — RELEASED_COMPLETE
PR: #99
merge: cd2b010f35be3673f7853b03c951025db7225b32
workflow run: 30874416525
job: 91882865431
artifact: 8879004626
artifact digest: sha256:c6078147307ef853887a3618394c4758b6ed422b7ec815b1f22e92a554960961
receipt hash: bcd39b3689ba0fbe7f18b99e114984543d784c80d3fd8ad5842cc551926df34c
```

## Current canonical runtime owners

### Ecosystem Chat activation

```text
MERGED INTO: StegVerse-org/LLM-adapter#18
state: MACHINE_OWNED_BLOCKED
latest receipt: receipts/ecosystem-chat-authorized-provider-activation.latest.json
observed_at: 2026-08-04T17:19:57.702516+00:00
state: CONFIGURATION_REQUIRED
result_sha256: b92ad8ff8386fd6a611429f315d5956e7efe88c25c7ead8793e77e13c39d6a56
manual_user_action_required: false
```

Missing protected runtime bindings:

```text
STEGVERSE_PROVIDER_ENDPOINT
STEGVERSE_PROVIDER_MODEL
STEGVERSE_PROVIDER_TOKEN
STEGVERSE_MASTER_RECORDS_ENDPOINT
STEGVERSE_MASTER_RECORDS_TOKEN
```

The existing observer owns the transition from provider response through usage persistence, provider-usage custody, transition custody, and transition reconstruction. No secret may be synthesized or stored in repository source, logs, receipts, or artifacts.

### VA Claims provider execution

```text
MERGED INTO: StegVerse-org/LLM-adapter#90
canonical task: tasks/VACP-ADAPTER-AUTHORIZED-EXECUTION-005.json
state: BLOCKED
claimant: null
execution limit: one request; maximum USD 0.10
```

Machine-observable release conditions:

```text
hosted provider preflight = READY_FOR_EXPLICIT_AUTHORIZED_EXECUTION
observation source = GITHUB_ACTIONS_WORKFLOW
protected Master Records endpoint, allowed-host, and token bindings present
valid unexpired exact-caller VA provider authority
fresh single-use TVC admission from the pinned reusable workflow
hosted privacy receipt PASS with exact hash bcd39b3689ba0fbe7f18b99e114984543d784c80d3fd8ad5842cc551926df34c
privacy_guarded_dispatch executes before authority consumption, provider permission, or model input
```

The task cannot execute from push, schedule, pull request, credential presence, or privacy PASS alone.

### Master Records custody

```text
MERGED INTO: master-records/orchestration#15
machine task: master-records/orchestration/tasks/MR-VA-PRIVACY-ADAPTER-IMPORT-002.json
machine owner: .github/workflows/runtime-evidence-validation.yml
state: MACHINE_OWNED_BLOCKED
```

Released import evidence:

```text
PR: master-records/orchestration#18
merge: e855fc32f60ac7bb6348d76cb0251356aaf70542
run: 30930512789
job: 92063699933
artifact: 8900933300
digest: sha256:ada53bbdc053662355be176bf1bfb6fc30dba23f6ae8c2565d19ebbb176609ce
import receipt hash: 91a754b2ba46954e02c3fcb1eb9fa5f1fb0d8f1626bebc810789d162ac4f1da2
```

Exact blockers:

```text
operational_privacy_event_missing
provider_execution_evidence_missing
provider_execution_receipt_missing
```

The existing workflow will append custody and reconstruction records automatically only after both genuine adapter events exist.

### Site and source authority

```text
MERGED INTO: StegVerse-Labs/Site#113 — governed session and receipt-derived projection
MERGED INTO: StegVerse-Labs/Site#116 — production document privacy and execution
MERGED INTO: StegVerse-Labs/TVC#9 — ephemeral route admission and credential linkage
```

Site must not display `GOVERNED_CLAIM_SESSION`, enable private upload, or infer filing authority before the applicable receipts pass. `urgent_safety` remains fail closed until the Site source registry admits a current official source with authority, effective, retrieval, supersession, and proposition-support fields.

## Adjacent goals durably transferred

The machine-readable inventory preserves:

- persistent package publication and authorized public hosting;
- provider usage persistence and both custody/reconstruction chains;
- Site activation and downstream ingestion;
- VA route generation and proposition-level provenance;
- raw-PII and raw-document rejection before model input;
- TVC admission, expiry, revocation, and exact caller binding;
- privacy-minimized operational custody;
- production document detection, redaction, leakage, page anchors, retention, deletion, and export;
- official urgent-safety source admission;
- veteran-retained fact confirmation, signature, filing, revocation, duplicate prevention, confirmation, and custody;
- downstream verification for Site, Publisher, admissibility-wiki, and stegguardian-wiki after activation evidence exists.

No adjacent goal remains only in chat.

## Duplicate and converged work disposition

```text
Profile implementation: COMPLETE; do not recreate.
Session binding: COMPLETE; do not recreate.
Ecosystem live runtime: issue #18 is canonical; no second gateway or host architecture.
VA provider execution: VACP-ADAPTER-AUTHORIZED-EXECUTION-005 is canonical; no competing workflow or authority receipt.
VA route and privacy implementation: released; no competing generator or PII runtime.
TVC: TVC#9 reusable admission is canonical; no adapter-owned credential duplicate.
Master Records: issue #15 and MR-VA-PRIVACY-ADAPTER-IMPORT-002 are canonical; no local custody simulation.
Site: Site#113/#116 are canonical; no external session may mutate Site paths without Site machine admission.
Earlier VA session archive: preserved and extended, not replaced; this handoff adds the later profile and session-binding slices.
```

## Automation

Workflow:

```text
.github/workflows/ecosystem-va-chat-session-consolidation.yml
```

Triggers:

```text
pull request on owned or dependency paths
push to main on owned or dependency paths
daily schedule
workflow dispatch
```

Deterministic outputs:

```text
receipts/ecosystem-va-chat-session-consolidation-validation.json
artifact ecosystem-va-chat-session-consolidation-validation
```

The validator fails closed on missing inventory fields, duplicate or vague work assignments, changed profile/session receipt hashes, unreleased implementation tasks, a claimed VA provider task, an invalid Ecosystem runtime authority projection, unassigned work, manual user tasks, or archive assertions that imply authority.

Validation command:

```bash
python scripts/validate_ecosystem_va_chat_session_consolidation.py
```

## Current completion state

```text
inventory items: 15/15
session requirements transferred: 18/18
profile implementation: 100 percent
session-binding implementation: 100 percent
VA route implementation: 100 percent
VA privacy implementation: 100 percent
combined archive package files before receipt: 5/5
scaffolding or stubs: 0
hosted validation: pending
mainline integration: pending
active chat-owned claim: LLMA-ECOSYSTEM-VA-CHAT-CONSOLIDATION-011 only
unowned tasks: 0
manual user tasks: 0
goal activation: profile and session layers complete; live runtime activation remains with named owners
```

## Claim release and archive conditions

This session becomes archive-safe only after:

1. hosted Python 3.9, 3.11, and 3.12 jobs pass;
2. repository-wide checks pass;
3. the validation artifact and digest are inspected;
4. the receipt is retained on `main`;
5. task `LLMA-ECOSYSTEM-VA-CHAT-CONSOLIDATION-011` becomes `RELEASED_COMPLETE` with no claimant;
6. the inventory records zero active chat-owned claims and posture `ARCHIVE_READY`;
7. this handoff records the final merge, run, jobs, artifact, digest, receipt commit, and receipt hash;
8. issue #107 closes completed.

Archive disposition grants no provider, execution, custody, filing, publication, deployment, release, Site mutation, or activation authority.
