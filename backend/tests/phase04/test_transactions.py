from concurrent.futures import ThreadPoolExecutor
from threading import Barrier,Event

import pytest

from backend.app.assurance_models import RunRequest


def test_duplicate_run_key_while_worker_pending_never_executes_twice(fast,monkeypatch,executed_fixtures):
    started,release=Event(),Event()
    calls=[]
    def delayed(request):
        calls.append(1)
        started.set()
        assert release.wait(10)
        return executed_fixtures(request)
    monkeypatch.setattr(fast.app.state.assurance,"runner",delayed)
    candidate=fast.candidate()
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(fast.run,candidate,"a_engineer","operation_concurrent_001")
        assert started.wait(10)
        replay=fast.run(candidate,operation="operation_concurrent_001")
        assert replay.status_code==202 and replay.json()["operation_replayed"] is True
        assert fast.run(candidate,operation="another_operation_002").status_code==409
        release.set()
        first=pending.result(timeout=15)
    assert first.status_code==200 and first.json()["status"]=="COMPLETE"
    assert len(calls)==1
    with fast.service.repository.transaction() as tx:
        assert len(tx.find("security_runs"))==len(tx.find("security_results"))==1
    again=fast.run(candidate,operation="operation_concurrent_001").json()
    assert again["id"]==first.json()["id"] and len(calls)==1


def test_idempotency_key_cannot_change_request_payload_or_create_duplicate_findings(fast):
    weak=fast.candidate("WEAK_TEST_ONLY")
    first=fast.run(weak,operation="fixed_operation_key_001").json()
    replay=fast.run(weak,operation="fixed_operation_key_001").json()
    assert replay["id"]==first["id"]
    assert all(item["occurrences"]==1 for item in fast.findings())
    other=fast.candidate()
    assert fast.run(other,operation="fixed_operation_key_001").status_code==409


def test_candidate_changed_during_execution_cannot_publish_stale_pass(fast,monkeypatch,executed_fixtures):
    started,release=Event(),Event()
    def delayed(request):
        started.set()
        assert release.wait(10)
        return executed_fixtures(request)
    monkeypatch.setattr(fast.app.state.assurance,"runner",delayed)
    candidate=fast.candidate()
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(fast.run,candidate)
        assert started.wait(10)
        change=fast.request("PATCH",f"/v1/redteam/candidates/{candidate['id']}",data=dict(expected_version=1,profile="WEAK_TEST_ONLY"))
        assert change.status_code==200
        release.set()
        run=pending.result(timeout=15).json()
    assert run["status"]=="STALE" and run["current_binding_valid"] is False
    assert fast.gate(change.json(),run).status_code==409


def test_logout_during_run_preserves_failure_audit_without_returning_private_results(fast,monkeypatch,executed_fixtures):
    started,release=Event(),Event()
    def delayed(request):
        started.set()
        assert release.wait(10)
        return executed_fixtures(request)
    monkeypatch.setattr(fast.app.state.assurance,"runner",delayed)
    candidate=fast.candidate()
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(fast.run,candidate)
        assert started.wait(10)
        assert fast.request("POST","/v1/auth/logout").status_code==200
        release.set()
        response=pending.result(timeout=15)
    assert response.status_code==401 and "results" not in response.json()
    run=fast.request("GET","/v1/redteam/runs","a_reviewer").json()["items"][0]
    assert run["status"]=="FAILED" and run["error_code"]=="RUN_AUTHORIZATION_CHANGED"


def test_interrupted_or_timeout_run_cannot_be_a_release_pass(sec):
    candidate=sec.candidate()
    request=RunRequest(candidate_id=candidate["id"],expected_candidate_version=1,idempotency_key="interrupted_operation_001")
    pending,_=sec.app.state.assurance.start(sec.tokens["a_engineer"],request)
    run=pending[0]
    assert sec.request("GET",f"/v1/redteam/runs/{run['id']}").json()["status"]=="RUNNING"
    sec.clock.advance(26)
    assert sec.request("GET",f"/v1/redteam/runs/{run['id']}").json()["status"]=="INTERRUPTED"
    assert sec.gate(candidate,run).status_code==409


