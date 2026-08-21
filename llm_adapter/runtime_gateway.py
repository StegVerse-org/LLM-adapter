from __future__ import annotations

import os
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_VA_REGISTRY = _PACKAGE_ROOT / "va_claim_assistant" / "source-registry.site-projection.json"
os.environ.setdefault("STEGVERSE_VA_SOURCE_REGISTRY_FILE", str(_DEFAULT_VA_REGISTRY))

from .math_solver_gateway import app  # noqa: E402
from . import va_claims_runtime_gateway as _va_claims_runtime_gateway  # noqa: E402,F401


def main() -> None:
    import uvicorn

    uvicorn.run(
        "llm_adapter.runtime_gateway:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )


if __name__ == "__main__":
    main()
