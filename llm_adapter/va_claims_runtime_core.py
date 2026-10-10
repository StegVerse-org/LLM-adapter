"""VA Claims Chat (VACC): manifest-bound transport on stegverse.route.va-scoped-chat.v1.

Existing owner: SDK-MANIFEST-COLLAB-INGRESS-CONFORMANCE-001, with
LLMA-DECLARED-PATH-CONFORMANCE-368.

VACC is a VA-scoped specialization of Ecosystem Chat. A turn is translated into
the SDK's `stegverse.va-scoped-chat-request/v1` with this deployment's VA scope
policy declared in the manifest (`policy_id`, `va_ref`, `allowed_topics`), built
with the SDK builder and handed to `stegverse.manifest_execution.execute_manifest`
through `sdk_boundary`. The SDK evaluates the scope: a topic outside
`allowed_topics` is a governed DENY before any handoff. Otherwise, until the
canonical organization boundary resolves, the disposition is FAIL_CLOSED
`CANONICAL_ORGANIZATION_INGRESS_ENDPOINT_NOT_RESOLVED`.

The keyword classifier only populates the draft's `requested_topic`. No local
answer is generated, no local model is called, no TVC route receipt file or
other environment input is read, no usage is attributed, and no repo-local
receipt closes the turn -- so none can be mislabelled as an Organization
observation. Master Records is non-gating.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any

from pydantic import BaseModel, Field

from . import collab_ingress

SCHEMA = "stegverse.va_claims.runtime/v1"
OWNING_EXISTING_GOAL = "LLMA-DECLARED-PATH-CONFORMANCE-368"
RETRY_ENTRYPOINT = "POST /api/va-claims/v1/chat"
SURFACE = "va-claims-chat"
NON_ALLOW_FIELDS = (
    "failure_code",
    "failed_predicate",
    "required_evidence_or_repair",
    "retry_entrypoint",
    "owning_existing_goal",
    "next_attempt",
)

ROUTE_KEYWORDS = (
    ("urgent_safety", ("suicide", "kill myself", "hurt myself", "crisis", "immediate danger")),
    ("home_loan", ("home loan", "va loan", "mortgage", "certificate of eligibility", "coe")),
    ("education", ("gi bill", "education benefit", "school benefit", "tuition", "chapter 33", "chapter 35")),
    ("health_care", ("va health care", "healthcare eligibility", "enroll in va health", "medical care")),
    ("community_care", ("community care", "outside va doctor", "referral authorization", "community provider")),
    ("pharmacy_billing", ("pharmacy", "prescription", "copay", "billing", "medical bill")),
    ("vre", ("vr&e", "vre", "vocational rehabilitation", "chapter 31")),
    ("caregiver_family", ("caregiver", "dependent", "spouse benefit", "family benefit")),
    ("burial_memorial", ("burial", "cemetery", "memorial", "headstone")),
    ("appeal_or_supplemental_claim", ("appeal", "supplemental claim", "higher-level review", "board appeal", "denial")),
    ("effective_date", ("effective date", "back pay", "retroactive")),
    ("rating_criteria", ("rating criteria", "diagnostic code", "percentage", "disability rating")),
    ("cp_examination", ("c&p", "compensation and pension", "exam")),
    ("lay_statement", ("lay statement", "buddy statement", "personal statement")),
    ("private_record_collection", ("private medical record", "private records", "civilian doctor record")),
    ("procedural_filing", ("file a claim", "submit a claim", "526ez", "21-526ez")),
    ("evidence_requirement", ("evidence", "what do i need", "documents needed", "proof")),
    ("service_connection", ("service connection", "secondary condition", "nexus", "in service", "aggravation")),
)

DEFAULT_TOPIC = "claim_type"

#: This deployment's VA scope, declared in every manifest it builds. It is
#: policy, not a caller input: a request cannot widen it.
VA_SCOPE_POLICY = {
    "policy_id": "stegverse.vacc.va-scope.v1",
    "va_ref": "StegVerse-org/LLM-adapter:va_claim_assistant",
    "allowed_topics": [route for route, _terms in ROUTE_KEYWORDS] + [DEFAULT_TOPIC],
}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: str | None = Field(default=None, max_length=160)
    route_scope: str = Field(default="VA_CLAIMS_CHAT", max_length=64)
    requested_capability: str = Field(default="COORDINATED_VA_RESOURCES_LLM", max_length=64)
    source_policy: str = Field(default="ADMITTED_OFFICIAL_VA_ONLY", max_length=64)
    private_document_context: bool = False
    filing_requested: bool = False
    authority_required: bool = True
    receipt_required: bool = True
    transition_identity: dict[str, Any] | None = None
    #: Optional topic the caller asks about. It populates the manifest draft
    #: only; the manifest-declared VA scope policy decides whether it is in
    #: scope, and the manifest route selects processing.
    requested_topic: str | None = Field(default=None, min_length=1, max_length=64)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def non_allow(failure_code: str, failed_predicate: str, required_evidence_or_repair: str, *,
              next_attempt: str = "retry the turn once the failed predicate holds",
              disposition: str = "FAIL_CLOSED", **detail: Any) -> dict[str, Any]:
    """A refused or failed turn, stated as the six fields a caller can act on."""
    return {
        "schema": SCHEMA,
        "disposition": disposition,
        "failure_code": failure_code,
        "failed_predicate": failed_predicate,
        "required_evidence_or_repair": required_evidence_or_repair,
        "retry_entrypoint": RETRY_ENTRYPOINT,
        "owning_existing_goal": OWNING_EXISTING_GOAL,
        "next_attempt": next_attempt,
        **detail,
        "authority_effect": False,
        "activation_effect": False,
    }


def non_allow_from_exception(exc: BaseException) -> dict[str, Any]:
    """The six-field disposition for a turn that raised before it could close."""
    code = str(exc) or type(exc).__name__
    return non_allow(
        code,
        "va_claims_turn_preconditions_hold",
        "correct the request or runtime input named by failure_code",
        error_class=type(exc).__name__,
    )


def readiness_record() -> dict[str, Any]:
    """What a VACC turn is bound to. Reads no environment input."""
    return {
        "state": "MANIFEST_BOUND_TRANSPORT",
        "schema": SCHEMA,
        "route_id": collab_ingress.ROUTES[collab_ingress.VA_SCOPED_CHAT]["route_id"],
        "canonical_entrypoint": "stegverse.manifest_execution.execute_manifest",
        "va_scope_policy": dict(VA_SCOPE_POLICY),
        "va_scope_policy_source": "MANIFEST_DECLARED",
        "processing_selected_by": "MANIFEST_DECLARED_ROUTE",
        "keyword_classifier_role": "MANIFEST_DRAFT_TOPIC_HINT_ONLY",
        "source_policy": "ADMITTED_OFFICIAL_VA_ONLY",
        "turn_disposition_source": "SDK_MANIFEST_DISPOSITION",
        "local_receipt_is_organization_observation": False,
        "master_records_gating": False,
        "credential_requirement": "NONE",
        "github_token_required": False,
        "authority_effect": False,
        "activation_effect": False,
    }


def classify_route(question: str) -> str:
    """A keyword hint for the manifest draft's `requested_topic`.

    It never selects processing: the manifest route does, and the VA scope
    policy decides whether the topic is admitted.
    """
    normalized = re.sub(r"\s+", " ", question.lower()).strip()
    for route, terms in ROUTE_KEYWORDS:
        if any(term in normalized for term in terms):
            return route
    return "claim_type"


def va_scoped_chat_request(request: ChatRequest, *, session_id: str) -> dict[str, Any]:
    """The SDK's VA-scoped chat processor request for one turn."""
    return {
        "schema": collab_ingress.ROUTES[collab_ingress.VA_SCOPED_CHAT]["request_schema"],
        "session_ref": session_id,
        "message": request.message,
        "requested_topic": request.requested_topic or classify_route(request.message),
        "va_scope": {**VA_SCOPE_POLICY, "allowed_topics": list(VA_SCOPE_POLICY["allowed_topics"])},
    }


