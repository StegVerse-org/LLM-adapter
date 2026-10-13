import unittest
import base64
import hashlib
import json

from llm_adapter.southbound_sdk_return import (
    SouthboundSDKReturnError,
    admit_intr_egress,
    prepare_sdk_return_for_intr,
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def binding_bytes():
    value = {
        "schema": "stegverse.sdk.publisher-return-binding/v1",
        "direction": "SOUTH",
        "manifest_receipt_id": "MR-ABC123",
        "initiator": {"class": "external_framework", "ref": "framework-1"},
        "return_projection": {"mode": "ALL", "transition_classes": []},
        "publisher": {"return_sha256": "sha256:" + "a" * 64},
        "egress": {
            "final_stegverse_transition_surface": "LLM_ADAPTER",
            "transport": "INTERLOCK_INTR",
            "far_side_transition_required": True,
            "destination_profile": "MIR",
        },
        "communication_state": "READY_FOR_FINAL_STEGVERSE_EGRESS_TRANSITION",
        "final_stegverse_transition_observed": False,
        "interlock_intr_egress_observed": False,
        "far_side_transition_observed": False,
        "communication_complete": False,
        "authority_effect": "NONE",
    }
    digest = hashlib.sha256(canonical(value)).hexdigest()
    value["binding_sha256"] = "sha256:" + digest
    return canonical(value)


class SouthboundSdkReturnTests(unittest.TestCase):
    def test_prepares_exact_sdk_binding_for_intr_without_claiming_completion(self):
        raw = binding_bytes()
        result = prepare_sdk_return_for_intr(raw, transition_id="south-001")
        assert result["state"] == "FINAL_STEGVERSE_SIDE_TRANSITION_PREPARED"
        assert result["transition_surface"] == "LLM_ADAPTER"
        assert result["destination_profile"] == "MIR"
        assert result["intr_handoff"]["destination_profile"] == "MIR"
        assert result["final_stegverse_transition_surface_reached"] is True
        assert result["interlock_intr_egress_admitted"] is False
        assert result["far_side_transition_observed"] is False
        assert result["communication_complete"] is False
        assert result["authority_effect"] == "NONE"
        assert base64.b64decode(result["intr_handoff"]["payload_base64"]) == raw
        assert result["intr_handoff"]["sdk_binding_sha256"] == hashlib.sha256(raw).hexdigest()


    def test_rejects_binding_for_other_egress_surface(self):
        value = json.loads(binding_bytes())
        value["egress"]["final_stegverse_transition_surface"] = "DIRECT_SDK"
        with self.assertRaisesRegex(SouthboundSDKReturnError, "not addressed"):
            prepare_sdk_return_for_intr(canonical(value), transition_id="south-001")


    def test_rejects_missing_destination_profile(self):
        value = json.loads(binding_bytes())
        del value["egress"]["destination_profile"]
        with self.assertRaisesRegex(SouthboundSDKReturnError, "destination_profile required"):
            prepare_sdk_return_for_intr(canonical(value), transition_id="south-001")


    def test_rejects_early_completion_claim(self):
        value = json.loads(binding_bytes())
        value["communication_complete"] = True
        with self.assertRaisesRegex(SouthboundSDKReturnError, "boundary invalid"):
            prepare_sdk_return_for_intr(canonical(value), transition_id="south-001")


    def test_intr_admission_requires_exact_sdk_binding_hash_and_destination_profile(self):
        transition = prepare_sdk_return_for_intr(binding_bytes(), transition_id="south-001")
        admitted = admit_intr_egress(
            transition,
            disposition="ALLOW",
            egress_receipt_hash="b" * 64,
            admitted_sdk_binding_sha256=transition["intr_handoff"]["sdk_binding_sha256"],
        )
        assert admitted["state"] == "EGRESS_ADMITTED"
        assert admitted["transition_authority"] == "Interlock/InTr"
        assert admitted["destination_profile"] == "MIR"
        assert admitted["far_side_transition_observed"] is False
        assert admitted["communication_complete"] is False


    def test_intr_admission_rejects_destination_profile_substitution(self):
        transition = prepare_sdk_return_for_intr(binding_bytes(), transition_id="south-001")
        transition["intr_handoff"]["destination_profile"] = "NOT-MIR"
        with self.assertRaisesRegex(SouthboundSDKReturnError, "destination_profile binding mismatch"):
            admit_intr_egress(
                transition,
                disposition="ALLOW",
                egress_receipt_hash="b" * 64,
                admitted_sdk_binding_sha256=transition["intr_handoff"]["sdk_binding_sha256"],
            )


    def test_intr_admission_rejects_wrong_binding_hash(self):
        transition = prepare_sdk_return_for_intr(binding_bytes(), transition_id="south-001")
        with self.assertRaisesRegex(SouthboundSDKReturnError, "exact SDK return"):
            admit_intr_egress(
                transition,
                disposition="ALLOW",
                egress_receipt_hash="b" * 64,
                admitted_sdk_binding_sha256="c" * 64,
            )


if __name__ == "__main__":
    unittest.main()
