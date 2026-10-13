import unittest
from copy import deepcopy

from llm_adapter.system_boundary import default_adapter_system_boundary
from llm_adapter.system_boundary_binding import (
    bind_system_boundary_declaration,
    verify_system_boundary_binding,
)


def sample_payload():
    return {
        "session_id": "session-001",
        "adapter_result": {"decision": "DEFER"},
        "commitment_request": {"status": "PENDING"},
        "execution_handoff": {"status": "DISABLED"},
    }


class SystemBoundaryBindingTests(unittest.TestCase):
    def test_binds_declaration_and_deterministic_reference_without_mutating_source(self):
        source = sample_payload()
        bound = bind_system_boundary_declaration(
            source,
            config=default_adapter_system_boundary(
                session_ref="session://session-001",
                receipt_refs=("receipt://adapter/session-001",),
            ),
            declaration_id="sbd-session-001",
            generated_at="2026-07-14T12:00:00Z",
        )

        assert "system_boundary_declaration" not in source
        assert bound["system_boundary_declaration"]["system_id"] == "stegverse-llm-adapter"
        assert bound["system_boundary_declaration_ref"]["algorithm"] == "sha256"
        assert bound["system_boundary_declaration_ref"]["authorizing"] is False
        assert verify_system_boundary_binding(bound) == []


    def test_identical_inputs_produce_identical_reference(self):
        kwargs = {
            "config": default_adapter_system_boundary(receipt_refs=("receipt://adapter/001",)),
            "declaration_id": "sbd-repeatable",
            "generated_at": "2026-07-14T12:00:00Z",
        }
        first = bind_system_boundary_declaration(sample_payload(), **kwargs)
        second = bind_system_boundary_declaration(sample_payload(), **kwargs)

        assert first["system_boundary_declaration_ref"]["digest"] == second["system_boundary_declaration_ref"]["digest"]


    def test_rejects_reserved_field_overwrite(self):
        payload = sample_payload()
        payload["system_boundary_declaration"] = {}

        with self.assertRaisesRegex(ValueError, "already contains"):
            bind_system_boundary_declaration(
                payload,
                config=default_adapter_system_boundary(),
                declaration_id="duplicate",
            )


    def test_verifier_rejects_digest_drift_and_authority_escalation(self):
        bound = bind_system_boundary_declaration(
            sample_payload(),
            config=default_adapter_system_boundary(),
            declaration_id="sbd-tamper",
            generated_at="2026-07-14T12:00:00Z",
        )
        tampered = deepcopy(bound)
        tampered["system_boundary_declaration"]["authority"]["model_has_execution_authority"] = True

        errors = verify_system_boundary_binding(tampered)
        assert "system_boundary_declaration_ref.digest mismatch" in errors
        assert "model_has_execution_authority must be false" in errors


    def test_verifier_rejects_receipt_reference_claim_escalation(self):
        bound = bind_system_boundary_declaration(
            sample_payload(),
            config=default_adapter_system_boundary(),
            declaration_id="sbd-ref-claim",
            generated_at="2026-07-14T12:00:00Z",
        )
        bound["system_boundary_declaration_ref"]["custody_transferred"] = True

        errors = verify_system_boundary_binding(bound)
        assert "system_boundary_declaration_ref.custody_transferred must be false" in errors


if __name__ == "__main__":
    unittest.main()
