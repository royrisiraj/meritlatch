import json


def test_real_isolated_safe_and_deliberate_weak_candidate_execute_against_independent_oracle(sec):
    weak=sec.candidate("WEAK_TEST_ONLY")
    result=sec.run(weak)
    assert result.status_code==200,result.text
    run=result.json()
    assert run["status"]=="COMPLETE" and run["summary"]["total_executed"]==38
    assert run["summary"]["false_approvals"]==1 and run["summary"]["review_bypasses"]==1
    actual=next(r for r in run["results"] if r["scenario_id"]=="A02")
    assert actual["expected"]["decision"]=="DENY" and actual["actual"]["decision"]=="ALLOW"
    assert actual["mismatch"]=="FALSE_APPROVAL"
    finding=next(item for item in sec.findings() if item["scenario_id"]=="A02")
    assert finding["severity"]=="HIGH" and finding["occurrences"]==1
    blocked=sec.gate(weak,run).json()
    assert blocked["decision"]=="BLOCKED" and "FALSE_APPROVAL_PRESENT" in blocked["reason_codes"]
    safe=sec.candidate()
    good=sec.run(safe).json()
    assert good["summary"]["passed"]==38 and good["summary"]["failed"]==0
    assert good["summary"]["true_positive"]==26 and good["summary"]["true_negative"]==6
    assert good["summary"]["review_expected"]==6
    assert next(r for r in good["results"] if r["scenario_id"]=="A02")["actual"]["decision"]=="DENY"
    assert len(sec.findings())==2  # Correct denials create no alert.
    with sec.service.repository.transaction() as tx:
        for table in ("cases","policies","approvals","action_runs","manager_reviews"):
            assert tx.find(table)==[]  # Isolated worker never writes the outer business DB.


def test_false_rejections_are_measured_and_deny_everything_cannot_pass(fast):
    candidate=fast.candidate("OVERRESTRICTIVE_TEST_ONLY")
    run=fast.run(candidate).json()
    m=run["summary"]
    assert m["false_rejections"]==2 and m["false_rejection_denominator"]==4
    assert m["false_rejection_rate"]==0.5 and m["review_abstentions"]==8
    assert m["regression_failures"]==19
    assert fast.gate(candidate,run).json()["decision"]=="BLOCKED"


def test_findings_deduplicate_preserve_occurrences_and_redact_untrusted_data(fast):
    weak=fast.candidate("WEAK_TEST_ONLY")
    first=fast.run(weak).json()
    initial=fast.findings()
    second=fast.run(weak).json()
    repeated=fast.findings()
    assert {f["id"] for f in initial}=={f["id"] for f in repeated}
    assert all(f["occurrences"]==2 and f["version"]==2 for f in repeated)
    details=fast.request("GET",f"/v1/alerts/{repeated[0]['id']}").json()
    assert {r["run_id"] for r in details["occurrences_history"]}=={first["id"],second["id"]}
    text=json.dumps(details)
    for forbidden in ("FICTIONAL-ASSURANCE-CHALLENGE","Ignore all rules","binding_json","key_hash","observation_json"):
        assert forbidden not in text
    assert all(token not in text for token in fast.tokens.values())
    assert fast.request("GET","/v1/alerts?severity=LOW").json()["items"]==[]
    assert len(fast.request("GET","/v1/alerts?severity=HIGH&policy_id=fictional-pump-inspection").json()["items"])==2


def test_human_review_and_safe_gate_require_independent_authenticated_engineer(fast):
    weak,wr,finding,safe,sr,proposal,review=fast.correction()
    assert review["decision"]=="APPROVE" and review["reviewer_id"]==fast.ids["a_reviewer"]
    gate=fast.gate(safe,sr,review)
    assert gate.status_code==200,gate.text
    accepted=gate.json()
    assert accepted["decision"]=="READY_FOR_MANUAL_RELEASE" and accepted["published"] is False
    assert accepted["current_binding_valid"] is True
    current=fast.request("GET",f"/v1/alerts/{finding['id']}").json()
    verified=fast.request("POST",f"/v1/alerts/{finding['id']}/triage",data=dict(expected_version=current["version"],
        status="VERIFIED",reason="REGRESSION_VERIFIED",gate_id=accepted["id"]))
    assert verified.status_code==200 and verified.json()["status"]=="VERIFIED"
    audit=fast.request("GET","/v1/redteam/audit?limit=50").json()["items"]
    assert {"REMEDIATION_PROPOSED","CANDIDATE_REVIEWED","RELEASE_GATE_EVALUATED","FINDING_TRIAGED"}<={r["action"] for r in audit}
    with fast.service.repository.transaction() as tx:
        assert not tx.find("policies") and not tx.find("approvals") and not tx.find("cases")


def test_self_review_fails_and_even_human_approval_cannot_release_weak_candidate(fast):
    weak=fast.candidate("WEAK_TEST_ONLY")
    run=fast.run(weak).json()
    finding=fast.findings()[0]
    proposal=fast.proposal(finding,weak).json()
    assert fast.review(weak,run,proposal,key="a_engineer").status_code==403
    review=fast.review(weak,run,proposal).json()
    gate=fast.gate(weak,run,review).json()
    assert gate["decision"]=="BLOCKED" and "FALSE_APPROVAL_PRESENT" in gate["reason_codes"]


def test_dismissal_requires_reason_and_does_not_erase_failing_regression(fast):
    weak=fast.candidate("WEAK_TEST_ONLY")
    run=fast.run(weak).json()
    finding=fast.findings()[0]
    path=f"/v1/alerts/{finding['id']}/triage"
    assert fast.request("POST",path,data=dict(expected_version=1,status="DISMISSED")).status_code==422
    assert fast.request("POST",path,data=dict(expected_version=1,status="DISMISSED",reason="REPRODUCED")).status_code==422
    result=fast.request("POST",path,data=dict(expected_version=1,status="DISMISSED",reason="ACCEPTED_TEST_ONLY_RISK"))
    assert result.status_code==200 and result.json()["status"]=="DISMISSED"
    assert fast.request("POST",path,data=dict(expected_version=1,status="ACKNOWLEDGED",reason="REPRODUCED")).status_code==409
    assert fast.gate(weak,run).json()["decision"]=="BLOCKED"
    assert fast.request("GET",f"/v1/redteam/runs/{run['id']}").json()["summary"]["false_approvals"]==1
