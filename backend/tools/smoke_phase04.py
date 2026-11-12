"""Actual TCP/HTTP engineering workflow, disposable fiction and no live providers."""

import json
from pathlib import Path
import secrets
import socket
from tempfile import TemporaryDirectory
from threading import Thread
import time

import httpx
import uvicorn

from backend.app.api import create_app
from backend.app.provisioning import provision_user
from backend.app.settings import Settings


class Journey:
    def __init__(self,client,ids,passwords):
        self.client,self.ids,self.passwords=client,ids,passwords
        self.tokens={}

    def login(self,name):
        response=self.client.post("/v1/auth/login",json=dict(tenant_id="phase04-b" if name=="other_engineer" else "phase04-a",
            username=name,password=self.passwords[name]))
        assert response.status_code==200,"Isolated login failed"
        self.tokens[name]=response.json()["access_token"]

    def call(self,method,path,body=None,actor="engineer",status=200):
        response=self.client.request(method,path,json=body,headers={"Authorization":"Bearer "+self.tokens[actor]})
        assert response.status_code==status,f"Unexpected {response.status_code} for {method} {path}"
        return response.json()

    def candidate(self,profile):
        return self.call("POST","/v1/redteam/candidates",{"profile":profile},status=201)

    def run(self,candidate,key):
        return self.call("POST","/v1/redteam/run",dict(candidate_id=candidate["id"],expected_candidate_version=candidate["version"],idempotency_key=key))

    def propose(self,finding,candidate):
        return self.call("POST",f"/v1/alerts/{finding['id']}/remediations",dict(expected_version=finding["version"],
            candidate_id=candidate["id"],expected_candidate_version=candidate["version"],remediation="RESTORE_BASELINE_BOUNDS"),status=201)

    def review(self,candidate,run,proposal):
        body=dict(expected_version=candidate["version"],expected_review_version=0,proposal_id=proposal["id"],run_id=run["id"],
            decision="APPROVE",reason="REGRESSION_REVIEWED")
        self.call("POST",f"/v1/redteam/candidates/{candidate['id']}/reviews",body,status=403)
        return self.call("POST",f"/v1/redteam/candidates/{candidate['id']}/reviews",body,actor="reviewer",status=201)

    def gate(self,candidate,run,review=None):
        return self.call("POST",f"/v1/redteam/candidates/{candidate['id']}/release-gate",dict(expected_version=candidate["version"],
            run_id=run["id"],review_id=review["id"] if review else None))

    @staticmethod
    def record(name,run,gate=None):
        review_matches=sum(item["expected"]["decision"]=="NEEDS_REVIEW" and item["passed"] for item in run["results"])
        print(json.dumps(dict(scenario=name,source="SYNTHETIC",run_id=run["id"],status=run["status"],
            artifact_sha256=run["artifact_sha256"],corpus_sha256=run["corpus_sha256"],summary=run["summary"],
            exact_review_matches=review_matches,gate=gate["decision"] if gate else None,published=False),sort_keys=True))

    def execute(self):
        weak=self.candidate("WEAK_TEST_ONLY")
        operation=secrets.token_urlsafe(24)
        weakrun=self.run(weak,operation)
        assert weakrun["status"]=="COMPLETE" and weakrun["summary"]["false_approvals"]==1 and weakrun["summary"]["review_bypasses"]==1
        saved=self.call("GET",f"/v1/redteam/runs/{weakrun['id']}")
        assert saved["summary"]==weakrun["summary"]
        findings=self.call("GET","/v1/alerts?severity=HIGH")["items"]
        finding=next(item for item in findings if item["scenario_id"]=="A02")
        detail=self.call("GET",f"/v1/alerts/{finding['id']}")
        assert detail["expected"]["decision"]=="DENY" and detail["actual"]["decision"]=="ALLOW"
        text=json.dumps(detail)
        assert "FICTIONAL-ASSURANCE-CHALLENGE" not in text and "Ignore all rules" not in text
        assert all(token not in text for token in self.tokens.values())
        ack=self.call("POST",f"/v1/alerts/{finding['id']}/triage",dict(expected_version=finding["version"],status="ACKNOWLEDGED",reason="REPRODUCED"))
        self.call("POST",f"/v1/alerts/{finding['id']}/triage",dict(expected_version=finding["version"],status="ACKNOWLEDGED",reason="REPRODUCED"),status=409)
        weakproposal=self.propose(ack,weak)
        weakreview=self.review(weak,weakrun,weakproposal)
        weakgate=self.gate(weak,weakrun,weakreview)
        assert weakgate["decision"]=="BLOCKED" and "FALSE_APPROVAL_PRESENT" in weakgate["reason_codes"]
        self.record("WEAK_CANDIDATE_REPRODUCED",weakrun,weakgate)
        replay=self.run(weak,operation)
        assert replay["operation_replayed"] and replay["id"]==weakrun["id"]
        assert self.call("GET",f"/v1/alerts/{finding['id']}")["occurrences"]==1

        safe=self.candidate("SAFE_BASELINE")
        saferun=self.run(safe,secrets.token_urlsafe(24))
        assert saferun["summary"]["passed"]==38 and saferun["summary"]["regression_failures"]==0
        assert self.gate(safe,saferun)["decision"]=="BLOCKED"  # Green alone cannot replace review.
        current=self.call("GET",f"/v1/alerts/{finding['id']}")
        proposal=self.propose(current,safe)
        review=self.review(safe,saferun,proposal)
        gate=self.gate(safe,saferun,review)
        assert gate["decision"]=="READY_FOR_MANUAL_RELEASE" and gate["current_binding_valid"] and not gate["published"]
        assert self.call("GET",f"/v1/redteam/release-gates/{gate['id']}")["decision"]==gate["decision"]
        current=self.call("GET",f"/v1/alerts/{finding['id']}")
        verified=self.call("POST",f"/v1/alerts/{finding['id']}/triage",dict(expected_version=current["version"],
            status="VERIFIED",reason="REGRESSION_VERIFIED",gate_id=gate["id"]))
        assert verified["status"]=="VERIFIED"
        self.record("SAFE_REMEDIATION_REVIEWED",saferun,gate)

        strict=self.candidate("OVERRESTRICTIVE_TEST_ONLY")
        strict_run=self.run(strict,secrets.token_urlsafe(24))
        assert strict_run["summary"]["false_rejections"]==2 and strict_run["summary"]["review_abstentions"]==8
        strict_gate=self.gate(strict,strict_run)
        assert strict_gate["decision"]=="BLOCKED"
        self.record("FALSE_REJECTION_CONTROL",strict_run,strict_gate)

        for actor in ("manager","contractor","agent"):
            self.call("GET","/v1/alerts",actor=actor,status=403)
            self.call("POST","/v1/redteam/run",dict(candidate_id=weak["id"],expected_candidate_version=1,idempotency_key=secrets.token_urlsafe(20)),actor=actor,status=403)
        self.call("GET",f"/v1/redteam/candidates/{weak['id']}",actor="other_engineer",status=404)
        assert self.call("GET","/v1/alerts",actor="other_engineer")["items"]==[]
        assert self.call("POST","/v1/redteam/suggest")["status"]=="BLOCKED"
        job=self.call("POST","/v1/jobs",dict(asset_id="PUMP-042",contractor_id=self.ids["contractor"],
            engineer_id=self.ids["engineer"],service_agent_id=self.ids["agent"]),actor="manager",status=201)
        case=self.call("POST","/v1/cases",{"job_id":job["id"]},actor="manager",status=201)
        self.call("POST",f"/v1/cases/{case['id']}/approvals",{"expected_case_version":case["version"]},status=403)
        audit=self.call("GET","/v1/redteam/audit?limit=50")["items"]
        assert any(item["action"]=="RELEASE_GATE_EVALUATED" for item in audit)
        print("PASS Phase 04 actual TCP/HTTP; SYNTHETIC and isolated MOCK_AI only; Gemini frozen; no publication")


