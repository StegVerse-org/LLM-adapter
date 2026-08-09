from __future__ import annotations

"""Governed deterministic Math Solver service surface.

The arithmetic evaluator is intentionally narrow.  It never executes arbitrary Python;
only numeric literals and an allowlist of arithmetic AST nodes are accepted.  The
solver callback is reachable only through the canonical portable StegGate consumer.
"""

import ast
import hashlib
import json
import math
import operator
import os
import uuid
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .service_gateway_site import app
from .steggate_portable_consumer import (
    GovernanceFacts,
    UserLLMIntent,
    create_user_llm_governed_package,
    execute_user_llm_governed_package,
)

ROUTE_VERSION = "MATH-SOLVER-STEGGATE-v1"
SOLVER_ID = "safe-arithmetic-v1"
MAX_EXPRESSION_CHARS = 256
MAX_AST_NODES = 64
MAX_ABS_RESULT = 10**100
MAX_EXPONENT = 12

_BINARY: dict[type[ast.operator], Callable[[float | int, float | int], float | int]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY: dict[type[ast.unaryop], Callable[[float | int], float | int]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class SolveRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=MAX_EXPRESSION_CHARS)
    request_id: str | None = Field(default=None, max_length=96)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _evaluate_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _evaluate_node(node.body)
    if isinstance(node, ast.Constant):
        value = node.value
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("numeric_literals_only")
        if not math.isfinite(float(value)):
            raise ValueError("non_finite_literal")
        return value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_evaluate_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(float(right)) > MAX_EXPONENT:
            raise ValueError("exponent_limit_exceeded")
        try:
            result = _BINARY[type(node.op)](left, right)
        except (ZeroDivisionError, OverflowError) as exc:
            raise ValueError(type(exc).__name__.lower()) from exc
        if isinstance(result, complex) or not math.isfinite(float(result)):
            raise ValueError("non_finite_result")
        if abs(float(result)) > MAX_ABS_RESULT:
            raise ValueError("result_limit_exceeded")
        return result
    raise ValueError(f"unsupported_syntax:{type(node).__name__}")


def solve_expression(expression: str) -> float | int:
    if len(expression) > MAX_EXPRESSION_CHARS:
        raise ValueError("expression_too_long")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("invalid_expression") from exc
    if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
        raise ValueError("expression_too_complex")
    return _evaluate_node(tree)


def _governance(request_hash: str) -> GovernanceFacts:
    return GovernanceFacts(
        refusal_available=True,
        operator_recoverability="available",
        workload_state="bounded_deterministic",
        time_pressure="normal",
        isolation_state="local_deterministic_executor",
        judgment_evidence_refs=(f"math-request:sha256:{request_hash}",),
        admitted_signal_refs=(f"math-expression:sha256:{request_hash}",),
        missing_inputs=(),
        uncertainty_state="bounded",
        reference_state_hash=f"math-solver-policy:{ROUTE_VERSION}",
        expected_reference_state_hash=f"math-solver-policy:{ROUTE_VERSION}",
        reconstruction_available=True,
        transformation_provenance_complete=True,
        actor_authority_current=True,
        policy_current=True,
        delegation_current=True,
        evidence_current=True,
        affected_entity_conditions_represented=True,
        recoverability_profile="replayable",
        validity_window_open=True,
        policy_ref=f"policy:math-solver:{ROUTE_VERSION}",
        delegation_ref="delegation:public-math-solver:v1",
        execution_evidence_refs=(f"math-request:sha256:{request_hash}",),
        capability_allowed=True,
        continuity_required=False,
        previous_receipt_verified=None,
        previous_receipt_hash=None,
        approval_required=False,
        permission_present=True,
    )


def governed_solve(expression: str, *, request_id: str | None = None) -> dict[str, Any]:
    normalized = expression.strip()
    request_record = {
        "schema_version": ROUTE_VERSION,
        "expression": normalized,
        "solver_id": SOLVER_ID,
    }
    request_hash = _sha256(_canonical_json(request_record))
    effective_request_id = request_id or f"MATH-{uuid.uuid4().hex[:20].upper()}"
    intent = UserLLMIntent(
        user_id="public-anonymous",
        llm_id="math-solver",
        provider="local-deterministic",
        model=SOLVER_ID,
        prompt_hash=f"sha256:{request_hash}",
        route="math_solver",
        action="solve_expression",
    )
    package = create_user_llm_governed_package(
        package_id=effective_request_id,
        intent=intent,
        governance=_governance(request_hash),
        declared_execution_context={"solver_id": SOLVER_ID, "request_hash": request_hash},
    )

    def execute() -> dict[str, Any]:
        result = solve_expression(normalized)
        result_record = {"request_hash": request_hash, "result": result, "solver_id": SOLVER_ID}
        return {"result": result, "result_hash": _sha256(_canonical_json(result_record))}

    receipt = execute_user_llm_governed_package(package, execute)
    observation = dict(receipt.execution_observation)
    evaluation = dict(observation.get("evaluation") or {})
    response: dict[str, Any] = {
        "schema_version": ROUTE_VERSION,
        "request_id": effective_request_id,
        "request_hash": request_hash,
        "solver_id": SOLVER_ID,
        "steggate_package_hash": package.package_hash,
        "steggate_profile": package.micronode.profile,
        "execution_state": receipt.state,
        "disposition": evaluation.get("disposition"),
        "candidate_hash": evaluation.get("candidate_hash"),
        "decision_state_hash": evaluation.get("decision_state_hash"),
        "matrix": evaluation.get("matrix"),
        "executor_invoked": observation.get("executor_invoked", False),
        "result": None,
        "result_hash": None,
        "replay_contract": {
            "request_hash_algorithm": "sha256",
            "solver_id": SOLVER_ID,
            "same_expression_same_solver_result": True,
        },
    }
    if receipt.state == "EXECUTED" and observation.get("executor_invoked") is True:
        result = observation.get("result") or {}
        response["result"] = result.get("result")
        response["result_hash"] = result.get("result_hash")
    response["response_hash"] = _sha256(_canonical_json(response))
    return response


router = APIRouter(prefix="/api/math-solver/v1", tags=["math-solver"])


@router.get("/readiness")
def readiness() -> dict[str, Any]:
    try:
        from stegcore.portable_steggate import runtime_fingerprint
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="canonical_stegcore_runtime_unavailable") from exc
    return {
        "state": "READY",
        "schema_version": ROUTE_VERSION,
        "solver_id": SOLVER_ID,
        "canonical_steggate_bound": True,
        "runtime_fingerprint": runtime_fingerprint(),
        "arbitrary_code_execution": False,
    }


@router.post("/solve")
def solve(request: SolveRequest) -> dict[str, Any]:
    try:
        response = governed_solve(request.expression, request_id=request.request_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if response["execution_state"] != "EXECUTED":
        raise HTTPException(status_code=403, detail={
            "state": response["execution_state"],
            "disposition": response["disposition"],
            "decision_state_hash": response["decision_state_hash"],
            "executor_invoked": response["executor_invoked"],
        })
    return response


app.include_router(router)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "llm_adapter.math_solver_gateway:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )


if __name__ == "__main__":
    main()
