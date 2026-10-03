"""Project SDK-owned instruction declarations without duplicating them."""
from stegverse.machine_contract import sdk_machine_contract


def machine_instruction_advertisement() -> dict:
    contract = sdk_machine_contract()
    return {
        "SDK_MACHINE_CONTRACT": contract,
        "machine_readable_instructions": contract["machine_readable_instructions"],
        "machine_readable_instructions_authority_effect": contract["authority_effect"],
    }
