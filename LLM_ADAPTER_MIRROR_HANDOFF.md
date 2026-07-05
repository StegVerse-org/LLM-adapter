# LLM Adapter Mirror Handoff

## Current source of truth

This file is the handoff source of truth for `StegVerse-org/LLM-adapter` until superseded.

## Active goal

Goal 7: bounded free-tier trust activation for the StegVerse governed LLM entry point.

Goal 4 proved the micro-node governed return-path fixture. Goal 6 provided the adapter-side pieces needed by the StegVerse AI Entry Point: provider comparison boundary, backend response scaffold, pure endpoint function, and service wrapper scaffold. Goal 7 now adds the free-tier trust policy and quota evaluation boundary so a public user can build confidence through bounded live governed inquiries rather than static demonstration material.

## Goal 6 proof path

```text
Site AI Entry request
-> LLM-adapter endpoint wrapper
-> backend response scaffold
-> provider comparison boundary
-> preview metadata
-> response shape for Site
```

## Goal 7 trust path

```text
public user inquiry
-> bounded free-tier quota envelope
-> governed LLM adapter request
-> transition receipt inspection
-> limited replay / reconstruction window
-> upgrade only for scale, retention, connectors, premium models, or API depth
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

## Installed for Goal 6

```text
docs/AI_ENTRY_PROVIDER_BOUNDARY.md
llm_adapter/ai_entry_provider_boundary.py
llm_adapter/ai_entry_backend_service.py
llm_adapter/ai_entry_endpoint.py
llm_adapter/ai_entry_service_wrapper.py
scripts/verify_ai_entry_provider_boundary.py
scripts/verify_ai_entry_backend_service.py
scripts/verify_ai_entry_endpoint.py
scripts/verify_ai_entry_service_wrapper.py
tests/test_ai_entry_provider_boundary.py
tests/test_ai_entry_backend_service.py
tests/test_ai_entry_backend_preview_marker.py
tests/test_ai_entry_endpoint.py
tests/test_ai_entry_service_wrapper.py
scripts/verify_goal4.py updated to include Goal 6 checks
```

## Installed for Goal 7

```text
docs/FREE_TIER_TRUST_POLICY.md
examples/free_tier_trust_policy.json
llm_adapter/free_tier_quota.py
scripts/verify_free_tier_quota.py
tests/test_free_tier_quota.py
```

## Required invariant

```text
provider_output_is_authority == false
comparison_only == true
live_provider_call_enabled == false
credential_surface_enabled == false
provider_secret_required_for_tests == false
receipt_capture_preview_only == true
endpoint_side_effects_performed == false
service_wrapper_live_calls_enabled == false
fixture_mode_default == true
returned_to_origin == true
free_tier_is_bounded_live_use == true
static_demo_is_sufficient_trust_proof == false
quota_allow_is_admissibility == false
quota_allow_is_execution_authority == false
upgrade_changes_admissibility_requirements == false
```

## Canonical verification command

```bash
python scripts/verify_goal4.py
python scripts/verify_free_tier_quota.py
python -m pytest tests/test_free_tier_quota.py -v
```

The existing aggregate verifier still includes:

```bash
python scripts/verify_micro_node_return_path.py
python scripts/verify_ai_entry_provider_boundary.py
python scripts/verify_ai_entry_backend_service.py
python scripts/verify_ai_entry_endpoint.py
python scripts/verify_ai_entry_service_wrapper.py
python -m pytest tests/test_micro_node_return_path.py -v
python -m pytest tests/test_ai_entry_provider_boundary.py -v
python -m pytest tests/test_ai_entry_backend_service.py -v
python -m pytest tests/test_ai_entry_endpoint.py -v
python -m pytest tests/test_ai_entry_service_wrapper.py -v
python -m pytest tests/ -v
```

## Downstream sync targets

```text
StegVerse-Labs/Site
  -> can consume the endpoint-shaped AI Entry response contract
  -> should later display the free-tier trust envelope after Site mirror validation is clean

StegVerse-org/StegVerse-SDK
  -> contains the SDK receipt-capture preview boundary
  -> should later ingest quota/receipt/replay policy metadata
```

## Remaining files or modules to install

```text
StegVerse-org/LLM-adapter:
  - receipt export limit contract
  - replay/reconstruction limit contract
  - Site response metadata for free-tier availability
  - optional aggregate verifier wiring into scripts/verify_goal4.py after confirming no Goal 4 naming conflict

StegVerse-Labs/Site:
  - public LLM page section for bounded live trust tier
  - checker coverage after active Site mirror guard path is complete

StegVerse-org/StegVerse-SDK:
  - quota/receipt/replay metadata ingestion contract
```

## Archive posture

This handoff preserves the Goal 7 bounded free-tier trust activation state so the complete thread can be archived without needing additional context to continue. Next work should add the receipt export and replay/reconstruction limit contracts in `StegVerse-org/LLM-adapter`, then mirror the public-facing summary to `StegVerse-Labs/Site` after the current Site mirror validation task is clean.
