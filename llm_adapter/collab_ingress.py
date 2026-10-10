"""Bind collaborative-ingress surfaces to the SDK's published manifest routes.

Existing owner: SDK-MANIFEST-COLLAB-INGRESS-CONFORMANCE-001, with
LLMA-DECLARED-PATH-CONFORMANCE-368.

HIL intake, Ecosystem Chat and VA-scoped chat each arrive here as a request on
an HTTP surface. None of those surfaces decides processing. Each translates its
request into the SDK's own processor request for one published route, builds a
manifest with the SDK builder, and hands that manifest to
`stegverse.manifest_execution.execute_manifest` through `sdk_boundary`. The
route the manifest declares is the only thing that selects processing: a
caller's route field, a keyword hint or this adapter cannot.

What comes back is the SDK's disposition, carried rather than replaced. Until
the canonical organization boundary resolves, that disposition is FAIL_CLOSED
`CANONICAL_ORGANIZATION_INGRESS_ENDPOINT_NOT_RESOLVED`, and that is the correct
answer: this module never manufactures an ALLOW. A VA-scoped request outside
its manifest-declared scope is refused by the SDK as DENY before any handoff.

No credential is read here, from the environment or anywhere else, and no
network connection is opened. A surface that would need a credential after an
admitted manifest and has no TV/TVC-sourced binding in this repository returns
FAIL_CLOSED `TVC_CREDENTIAL_SOURCE_NOT_BOUND` (see `credential_not_bound`).
Master Records is non-gating.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from . import sdk_boundary
from .governed_manifest_ingress import NON_ALLOW_FIELDS

OWNER_TASK_ID = "SDK-MANIFEST-COLLAB-INGRESS-CONFORMANCE-001"
OWNING_EXISTING_GOAL = "LLMA-DECLARED-PATH-CONFORMANCE-368"
DISPOSITION_SCHEMA = "stegverse.collab-ingress-disposition.v1"
SOURCE_FRAMEWORK = "stegverse-llm-adapter"
SUBMIT_MODE = "TEST"

HIL_INTAKE = "hil_intake"
ECOSYSTEM_CHAT = "ecosystem_chat"
VA_SCOPED_CHAT = "va_scoped_chat"

#: Published route id and processor-request schema for each capability. These
#: name the SDK's routes; they do not describe them. The SDK builder resolves
#: the route declaration and refuses a request that does not fit it.
ROUTES: Mapping[str, Mapping[str, str]] = {
    HIL_INTAKE: {"route_id": "stegverse.route.hil-intake.v1",
                 "request_schema": "stegverse.hil-intake-request/v1"},
    ECOSYSTEM_CHAT: {"route_id": "stegverse.route.ecosystem-chat.v1",
                     "request_schema": "stegverse.ecosystem-chat-request/v1"},
    VA_SCOPED_CHAT: {"route_id": "stegverse.route.va-scoped-chat.v1",
                     "request_schema": "stegverse.va-scoped-chat-request/v1"},
}

CANONICAL_BOUNDARY_NOT_RESOLVED = "CANONICAL_ORGANIZATION_INGRESS_ENDPOINT_NOT_RESOLVED"
TVC_CREDENTIAL_SOURCE_NOT_BOUND = "TVC_CREDENTIAL_SOURCE_NOT_BOUND"
MANIFEST_NOT_ADMITTED = "COLLAB_INGRESS_MANIFEST_NOT_ADMITTED"

#: HTTP status a surface answers each disposition with. The body always
#: carries the disposition itself; the status only keeps HTTP clients honest.
HTTP_STATUS = {"ALLOW": 200, "REVIEW": 202, "DENY": 403, "FAIL_CLOSED": 503}


def digest(value: Any) -> str:
    """`sha256:` digest of canonical JSON, or of raw bytes."""
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
    else:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def surface_standing(surface: str) -> dict[str, Any]:
    """The standing this surface declares for its own crossing.

    Explicit generation-1 genesis, re-declared on every call. It is structural
    standing, not authenticated standing, and grants nothing.
    """
    return {"node_endpoint": {"node_id": f"llm-adapter:{surface}", "recognized": True},
            "generation": 1, "predecessor": None}


class ManifestNotAdmitted(ValueError):
    """The SDK builder refused the translated request; nothing was submitted."""


def build(capability: str, processor_request: Mapping[str, Any], *,
          source_output_id: str, data: Any) -> dict[str, Any]:
    """Build the manifest for one published route, or raise the SDK's refusal."""
    if capability not in ROUTES:
        raise ManifestNotAdmitted(f"no published collaborative-ingress route for {capability}")
    result = sdk_boundary.build({"arguments": {
        "data": data,
        "source_framework": SOURCE_FRAMEWORK,
        "source_output_id": source_output_id,
        "processor_request": dict(processor_request),
        "process": capability,
    }})
    if result.get("accepted") is not True:
        raise ManifestNotAdmitted(str(result.get("sdk_rejection") or "manifest_not_built"))
    manifest = result["manifest"]
    processing = manifest.get("processing") if isinstance(manifest, Mapping) else None
    if not isinstance(processing, Mapping) or processing.get("route_id") != ROUTES[capability]["route_id"]:
        # The builder returned a resolution (e.g. capability development
        # requested) rather than a manifest on the published route.
        raise ManifestNotAdmitted("manifest_does_not_select_published_route:" + capability)
    return manifest


