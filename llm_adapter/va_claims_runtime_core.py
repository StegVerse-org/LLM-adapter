from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
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
    "urgent_safety": "This needs immediate attention. Use the official Veterans Crisis Line now rather than continuing an ordinary benefits workflow.",
    "home_loan": "VA-backed home loan eligibility usually starts with confirming eligibility and obtaining a Certificate of Eligibility (COE). A lender still makes the loan and applies credit and underwriting requirements.",
    "education": "VA education benefits depend on the specific program and your eligibility history. The first useful step is identifying which education benefit applies to what you want to do.",
    "health_care": "VA health care access depends on enrollment and eligibility. The next step depends on whether you are trying to enroll, schedule care, understand eligibility, or fix an access problem.",
    "community_care": "VA Community Care generally requires VA authorization before covered community treatment. If a community provider cannot locate an authorization VA says it issued, that is an authorization-workflow problem that should be traced rather than pushed back onto you as a technical task.",
    "pharmacy_billing": "VA pharmacy and billing problems are handled differently depending on whether this is a prescription or refill, a VA copay, insurance billing, or a charge connected to authorized community care.",
    "vre": "Veteran Readiness and Employment (VR&E) is a separate VA benefit program covering several kinds of employment, training, education, and independent-living support.",
    "caregiver_family": "VA caregiver and family benefits vary by program, so the fastest path is to identify whether this concerns caregiver support, dependents, survivor benefits, or another family benefit.",
    "burial_memorial": "VA burial and memorial benefits vary by eligibility and the service needed, including burial allowances, national cemeteries, headstones or markers, and memorial benefits.",
}

