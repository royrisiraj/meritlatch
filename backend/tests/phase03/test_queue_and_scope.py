import pytest


def test_queue_defaults_to_attention_and_filters_current_state(wf):
    _, unsubmitted = wf.new()
    _, eligible, _ = wf.ready()
    _, unsafe, _ = wf.ready(pressure_value=999)
    _, to_reject, _ = wf.ready()
    rejected = wf.reject(to_reject).json()
    queue = wf.request("GET", "/v1/cases")
    assert queue.status_code == 200, queue.text
    assert {item["id"] for item in queue.json()["items"]} == {eligible["id"], unsafe["id"], rejected["id"]}
    filtered = wf.request("GET", "/v1/cases?approval_eligible=true").json()
    assert [item["id"] for item in filtered["items"]] == [eligible["id"]]
    alert = wf.request("GET", "/v1/cases?inspection_status=SAFETY_ALERT").json()
    assert [item["id"] for item in alert["items"]] == [unsafe["id"]]
    states = wf.request("GET", "/v1/cases?business_status=REJECTED").json()
    assert [item["id"] for item in states["items"]] == [rejected["id"]]
    all_cases = wf.request("GET", "/v1/cases?attention_only=false").json()["items"]
    assert unsubmitted["id"] in {item["id"] for item in all_cases}
    assert all("observation" not in item and "media" not in item for item in all_cases)


def test_queue_order_and_keyset_pagination_are_deterministic(wf):
    ids = []
    for _ in range(5):
        _, case = wf.new()
        ids.append(case["id"])
    first = wf.request("GET", "/v1/cases?attention_only=false&limit=2").json()
    repeated = wf.request("GET", "/v1/cases?attention_only=false&limit=2").json()
    assert first == repeated
    seen = [item["id"] for item in first["items"]]
    cursor = first["next_cursor"]
    while cursor:
        page = wf.request("GET", "/v1/cases?attention_only=false&limit=2&cursor=" + cursor).json()
        seen += [item["id"] for item in page["items"]]
        cursor = page["next_cursor"]
    assert seen == sorted(ids)
    assert len(seen) == len(set(seen)) == 5


@pytest.mark.parametrize("key", ["a_contractor", "a_engineer", "a_agent"])
def test_manager_queue_details_and_templates_are_not_role_switchable(wf, key):
    _, case, _ = wf.ready()
    assert wf.request("GET", "/v1/cases", key).status_code == 403
    assert wf.review(case, key).status_code == 403
    assert wf.request("GET", "/v1/policy-templates", key).status_code == 403
    assert wf.reject(case, key=key).status_code == 403


def test_queue_review_rejection_and_cursor_do_not_cross_tenants(wf):
    _, case, _ = wf.ready()
    assert wf.request("GET", "/v1/cases", "b_manager").json()["items"] == []
    assert wf.request("GET", "/v1/cases?cursor=" + case["id"], "b_manager").status_code == 404
    assert wf.review(case, "b_manager").status_code == 404
    assert wf.reject(case, key="b_manager").status_code == 404
    assert wf.request("GET", "/v1/cases?contractor_id=" + wf.ids["a_contractor"], "b_manager").status_code == 404


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "business_status=GRANTED_L3", "inspection_status=SAFE_ALWAYS"])
def test_queue_rejects_invalid_filters_and_unbounded_pages(wf, query):
    assert wf.request("GET", "/v1/cases?" + query).status_code == 422


@pytest.mark.parametrize("method,path,body", [
    ("GET", "/v1/cases", None), ("GET", "/v1/policy-templates", None), ("GET", "/v1/cases/id/review", None),
    ("POST", "/v1/cases/id/rejections", {"expected_case_version": 1, "reason": "CORRECTION_REQUESTED"}),
    ("POST", "/v1/cases/id/evidence/e/reanalysis", {"expected_case_version": 1, "idempotency_key": "operation_00000001"})])
def test_new_endpoints_require_bearer_auth(wf, method, path, body):
    assert wf.client.request(method, path, json=body).status_code == 401


def test_case_details_expose_safe_observations_versions_feedback_and_actions(wf):
    job, case, ch = wf.ready(pressure_value=None, uncertain_fields=["pressure_value"])
    response = wf.review(case)
    assert response.status_code == 200
    detail = response.json()
    assert "pressure_value" in detail["missing_fields"] and "pressure_value" in detail["uncertain_fields"]
    assert detail["case"]["submitted_at"] == wf.clock().timestamp()
    assert detail["case"]["processing_status"] == "SUCCESS"
    assert detail["case"]["provider_mode"] == "MOCK_AI"
    assert detail["case"]["approval_eligible"] is False
    assert ch["token"] not in response.text and ch["evidence_session_id"] not in response.text
    assert "storage_key" not in response.text and "internal_approval_id" not in response.text
