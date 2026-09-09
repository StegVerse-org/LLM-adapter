from __future__ import annotations

import logging
import os
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_VA_REGISTRY = _PACKAGE_ROOT / "va_claim_assistant" / "source-registry.site-projection.json"
os.environ.setdefault("STEGVERSE_VA_SOURCE_REGISTRY_FILE", str(_DEFAULT_VA_REGISTRY))

from .math_solver_gateway import app  # noqa: E402
from . import va_claims_runtime_gateway as _va_claims_runtime_gateway  # noqa: E402,F401
from . import service_gateway_composed as _service_gateway_composed  # noqa: E402,F401
from . import service_gateway_kv_onboarding as _service_gateway_kv_onboarding  # noqa: E402,F401

_ACCESS_LOGGER = logging.getLogger("stegverse.service_gateway.access")


@app.middleware("http")
async def _query_secret_safe_access_log(request, call_next):
    """Retain method/path/status observability without serializing request queries.

    Uvicorn's built-in request-target access logger is disabled in ``main`` because
    a provider callback may carry protected authorization material in its query
    string.  This middleware intentionally reads only the canonical ASGI ``path``.
    """
    method = str(request.scope.get("method") or "UNKNOWN")
    path = str(request.scope.get("path") or "/")
    try:
        response = await call_next(request)
    except Exception:
        _ACCESS_LOGGER.info("method=%s path=%s status=500", method, path)
        raise
    _ACCESS_LOGGER.info(
        "method=%s path=%s status=%s",
        method,
        path,
        int(response.status_code),
    )
    return response


def main() -> None:
    import uvicorn

    uvicorn.run(
        "llm_adapter.runtime_gateway:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        access_log=False,
    )


if __name__ == "__main__":
    main()