FOLLOW_UPS = {
    "home_loan": "Are you buying a home, refinancing one you already own, or just checking whether you qualify?",
    "education": "Are you trying to choose a benefit, apply for one, or fix a problem with benefits you already have?",
    "health_care": "Are you trying to enroll, get an appointment, understand eligibility, or resolve a problem with care?",
    "community_care": "Is the problem that VA says it sent an authorization but the community provider cannot find it?",
    "pharmacy_billing": "Is this about a prescription, a copay, insurance billing, or a community-care charge?",
    "vre": "Are you checking eligibility, applying, working with a counselor, or trying to resolve a current VR&E problem?",
    "caregiver_family": "Which benefit are you trying to get help with: caregiver support, a dependent or spouse benefit, survivor benefits, or something else?",
    "burial_memorial": "Do you need help with a burial allowance, cemetery eligibility, a headstone or marker, or another memorial benefit?",
    "appeal_or_supplemental_claim": "What decision are you trying to challenge, and when was the decision dated?",
    "effective_date": "Is this about the effective date on a decision you already received, or a claim you are preparing now?",
    "rating_criteria": "Which condition or diagnostic code are you trying to understand?",
    "cp_examination": "Is the exam upcoming, already completed, or are you trying to understand what happened afterward?",
    "lay_statement": "Is this statement from you or from someone who personally observed the facts you want to document?",
    "private_record_collection": "Are you trying to identify which private records matter, or obtain records from a specific provider?",
    "procedural_filing": "Are you starting a new disability claim or continuing one you already began?",
    "evidence_requirement": "What condition or claim issue are you gathering evidence for?",
    "service_connection": "Is this a direct service-connection claim, a secondary condition, or an aggravation claim?",
    "claim_type": "What VA benefit or claim are you trying to handle?",
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
    if route.get("canonical_micro_node_proof_consumed") is not True:
        raise RuntimeError("tvc_route_noncanonical_proof")
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


def _master_records_root() -> Path:
    candidates: list[Path] = []
    override = os.getenv("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "").strip()
    if override:
        candidates.append(Path(override).expanduser().resolve())
    candidates.extend([
        Path.home() / ".stegverse" / "workloads" / "master-records" / "orchestration",
        Path("/var/lib/stegverse/workloads/master-records/orchestration"),
    ])
    required = Path("scripts/reconstruct_ecosystem_chat_sovereign_execution.py")
    for candidate in candidates:
        if (candidate / required).is_file():
            return candidate
    raise RuntimeError("master_records_local_capsule_not_materialized")


def _runtime_receipt_dir() -> Path:
    override = os.getenv("STEGVERSE_VA_RUNTIME_RECEIPT_DIR", "").strip()
    if override:
        path = Path(override).expanduser().resolve()
    else:
        proof_path = Path(os.environ["STEGVERSE_CANONICAL_RUNTIME_PROOF_FILE"]).expanduser().resolve()
        path = proof_path.parent / "va-conversations"
    path.mkdir(parents=True, exist_ok=True)
    return path


def readiness_record() -> dict[str, Any]:
    registry = load_object_env("STEGVERSE_VA_SOURCE_REGISTRY_FILE")
    proof = load_object_env("STEGVERSE_CANONICAL_RUNTIME_PROOF_FILE")
    route_receipt = load_object_env("STEGVERSE_TVC_ROUTE_RECEIPT_FILE")
    validate_tvc_route(route_receipt, proof)
    if not registry.get("sources"):
        raise RuntimeError("va_source_registry_empty")
    _master_records_root()
    return {
        "state": "READY",
        "schema": SCHEMA,
        "source_policy": "ADMITTED_OFFICIAL_VA_ONLY",
        "per_turn_reconstruction": "REQUIRED",
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
        "Use only the admitted VA context below. Answer the veteran directly in plain language. "
        "Ask at most one useful follow-up question. Do not invent facts, diagnoses, nexus opinions, eligibility determinations, ratings, deadlines, or filing confirmations. "
        "Do not mention internal governance, runtimes, receipts, models, routes, or capability states. Context: "
        + json.dumps(context, sort_keys=True, ensure_ascii=False)
    )


def _execution_receipt(*, proof: dict[str, Any], route: dict[str, Any], execution: Any, session_id: str, transition_id: str, measurement_id: str) -> dict[str, Any]:
    binding = dict(execution.binding_receipt)
    output = execution.response.output
    route_base = str(route.get("endpoint") or "").rstrip("/")
    return {
        "schema": "stegverse.llm_adapter.canonical_sovereign_route_execution/v1",
        "task_id": "VACC-SOVEREIGN-CONVERSATIONAL-EXECUTION-001",
        "state": "EXECUTED" if output.strip() else "FAILED",
        "session_id": session_id,
        "transition_id": transition_id,
        "measurement_id": measurement_id,
        "route_authority": "StegVerse-Labs/TVC",
        "route_receipt_hash": route.get("receipt_hash"),
        "runtime_proof_hash": stable_hash(proof),
        "route_base_endpoint": route_base,
        "transport_endpoint": route_base + "/v1/chat/completions",
        "model_id": binding["model_id"],
        "model_hash": binding["model_hash"],
        "request_hash": binding["request_hash"],
        "response_hash": binding["response_hash"],
        "response_text_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "measured_usage": binding["measured_usage"],
        "provider_usage_event": execution.usage_event,
        "master_records_usage": execution.master_records_usage,
        "binding_receipt": binding,
        "provider_usage_custody_recorded": binding.get("provider_usage_custody_recorded", False),
        "provider_usage_reconstruction_pass": binding.get("provider_usage_reconstruction_pass", False),
        "reference_model_only": binding.get("reference_model_only", True),
        "credential_requirement": "NONE",
        "github_token_required": False,
        "third_party_execution_platform_required": False,
        "execution_authority": False,
        "authority_effect": "NONE",
        "next_transition": "MASTER_RECORDS_SAME_EXECUTION_TRANSITION_RECONSTRUCTION",
    }


def _reconstruct_turn(*, proof: dict[str, Any], route: dict[str, Any], execution_receipt: dict[str, Any], session_id: str, measurement_id: str) -> dict[str, Any]:
    root = _master_records_root()
    receipt_dir = _runtime_receipt_dir() / session_id
    receipt_dir.mkdir(parents=True, exist_ok=True)
    safe_measurement = re.sub(r"[^A-Za-z0-9_.-]", "_", measurement_id)[:180]
    execution_path = receipt_dir / f"{safe_measurement}.execution.json"
    reconstruction_path = receipt_dir / f"{safe_measurement}.reconstruction.json"
    execution_path.write_text(json.dumps(execution_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    packet = {
        "runtime_proof": proof,
        "tvc_route_receipt": route,
        "llm_adapter_execution_receipt": execution_receipt,
    }
    packet_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=receipt_dir, prefix="packet-", suffix=".json", delete=False) as handle:
            json.dump(packet, handle, sort_keys=True)
            handle.write("\n")
            packet_path = Path(handle.name)
        script = root / "scripts" / "reconstruct_ecosystem_chat_sovereign_execution.py"
        child_env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": str(root),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            **({"HOME": os.environ["HOME"]} if "HOME" in os.environ else {}),
        }
        process = subprocess.run(
            [sys.executable, str(script), "--packet", str(packet_path), "--output", str(reconstruction_path)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=child_env,
        )
        try:
            result = json.loads(reconstruction_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError("master_records_turn_reconstruction_receipt_missing") from exc
        required = (
            result.get("state") == "PASS",
            result.get("session_id") == execution_receipt.get("session_id"),
            result.get("transition_id") == execution_receipt.get("transition_id"),
            result.get("measurement_id") == execution_receipt.get("measurement_id"),
            result.get("provider_usage_custody_recorded") is True,
            result.get("provider_usage_reconstruction_pass") is True,
            result.get("transition_reconstruction_pass") is True,
            result.get("same_execution") is True,
            result.get("github_token_required") is False,
            result.get("execution_authority") is False,
            result.get("authority_effect") == "NONE",
        )
        if process.returncode != 0 or not all(required):
            raise RuntimeError("master_records_turn_reconstruction_failed")
        return {
            "state": "PASS",
            "receipt_hash": result.get("reconstruction_receipt_hash"),
            "execution_receipt_path": str(execution_path),
            "reconstruction_receipt_path": str(reconstruction_path),
            "provider_usage_custody_recorded": True,
            "provider_usage_reconstruction_pass": True,
            "transition_reconstruction_pass": True,
            "same_execution": True,
        }
    finally:
        if packet_path is not None:
            try:
                packet_path.unlink()
            except FileNotFoundError:
                pass


def _render_response(route: str, answer_record: dict[str, Any], model_text: str, *, reference_model_only: bool) -> str:
    if route == "urgent_safety":
        return BROAD_ROUTE_GUIDANCE[route]
    if not reference_model_only and len(model_text.strip()) >= 24:
        return model_text.strip()
    propositions = [str(item.get("text") or "").strip() for item in answer_record.get("propositions", []) if str(item.get("text") or "").strip()]
    body = " ".join(propositions[:2]).strip()
    follow_up = FOLLOW_UPS.get(route)
    if follow_up:
        return (body + "\n\n" + follow_up).strip()
    return body or "Tell me a little more about what you are trying to do with VA, and I’ll narrow it down."


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
    model_text = execution.response.output.strip()
    if not model_text:
        raise RuntimeError("model_response_empty")
    binding = dict(execution.binding_receipt)
    execution_receipt = _execution_receipt(
        proof=proof,
        route=route_receipt,
        execution=execution,
        session_id=session_id,
        transition_id=transition_id,
        measurement_id=measurement_id,
    )
    reconstruction = _reconstruct_turn(
        proof=proof,
        route=route_receipt,
        execution_receipt=execution_receipt,
        session_id=session_id,
        measurement_id=measurement_id,
    )

    citations = []
    seen = set()
    for proposition in answer_record.get("propositions", []):
        for support in proposition.get("support", []):
            locator = support.get("locator")
            if locator and locator not in seen:
                seen.add(locator)
                citations.append({"source_id": support.get("source_id"), "authority_class": support.get("authority_class"), "url": locator})

    text = _render_response(route, answer_record, model_text, reference_model_only=bool(binding.get("reference_model_only", True)))
    response = {
        "schema": SCHEMA,
        "response": text,
        "session_id": session_id,
        "route": route,
        "citations": citations[:4],
        "answer_receipt_hash": answer_record["receipt_hash"],
        "execution_receipt_hash": stable_hash(execution_receipt),
        "reconstruction_receipt_hash": reconstruction["receipt_hash"],
        "provider_usage_custody_recorded": True,
        "provider_usage_reconstruction_pass": True,
        "transition_reconstruction_pass": True,
        "same_execution": True,
        "authority_effect": False,
        "activation_effect": False,
        "filing_active": False,
        "private_document_context_used": False,
        "github_token_required": False,
        "credential_requirement": "NONE",
        "reference_model_fallback_renderer_used": bool(binding.get("reference_model_only", True)),
    }
    response["response_hash"] = stable_hash(response)
    return response
