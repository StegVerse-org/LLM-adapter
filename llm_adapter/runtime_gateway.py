from __future__ import annotations

import os
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_VA_REGISTRY = _PACKAGE_ROOT / "va_claim_assistant" / "source-registry.site-projection.json"
os.environ.setdefault("STEGVERSE_VA_SOURCE_REGISTRY_FILE", str(_DEFAULT_VA_REGISTRY))

from .math_solver_gateway import app as _base_app  # noqa: E402
from . import va_claims_runtime_gateway as _va_claims_runtime_gateway  # noqa: E402,F401
from . import service_gateway_composed as _service_gateway_composed  # noqa: E402,F401
from . import service_gateway_kv_onboarding as _service_gateway_kv_onboarding  # noqa: E402,F401
from . import service_gateway_external_collab_consent as _service_gateway_external_collab_consent  # noqa: E402,F401
from .query_safe_access_log import QuerySecretSafeAccessLogMiddleware  # noqa: E402

# Compose all existing routes first, then wrap the complete Gateway application in
# the query-secret-safe observability boundary.
app = QuerySecretSafeAccessLogMiddleware(_base_app)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "llm_adapter.runtime_gateway:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        # Built-in Uvicorn access logging serializes the request target and may
        # include provider callback query material. The replacement middleware
        # above logs only method + canonical path + status.
        access_log=False,
    )


if __name__ == "__main__":
    main()