@pytest.mark.parametrize("failure",["timeout","incomplete","forged_pass","exception_result"])
def test_worker_failures_or_forged_summaries_cannot_make_false_pass(fast,monkeypatch,executed_fixtures,failure):
    def broken(request):
        if failure=="timeout":return None,"RUN_TIMEOUT",20
        data,error,elapsed=executed_fixtures(request)
        if failure=="incomplete":data["results"].pop()
        if failure=="forged_pass":
            data["results"][0]["actual"]["decision"]="ALLOW"  # A01 already allowed; change required level.
            data["results"][0]["actual"]["max_permission"]=0
            data["results"][0]["passed"]=True
            data["summary"]["failed"]=0
        if failure=="exception_result":
            data["results"][0]["actual"]=dict(decision=None,error_code="EXECUTION_ERROR")
        return data,error,elapsed
    monkeypatch.setattr(fast.app.state.assurance,"runner",broken)
    candidate=fast.candidate()
    run=fast.run(candidate).json()
    assert run["status"] in {"COMPLETE","FAILED"}
    assert run["summary"]["regression_failures"]>0
    gate=fast.gate(candidate,run)
    assert gate.status_code==409 or gate.json()["decision"]=="BLOCKED"


def test_review_revision_is_compare_and_swap_and_rejection_revokes_prior_gate(fast):
    _,_,_,safe,run,proposal,review=fast.correction()
    assert fast.review(safe,run,proposal).status_code==409
    gate=fast.gate(safe,run,review).json()
    assert gate["decision"]=="READY_FOR_MANUAL_RELEASE"
    rejected=fast.request("POST",f"/v1/redteam/candidates/{safe['id']}/reviews","a_reviewer",dict(expected_version=1,
        expected_review_version=1,proposal_id=proposal["id"],run_id=run["id"],decision="REJECT",reason="CANDIDATE_NOT_ACCEPTABLE"))
    assert rejected.status_code==201
    historical=fast.request("GET",f"/v1/redteam/release-gates/{gate['id']}").json()
    assert historical["historical_decision"]=="READY_FOR_MANUAL_RELEASE"
    assert historical["decision"]=="BLOCKED" and historical["current_binding_valid"] is False
    assert fast.gate(safe,run,review).json()["decision"]=="BLOCKED"


def test_two_concurrent_reviews_have_only_one_revision_winner(fast):
    weak=fast.candidate("WEAK_TEST_ONLY")
    run=fast.run(weak).json()
    proposal=fast.proposal(fast.findings()[0],weak).json()
    barrier=Barrier(2)
    def review(_):
        barrier.wait(10)
        return fast.review(weak,run,proposal).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(review,range(2)))==[201,409]


@pytest.mark.parametrize("first",["gate","change","simultaneous"])
def test_candidate_change_and_gate_race_cannot_restore_stale_review(fast,first):
    _,_,_,safe,run,proposal,review=fast.correction()
    barrier,done=Barrier(2),Event()
    def call(kind):
        barrier.wait(10)
        if first!="simultaneous" and kind!=first:assert done.wait(10)
        try:
            return fast.gate(safe,run,review) if kind=="gate" else fast.request("PATCH",f"/v1/redteam/candidates/{safe['id']}",data=dict(expected_version=1,profile="SAFE_BASELINE"))
        finally:
            if kind==first:done.set()
    with ThreadPoolExecutor(max_workers=2) as pool:
        a,b=pool.submit(call,"gate"),pool.submit(call,"change")
        gate,change=a.result(15),b.result(15)
    assert change.status_code==200 and gate.status_code in {200,409}
    if gate.status_code==200:
        current=fast.request("GET",f"/v1/redteam/release-gates/{gate.json()['id']}").json()
        assert current["decision"]=="BLOCKED" and current["current_binding_valid"] is False
    assert fast.review(safe,run,proposal).status_code==409


def test_remediation_transaction_rolls_back_all_records_on_failure(fast,monkeypatch):
    weak=fast.candidate("WEAK_TEST_ONLY")
    fast.run(weak)
    finding=fast.findings()[0]
    original=fast.app.state.assurance.event
    def fail(tx,actor,now,action,*args,**kwargs):
        if action=="REMEDIATION_PROPOSED":raise RuntimeError("SECRET_FAILURE_MARKER")
        return original(tx,actor,now,action,*args,**kwargs)
    monkeypatch.setattr(fast.app.state.assurance,"event",fail)
    response=fast.proposal(finding,weak)
    assert response.status_code==500 and "SECRET_FAILURE_MARKER" not in response.text
    with fast.service.repository.transaction() as tx:
        assert tx.find("security_proposals")==[]
        assert tx.get("security_findings",id=finding["id"])["version"]==finding["version"]
