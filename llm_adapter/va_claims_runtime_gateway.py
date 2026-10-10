from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from . import collab_ingress
from .service_gateway_site import app
from .va_claims_runtime_core import (
    ChatRequest,
    classify_route,
    execute_chat,
    non_allow_from_exception,
    readiness_record,
)

router = APIRouter(prefix="/api/va-claims/v1", tags=["va-claims"])


@router.get("/readiness")
def readiness() -> dict[str, Any]:
    try:
        return readiness_record()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=non_allow_from_exception(exc)) from exc


@router.post("/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    """Manifest-bound transport: return the SDK disposition for the VA-scoped chat manifest."""
    try:
        result = execute_chat(request)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=non_allow_from_exception(exc)) from exc
    if result.get("disposition") != "ALLOW":
        raise HTTPException(status_code=collab_ingress.http_status(result), detail=result)
    return result


app.include_router(router)

__all__ = ["ChatRequest", "chat", "classify_route", "execute_chat", "readiness", "router"]