def execute_chat(request: ChatRequest) -> dict[str, Any]:
    """Bind the VA-scoped chat manifest and return the SDK disposition."""
    if request.private_document_context or request.filing_requested:
        raise RuntimeError("private_document_or_filing_route_not_active")
    if request.source_policy != "ADMITTED_OFFICIAL_VA_ONLY":
        raise RuntimeError("source_policy_not_admitted")
    session_id = request.session_id or f"va-session-{uuid.uuid4()}"
    transition = dict(request.transition_identity or {})
    va_request = va_scoped_chat_request(request, session_id=session_id)
    disposition = collab_ingress.execute(
        collab_ingress.VA_SCOPED_CHAT,
        va_request,
        surface=SURFACE,
        source_output_id=f"{SURFACE}:{session_id}:{stable_hash(request.model_dump())[:16]}",
        data={"message_sha256": collab_ingress.digest(request.message.encode("utf-8")),
              "va_scope_policy_id": VA_SCOPE_POLICY["policy_id"]},
    )
    result = {
        **disposition,
        "schema": SCHEMA,
        "collab_ingress_schema": disposition["schema"],
        # Kept for clients of the previous shape; nothing here is locally decided.
        "response": None,
        "session_id": session_id,
        "route": va_request["requested_topic"],
        "requested_topic": va_request["requested_topic"],
        "va_scope_policy_id": VA_SCOPE_POLICY["policy_id"],
        "citations": [],
        "transition_id": transition.get("transition_id"),
        "caller_transition_identity_is_manifest_identity": False,
        "turn_closed_on": "SDK_MANIFEST_DISPOSITION",
        "local_answer_generated": False,
        "local_model_called": False,
        "provider_usage_attributed": False,
        "authority_effect": False,
        "activation_effect": False,
        "filing_active": False,
        "private_document_context_used": False,
        "github_token_required": False,
        "credential_requirement": "NONE",
    }
    if result["disposition"] != "ALLOW":
        result["owning_existing_goal"] = result.get("owning_existing_goal") or OWNING_EXISTING_GOAL
    result["response_hash"] = stable_hash(result)
    return result
