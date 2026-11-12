import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_success_contains_no_business_or_secret_data():
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_documentation_and_only_health_business_schema():
    with TestClient(app) as client:
        docs = client.get("/docs")
        schema = client.get("/openapi.json")
    assert docs.status_code == 200
    assert "swagger-ui" in docs.text
    assert schema.status_code == 200
    assert set(schema.json()["paths"]) == {"/healthz"}


@pytest.mark.parametrize("path", ["/v1/cases", "/v1/cases/test/evidence/fixture",
    "/v1/cases/test/approvals", "/v1/redteam/run", "/api/v1/cases"])
def test_later_phase_routes_are_absent(path):
    with TestClient(app) as client:
        assert client.post(path, json={"role": "manager"}).status_code == 404


def test_health_is_read_only():
    with TestClient(app) as client:
        assert client.post("/healthz").status_code == 405
