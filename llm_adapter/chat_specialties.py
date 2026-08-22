"""Runtime-neutral specialty profiles layered on the canonical Ecosystem Chat LLM.

Specialties add context, source policy, pedagogy, and candidate tools. They do not
create a second LLM/provider runtime, custody path, or execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Tuple


class SpecialtyValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ChatSpecialtyProfile:
    schema: str
    specialty_id: str
    display_name: str
    purpose: str
    base_llm_profile: str
    inherits_full_llm_surface: bool
    input_modalities: Tuple[str, ...]
    context_policy: Mapping[str, Any]
    response_behaviors: Tuple[str, ...]
    candidate_tools: Tuple[Mapping[str, Any], ...]
    authority_policy: Mapping[str, bool]
    product_invariants: Mapping[str, Any]


REQUIRED_FALSE_AUTHORITIES = (
    "specialty_selection_is_execution_authority",
    "model_output_is_execution_authority",
    "tool_candidate_is_execution_authority",
    "provider_runtime_is_duplicated",
    "custody_path_is_duplicated",
)


def validate_specialty_manifest(manifest: Mapping[str, Any]) -> ChatSpecialtyProfile:
    if manifest.get("schema") != "stegverse.chat_specialty_profile.v1":
        raise SpecialtyValidationError("unsupported_specialty_schema")
    if manifest.get("base_llm_profile") != "ecosystem-chat-llm":
        raise SpecialtyValidationError("specialty_must_use_canonical_ecosystem_chat_llm")
    if manifest.get("inherits_full_llm_surface") is not True:
        raise SpecialtyValidationError("specialty_must_inherit_full_llm_surface")

    for field in ("specialty_id", "display_name", "purpose"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            raise SpecialtyValidationError(f"{field}_must_be_non_empty_string")

    modalities = manifest.get("input_modalities")
    if not isinstance(modalities, list) or not modalities or len(modalities) != len(set(modalities)):
        raise SpecialtyValidationError("input_modalities_must_be_unique_non_empty_array")
    if any(item not in {"text", "image", "file", "audio"} for item in modalities):
        raise SpecialtyValidationError("unsupported_input_modality")

    behaviors = manifest.get("response_behaviors")
    if not isinstance(behaviors, list) or not behaviors or len(behaviors) != len(set(behaviors)):
        raise SpecialtyValidationError("response_behaviors_must_be_unique_non_empty_array")

    context_policy = manifest.get("context_policy")
    if not isinstance(context_policy, Mapping) or not context_policy:
        raise SpecialtyValidationError("context_policy_must_be_non_empty_object")

    tools = manifest.get("candidate_tools")
    if not isinstance(tools, list):
        raise SpecialtyValidationError("candidate_tools_must_be_array")
    for tool in tools:
        if not isinstance(tool, Mapping):
            raise SpecialtyValidationError("candidate_tool_must_be_object")
        if tool.get("execution_state") != "CANDIDATE_ONLY_NOT_EXECUTED":
            raise SpecialtyValidationError("candidate_tool_cannot_claim_execution")
        if tool.get("execution_authority") is not False:
            raise SpecialtyValidationError("candidate_tool_execution_authority_must_be_false")

    authority = manifest.get("authority_policy")
    if not isinstance(authority, Mapping):
        raise SpecialtyValidationError("authority_policy_must_be_object")
    for field in REQUIRED_FALSE_AUTHORITIES:
        if authority.get(field) is not False:
            raise SpecialtyValidationError(f"authority_policy_must_be_false:{field}")

    invariants = manifest.get("product_invariants")
    if not isinstance(invariants, Mapping) or not invariants:
        raise SpecialtyValidationError("product_invariants_must_be_non_empty_object")
    if invariants.get("single_shared_conversation") is not True:
        raise SpecialtyValidationError("specialty_must_share_conversation")
    if invariants.get("single_shared_provider_runtime") is not True:
        raise SpecialtyValidationError("specialty_must_share_provider_runtime")

    if manifest["specialty_id"] == "mathematics-educator":
        if context_policy.get("source_image_state") != "source_image":
            raise SpecialtyValidationError("math_source_image_state_required")
        if context_policy.get("interpreted_transcription_state") != "interpreted_mathematical_transcription":
            raise SpecialtyValidationError("math_transcription_state_required")
        if context_policy.get("transcription_is_source_fact") is not False:
            raise SpecialtyValidationError("math_transcription_must_remain_interpretation")

    return ChatSpecialtyProfile(
        schema=manifest["schema"],
        specialty_id=manifest["specialty_id"],
        display_name=manifest["display_name"],
        purpose=manifest["purpose"],
        base_llm_profile=manifest["base_llm_profile"],
        inherits_full_llm_surface=True,
        input_modalities=tuple(modalities),
        context_policy=dict(context_policy),
        response_behaviors=tuple(behaviors),
        candidate_tools=tuple(dict(tool) for tool in tools),
        authority_policy={key: bool(value) for key, value in authority.items()},
        product_invariants=dict(invariants),
    )


def load_specialty(path: Path) -> ChatSpecialtyProfile:
    with path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, Mapping):
        raise SpecialtyValidationError("specialty_root_must_be_object")
    return validate_specialty_manifest(manifest)
