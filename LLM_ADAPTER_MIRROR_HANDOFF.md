# LLM Adapter Mirror Handoff

## Current source of truth

This file is the handoff source of truth for `StegVerse-org/LLM-adapter` until superseded.

## Active goal

Goal 4: micro-node governed return-path proof.

Goal 3 established the fixture-first governed LLM demonstrator. Goal 4 now proves that the LLM adapter can express a governed LLM response as a micro-node-compatible transition request and preserve the original customer return path without gaining execution authority.

## Goal 4 proof path

```text
external LLM / UI
-> LLM-adapter
-> micro-node-compatible transition request
-> transition-table role evaluation contract
-> terminal decision + receipt reference
-> governed return payload
-> original customer path
```

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

## Installed for Goal 4 on current build branch

```text
docs/MICRO_NODE_RETURN_PATH.md
examples/micro_node_return_path/request.json
examples/micro_node_return_path/governed_return.json
scripts/verify_micro_node_return_path.py
scripts/verify_goal4.py
tests/test_micro_node_return_path.py
```

## Required invariant

```text
provider_output_is_authority == false
commitment_request_is_authority == false
authority_decision_executes_side_effect == false
execution_handoff_executes_side_effect == false
execution_authority_granted == false
fixture_mode_default == true
live_provider_required == false
returned_to_origin == true
```

## Canonical verification command

```bash
python scripts/verify_goal4.py
```

The aggregate verifier runs:

```bash
python scripts/verify_micro_node_return_path.py
python -m pytest tests/test_micro_node_return_path.py -v
python -m pytest tests/ -v
```

## Downstream sync targets

```text
StegVerse-org/StegVerse-SDK
  -> validates micro-node request and governed return fixtures
  -> includes SDK-side Goal 4 aggregate verification
  -> treats micro-node-runtime as callable governed runtime target after contract stabilization

StegVerse-Labs/admissibility-wiki
  -> publishes public portable governed return-path overview
  -> points to adapter, SDK, and Site verification commands
```

## Remaining files or modules to install

```text
None for adapter Goal 4 fixture-bound proof.
```

## Archive posture

This handoff preserves the current Goal 4 build state so the complete thread can be archived without needing additional context to continue. Live clone/Codespaces verification remains the final external confirmation surface.
