from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from .service_gateway_site import app
from .sovereign_local_model_binding import SovereignLocalModelBindingError
from .va_claims_runtime_core import (
    ChatRequest,
    classify_route,
    execute_chat,
    readiness_record,
)
from va_claim_assistant.route_generators import AuthorityResolutionRequired, RouteGenerationError

router = APIRouter(prefix="/api/va-claims/v1", tags=["va-claims"])


@router.get("/readiness")
def readiness() -> dict[str, Any]:
    try:
        return readiness_record()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    try:
        return execute_chat(request)
    except (AuthorityResolutionRequired, RouteGenerationError, SovereignLocalModelBindingError, RuntimeError, OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


app.include_router(router)

__all__ = ["ChatRequest", "chat", "classify_route", "execute_chat", "readiness", "router"]
