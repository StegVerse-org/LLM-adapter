"""Project SDK-owned instruction declarations without duplicating them."""
from copy import deepcopy
from stegverse.machine_contract import sdk_machine_contract


def machine_instruction_advertisement() -> dict:
    contract = sdk_machine_contract()
    profiles = deepcopy(contract["machine_readable_instructions"])
    for profile in profiles.values():
        # This advertisement describes the existing adapter ingress only.
        # Native SDK callers retain their independently projected SDK path.
        profile["receiving_owner"] = "llm_adapter.governed_manifest_ingress"
        profile["submission_api"] = "llm_adapter.governed_manifest_ingress.process_manifest"
        # Standing is enforced by the adapter boundary, not by the SDK-owned
        # native projection. Preserve that boundary requirement explicitly on
        # the adapter-scoped copy without mutating SDK_MACHINE_CONTRACT.
        profile["direct_bypass_without_standing"] = "FAIL_CLOSED"
        profile["enclosed_validation_is_canonical"] = False
    return {
        "SDK_MACHINE_CONTRACT": contract,
        "machine_readable_instructions": profiles,
        "machine_readable_instructions_authority_effect": contract["authority_effect"],
    }
