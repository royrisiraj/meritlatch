import hashlib

import pytest

from backend.app.auth import hash_password, verify_password, token_digest
from backend.app.repository import SQLiteRepository


PROTECTED = [
    ("GET", "/v1/me", None), ("POST", "/v1/auth/logout", None),
    ("GET", "/v1/jobs", None), ("GET", "/v1/jobs/id", None),
    ("POST", "/v1/jobs", dict(asset_id="PUMP-042", contractor_id="c", engineer_id="e", service_agent_id="s")),
    ("PATCH", "/v1/jobs/id/assignment", dict(expected_job_version=1, contractor_id="c")),
    ("POST", "/v1/cases", dict(job_id="j")), ("GET", "/v1/cases/id", None),
    ("POST", "/v1/jobs/id/challenges", dict(case_id="id", expected_case_version=1)),
    ("PATCH", "/v1/cases/id/invoice", dict(expected_case_version=1, invoice_amount_paise=500000)),
    ("PATCH", "/v1/cases/id/policy", dict(expected_case_version=1, policy_version="2")),
    ("POST", "/v1/cases/id/approvals", dict(expected_case_version=1)),
    ("GET", "/v1/cases/id/audit", None),
    ("POST", "/v1/cases/id/actions/evaluate", dict(expected_case_version=1, action="prepare_invoice")),
    ("POST", "/v1/cases/id/actions/execute", dict(expected_case_version=1, action="complete_simulated_action")),
]


@pytest.mark.parametrize("method,path,data", PROTECTED)
def test_all_business_operations_require_authentication(world, method, path, data):
    response = world.client.request(method, path, json=data)
    assert response.status_code == 401
    assert response.json()["reason_codes"] == ["AUTHENTICATION_REQUIRED"]


def test_login_uses_password_and_server_side_role(world):
    response = world.client.post("/v1/auth/login", json=dict(tenant_id="a", username="contractor", password=world.passwords["a_contractor"]))
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert len(token) == 43
    assert token != world.tokens["a_contractor"]
    me = world.client.get("/v1/me", headers={"Authorization": "Bearer " + token, "X-Role": "MANAGER", "X-Tenant-ID": "b"})
    assert me.json()["role"] == "CONTRACTOR"
    assert me.json()["tenant_id"] == "a"
    assert me.headers["cache-control"] == "no-store"
    with world.service.repository.transaction() as tx:
        assert tx.get("sessions", token_hash=token_digest(token))
        assert not tx.get("sessions", token_hash=token)


@pytest.mark.parametrize("headers", [{"Authorization": "Bearer " + "x" * 43}, {"Authorization": "Basic fake"},
    {"Cookie": "session=manager"}, {"X-Role": "MANAGER"}])
def test_forged_token_cookie_or_role_header_cannot_authenticate(world, headers):
    assert world.client.get("/v1/me", headers=headers).status_code == 401


@pytest.mark.parametrize("extra", [{"role": "MANAGER"}, {"max_permission": 3}, {"tenant": "b"}])
def test_login_rejects_client_authority_fields(world, extra):
    response = world.client.post("/v1/auth/login", json=dict(tenant_id="a", username="contractor", password="secret-marker-too-short", **extra))
    assert response.status_code == 422
    assert "secret-marker" not in response.text


def test_logout_revokes_only_that_session(world):
    token = world.service.login("a", "contractor", world.passwords["a_contractor"])["access_token"]
    assert world.request("POST", "/v1/auth/logout", "a_contractor").status_code == 200
    assert world.request("GET", "/v1/me", "a_contractor").status_code == 401
    assert world.client.get("/v1/me", headers={"Authorization": "Bearer " + token}).status_code == 200


def test_session_expiry_and_user_deactivation_are_checked_on_every_request(world):
    with world.service.repository.transaction() as tx:
        tx.change("users", {"id": world.ids["a_manager"]}, {"active": False})
    assert world.request("GET", "/v1/me").status_code == 401
    world.clock.advance(3600)
    assert world.request("GET", "/v1/jobs", "a_contractor").status_code == 401


def test_role_is_loaded_from_database_not_captured_in_session(world):
    with world.service.repository.transaction() as tx:
        tx.change("users", {"id": world.ids["a_manager"]}, {"role": "ENGINEER"})
    assert world.request("GET", "/v1/me").json()["role"] == "ENGINEER"
    assert world.request("POST", "/v1/cases", data={"job_id": "unknown"}).status_code == 403


def test_login_attempt_limit_is_persistent_and_uses_server_time(world):
    payload = dict(tenant_id="a", username="manager", password="incorrect-password")
    for _ in range(5):
        assert world.client.post("/v1/auth/login", json=payload).status_code == 401
    assert world.client.post("/v1/auth/login", json=payload).status_code == 429
    world.service.repository.close()
    assert world.client.post("/v1/auth/login", json=payload).status_code == 429
    world.clock.advance(901)
    payload["password"] = world.passwords["a_manager"]
    assert world.client.post("/v1/auth/login", json=payload).status_code == 200


def test_unknown_account_has_same_redacted_error_as_wrong_password(world):
    responses = [world.client.post("/v1/auth/login", json=dict(tenant_id="a", username=u, password="invalid-password"))
                 for u in ("manager", "does-not-exist")]
    assert responses[0].status_code == responses[1].status_code == 401
    assert responses[0].json() == responses[1].json()


def test_password_hash_is_salted_and_verified():
    first = hash_password("test-only-password-example")
    second = hash_password("test-only-password-example")
    assert first != second
    assert "test-only-password-example" not in first
    assert verify_password("test-only-password-example", first)
    assert not verify_password("wrong-password", first)
    assert not verify_password("anything", "invalid-encoding")
    with pytest.raises(ValueError):
        hash_password("short")


def test_no_public_role_provisioning_or_cookie_authentication(world):
    assert world.request("POST", "/v1/users", data={"role": "MANAGER"}).status_code == 404
    assert world.request("POST", "/v1/auth/register", data={"role": "MANAGER"}).status_code == 404
    assert not world.request("GET", "/v1/me").headers.get("set-cookie")
