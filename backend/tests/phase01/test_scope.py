import pytest


def test_job_lists_respect_assignments_and_agent_is_action_only(world):
    job, case = world.new()
    second, _ = world.new(contractor="other_contractor")
    assert {j["id"] for j in world.request("GET", "/v1/jobs", "a_contractor").json()} == {job["id"]}
    assert len(world.request("GET", "/v1/jobs").json()) == 2
    assert world.request("GET", "/v1/jobs", "b_manager").json() == []
    assert world.request("GET", "/v1/jobs", "a_agent").status_code == 403
    assert world.request("GET", f"/v1/cases/{case['id']}", "a_agent").status_code == 403
    assert world.request("GET", "/v1/jobs", "a_reviewer").json() == []


@pytest.mark.parametrize("suffix", ["", "/audit"])
def test_contractor_cannot_read_unassigned_cases(world, suffix):
    job, case = world.new()
    assert world.request("GET", f"/v1/cases/{case['id']}" + suffix, "a_other_contractor").status_code == 404
    assert world.request("GET", f"/v1/jobs/{job['id']}", "a_other_contractor").status_code == 404


@pytest.mark.parametrize("role", ["manager", "contractor", "engineer", "agent"])
def test_tenant_b_cannot_read_or_evaluate_tenant_a(world, role):
    job, case = world.new()
    key = "b_" + role
    if role != "agent":
        assert world.request("GET", f"/v1/cases/{case['id']}", key).status_code == 404
        assert world.request("GET", f"/v1/cases/{case['id']}/audit", key).status_code == 404
    result = world.act(case, "create_draft", key)
    assert result.status_code == 404


@pytest.mark.parametrize("operation", ["invoice", "approval", "challenge", "assignment", "policy"])
def test_cross_tenant_mutations_fail_without_changing_case(world, operation):
    job, case = world.new()
    if operation == "invoice":
        response = world.request("PATCH", f"/v1/cases/{case['id']}/invoice", "b_manager", dict(expected_case_version=1, invoice_amount_paise=1))
    elif operation == "approval":
        response = world.approve(case, "b_manager")
    elif operation == "assignment":
        response = world.request("PATCH", f"/v1/jobs/{job['id']}/assignment", "b_manager", dict(expected_job_version=1, contractor_id=world.ids["b_contractor"]))
    elif operation == "policy":
        response = world.request("PATCH", f"/v1/cases/{case['id']}/policy", "b_engineer", dict(expected_case_version=1, policy_version="1.0.0"))
    else:
        response = world.request("POST", f"/v1/jobs/{job['id']}/challenges", "b_contractor", dict(case_id=case["id"], expected_case_version=1))
    assert response.status_code == 404
    current = world.request("GET", f"/v1/cases/{case['id']}").json()
    assert current["version"] == 1
    assert current["max_permission"] == 0


@pytest.mark.parametrize("key", ["a_contractor", "a_engineer", "a_agent"])
def test_only_manager_can_create_jobs_or_cases(world, key):
    data = dict(asset_id="PUMP-042", contractor_id=world.ids["a_contractor"], engineer_id=world.ids["a_engineer"], service_agent_id=world.ids["a_agent"])
    assert world.request("POST", "/v1/jobs", key, data).status_code == 403
    assert world.request("POST", "/v1/cases", key, {"job_id": "unknown"}).status_code == 403


@pytest.mark.parametrize("field,user", [("contractor_id", "b_contractor"), ("contractor_id", "a_manager"), ("engineer_id", "a_manager"), ("service_agent_id", "b_agent")])
def test_manager_cannot_create_cross_tenant_or_wrong_role_assignments(world, field, user):
    data = dict(asset_id="PUMP-042", contractor_id=world.ids["a_contractor"], engineer_id=world.ids["a_engineer"], service_agent_id=world.ids["a_agent"])
    data[field] = world.ids[user]
    assert world.request("POST", "/v1/jobs", data=data).status_code == 422


def test_reassignment_invalidates_evidence_approval_and_old_contractor_access(world):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    response = world.request("PATCH", f"/v1/jobs/{job['id']}/assignment", data=dict(expected_job_version=job["version"], contractor_id=world.ids["a_other_contractor"]))
    assert response.status_code == 200
    assert world.request("GET", f"/v1/cases/{case['id']}", "a_contractor").status_code == 404
    current = world.request("GET", f"/v1/cases/{case['id']}", "a_other_contractor").json()
    assert current["max_permission"] == 0
    assert current["evidence_sha256"] is None
    assert current["version"] > approved["version"]
    assert world.act(current, "complete_simulated_action").json()["decision"] == "DENY"
    assert world.challenge(response.json(), current, "a_other_contractor")["token"] != ch["token"]


def test_service_agent_cannot_act_on_another_agents_job(world):
    job, case, ch = world.ready()
    assert world.act(case, "prepare_invoice", "a_other_agent", True).status_code == 404


@pytest.mark.parametrize("asset", ["N/A", "UNKNOWN", " "])
def test_manager_cannot_create_placeholder_asset_job(world, asset):
    data = dict(asset_id=asset, contractor_id=world.ids["a_contractor"], engineer_id=world.ids["a_engineer"], service_agent_id=world.ids["a_agent"])
    assert world.request("POST", "/v1/jobs", data=data).status_code == 422


def test_unassigned_contractor_cannot_issue_challenge_or_reassign_job(world):
    job, case = world.new()
    response = world.request("POST", f"/v1/jobs/{job['id']}/challenges", "a_other_contractor", dict(case_id=case["id"], expected_case_version=1))
    assert response.status_code == 404
    response = world.request("PATCH", f"/v1/jobs/{job['id']}/assignment", "a_contractor", dict(expected_job_version=1, contractor_id=world.ids["a_contractor"]))
    assert response.status_code == 403
