# LLM Adapter Mirror Handoff

## Current source of truth

This file is the handoff source of truth for `StegVerse-org/LLM-adapter` until superseded.

## Active goal

Goal 6: StegVerse AI Entry provider boundary.

Goal 4 proved the micro-node governed return-path fixture. Goal 6 now adds the disabled-by-default provider comparison boundary needed by the StegVerse AI Entry Point without enabling live provider calls, credentials, external authority, or receipt claims.

## Goal 6 proof path

```text
Site AI Entry request
-> LLM-adapter provider boundary
-> disabled provider comparison declarations
-> non-authoritative comparison placeholders
-> return-path preserving response surface
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

## Installed for Goal 4

```text
docs/MICRO_NODE_RETURN_PATH.md
examples/micro_node_return_path/request.json
examples/micro_node_return_path/governed_return.json
scripts/verify_micro_node_return_path.py
tests/test_micro_node_return_path.py
```

## Installed for Goal 6 on current build branch

```text
docs/AI_ENTRY_PROVIDER_BOUNDARY.md
llm_adapter/ai_entry_provider_boundary.py
scripts/verify_ai_entry_provider_boundary.py
tests/test_ai_entry_provider_boundary.py
scripts/verify_goal4.py updated to include Goal 6 boundary checks
```

## Required invariant

```text
provider_output_is_authority == false
comparison_only == true
live_provider_call_enabled == false
credential_surface_enabled == false
provider_secret_required_for_tests == false
receipt_capture_required_before_live_activation == true
commitment_request_is_authority == false
execution_authority_granted == false
fixture_mode_default == true
returned_to_origin == true
```

## Canonical verification command

```bash
python scripts/verify_goal4.py
```

The aggregate verifier runs:

```bash
python scripts/verify_micro_node_return_path.py
python scripts/verify_ai_entry_provider_boundary.py
python -m pytest tests/test_micro_node_return_path.py -v
python -m pytest tests/test_ai_entry_provider_boundary.py -v
python -m pytest tests/ -v
```

## Downstream sync targets

```text
StegVerse-org/StegVerse-SDK
  -> validates micro-node request and governed return fixtures
  -> next target: SDK receipt capture boundary for AI Entry activation

StegVerse-Labs/Site
  -> AI Entry Point local-ready/live-disabled surface
  -> consumes provider comparison panes as comparison-only
```

## Remaining files or modules to install

Destination: `StegVerse-org/StegVerse-SDK`

```text
AI Entry SDK receipt capture boundary
```

Destination: governed backend service repo when selected

```text
HTTP endpoint wrapping Site API contract and adapter provider boundary
secret boundary for provider adapters
real receipt issuance service after governed activation
```

## Archive posture

This handoff preserves the current Goal 6 provider-boundary build state so the complete thread can be archived without needing additional context to continue. Next work should start in `StegVerse-org/StegVerse-SDK` with SDK receipt capture boundary installation.
