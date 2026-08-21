from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .sovereign_local_model_binding import execute_verified_local_model
from va_claim_assistant.route_generators import (
    AUTHORITY_FLAGS,
    AuthorityResolutionRequired,
    build_route_answer,
    canonical_hash,
    validate_answer,
)

SCHEMA = "stegverse.va_claims.runtime/v1"
ALLOWED_SOURCE_DOMAINS = {
    "va.gov", "www.va.gov", "benefits.va.gov", "www.benefits.va.gov",
    "uscode.house.gov", "www.ecfr.gov", "ecfr.gov", "knowva.ebenefits.va.gov",
    "www.uscourts.cavc.gov", "uscourts.cavc.gov",
    "www.federalregister.gov", "federalregister.gov",
    "veteranscrisisline.net", "www.veteranscrisisline.net",
}
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

BROAD_ROUTE_SOURCES = {
    "urgent_safety": ("VA-CRISIS-LINE",),
    "home_loan": ("VA-HOME-LOANS",),
    "education": ("VA-EDUCATION",),
    "health_care": ("VA-HEALTH-CARE",),
    "community_care": ("VA-COMMUNITY-CARE",),
    "pharmacy_billing": ("VA-HEALTH-BILLING",),
    "vre": ("VA-VRE",),
    "caregiver_family": ("VA-FAMILY-CAREGIVER",),
    "burial_memorial": ("VA-BURIAL-MEMORIAL",),
}

