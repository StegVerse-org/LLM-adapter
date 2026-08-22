# Unified Chat Specialties Mirror Handoff

## Source of truth

```text
goal_id: LLMA-UNIFIED-SPECIALTY-PROFILES-180
repository: StegVerse-org/LLM-adapter
canonical_issue: #180
parent_site_goal: StegVerse-Labs/Site#239
canonical_full_llm_profile: ecosystem-chat-llm
runtime_owner: StegVerse-org/LLM-adapter#18
vacc_route_owner: StegVerse-org/LLM-adapter#90
math_site_owner: StegVerse-Labs/Site#240
```

## Product correction

The canonical conversational topology is one full LLM surface with specialty capability profiles layered on top:

```text
ecosystem-chat-llm
  -> VACC specialty
  -> mathematics educator specialty
  -> future specialty profiles
```

A specialty profile contributes context, source policy, response behavior, input modalities, and candidate tools. It does not create another provider/runtime, conversation history, execution authority, custody path, or credential plane.

## Implemented source slice

```text
contracts/chat-specialty-profile.schema.json
profiles/vacc-specialty.v1.json
profiles/math-educator-specialty.v1.json
llm_adapter/chat_specialties.py
tests/test_chat_specialty_profiles.py
tasks/LLMA-UNIFIED-SPECIALTY-PROFILES-180.json
```

### VACC

The VACC specialty consumes `ecosystem-chat-llm`, references the already released broad public-information profile and the stricter claims profile, treats disability claims as one deep subdomain rather than the whole specialty, and keeps private-record use behind separate privacy admission.

### Mathematics educator

The mathematics specialty consumes the same full LLM surface, supports text/image/file input, broad mathematics including history/foundations/philosophy, and educator behaviors such as hints, guided solutions, checking work, alternate methods, prerequisite explanation, and difficulty variation.

For photographed problems the following are different states:

```text
source_image
interpreted_mathematical_transcription
```

The transcription is interpretation, not source fact. Correction creates a successor transcription state; the original image is preserved.

The deterministic solver and verifier are candidate tools only. Tool candidacy does not execute them and successful calculation is not mathematical proof authority.

## Preserved released work

Do not reopen or duplicate:
- `docs/CHAT_LLM_PROFILES_MIRROR_HANDOFF.md` released full LLM profile layer;
- `docs/CHAT_LLM_SESSION_BINDING_MIRROR_HANDOFF.md` provider-neutral session layer;
- `docs/VACC_PUBLIC_INFORMATION_PROFILE_MIRROR_HANDOFF.md` broad VACC source-policy layer;
- issue #18 provider/runtime path;
- issue #90 VACC governed retrieval/runtime;
- Master Records custody/reconstruction authority.

## Authority boundary

```text
credential authority: TV/TVC
GitHub token runtime authority: NONE
NON-TV/TVC secret/token required: false
specialty selection authority effect: false
model output execution authority: false
candidate tool execution authority: false
provider/runtime duplication: false
custody-path duplication: false
Site mutation authority: false
Render production dependency: NONE
```

## Validation gate

Source completion requires deterministic tests proving both specialties bind `ecosystem-chat-llm`, preserve the full LLM surface, reject a duplicated provider/runtime or custody path, keep candidate tools non-authorizing, and preserve the mathematics image/transcription distinction.

Source validation is not provider execution, Site activation, tool execution, custody, publication, or product activation.
