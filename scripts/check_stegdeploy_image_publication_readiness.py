#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "stegdeploy-image.yml"
RECEIPT = ROOT / "receipts" / "stegdeploy-image-publication.json"
STATUS = ROOT / "status" / "stegdeploy-image-publication-readiness.json"

REQUIRED_WORKFLOW_MARKERS = (
    "Verify published main image pull",
    "Write publication or blocker receipt",
    '"schema": "stegdeploy.image-publication.v2"',
    '"state": "PUBLISHED" if published else "BLOCKED"',
    '"consumer_pull_verified"',
    '"package_visibility_asserted": False',
    "Retain publication evidence on main",
    "Enforce successful publication after retaining evidence",
)


def main() -> int:
    failures: list[str] = []
    if not WORKFLOW.exists():
        failures.append("missing canonical StegDeploy image workflow")
        workflow_text = ""
    else:
        workflow_text = WORKFLOW.read_text(encoding="utf-8")
        for marker in REQUIRED_WORKFLOW_MARKERS:
            if marker not in workflow_text:
                failures.append(f"workflow missing marker: {marker}")
        if "schedule:" in workflow_text:
            failures.append("scheduled workflow is not permitted outside StegVerse-Healer")

    receipt = json.loads(RECEIPT.read_text(encoding="utf-8")) if RECEIPT.exists() else None
    receipt_schema = receipt.get("schema") if receipt else None
    receipt_state = receipt.get("state") if receipt else None
    digest = receipt.get("digest") if receipt else None
    consumer_pull_verified = receipt.get("consumer_pull_verified") if receipt else False

    publication_ready = (
        receipt_schema == "stegdeploy.image-publication.v2"
        and receipt_state == "PUBLISHED"
        and isinstance(digest, str)
        and digest.startswith("sha256:")
        and consumer_pull_verified is True
        and not failures
    )

    status = {
        "schema": "stegdeploy.image-publication-readiness.v1",
        "repository": "StegVerse-org/LLM-adapter",
        "workflow": ".github/workflows/stegdeploy-image.yml",
        "receipt": "receipts/stegdeploy-image-publication.json",
        "workflow_contract_valid": not failures,
        "observed_receipt_schema": receipt_schema,
        "observed_receipt_state": receipt_state,
        "observed_digest": digest,
        "consumer_pull_verified": consumer_pull_verified is True,
        "state": "READY" if publication_ready else "BLOCKED",
        "blockers": failures + ([] if receipt_schema == "stegdeploy.image-publication.v2" else ["current retained receipt predates v2 publication contract"]) + ([] if consumer_pull_verified is True else ["fresh consumer pull verification not retained"]),
        "provider_execution_authorized": False,
        "persistent_deployment_authorized": False,
        "custody_authorized": False,
        "site_activation_authorized": False,
        "manual_user_action_required": False,
    }
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if failures:
        print("STEGDEPLOY IMAGE PUBLICATION READINESS: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"STEGDEPLOY IMAGE PUBLICATION READINESS: {status['state']}")
    for blocker in status["blockers"]:
        print(f"- {blocker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
