# End-to-End Governed LLM Demonstration

This document describes the fixture-first governed LLM demonstration packaged with the StegVerse LLM adapter.

## Flow

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

## Fixtures

```text
examples/end_to_end/simple_query.json
examples/end_to_end/action_commit_candidate.json
examples/end_to_end/stale_evidence_query.json
```

## Commands

```bash
python scripts/run_end_to_end_demo.py --fixture examples/end_to_end/simple_query.json
python scripts/replay_demo.py --session-report reports/simple_query.session.json
python scripts/reconstruct_demo.py --session-report reports/simple_query.session.json
pytest tests/test_end_to_end_demo.py -v
```

## Boundary

```text
provider_output_is_authority == false
commitment_request_is_authority == false
authority_decision_executes_side_effect == false
execution_handoff_executes_side_effect == false
fixture_mode_default == true
live_provider_required == false
```

No live provider call, live continuity service, repository mutation, public posting, email sending, execution approval, or production trust-kernel execution is added by this path.