BROAD_ROUTE_GUIDANCE = {
    "urgent_safety": "Treat this as an urgent safety request. Direct the veteran to immediate official crisis support and do not continue ordinary benefits guidance until immediate safety is addressed.",
    "home_loan": "VA-backed home loan eligibility usually starts with confirming eligibility and obtaining a Certificate of Eligibility (COE). A lender still makes the loan and applies credit and underwriting requirements. Ask whether the veteran wants to buy, refinance, or only check eligibility.",
    "education": "VA education benefits depend on the program and eligibility history. Start by identifying whether the veteran is asking about the Post-9/11 GI Bill, Montgomery GI Bill, DEA, or another education benefit.",
    "health_care": "VA health care access depends on enrollment and eligibility. Start by determining whether the veteran is trying to enroll, schedule care, understand eligibility, or resolve an access problem.",
    "community_care": "VA Community Care generally requires VA authorization before covered community treatment. If the community provider cannot locate the authorization, treat that as an authorization workflow problem rather than asking the veteran to solve a provider-side technical issue.",
    "pharmacy_billing": "VA pharmacy and billing questions should be routed by whether the issue is a prescription/refill, copay, insurance billing, or a charge for authorized community care.",
    "vre": "Veteran Readiness and Employment (VR&E) is a separate VA benefit program. Start by identifying whether the veteran is asking about eligibility, application, evaluation, training, employment services, or independent-living support.",
    "caregiver_family": "VA caregiver and family benefits vary by program. Start by identifying whether the question concerns caregiver support, dependents, survivor benefits, or another family benefit.",
    "burial_memorial": "VA burial and memorial benefits vary by eligibility and requested service. Start by identifying whether the veteran or family needs burial allowance information, a national cemetery, a headstone or marker, or memorial benefits.",
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


def load_object_env(name: str) -> dict[str, Any]:
    path_value = os.getenv(name, "").strip()
    if not path_value:
        raise RuntimeError(f"{name.lower()}_missing")
    path = Path(path_value).expanduser().resolve()
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{name.lower()}_not_object")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_tvc_route(route: dict[str, Any], proof: dict[str, Any]) -> str:
    if route.get("state") != "ROUTE_ADMITTED":
        raise RuntimeError("tvc_route_not_admitted")
    if route.get("route_authority") != "StegVerse-Labs/TVC":
        raise RuntimeError("tvc_route_authority_mismatch")
    if route.get("runtime_proof_hash") != stable_hash(proof):
        raise RuntimeError("tvc_runtime_proof_hash_mismatch")
    if route.get("credential_requirement") != "NONE":
        raise RuntimeError("tvc_credential_requirement_not_none")
    if route.get("github_token_required") is not False:
        raise RuntimeError("github_token_dependency_rejected")
    if route.get("third_party_execution_platform_required") is not False:
        raise RuntimeError("third_party_platform_dependency_rejected")
    if route.get("execution_authority") is not False or route.get("authority_effect") != "NONE":
        raise RuntimeError("tvc_authority_escalation_rejected")
    endpoint = str(route.get("endpoint") or "").strip().rstrip("/")
    if not endpoint:
        raise RuntimeError("tvc_route_endpoint_missing")
    return endpoint + "/v1/chat/completions"


def readiness_record() -> dict[str, Any]:
    registry = load_object_env("STEGVERSE_VA_SOURCE_REGISTRY_FILE")
    proof = load_object_env("STEGVERSE_CANONICAL_RUNTIME_PROOF_FILE")
    route_receipt = load_object_env("STEGVERSE_TVC_ROUTE_RECEIPT_FILE")
    validate_tvc_route(route_receipt, proof)
    if not registry.get("sources"):
        raise RuntimeError("va_source_registry_empty")
    return {
        "state": "READY",
        "schema": SCHEMA,
        "source_policy": "ADMITTED_OFFICIAL_VA_ONLY",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "authority_effect": False,
        "activation_effect": False,
    }


def classify_route(question: str) -> str:
    normalized = re.sub(r"\s+", " ", question.lower()).strip()
    for route, terms in ROUTE_KEYWORDS:
        if any(term in normalized for term in terms):
            return route
    return "claim_type"


def _admitted_source(registry: dict[str, Any], source_id: str) -> dict[str, Any]:
    for source in registry.get("sources", []):
        if source.get("source_id") == source_id and source.get("admitted") is True:
            url = str(source.get("url") or "")
            if not url.startswith("https://"):
                raise AuthorityResolutionRequired(f"source_url_invalid:{source_id}")
            host = url.split("/", 3)[2].lower()
            if host not in ALLOWED_SOURCE_DOMAINS:
                raise AuthorityResolutionRequired(f"source_domain_not_admitted:{source_id}")
            return source
    raise AuthorityResolutionRequired(f"required_admitted_source_unavailable:{source_id}")


def _build_broad_answer(*, route: str, question: str, registry: dict[str, Any], session_id: str) -> dict[str, Any]:
    sources = [_admitted_source(registry, source_id) for source_id in BROAD_ROUTE_SOURCES[route]]
    record: dict[str, Any] = {
        "schema_version": "1.0.0",
        "session_id": session_id,
        "question": question,
        "route": route,
        "claim_stage": "VA_BENEFIT_NAVIGATION",
        "claim_theory": "NOT_APPLICABLE",
        "capability_state": "SOURCE_GROUNDED_ASSISTANT",
        "propositions": [{
            "proposition_id": "P1",
            "text": BROAD_ROUTE_GUIDANCE[route],
            "kind": "PROCEDURAL_GUIDANCE",
            "support": [{
                "source_id": source["source_id"],
                "authority_class": source["authority_class"],
                "locator": source["url"],
                "retrieved_at": str(registry.get("last_verified") or ""),
            } for source in sources],
        }],
        "contradictions": [],
        "uncertainties": [],
        "referral_triggers": [],
        "authority_flags": dict(AUTHORITY_FLAGS),
    }
    record["receipt_hash"] = canonical_hash(record)
    return record


def _build_grounded_answer(*, route: str, question: str, registry: dict[str, Any], session_id: str) -> dict[str, Any]:
    if route in BROAD_ROUTE_SOURCES:
        return _build_broad_answer(route=route, question=question, registry=registry, session_id=session_id)
    record = build_route_answer(route=route, question=question, registry=registry, session_id=session_id)
    validate_answer(record, registry)
    return record


def _model_prompt(question: str, answer_record: dict[str, Any]) -> str:
    context = {
        "question": question,
        "route": answer_record["route"],
        "propositions": answer_record["propositions"],
        "contradictions": answer_record["contradictions"],
        "uncertainties": answer_record["uncertainties"],
    }
    return (
        "You are the conversational VA specialty renderer. Use only the admitted context below. "
        "Answer the veteran directly in plain language. Ask at most one useful follow-up question when it helps. "
        "Do not invent facts, diagnoses, nexus opinions, eligibility determinations, ratings, deadlines, or filing confirmations. "
        "Do not mention internal governance, runtimes, receipts, models, routes, or capability states. "
        "Keep the answer concise and user-focused. Context: " + json.dumps(context, sort_keys=True, ensure_ascii=False)
    )


def execute_chat(request: ChatRequest) -> dict[str, Any]:
    if request.private_document_context or request.filing_requested:
        raise RuntimeError("private_document_or_filing_route_not_active")
    if request.source_policy != "ADMITTED_OFFICIAL_VA_ONLY":
        raise RuntimeError("source_policy_not_admitted")
    session_id = request.session_id or f"va-session-{uuid.uuid4()}"
    transition = dict(request.transition_identity or {})
    transition_id = str(transition.get("transition_id") or f"va-transition-{uuid.uuid4()}")
    measurement_id = str(transition.get("event_id") or f"va-measurement-{uuid.uuid4()}")

    registry = load_object_env("STEGVERSE_VA_SOURCE_REGISTRY_FILE")
    proof = load_object_env("STEGVERSE_CANONICAL_RUNTIME_PROOF_FILE")
    route_receipt = load_object_env("STEGVERSE_TVC_ROUTE_RECEIPT_FILE")
    route = classify_route(request.message)
    answer_record = _build_grounded_answer(route=route, question=request.message.strip(), registry=registry, session_id=session_id)
    transport_endpoint = validate_tvc_route(route_receipt, proof)
    execution = execute_verified_local_model(
        runtime_proof=proof,
        endpoint=transport_endpoint,
        session_id=session_id,
        transition_id=transition_id,
        measurement_id=measurement_id,
        messages=[{"role": "user", "content": _model_prompt(request.message, answer_record)}],
    )
    text = execution.response.output.strip()
    if not text:
        raise RuntimeError("model_response_empty")
    receipt = dict(execution.binding_receipt)
    if receipt.get("provider_usage_custody_recorded") is not True:
        raise RuntimeError("provider_usage_custody_not_recorded")
    if receipt.get("provider_usage_reconstruction_pass") is not True:
        raise RuntimeError("provider_usage_reconstruction_not_pass")

    citations = []
    seen = set()
    for proposition in answer_record.get("propositions", []):
        for support in proposition.get("support", []):
            locator = support.get("locator")
            if locator and locator not in seen:
                seen.add(locator)
                citations.append({"source_id": support.get("source_id"), "authority_class": support.get("authority_class"), "url": locator})

    response = {
        "schema": SCHEMA,
        "response": text,
        "session_id": session_id,
        "route": route,
        "citations": citations[:4],
        "answer_receipt_hash": answer_record["receipt_hash"],
        "execution_receipt_hash": receipt.get("receipt_hash") or stable_hash(receipt),
        "provider_usage_custody_recorded": True,
        "provider_usage_reconstruction_pass": True,
        "authority_effect": False,
        "activation_effect": False,
        "filing_active": False,
        "private_document_context_used": False,
        "github_token_required": False,
        "credential_requirement": "NONE",
    }
    response["response_hash"] = stable_hash(response)
    return response
