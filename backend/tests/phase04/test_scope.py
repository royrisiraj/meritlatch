import pytest


ROUTES=[
    ("GET","/v1/redteam/candidates",None),("POST","/v1/redteam/candidates",{"profile":"SAFE_BASELINE"}),
    ("GET","/v1/redteam/candidates/unknown",None),("PATCH","/v1/redteam/candidates/unknown",{"expected_version":1,"profile":"SAFE_BASELINE"}),
    ("POST","/v1/redteam/run",{"candidate_id":"unknown","expected_candidate_version":1,"idempotency_key":"test_operation_0001"}),
    ("GET","/v1/redteam/runs",None),("GET","/v1/redteam/runs/unknown",None),("POST","/v1/redteam/suggest",None),
    ("GET","/v1/alerts",None),("GET","/v1/alerts/unknown",None),
    ("POST","/v1/alerts/unknown/triage",{"expected_version":1,"status":"ACKNOWLEDGED","reason":"REPRODUCED"}),
    ("POST","/v1/alerts/unknown/remediations",{"expected_version":1,"candidate_id":"unknown","expected_candidate_version":1,"remediation":"RESTORE_BASELINE_BOUNDS"}),
    ("POST","/v1/redteam/candidates/unknown/reviews",{"expected_version":1,"proposal_id":"unknown","run_id":"unknown","decision":"APPROVE","reason":"REGRESSION_REVIEWED"}),
    ("POST","/v1/redteam/candidates/unknown/release-gate",{"expected_version":1,"run_id":"unknown"}),
    ("GET","/v1/redteam/release-gates/unknown",None),("GET","/v1/redteam/audit",None)]


@pytest.mark.parametrize("key",["a_manager","a_contractor","a_agent"])
def test_every_engineering_route_rejects_business_roles(sec,key):
    for method,path,body in ROUTES:
        response=sec.request(method,path,key,body)
        assert response.status_code==403,(path,response.text)


def test_every_engineering_route_requires_authentication(sec):
    for method,path,body in ROUTES:
        assert sec.client.request(method,path,json=body).status_code==401,path


def test_current_factory_documents_real_engineering_auth_and_legacy_factory_retains_historical_surface(sec,tmp_path):
    from fastapi.testclient import TestClient
    from backend.testing import create_test_app
    paths=sec.client.get("/openapi.json").json()["paths"]
    assert "/v1/redteam/run" in paths and "/v1/redteam/suggest" in paths and "/v1/alerts" in paths
    for path,methods in paths.items():
        if path.startswith(("/v1/redteam","/v1/alerts")):
            for operation in methods.values():
                assert operation["security"]==[{"HTTPBearer":[]}]
    assert not any("fixture" in path or path.startswith("/api/") for path in paths)
    with TestClient(create_test_app(tmp_path/"legacy-fixture.sqlite",sec.clock)) as legacy:
        assert legacy.get("/v1/redteam/runs",headers=sec.headers()).status_code==404
        assert not any("redteam" in path for path in legacy.get("/openapi.json").json()["paths"])


def test_tenant_boundaries_cover_runs_findings_candidates_reviews_gates_and_cursors(fast):
    weak=fast.candidate("WEAK_TEST_ONLY")
    run=fast.run(weak).json()
    finding=fast.findings()[0]
    gate=fast.gate(weak,run).json()
    for path in (f"/v1/redteam/candidates/{weak['id']}",f"/v1/redteam/runs/{run['id']}",f"/v1/alerts/{finding['id']}",f"/v1/redteam/release-gates/{gate['id']}",
                 f"/v1/redteam/candidates?before={weak['id']}",f"/v1/alerts?before={finding['id']}"):
        assert fast.request("GET",path,"b_engineer").status_code==404,path
    for path in ("/v1/redteam/candidates","/v1/redteam/runs","/v1/alerts"):
        assert fast.request("GET",path,"b_engineer").json()["items"]==[]
    assert fast.run(weak,key="b_engineer").status_code==404
    assert fast.request("POST",f"/v1/alerts/{finding['id']}/triage","b_engineer",dict(expected_version=1,status="ACKNOWLEDGED",reason="REPRODUCED")).status_code==404
    assert fast.request("POST",f"/v1/redteam/candidates/{weak['id']}/release-gate","b_engineer",dict(expected_version=1,run_id=run["id"])).status_code==404


@pytest.mark.parametrize("path",["/v1/alerts?limit=0","/v1/alerts?limit=51","/v1/alerts?severity=CRITICAL","/v1/redteam/runs?limit=100000"])
def test_queries_are_typed_and_bounded(sec,path):
    assert sec.request("GET",path).status_code==422


@pytest.mark.parametrize("body",[{"profile":"LIVE"},{"profile":"SAFE_BASELINE","pressure_max":999},{"profile":"SAFE_BASELINE","python":"import os"}])
def test_no_arbitrary_policy_or_code_upload(sec,body):
    assert sec.request("POST","/v1/redteam/candidates",data=body).status_code==422


def test_suggestions_are_disabled_audited_and_engineer_cannot_approve_business_work(sec):
    response=sec.request("POST","/v1/redteam/suggest")
    assert response.status_code==200
    assert response.json()==dict(status="BLOCKED",source="DISABLED",reason_codes=["GEMINI_FROZEN"],candidates=[])
    assert any(r["action"]=="SUGGESTION_BLOCKED" for r in sec.request("GET","/v1/redteam/audit").json()["items"])
    job,case=sec.new()
    assert sec.approve(case,key="a_engineer").status_code==403
    assert sec.request("PATCH",f"/v1/cases/{case['id']}/invoice",data=dict(expected_case_version=case["version"],invoice_amount_paise=500001)).status_code==403


def test_security_pagination_and_filters_remain_scoped(sec):
    ids={sec.candidate()["id"] for _ in range(5)}
    found=set()
    cursor=None
    for _ in range(4):
        page=sec.request("GET","/v1/redteam/candidates?limit=2"+("&before="+cursor if cursor else "")).json()
        assert not (found & {r["id"] for r in page["items"]})
        found|={r["id"] for r in page["items"]}
        cursor=page["next_cursor"]
        if not cursor:break
    assert found==ids and cursor is None