def _body(*, surface: str, capability: str, disposition: str,
          manifest: Mapping[str, Any] | None, boundary: Mapping[str, Any] | None,
          non_allow: Mapping[str, Any] | None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": DISPOSITION_SCHEMA,
        "surface": surface,
        "capability": capability,
        "route_id": ROUTES[capability]["route_id"],
        "disposition": disposition,
        "manifest_bound_before_processing": True,
        "processing_selected_by": "MANIFEST_DECLARED_ROUTE",
        "caller_route_fields_select_processing": False,
        "keyword_hints_select_processing": False,
        "canonical_entrypoint": sdk_boundary.CANONICAL_ENTRYPOINT,
        "handed_off": bool(boundary and boundary.get("handed_off") is True),
        "manifest_sha256": digest(manifest) if manifest is not None else None,
        "credential_read_from_environment": False,
        "network_call_performed_by_adapter": False,
        "master_records_gating": False,
        "local_receipt_is_organization_observation": False,
        "owner_task_id": OWNER_TASK_ID,
        "authority_effect": "NONE_TRANSPORT_ONLY",
        "sdk_boundary": dict(boundary) if boundary is not None else None,
    }
    if disposition != "ALLOW":
        body.update({key: (non_allow or {}).get(key) for key in NON_ALLOW_FIELDS})
    body["disposition_sha256"] = digest(body)
    return body


def refused(surface: str, capability: str, reason: str) -> dict[str, Any]:
    """FAIL_CLOSED for a request the SDK builder would not turn into a manifest."""
    return _body(surface=surface, capability=capability, disposition="FAIL_CLOSED",
                 manifest=None, boundary=None, non_allow={
                     "failure_code": MANIFEST_NOT_ADMITTED,
                     "failed_predicate": reason,
                     "required_evidence_or_repair": "a request the SDK builder admits on " + ROUTES[capability]["route_id"],
                     "retry_entrypoint": "the same surface",
                     "next_attempt": "correct the field the SDK named and resubmit",
                     "owning_existing_goal": OWNING_EXISTING_GOAL,
                 })


def submit(manifest: Mapping[str, Any], *, surface: str, capability: str) -> dict[str, Any]:
    """Hand the manifest to the SDK's canonical entrypoint and carry its disposition."""
    boundary = sdk_boundary.submit({"manifest": dict(manifest), "mode": SUBMIT_MODE,
                                    "standing_evidence": surface_standing(surface)})
    disposition = str(boundary.get("disposition") or "FAIL_CLOSED")
    return _body(surface=surface, capability=capability, disposition=disposition,
                 manifest=manifest, boundary=boundary, non_allow=boundary)


def execute(capability: str, processor_request: Mapping[str, Any], *, surface: str,
            source_output_id: str, data: Any) -> dict[str, Any]:
    """Build, then submit. A refused build is FAIL_CLOSED and submits nothing."""
    try:
        manifest = build(capability, processor_request,
                         source_output_id=source_output_id, data=data)
    except ManifestNotAdmitted as exc:
        return refused(surface, capability, str(exc))
    return submit(manifest, surface=surface, capability=capability)


def credential_not_bound(admitted: Mapping[str, Any], *, credential: str) -> dict[str, Any]:
    """FAIL_CLOSED after an admitted manifest when the credential has no TV/TVC source.

    The adapter does not fall back to the environment. The SDK disposition the
    surface received is kept beside this one so neither is lost.
    """
    body = {key: value for key, value in admitted.items() if key != "disposition_sha256"}
    body.update({
        "disposition": "FAIL_CLOSED",
        "failure_code": TVC_CREDENTIAL_SOURCE_NOT_BOUND,
        "failed_predicate": f"TV_TVC_SOURCED_CREDENTIAL_BOUND:{credential}",
        "required_evidence_or_repair": f"bind {credential} to a TV/TVC-sourced credential path; environment credentials are not read",
        "retry_entrypoint": "the same surface",
        "next_attempt": "resubmit once the TV/TVC credential binding exists",
        "owning_existing_goal": OWNING_EXISTING_GOAL,
        "sdk_disposition": admitted.get("disposition"),
    })
    body["disposition_sha256"] = digest(body)
    return body


def http_status(body: Mapping[str, Any]) -> int:
    return HTTP_STATUS.get(str(body.get("disposition")), 503)


__all__ = [
    "OWNER_TASK_ID", "OWNING_EXISTING_GOAL", "DISPOSITION_SCHEMA", "ROUTES",
    "HIL_INTAKE", "ECOSYSTEM_CHAT", "VA_SCOPED_CHAT",
    "CANONICAL_BOUNDARY_NOT_RESOLVED", "TVC_CREDENTIAL_SOURCE_NOT_BOUND", "MANIFEST_NOT_ADMITTED",
    "ManifestNotAdmitted", "build", "submit", "execute", "refused", "credential_not_bound",
    "surface_standing", "http_status", "digest",
]
