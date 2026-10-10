"""Keep test runs out of this repository's real transition ledger.

The ingress boundary appends a receipt for every admitted registration, and the
route that reaches it is exercised across several test files. Without this, a
suite run writes into the ledger root a deployed node uses -- which is how a
test ends up writing runtime reality, and how the node ingress chain ends up
carrying receipts for nodes that never existed.

The redirect is autouse and session-scoped rather than opt-in: a test that
reaches the boundary without remembering to redirect is exactly the case that
caused this, so there is nothing to remember.
"""
import os
import tempfile

import pytest

LEDGER_ROOT = "STEGVERSE_REPO_LEDGER_ROOT"


@pytest.fixture(scope="session", autouse=True)
def repository_ledger_root():
    with tempfile.TemporaryDirectory(prefix="llm-adapter-test-ledger-") as root:
        previous = os.environ.get(LEDGER_ROOT)
        os.environ[LEDGER_ROOT] = root
        try:
            yield root
        finally:
            if previous is None:
                os.environ.pop(LEDGER_ROOT, None)
            else:
                os.environ[LEDGER_ROOT] = previous


@pytest.fixture
def organization_admits_manifests(monkeypatch):
    """Stand in for an organization that admitted the manifest and recorded it.

    In this repository the canonical organization boundary is never resolved,
    so a collaborative-ingress surface correctly returns FAIL_CLOSED. Tests of
    what a surface does *after* an organization-admitted ALLOW use this far-side
    double. It still validates every manifest with the real SDK contract and
    records what it was handed, so a test can prove the manifest was bound
    before anything else ran.
    """
    from llm_adapter import sdk_boundary

    handed: list[dict] = []

    def admitted(payload):
        manifest = dict(payload["manifest"])
        verdict = sdk_boundary.validate({"manifest": manifest})
        assert verdict["accepted"] is True, verdict
        handed.append(manifest)
        return {
            "schema": sdk_boundary.BOUNDARY_SCHEMA,
            "surface": "MANIFEST_SUBMIT",
            "handed_off": True,
            "disposition": "ALLOW",
            "canonical_entrypoint": sdk_boundary.CANONICAL_ENTRYPOINT,
            "envelope": {"governance_state": "ALLOW", "organization_receipt_observed": True,
                         "reached_sdk_runtime": True, "consequence_executed": False},
            "test_double": "ORGANIZATION_ADMITTED_FAR_SIDE",
            "authority_effect": "NONE_HANDOFF_ONLY",
        }

    monkeypatch.setattr(sdk_boundary, "submit", admitted)
    return handed
