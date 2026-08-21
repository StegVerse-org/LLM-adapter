from __future__ import annotations

import os

from .math_solver_gateway import app
from . import va_claims_runtime_gateway as _va_claims_runtime_gateway  # noqa: F401


def main() -> None:
    import uvicorn

    uvicorn.run(
        "llm_adapter.runtime_gateway:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )


if __name__ == "__main__":
    main()
