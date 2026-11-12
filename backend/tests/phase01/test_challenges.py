import pytest

from backend.app.errors import AppError


def test_challenge_is_random_and_bound_to_server_context(world):
    job, case = world.new()
    first = world.challenge(job, case)
    current = world.request("GET", f"/v1/cases/{case['id']}").json()
    second = world.challenge(job, current)
    assert first["token"] != second["token"]
    assert first["evidence_session_id"] != second["evidence_session_id"]
    assert len(second["token"]) == len(second["evidence_session_id"]) == 43
    assert second["tenant_id"] == "a"
    assert second["job_id"] == job["id"]
    assert second["case_id"] == case["id"]
    assert second["asset_id"] == "PUMP-042"
    assert second["expires_at"] == world.clock().timestamp() + 300
    assert second["supporting_evidence_only"] is True
    with world.service.repository.transaction() as tx:
        persisted = tx.get("challenges", id=second["id"])
        session = tx.get("sessions", id=persisted["auth_session_id"])
        assert session["user_id"] == world.ids["a_contractor"]
    with pytest.raises(AppError) as exc:
        world.inject(case, first, expected=second["case_version"])
    assert exc.value.code == "CHALLENGE_INVALID"


@pytest.mark.parametrize("extra", [{"token": "chosen-token"}, {"expires_at": 9999999999}, {"tenant_id": "b"}, {"evidence_session_id": "chosen-session"}])
def test_client_cannot_set_challenge_or_expiry(world, extra):
    job, case = world.new()
    response = world.request("POST", f"/v1/jobs/{job['id']}/challenges", "a_contractor", dict(case_id=case["id"], expected_case_version=1, **extra))
    assert response.status_code == 422


@pytest.mark.parametrize("change", ["session", "case", "evidence_session"])
def test_challenge_cannot_cross_session_case_or_evidence_session(world, change):
    job, case = world.new()
    ch = world.challenge(job, case)
    if change == "session":
        world.tokens = {**world.tokens, "fresh": world.service.login("a", "contractor", world.passwords["a_contractor"])["access_token"]}
        args = {"key": "fresh"}
    elif change == "case":
        second = world.request("POST", "/v1/cases", data={"job_id": job["id"]}).json()
        case = second
        args = {"expected": second["version"]}
    else:
        ch = {**ch, "evidence_session_id": "wrong-session"}
        args = {}
    with pytest.raises(AppError) as exc:
        world.inject(case, ch, **args)
    assert exc.value.code == "CHALLENGE_INVALID"


def test_challenge_issue_limit_is_per_actor_job_and_persistent(world):
    job, case = world.new()
    for _ in range(5):
        ch = world.challenge(job, case)
        case = {**case, "version": ch["case_version"]}
    response = world.request("POST", f"/v1/jobs/{job['id']}/challenges", "a_contractor", dict(case_id=case["id"], expected_case_version=case["version"]))
    assert response.status_code == 429
    fresh = world.service.login("a", "contractor", world.passwords["a_contractor"])["access_token"]
    response = world.client.post(f"/v1/jobs/{job['id']}/challenges", headers={"Authorization": "Bearer " + fresh}, json=dict(case_id=case["id"], expected_case_version=case["version"]))
    assert response.status_code == 429
    world.clock.advance(601)
    assert world.challenge(job, case)["token"]


@pytest.mark.parametrize("cause", ["expiry", "logout", "reviewer_deactivated"])
def test_time_or_identity_change_invalidates_l3_at_evaluation_time(world, cause):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    if cause == "expiry":
        world.clock.advance(300)
    elif cause == "logout":
        assert world.request("POST", "/v1/auth/logout", "a_contractor").status_code == 200
    else:
        with world.service.repository.transaction() as tx:
            tx.change("users", {"id": world.ids["a_manager"]}, {"active": False})
    evaluated = world.act(approved, "complete_simulated_action", execute=True)
    assert evaluated.status_code == 409
    assert evaluated.json()["decision"] == "DENY"
    with world.service.repository.transaction() as tx:
        current = tx.get("cases", id=case["id"])
        assert current["approval_id"] is None
        assert not tx.find("action_runs", case_id=case["id"])
    # Invalidation committed despite the version conflict response.
    again = world.act({**approved, "version": current["version"]}, "complete_simulated_action")
    assert again.json()["decision"] == "DENY"


def test_challenge_rotation_clears_current_evidence_and_approval(world):
    job, case, first = world.ready()
    approved = world.approve(case).json()
    second = world.challenge(job, approved)
    current = world.request("GET", f"/v1/cases/{case['id']}").json()
    assert current["max_permission"] == 0
    assert current["evidence_sha256"] is None
    assert world.act(current, "complete_simulated_action").json()["decision"] == "DENY"
