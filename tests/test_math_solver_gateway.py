from fastapi.testclient import TestClient

from llm_adapter.math_solver_gateway import app, governed_solve, solve_expression


def test_safe_arithmetic_evaluator_accepts_bounded_numeric_expression():
    assert solve_expression("(2 + 3) * 4 - 5") == 15
    assert solve_expression("2 ** 8") == 256


def test_safe_arithmetic_evaluator_rejects_code_and_unbounded_exponent():
    for expression in ("__import__('os').system('id')", "2 ** 1000", "[1,2,3]"):
        try:
            solve_expression(expression)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe expression accepted: {expression}")


def test_governed_solver_executes_only_after_canonical_steggate_allow():
    response = governed_solve("12 / 3 + 7", request_id="MATH-TEST-ALLOW")
    assert response["execution_state"] == "EXECUTED"
    assert response["disposition"] == "ALLOW"
    assert response["executor_invoked"] is True
    assert response["result"] == 11
    assert response["request_hash"]
    assert response["result_hash"]
    assert response["response_hash"]
    assert response["steggate_package_hash"]
    assert response["decision_state_hash"]
    assert response["matrix"]


def test_same_request_replays_to_same_request_and_result_hashes():
    first = governed_solve("144 / 12", request_id="MATH-REPLAY-A")
    second = governed_solve("144 / 12", request_id="MATH-REPLAY-B")
    assert first["request_hash"] == second["request_hash"]
    assert first["result"] == second["result"] == 12
    assert first["result_hash"] == second["result_hash"]


def test_http_surface_exposes_readiness_and_governed_result():
    client = TestClient(app)
    readiness = client.get("/api/math-solver/v1/readiness")
    assert readiness.status_code == 200
    assert readiness.json()["canonical_steggate_bound"] is True

    solved = client.post("/api/math-solver/v1/solve", json={"expression": "6 * 7", "request_id": "MATH-HTTP-1"})
    assert solved.status_code == 200
    payload = solved.json()
    assert payload["result"] == 42
    assert payload["disposition"] == "ALLOW"
    assert payload["executor_invoked"] is True
