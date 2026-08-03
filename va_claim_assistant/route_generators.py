#!/usr/bin/env python3
"""Governed route generators for the StegVerse VA Claim Assistant.

The generators produce source-grounded or sanitized-derived-context answer
records. They do not adjudicate, represent, diagnose, rate, sign, submit,
publish, or activate any claim capability.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

ROUTES = (
    "claim_type",
    "evidence_requirement",
    "service_connection",
    "rating_criteria",
    "effective_date",
    "appeal_or_supplemental_claim",
    "cp_examination",
    "document_organization",
    "lay_statement",
    "private_record_collection",
    "procedural_filing",
    "representation_referral",
    "urgent_safety",
)

AUTHORITY_RANK = {
    "CONTROLLING": 1,
    "OFFICIAL_OPERATIONAL": 2,
    "PROFESSIONAL_SUPPORT": 3,
    "EXPERIENTIAL": 4,
}

AUTHORITY_FLAGS = {
    "adjudication": False,
    "representation": False,
    "medical_opinion": False,
    "rating": False,
    "execution": False,
    "publication": False,
}

ALLOWED_REFERRAL_TRIGGERS = {
    "PRIOR_DENIAL",
    "EFFECTIVE_DATE_DISPUTE",
    "POSSIBLE_CUE",
    "SEVERANCE_OR_REDUCTION",
    "COMPLEX_SECONDARY_CAUSATION",
    "AGGRAVATION",
    "TDIU",
    "SMC",
    "CHARACTER_OF_DISCHARGE",
    "CONFLICTING_MEDICAL_OPINIONS",
    "APPEAL_DEADLINE",
    "URGENT_SAFETY",
}

TOP_LEVEL_ANSWER_KEYS = {
    "schema_version",
    "session_id",
    "question",
    "route",
    "claim_stage",
    "claim_theory",
    "capability_state",
    "propositions",
    "contradictions",
    "uncertainties",
    "referral_triggers",
    "authority_flags",
    "receipt_hash",
}

PROHIBITED_CONTEXT_KEYS = {
    "raw_document",
    "raw_documents",
    "raw_bytes",
    "document_bytes",
    "full_text",
    "ssn",
    "social_security_number",
    "veteran_name",
    "email",
    "phone",
    "address",
    "credential",
    "credentials",
    "access_token",
    "refresh_token",
    "password",
    "identity_proofing_artifact",
}

PII_PATTERNS = (
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"),
)

HEX64 = re.compile(r"^[a-f0-9]{64}$")


class RouteGenerationError(ValueError):
    """Base fail-closed route generation exception."""


class AuthorityResolutionRequired(RouteGenerationError):
    """A required admitted source is missing, stale, or superseded."""


class DocumentContextRequired(RouteGenerationError):
    """The route requires sanitized derived document context."""


class PrivacyBoundaryError(RouteGenerationError):
    """Sanitized context contains a prohibited field or direct identifier."""


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _source_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in registry.get("sources", []):
        source_id = item.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise AuthorityResolutionRequired("source_registry_invalid_source_id")
        if source_id in result:
            raise AuthorityResolutionRequired(f"duplicate_source_id:{source_id}")
        authority = item.get("authority_class")
        if authority not in AUTHORITY_RANK:
            raise AuthorityResolutionRequired(f"invalid_authority_class:{source_id}")
        result[source_id] = item
    return result


def _require_sources(registry: dict[str, Any], source_ids: tuple[str, ...]) -> list[dict[str, Any]]:
    sources = _source_map(registry)
    selected: list[dict[str, Any]] = []
    for source_id in source_ids:
        source = sources.get(source_id)
        if source is None or source.get("admitted") is not True:
            raise AuthorityResolutionRequired(f"required_admitted_source_unavailable:{source_id}")
        state = str(source.get("state", "")).upper()
        if source.get("superseded") is True or state in {"SUPERSEDED", "STALE", "REVOKED"}:
            raise AuthorityResolutionRequired(f"required_source_not_current:{source_id}")
        selected.append(source)
    selected.sort(key=lambda source: AUTHORITY_RANK[source["authority_class"]])
    return selected


def _support(source: dict[str, Any], retrieved_at: str) -> dict[str, Any]:
    return {
        "source_id": source["source_id"],
        "authority_class": source["authority_class"],
        "locator": source["url"],
        "retrieved_at": retrieved_at,
    }


PUBLIC_ROUTE_SPECS: dict[str, dict[str, Any]] = {
    "claim_type": {
        "claim_stage": "INTAKE_AND_ROUTE_SELECTION",
        "claim_theory": "UNDETERMINED",
        "sources": ("USC-TITLE-38", "VA-FORMS", "VA-EVIDENCE-NEEDED"),
        "propositions": (
            (
                "The appropriate claim lane depends on the benefit sought, prior decisions, and whether the veteran is presenting a new, increased, secondary, or review theory.",
                ("USC-TITLE-38", "VA-EVIDENCE-NEEDED"),
            ),
            (
                "The current official form and filing instructions should be verified before a package is prepared.",
                ("VA-FORMS",),
            ),
        ),
        "uncertainty": "No veteran-specific procedural history was supplied, so the system cannot select the final claim lane.",
        "referrals": (),
    },
    "evidence_requirement": {
        "claim_stage": "EVIDENCE_DEVELOPMENT",
        "claim_theory": "UNDETERMINED",
        "sources": ("VA-EVIDENCE-NEEDED", "VA-COMPENSATION-EVIDENCE"),
        "propositions": (
            (
                "Evidence requirements depend on the type and procedural posture of the disability claim.",
                ("VA-EVIDENCE-NEEDED",),
            ),
            (
                "A claimant should identify current disability or symptoms, the relevant in-service event or exposure, and evidence connecting the two when the applicable theory requires a nexus.",
                ("VA-COMPENSATION-EVIDENCE",),
            ),
        ),
        "uncertainty": "No veteran-specific records were supplied, so the response cannot determine which evidence is present or missing.",
        "referrals": (),
    },
    "service_connection": {
        "claim_stage": "ENTITLEMENT_THEORY_DEVELOPMENT",
        "claim_theory": "SERVICE_CONNECTION_UNDETERMINED",
        "sources": ("USC-TITLE-38", "ECFR-TITLE-38", "VA-EVIDENCE-NEEDED"),
        "propositions": (
            (
                "Service connection generally requires evidence addressing a current disability or persistent symptoms, an in-service event, injury, disease, or exposure, and a relationship under the applicable theory.",
                ("USC-TITLE-38", "ECFR-TITLE-38", "VA-EVIDENCE-NEEDED"),
            ),
            (
                "Claims Chat can organize the evidence and identify gaps, but it cannot create a diagnosis, medical nexus, or entitlement determination.",
                ("VA-EVIDENCE-NEEDED",),
            ),
        ),
        "uncertainty": "The applicable direct, secondary, presumptive, or aggravation theory cannot be selected without veteran-specific facts and records.",
        "referrals": (),
    },
    "rating_criteria": {
        "claim_stage": "RATING_EVIDENCE_ORGANIZATION",
        "claim_theory": "CONDITION_SPECIFIC_CRITERIA_REQUIRED",
        "sources": ("VA-RATING-SCHEDULE", "ECFR-TITLE-38"),
        "propositions": (
            (
                "VA disability evaluations use condition-specific criteria in the current Schedule for Rating Disabilities.",
                ("VA-RATING-SCHEDULE",),
            ),
            (
                "Claims Chat may organize evidence against current criteria but must not predict, promise, or optimize a disability percentage.",
                ("VA-RATING-SCHEDULE", "ECFR-TITLE-38"),
            ),
        ),
        "uncertainty": "No condition, diagnostic code, current criteria snapshot, or admitted veteran record was supplied.",
        "referrals": (),
    },
    "effective_date": {
        "claim_stage": "EFFECTIVE_DATE_REVIEW",
        "claim_theory": "DATE_ENTITLEMENT_UNDETERMINED",
        "sources": ("USC-TITLE-38", "ECFR-TITLE-38"),
        "propositions": (
            (
                "Effective-date rules depend on the claim type, filing history, facts found, and any applicable statutory or regulatory exception.",
                ("USC-TITLE-38", "ECFR-TITLE-38"),
            ),
            (
                "A specific effective date cannot be determined without the complete procedural record and the current controlling provisions.",
                ("USC-TITLE-38", "ECFR-TITLE-38"),
            ),
        ),
        "uncertainty": "The filing timeline, prior decisions, and facts-found record are not available.",
        "referrals": ("EFFECTIVE_DATE_DISPUTE",),
    },
    "appeal_or_supplemental_claim": {
        "claim_stage": "DECISION_REVIEW",
        "claim_theory": "REVIEW_LANE_UNDETERMINED",
        "sources": ("USC-TITLE-38", "ECFR-TITLE-38", "VA-FORMS"),
        "propositions": (
            (
                "Available decision-review lanes and their evidence rules depend on the decision and the review option selected.",
                ("USC-TITLE-38", "ECFR-TITLE-38"),
            ),
            (
                "The veteran should verify the current official form and the deadline stated in the decision notice before selecting a review lane.",
                ("VA-FORMS",),
            ),
        ),
        "uncertainty": "The decision date, notice, issues decided, and evidence posture were not supplied.",
        "referrals": ("PRIOR_DENIAL", "APPEAL_DEADLINE"),
    },
    "cp_examination": {
        "claim_stage": "EXAMINATION_PREPARATION",
        "claim_theory": "EXAM_SCOPE_UNDETERMINED",
        "sources": ("VA-M21-1", "VA-EVIDENCE-NEEDED"),
        "propositions": (
            (
                "A compensation and pension examination may be used to develop evidence relevant to a claim; the examiner does not grant benefits.",
                ("VA-M21-1", "VA-EVIDENCE-NEEDED"),
            ),
            (
                "The veteran should provide accurate information about history, symptoms, and functional effects, while Claims Chat makes no medical or rating determination.",
                ("VA-EVIDENCE-NEEDED",),
            ),
        ),
        "uncertainty": "The examination request, disability questionnaire, and relevant admitted records were not supplied.",
        "referrals": (),
    },
    "lay_statement": {
        "claim_stage": "LAY_EVIDENCE_PREPARATION",
        "claim_theory": "FIRSTHAND_OBSERVATION",
        "sources": ("VA-EVIDENCE-NEEDED", "VA-FORMS"),
        "propositions": (
            (
                "A lay statement may describe firsthand observations such as events, symptoms, frequency, duration, and functional effects.",
                ("VA-EVIDENCE-NEEDED", "VA-FORMS"),
            ),
            (
                "The statement should distinguish personal observation from a medical diagnosis or nexus opinion.",
                ("VA-EVIDENCE-NEEDED",),
            ),
        ),
        "uncertainty": "No draft statement, witness role, date range, or claimed event was supplied.",
        "referrals": (),
    },
    "private_record_collection": {
        "claim_stage": "PRIVATE_RECORD_DEVELOPMENT",
        "claim_theory": "RECORD_SOURCE_IDENTIFICATION",
        "sources": ("VA-EVIDENCE-NEEDED", "VA-FORMS"),
        "propositions": (
            (
                "Private records should be identified by provider and date range, and the current VA form or submission method should be verified.",
                ("VA-EVIDENCE-NEEDED", "VA-FORMS"),
            ),
            (
                "Only records authorized by the veteran should be requested or transmitted; Claims Chat must not collect provider credentials.",
                ("VA-FORMS",),
            ),
        ),
        "uncertainty": "Provider identities, date ranges, authorization state, and record availability were not supplied.",
        "referrals": (),
    },
    "procedural_filing": {
        "claim_stage": "PACKAGE_PREPARATION",
        "claim_theory": "FILING_CHANNEL_UNDETERMINED",
        "sources": ("VA-FORMS", "VA-EVIDENCE-NEEDED"),
        "propositions": (
            (
                "Filing requires the current form or authorized submission channel and the evidence appropriate to the claim type.",
                ("VA-FORMS", "VA-EVIDENCE-NEEDED"),
            ),
            (
                "Claims Chat may prepare a draft package but cannot sign or submit it without the veteran's exact-package authorization and an admitted transport.",
                ("VA-FORMS",),
            ),
        ),
        "uncertainty": "The claim type, current form, veteran confirmation, signature state, package hash, and transport authorization are not established.",
        "referrals": (),
    },
    "representation_referral": {
        "claim_stage": "REPRESENTATION_REFERRAL",
        "claim_theory": "ACCREDITATION_VERIFICATION_REQUIRED",
        "sources": ("USC-TITLE-38", "ECFR-TITLE-38"),
        "propositions": (
            (
                "Representation in VA matters is limited by applicable law and regulation to authorized persons or organizations.",
                ("USC-TITLE-38", "ECFR-TITLE-38"),
            ),
        ),
        "uncertainty": "The current Site registry does not include a dedicated official accreditation lookup source, so Claims Chat cannot verify a specific representative.",
        "referrals": (),
    },
    "urgent_safety": {
        "claim_stage": "URGENT_SAFETY_REFERRAL",
        "claim_theory": "IMMEDIATE_HUMAN_SUPPORT_REQUIRED",
        "sources": ("VA-CRISIS-LINE",),
        "propositions": (
            (
                "An urgent safety concern must be handled through immediate human emergency or crisis support rather than claim-processing guidance.",
                ("VA-CRISIS-LINE",),
            ),
        ),
        "uncertainty": "Claims Chat cannot assess or resolve an emergency.",
        "referrals": ("URGENT_SAFETY",),
    },
}


def _public_answer(*, route: str, question: str, registry: dict[str, Any], session_id: str) -> dict[str, Any]:
    spec = PUBLIC_ROUTE_SPECS[route]
    required = _require_sources(registry, spec["sources"])
    by_id = {source["source_id"]: source for source in required}
    retrieved_at = _now()
    propositions: list[dict[str, Any]] = []
    for index, (text, support_ids) in enumerate(spec["propositions"], start=1):
        propositions.append(
            {
                "proposition_id": f"P{index}",
                "text": text,
                "kind": "PROCEDURAL_GUIDANCE",
                "support": [_support(by_id[source_id], retrieved_at) for source_id in support_ids],
            }
        )
    record: dict[str, Any] = {
        "schema_version": "1.0.0",
        "session_id": session_id,
        "question": question,
        "route": route,
        "claim_stage": spec["claim_stage"],
        "claim_theory": spec["claim_theory"],
        "capability_state": "SOURCE_GROUNDED_ASSISTANT",
        "propositions": propositions,
        "contradictions": [],
        "uncertainties": [
            {
                "uncertainty_id": "U1",
                "description": spec["uncertainty"],
                "material": True,
            }
        ],
        "referral_triggers": list(spec["referrals"]),
        "authority_flags": dict(AUTHORITY_FLAGS),
    }
    record["receipt_hash"] = canonical_hash(record)
    return record


def _walk_context(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.strip().lower()
            if normalized in PROHIBITED_CONTEXT_KEYS:
                raise PrivacyBoundaryError(f"prohibited_context_field:{path}.{key}")
            _walk_context(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_context(child, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in PII_PATTERNS:
            if pattern.search(value):
                raise PrivacyBoundaryError(f"direct_identifier_detected:{path}")


def validate_sanitized_document_context(context: dict[str, Any]) -> None:
    if not isinstance(context, dict):
        raise DocumentContextRequired("sanitized_document_context_required")
    _walk_context(context)
    required = {
        "session_id",
        "source_document_hashes",
        "record_facts",
        "separately_labeled_inferences",
        "contradictions",
        "missing_evidence",
        "privacy_state",
        "consent_receipt",
        "derived_record_hash",
    }
    missing = sorted(required - set(context))
    if missing:
        raise DocumentContextRequired(f"sanitized_context_missing:{','.join(missing)}")
    if context["privacy_state"] not in {"PII_REDACTED_VERIFIED", "SANITIZED_DERIVED_CONTEXT"}:
        raise PrivacyBoundaryError("privacy_state_not_verified")
    hashes = context["source_document_hashes"]
    if not isinstance(hashes, list) or not hashes or any(not isinstance(item, str) or not HEX64.fullmatch(item) for item in hashes):
        raise PrivacyBoundaryError("source_document_hashes_invalid")
    if not isinstance(context["derived_record_hash"], str) or not HEX64.fullmatch(context["derived_record_hash"]):
        raise PrivacyBoundaryError("derived_record_hash_invalid")
    consent = context["consent_receipt"]
    if (
        not isinstance(consent, dict)
        or consent.get("state") != "VALID"
        or not isinstance(consent.get("receipt_hash"), str)
        or not HEX64.fullmatch(consent["receipt_hash"])
    ):
        raise PrivacyBoundaryError("consent_receipt_invalid")
    facts = context["record_facts"]
    if not isinstance(facts, list) or not facts:
        raise DocumentContextRequired("record_facts_required")
    fact_ids: set[str] = set()
    for fact in facts:
        if not isinstance(fact, dict):
            raise PrivacyBoundaryError("record_fact_invalid")
        fact_id = fact.get("fact_id")
        text = fact.get("text")
        document_hash = fact.get("document_hash")
        page_anchor = fact.get("page_anchor")
        if not all(isinstance(value, str) and value for value in (fact_id, text, page_anchor)):
            raise PrivacyBoundaryError("record_fact_fields_invalid")
        if fact_id in fact_ids:
            raise PrivacyBoundaryError(f"duplicate_fact_id:{fact_id}")
        if document_hash not in hashes:
            raise PrivacyBoundaryError(f"record_fact_unknown_document_hash:{fact_id}")
        fact_ids.add(fact_id)
    for inference in context["separately_labeled_inferences"]:
        if not isinstance(inference, dict):
            raise PrivacyBoundaryError("inference_invalid")
        support_ids = inference.get("supporting_fact_ids")
        if (
            not isinstance(inference.get("inference_id"), str)
            or not isinstance(inference.get("text"), str)
            or not isinstance(support_ids, list)
            or not support_ids
            or any(item not in fact_ids for item in support_ids)
        ):
            raise PrivacyBoundaryError("inference_support_invalid")
    for contradiction in context["contradictions"]:
        if not isinstance(contradiction, dict):
            raise PrivacyBoundaryError("contradiction_invalid")
        related = contradiction.get("related_fact_ids")
        if (
            not isinstance(contradiction.get("contradiction_id"), str)
            or not isinstance(contradiction.get("description"), str)
            or contradiction.get("status") not in {"UNRESOLVED", "RESOLVED", "REQUIRES_HUMAN_REVIEW"}
            or not isinstance(related, list)
            or not related
            or any(item not in fact_ids for item in related)
        ):
            raise PrivacyBoundaryError("contradiction_fields_invalid")
    for missing_item in context["missing_evidence"]:
        if (
            not isinstance(missing_item, dict)
            or not isinstance(missing_item.get("missing_id"), str)
            or not isinstance(missing_item.get("description"), str)
            or not isinstance(missing_item.get("material"), bool)
        ):
            raise PrivacyBoundaryError("missing_evidence_invalid")


def _document_answer(*, question: str, session_id: str, document_context: dict[str, Any] | None) -> dict[str, Any]:
    if document_context is None:
        raise DocumentContextRequired("sanitized_document_context_required")
    validate_sanitized_document_context(document_context)
    if document_context["session_id"] != session_id:
        raise PrivacyBoundaryError("document_context_session_mismatch")
    retrieved_at = _now()
    facts = document_context["record_facts"]
    fact_to_proposition: dict[str, str] = {}
    propositions: list[dict[str, Any]] = []
    for index, fact in enumerate(facts, start=1):
        proposition_id = f"F{index}"
        fact_to_proposition[fact["fact_id"]] = proposition_id
        propositions.append(
            {
                "proposition_id": proposition_id,
                "text": fact["text"],
                "kind": "USER_RECORD_FACT",
                "support": [
                    {
                        "source_id": f"USER-RECORD-{fact['document_hash'][:12]}",
                        "authority_class": "USER_RECORD",
                        "locator": "sanitized-derived-context",
                        "retrieved_at": retrieved_at,
                        "document_hash": fact["document_hash"],
                        "page_anchor": fact["page_anchor"],
                    }
                ],
            }
        )
    for index, inference in enumerate(document_context["separately_labeled_inferences"], start=1):
        support = []
        for fact_id in inference["supporting_fact_ids"]:
            fact = next(item for item in facts if item["fact_id"] == fact_id)
            support.append(
                {
                    "source_id": f"USER-RECORD-{fact['document_hash'][:12]}",
                    "authority_class": "USER_RECORD",
                    "locator": "sanitized-derived-context",
                    "retrieved_at": retrieved_at,
                    "document_hash": fact["document_hash"],
                    "page_anchor": fact["page_anchor"],
                }
            )
        propositions.append(
            {
                "proposition_id": f"I{index}",
                "text": inference["text"],
                "kind": "INFERENCE",
                "support": support,
            }
        )
    contradictions = [
        {
            "contradiction_id": item["contradiction_id"],
            "description": item["description"],
            "status": item["status"],
            "related_proposition_ids": [fact_to_proposition[fact_id] for fact_id in item["related_fact_ids"]],
        }
        for item in document_context["contradictions"]
    ]
    uncertainties = [
        {
            "uncertainty_id": item["missing_id"],
            "description": item["description"],
            "material": item["material"],
        }
        for item in document_context["missing_evidence"]
    ]
    record: dict[str, Any] = {
        "schema_version": "1.0.0",
        "session_id": session_id,
        "question": question,
        "route": "document_organization",
        "claim_stage": "DOCUMENT_EVIDENCE_ORGANIZATION",
        "claim_theory": "DERIVED_CONTEXT_ONLY",
        "capability_state": "DOCUMENT_AWARE_ASSISTANT",
        "propositions": propositions,
        "contradictions": contradictions,
        "uncertainties": uncertainties,
        "referral_triggers": [],
        "authority_flags": dict(AUTHORITY_FLAGS),
    }
    record["receipt_hash"] = canonical_hash(record)
    return record


def build_route_answer(
    *,
    route: str,
    question: str,
    registry: dict[str, Any],
    session_id: str,
    document_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if route not in ROUTES:
        raise RouteGenerationError(f"unsupported_route:{route}")
    if not isinstance(question, str) or not question.strip():
        raise RouteGenerationError("question_is_required")
    if route == "document_organization":
        return _document_answer(question=question, session_id=session_id, document_context=document_context)
    return _public_answer(route=route, question=question, registry=registry, session_id=session_id)


def validate_answer(record: dict[str, Any], registry: dict[str, Any]) -> None:
    required_keys = {
        "schema_version",
        "session_id",
        "question",
        "route",
        "capability_state",
        "propositions",
        "contradictions",
        "uncertainties",
        "referral_triggers",
        "authority_flags",
        "receipt_hash",
    }
    missing = required_keys - set(record)
    if missing:
        raise ValueError(f"answer_schema_missing_required:{','.join(sorted(missing))}")
    extra = set(record) - TOP_LEVEL_ANSWER_KEYS
    if extra:
        raise ValueError(f"answer_schema_additional_properties:{','.join(sorted(extra))}")
    if not isinstance(record.get("session_id"), str) or not record["session_id"]:
        raise ValueError("answer_session_id_invalid")
    if not isinstance(record.get("question"), str) or not record["question"]:
        raise ValueError("answer_question_invalid")
    route = record.get("route")
    if route not in ROUTES:
        raise ValueError("answer_route_invalid")
    if record.get("capability_state") not in {
        "BOUNDED_PROCEDURAL_ASSISTANT",
        "SOURCE_GROUNDED_ASSISTANT",
        "DOCUMENT_AWARE_ASSISTANT",
        "GOVERNED_CLAIM_SESSION",
    }:
        raise ValueError("answer_capability_state_invalid")
    flags = record.get("authority_flags")
    if not isinstance(flags, dict) or set(flags) != set(AUTHORITY_FLAGS):
        raise ValueError("authority_flags_invalid")
    if any(flags.values()):
        raise ValueError("authority escalation rejected")
    admitted = {item["source_id"]: item for item in registry.get("sources", []) if item.get("admitted") is True}
    propositions = record.get("propositions")
    if not isinstance(propositions, list):
        raise ValueError("answer_propositions_invalid")
    proposition_ids: set[str] = set()
    for proposition in propositions:
        proposition_id = proposition.get("proposition_id")
        if not isinstance(proposition_id, str) or not proposition_id or proposition_id in proposition_ids:
            raise ValueError("proposition_id_invalid")
        proposition_ids.add(proposition_id)
        if proposition.get("kind") not in {"SOURCE_FACT", "USER_RECORD_FACT", "INFERENCE", "PROCEDURAL_GUIDANCE"}:
            raise ValueError(f"proposition_kind_invalid:{proposition_id}")
        support_items = proposition.get("support")
        if not isinstance(support_items, list) or not support_items:
            raise ValueError(f"unsupported proposition: {proposition_id}")
        for support in support_items:
            authority = support.get("authority_class")
            if authority == "USER_RECORD":
                if (
                    route != "document_organization"
                    or not isinstance(support.get("document_hash"), str)
                    or not HEX64.fullmatch(support["document_hash"])
                    or not isinstance(support.get("page_anchor"), str)
                    or not support["page_anchor"]
                ):
                    raise ValueError("user_record_support_invalid")
            else:
                source = admitted.get(support.get("source_id"))
                if source is None:
                    raise ValueError(f"non-admitted source: {support.get('source_id')}")
                if source["authority_class"] != authority:
                    raise ValueError("source authority mismatch")
    for contradiction in record.get("contradictions", []):
        related = contradiction.get("related_proposition_ids")
        if (
            contradiction.get("status") not in {"UNRESOLVED", "RESOLVED", "REQUIRES_HUMAN_REVIEW"}
            or not isinstance(related, list)
            or not related
            or any(item not in proposition_ids for item in related)
        ):
            raise ValueError("contradiction_invalid")
    uncertainties = record.get("uncertainties")
    if not isinstance(uncertainties, list):
        raise ValueError("uncertainties_invalid")
    for item in uncertainties:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("uncertainty_id"), str)
            or not item["uncertainty_id"]
            or not isinstance(item.get("description"), str)
            or not item["description"]
            or not isinstance(item.get("material"), bool)
        ):
            raise ValueError("uncertainty_invalid")
    referrals = record.get("referral_triggers")
    if not isinstance(referrals, list) or any(item not in ALLOWED_REFERRAL_TRIGGERS for item in referrals):
        raise ValueError("referral_trigger_invalid")
    expected = canonical_hash({key: value for key, value in record.items() if key != "receipt_hash"})
    if record.get("receipt_hash") != expected:
        raise ValueError("receipt hash mismatch")
