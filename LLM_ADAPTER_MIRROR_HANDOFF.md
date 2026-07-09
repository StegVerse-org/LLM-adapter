# LLM Adapter Mirror Handoff

## Current source of truth

This file is the handoff source of truth for `StegVerse-org/LLM-adapter` until superseded.

## Active goal

Goal 8: HPS adapter consumption.

Goal 7 bounded free-tier trust activation is preserved below as completed prior context. Goal 8 adds consumption of SDK HPS route decisions before adapter-mediated consequence.

## Goal 8 upstream inputs

```text
Admissible-Existence/HPS
  -> HPS formalism and verifiers activated
  -> HPS Verify #12 observed successful by user screenshot
  -> 15 tests passed

StegVerse-org/StegVerse-SDK
  -> HPS SDK route contract installed
  -> SDK workflow observation pending/no run reported by connector

master-records/orchestration
  -> HPS ecosystem orchestration cycle installed
  -> LLM-adapter HPS participant record installed
```

## Goal 8 route consumption rule

```text
Adapter output is not execution.
SDK route ALLOW is not execution authority.
HPS route DENY or FAIL_CLOSED must block adapter-mediated consequence.
```

## Installed for Goal 8

```text
docs/HPS_ADAPTER_CONSUMPTION.md
examples/hps_adapter_route_allowed.json
examples/hps_adapter_route_denied.json
examples/hps_adapter_route_fail_closed.json
scripts/verify_hps_adapter_consumption.py
tests/test_hps_adapter_consumption.py
LLM_ADAPTER_MIRROR_HANDOFF.md updated
```

## Goal 8 verification commands

```bash
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_allowed.json
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_denied.json
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_fail_closed.json
pytest tests/test_hps_adapter_consumption.py -v
```

## Goal 8 downstream sync targets

```text
master-records/orchestration
  -> update LLM-adapter participant from PENDING to INSTALLED

StegVerse-Labs/Site
  -> consume HPS visualization status and adapter consumption state

StegVerse-Labs/admissibility-wiki
  -> explain adapter HPS route consumption after Site/adapter records align
```

---

## Preserved Goal 7 context

Goal 7: bounded free-tier trust activation for the StegVerse governed LLM entry point.

Goal 4 proved the micro-node governed return-path fixture. Goal 6 provided the adapter-side pieces needed by the StegVerse AI Entry Point: provider comparison boundary, backend response scaffold, pure endpoint function, and service wrapper scaffold. Goal 7 added the free-tier trust policy, quota evaluation boundary, receipt/replay/reconstruction limit boundary, Site-facing response metadata, aggregate verification wiring, README/status documentation, and machine-readable capability manifest support so a public user can build confidence through bounded live governed inquiries rather than static demonstration material.

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
-> Site-visible free-tier trust metadata
-> transition receipt inspection
-> bounded receipt export / replay / reconstruction limits
-> machine-readable capability discovery
-> aggregate verifier coverage
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
llm_adapter/free_tier_limits.py
llm_adapter/ai_entry_backend_service.py updated with free_tier_trust metadata
adapter.capabilities.json updated with free-tier trust fields
scripts/verify_free_tier_quota.py
scripts/verify_free_tier_limits.py
scripts/verify_ai_entry_free_tier_metadata.py
scripts/verify_free_tier_capability_manifest.py
scripts/verify_goal4.py updated to include Goal 7 checks
tests/test_free_tier_quota.py
tests/test_free_tier_limits.py
tests/test_ai_entry_free_tier_trust_metadata.py
README.md updated with free-tier trust boundary
docs/ACTIVATION_STATUS.md updated with Goal 7 status
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
site_metadata_exposes_free_tier_trust == true
capability_manifest_exposes_free_tier_trust == true
aggregate_verifier_covers_goal7 == true
quota_allow_is_admissibility == false
quota_allow_is_execution_authority == false
limit_allow_is_admissibility == false
limit_allow_is_execution_authority == false
replay_grants_commit_time_standing == false
reconstruction_grants_commit_time_standing == false
receipt_export_is_permanent_retention == false
upgrade_changes_admissibility_requirements == false
hps_route_decision_is_execution_authority == false
adapter_output_is_execution_authority == false
route_deny_blocks_consequence == true
route_fail_closed_blocks_consequence == true
route_allow_only_allows_next_boundary == true
```

## Canonical verification command

```bash
python scripts/verify_goal4.py
```

Additional Goal 8 verification:

```bash
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_allowed.json
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_denied.json
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_fail_closed.json
python -m pytest tests/test_hps_adapter_consumption.py -v
```

## Remaining files or modules to install

```text
StegVerse-org/LLM-adapter:
  - no known Goal 8 adapter-side files remain at this handoff

master-records/orchestration:
  - update LLM-adapter HPS participant record to INSTALLED

StegVerse-Labs/Site:
  - public HPS visualization / ecosystem chat integration after Site handoff review
```

## Archive posture

This handoff preserves the Goal 8 HPS adapter consumption state and prior Goal 7 bounded free-tier trust activation state so the complete thread can be archived without needing additional context to continue.