def main():
    with TemporaryDirectory(prefix="sentinel-phase04-http-") as folder:
        root=Path(folder)
        app=create_app(Settings(database_path=root/"smoke.sqlite",media_root=root/"private",provider_mode="DISABLED"))
        ids,passwords={},{}
        for name,role in (("engineer","ENGINEER"),("reviewer","ENGINEER"),("manager","MANAGER"),
                          ("contractor","CONTRACTOR"),("agent","SERVICE_AGENT"),("other_engineer","ENGINEER")):
            passwords[name]=secrets.token_urlsafe(24)
            ids[name]=provision_user(app.state.service.repository,"phase04-b" if name=="other_engineer" else "phase04-a",name,role,passwords[name])["id"]
        listener=socket.socket()
        listener.bind(("127.0.0.1",0))
        listener.listen(128)
        server=uvicorn.Server(uvicorn.Config(app,log_level="critical",access_log=False))
        thread=Thread(target=lambda:server.run(sockets=[listener]),daemon=True)
        thread.start()
        try:
            deadline=time.monotonic()+10
            while not server.started and thread.is_alive() and time.monotonic()<deadline:time.sleep(0.02)
            if not server.started:raise RuntimeError("Local smoke server did not start")
            with httpx.Client(base_url=f"http://127.0.0.1:{listener.getsockname()[1]}",timeout=35) as client:
                journey=Journey(client,ids,passwords)
                for name in passwords:journey.login(name)
                journey.execute()
        finally:
            server.should_exit=True
            thread.join(timeout=10)
            listener.close()
            app.state.service.repository.close()
            if thread.is_alive():raise RuntimeError("Local smoke server did not stop")


if __name__=="__main__":
    main()
