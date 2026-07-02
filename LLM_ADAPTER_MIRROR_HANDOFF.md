# LLM Adapter Mirror Handoff

## Current source of truth

This file is the handoff source of truth for `StegVerse-org/LLM-adapter` until superseded.

## Active goal

Goal 3: End-to-end governed LLM demonstrator.

The repository should prove:

```text
fixture query
-> provider request envelope
-> fixture provider response
-> continuity evidence pointers
-> governed session packet
-> action route
-> commitment request
-> authority decision
-> disabled execution handoff
-> demo report artifacts
-> replay verification
-> reconstruction verification
```

No live provider call, live continuity service, repository mutation, public posting, email sending, execution approval, or production trust-kernel execution is added by this path.

## Installed baseline already present

```text
adapter.capabilities.json
docs/ACTIVATION_STATUS.md
docs/GOVERNED_LLM_RUNTIME.md
fixtures/governed_response_fixture.json
llm_adapter/
scripts/smoke_governed_session.py
tests/
README.md
```

## Files to install for Goal 3

```text
examples/end_to_end/simple_query.json
examples/end_to_end/action_commit_candidate.json
examples/end_to_end/stale_evidence_query.json
scripts/run_end_to_end_demo.py
scripts/replay_demo.py
scripts/reconstruct_demo.py
docs/END_TO_END_DEMO.md
tests/test_end_to_end_demo.py
```

## Required invariant

```text
provider_output_is_authority == false
commitment_request_is_authority == false
authority_decision_executes_side_effect == false
execution_handoff_executes_side_effect == false
fixture_mode_default == true
live_provider_required == false
```

## Verification commands

```bash
python scripts/run_end_to_end_demo.py --fixture examples/end_to_end/simple_query.json
python scripts/replay_demo.py --session-report reports/simple_query.session.json
python scripts/reconstruct_demo.py --session-report reports/simple_query.session.json
pytest tests/test_end_to_end_demo.py -v
pytest tests/ -v
```

## Downstream sync targets

```text
StegVerse-org/StegVerse-SDK
  -> validate demo session packets
  -> build manifest
  -> build receipt handoff

StegVerse-Labs/admissibility-wiki
  -> publish public demo overview
  -> point to adapter and SDK verification commands
```

## Archive posture

Not archive-ready until the Goal 3 demo files are installed, verified locally, and reflected in SDK and wiki handoffs.
