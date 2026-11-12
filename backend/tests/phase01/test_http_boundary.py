import pytest

from backend.app.models import Action


def test_phase01_openapi_has_real_routes_and_bearer_security(world):
    response = world.client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/v1/cases" in paths
    assert "/v1/cases/{case_id}/approvals" in paths
    assert not any("fixture" in path or "redteam" in path or path.startswith("/api/") for path in paths)
    for path, methods in paths.items():
        for operation in methods.values():
            if path not in {"/healthz", "/v1/auth/login"}:
                assert operation["security"] == [{"HTTPBearer": []}]
    assert world.client.get("/docs").status_code == 200


@pytest.mark.parametrize("chunked", [True, False])
def test_json_body_limit_is_enforced_before_parsing_with_or_without_length(world, chunked):
    payload = b'{"password":"' + b"private-marker" * 2000 + b'"}'
    content = iter([payload[:10000], payload[10000:]]) if chunked else payload
    response = world.client.post("/v1/auth/login", content=content, headers={"Content-Type": "application/json"})
    assert response.status_code == 413
    assert response.json()["reason_codes"] == ["REQUEST_TOO_LARGE"]
    assert "private-marker" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_validation_errors_and_cors_do_not_expose_credentials(world):
    response = world.client.post("/v1/auth/login", content=b'{"password":"private-marker",', headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert "private-marker" not in response.text
    preflight = world.client.options("/v1/jobs", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"})
    assert preflight.status_code == 405
    assert "access-control-allow-origin" not in preflight.headers


@pytest.mark.parametrize("action", ["approve_payment", "publish_policy", "grant_role", "COMPLETE_SIMULATION", "prepare_invoice;approve"])
def test_only_documented_action_names_are_accepted(world, action):
    job, case = world.new()
    response = world.request("POST", f"/v1/cases/{case['id']}/actions/execute", "a_agent", dict(expected_case_version=case["version"], action=action))
    assert response.status_code == 422


def test_old_approval_pointer_cannot_restore_authority_after_evidence_change(world):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    with world.service.repository.transaction() as tx:
        obsolete = tx.get("cases", id=case["id"])["approval_id"]
    replacement = world.inject(case, ch, {"pressure_value": 36}, expected=approved["version"])
    # Simulate an erroneous stale writer. Effective version and full binding
    # are rechecked even if a pointer is accidentally restored by trusted code.
    with world.service.repository.transaction() as tx:
        tx.change("cases", {"id": case["id"]}, {"approval_id": obsolete})
    result = world.act(replacement, "complete_simulated_action", execute=True)
    assert result.status_code == 409
    assert result.json()["decision"] == "DENY"
    with world.service.repository.transaction() as tx:
        assert tx.get("cases", id=case["id"])["approval_id"] is None
