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
