from fastapi.testclient import TestClient

from llm_adapter.hil_browser_app import create_hil_browser_app


def test_hil_browser_surface_contains_dependency_absorbing_workflow():
    client = TestClient(create_hil_browser_app())
    response = client.get("/")
    assert response.status_code == 200
    assert "Build manifest and submit" in response.text
    assert "crypto.subtle.digest" in response.text
    assert "/api/hil/readiness" in response.text
    assert "/api/hil/submissions" in response.text
    assert "participant_consent_authority_acknowledged" in response.text
