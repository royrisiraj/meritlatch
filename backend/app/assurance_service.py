"""Tenant-scoped engineering plane. Never writes operational policy/case state."""

from hashlib import sha256
import json
import os
import subprocess
import sys
from time import monotonic

from .api_models import Role
from .assurance_corpus import ROOT, artifact, canonical, fingerprint, load_corpus
from .assurance_models import Profile, ScenarioResult
from .assurance_scoring import compare, summarize
from .case_service import uid
from .errors import AppError, conflict, not_found

WORKER_TIMEOUT = 20
MAX_OUTPUT = 512*1024


def isolated_run(request):
    # No API keys, user configuration, PYTHONPATH or provider flags inherited.
    environment = {name:os.environ[name] for name in ("SystemRoot","WINDIR","TEMP","TMP","PATH","PATHEXT") if name in os.environ}
    environment.update(PYTHONUTF8="1",SENTINEL_PROVIDER_MODE="DISABLED",SENTINEL_ALLOW_BILLABLE="false")
    started = monotonic()
    try:
        done = subprocess.run([sys.executable,"-m","backend.app.assurance_worker"],input=canonical(request),
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding="utf-8",cwd=ROOT,
            env=environment,timeout=WORKER_TIMEOUT,shell=False)
        if done.returncode or len(done.stdout.encode())>MAX_OUTPUT:
            return None,"ISOLATED_EXECUTION_FAILED",monotonic()-started
        return json.loads(done.stdout),None,monotonic()-started
    except subprocess.TimeoutExpired:
        return None,"RUN_TIMEOUT",monotonic()-started
    except Exception:
        return None,"ISOLATED_EXECUTION_FAILED",monotonic()-started


class AssuranceService:
    def __init__(self,cases):
        self.cases = cases
        self.runner = isolated_run

    def auth(self,tx,token):
        now = self.cases._now()
        actor = self.cases._actor(tx,token,now)
        self.cases._role(actor,Role.ENGINEER)
        return actor,now

    @staticmethod
    def scoped(tx,table,actor,identifier):
        row = tx.get(table,id=identifier,tenant_id=actor["tenant_id"])
        if not row: raise not_found()
        return row

    @staticmethod
    def version(row,expected):
        if row["version"] != expected: raise conflict()

    @staticmethod
    def event(tx,actor,now,action,subject,version=1,outcome="RECORDED",reasons=()):
        tx.add("security_events",dict(id=uid(),tenant_id=actor["tenant_id"],created_at=now,actor_id=actor["id"],
            action=action,subject_id=subject,subject_version=version,outcome=outcome,reasons_json=canonical(list(reasons))))

    def candidate_view(self,row):
        current = artifact(row["profile"],row["version"])
        return {**row,"current_binding_valid":current["sha256"]==row["artifact_sha256"],"test_only":True,
                "policy_id":current["policy_id"],"policy_version":current["policy_version"],"published":False}

    def create_candidate(self,token,profile):
        with self.cases.repository.transaction() as tx:
            actor,now=self.auth(tx,token)
            value=artifact(profile,1)
            row=dict(id=uid(),tenant_id=actor["tenant_id"],created_at=now,profile=Profile(profile).value,
                version=1,review_revision=0,artifact_sha256=value["sha256"],software_revision=value["software_revision"],author_id=actor["id"])
            tx.add("security_candidates",row)
            self.event(tx,actor,now,"CANDIDATE_CREATED",row["id"])
            return self.candidate_view(row)

    def change_candidate(self,token,identifier,expected,profile):
        with self.cases.repository.transaction() as tx:
            actor,now=self.auth(tx,token)
            row=self.scoped(tx,"security_candidates",actor,identifier)
            self.version(row,expected)
            value=artifact(profile,expected+1)
            updates=dict(profile=Profile(profile).value,version=expected+1,review_revision=0,artifact_sha256=value["sha256"],
                         software_revision=value["software_revision"],author_id=actor["id"])
            tx.change("security_candidates",dict(id=identifier,tenant_id=actor["tenant_id"],version=expected),updates)
            self.event(tx,actor,now,"CANDIDATE_REVISED",identifier,expected+1,reasons=["PREVIOUS_REVIEW_INVALIDATED"])
            return self.candidate_view(row|updates)

    def run_view(self,tx,run,now):
        result=tx.get("security_results",run_id=run["id"],tenant_id=run["tenant_id"])
        value={k:v for k,v in run.items() if k not in {"key_hash","request_hash"}}
        candidate=tx.get("security_candidates",id=run["candidate_id"],tenant_id=run["tenant_id"])
        value["current_binding_valid"]=bool(candidate and candidate["version"]==run["candidate_version"] and
            candidate["artifact_sha256"]==run["artifact_sha256"] and self.candidate_view(candidate)["current_binding_valid"])
        if not result:
            return value|dict(status="INTERRUPTED" if now>run["created_at"]+WORKER_TIMEOUT+5 else "RUNNING",summary=None,results=[])
        return value|dict(status=result["status"],summary=json.loads(result["summary_json"]),results=json.loads(result["results_json"]),
            elapsed_seconds=result["elapsed_seconds"],completed_at=result["created_at"],error_code=result["error_code"])

    def start(self,token,request):
        scenarios,labels,corpus=load_corpus()
        key=sha256(request.idempotency_key.encode()).hexdigest()
        signature=fingerprint(request.model_dump(exclude={"idempotency_key"})|{"corpus_sha256":corpus["sha256"]})
        with self.cases.repository.transaction() as tx:
            actor,now=self.auth(tx,token)
            known=tx.get("security_runs",tenant_id=actor["tenant_id"],actor_id=actor["id"],key_hash=key)
            if known:
                if known["request_hash"] != signature:
                    raise AppError(409,"IDEMPOTENCY_CONFLICT","Use a new key for a different candidate/version/trigger.")
                self.event(tx,actor,now,"RUN_REPLAYED",known["id"])
                return None,self.run_view(tx,known,now)|{"operation_replayed":True}
            candidate=self.scoped(tx,"security_candidates",actor,request.candidate_id)
            self.version(candidate,request.expected_candidate_version)
            if not self.candidate_view(candidate)["current_binding_valid"]:
                raise AppError(409,"CANDIDATE_SOURCE_CHANGED","Revise the candidate and rerun its corpus before review.")
            recent=tx.page("security_runs",{"tenant_id":actor["tenant_id"]},51)
            if any(now<row["created_at"]+WORKER_TIMEOUT+5 and not tx.get("security_results",run_id=row["id"]) for row in recent):
                raise AppError(409,"RUN_IN_PROGRESS","Wait for the current isolated tenant run to finish.")
            if sum(row["actor_id"]==actor["id"] and row["created_at"]>now-300 for row in recent)>=10:
                raise AppError(429,"ASSURANCE_RATE_LIMIT","At most ten new runs per engineer in five minutes.")
            row=dict(id=uid(),tenant_id=actor["tenant_id"],created_at=now,candidate_id=candidate["id"],
                candidate_version=candidate["version"],artifact_sha256=candidate["artifact_sha256"],software_revision=candidate["software_revision"],
                corpus_id=corpus["id"],corpus_version=corpus["version"],corpus_sha256=corpus["sha256"],scenario_count=corpus["count"],
                actor_id=actor["id"],key_hash=key,request_hash=signature,trigger=request.trigger)
            tx.add("security_runs",row)
            self.event(tx,actor,now,"RUN_STARTED",row["id"])
            return (row,candidate,corpus),None

    def run(self,token,request):
        pending,replay=self.start(token,request)
        if replay is not None:return replay
        row,candidate,corpus=pending
        try:
            data,error,elapsed=self.runner(dict(profile=candidate["profile"],version=candidate["version"],
                artifact_sha256=row["artifact_sha256"],corpus_sha256=row["corpus_sha256"]))
        except Exception:
            data,error,elapsed=None,"ISOLATED_EXECUTION_FAILED",0
        return self.finish(token,row,data,error,elapsed)

    def finish(self,token,run,data,error,elapsed):
        scenarios,labels,corpus=load_corpus()
        results=[]
        if not error:
            try:
                if data["artifact"]["sha256"]!=run["artifact_sha256"] or data["corpus"]["sha256"]!=run["corpus_sha256"]:
                    raise ValueError("Changed artifact")
                rows=[ScenarioResult.model_validate(item) for item in data["results"]]
                if [(item.scenario_id,item.scenario_version) for item in rows]!=[(s.id,s.version) for s in scenarios]:
                    raise ValueError("Incomplete or duplicate results")
                # Recompute from our pinned labels. Worker passed/expected/summary
                # fields cannot redefine success or overwrite the parent oracle.
                results=[compare(s,labels[(s.id,s.version)],item.actual) for s,item in zip(scenarios,rows)]
            except Exception:
                error="INVALID_WORKER_RESULT"
        summary=summarize(results,len(scenarios))
        auth_error=None
        with self.cases.repository.transaction() as tx:
            now=self.cases._now()
            original_actor=dict(id=run["actor_id"],tenant_id=run["tenant_id"])
            try:
                actor,_=self.auth(tx,token)
                if actor["id"]!=run["actor_id"] or actor["tenant_id"]!=run["tenant_id"]:
                    raise AppError(403,"ROLE_FORBIDDEN","This run belongs to a different authenticated actor.")
            except AppError as exc:
                actor=original_actor
                error="RUN_AUTHORIZATION_CHANGED"
                auth_error=exc
            prior=tx.get("security_results",run_id=run["id"],tenant_id=run["tenant_id"])
            if prior:
                if auth_error:raise auth_error
                return self.run_view(tx,run,now)
            candidate=tx.get("security_candidates",id=run["candidate_id"],tenant_id=run["tenant_id"])
            stale=(candidate["version"]!=run["candidate_version"] or candidate["artifact_sha256"]!=run["artifact_sha256"] or
                artifact(candidate["profile"],candidate["version"])["sha256"]!=run["artifact_sha256"] or corpus["sha256"]!=run["corpus_sha256"])
            status="FAILED" if error or summary["unevaluable"] else "STALE" if stale else "COMPLETE"
            tx.add("security_results",dict(id=uid(),tenant_id=run["tenant_id"],created_at=now,run_id=run["id"],status=status,
                summary_json=canonical(summary),results_json=canonical([item.model_dump(mode="json") for item in results]),
                elapsed_seconds=max(0,float(elapsed)),error_code=error or ("CANDIDATE_CHANGED" if stale else None)))
            if not error:
                for item in results:
                    if not item.passed and item.mismatch!="UNEVALUABLE":self.finding(tx,actor,now,run,item)
            self.event(tx,actor,now,"RUN_FINISHED",run["id"],outcome=status,reasons=[error] if error else [])
            response=self.run_view(tx,run,now)
        if auth_error:raise auth_error
        return response

    def finding(self,tx,actor,now,run,item):
        expected=item.expected.model_dump(mode="json")
        actual=item.actual.model_dump(mode="json")
        key=fingerprint(dict(artifact=run["artifact_sha256"],corpus=run["corpus_sha256"],scenario=item.scenario_id,
            version=item.scenario_version,expected=expected,actual=actual,mismatch=item.mismatch))
        row=tx.get("security_findings",tenant_id=run["tenant_id"],fingerprint=key)
        if row:
            updates=dict(version=row["version"]+1,last_seen=now,occurrences=row["occurrences"]+1)
            tx.change("security_findings",dict(id=row["id"],tenant_id=run["tenant_id"],version=row["version"]),updates)
            row|=updates
        else:
            row=dict(id=uid(),tenant_id=run["tenant_id"],created_at=now,fingerprint=key,version=1,status="OPEN",
                severity="HIGH" if item.mismatch in {"FALSE_APPROVAL","REVIEW_BYPASS"} else "LOW" if item.mismatch=="REASON_MISMATCH" else "MEDIUM",
                mismatch=item.mismatch,scenario_id=item.scenario_id,scenario_version=item.scenario_version,candidate_id=run["candidate_id"],
                artifact_sha256=run["artifact_sha256"],policy_id="fictional-pump-inspection",policy_version="1.0.0",corpus_sha256=run["corpus_sha256"],
                expected_json=canonical(expected),actual_json=canonical(actual),owner_id=actor["id"],first_seen=now,last_seen=now,occurrences=1)
            tx.add("security_findings",row)
        tx.add("security_occurrences",dict(id=uid(),tenant_id=run["tenant_id"],created_at=now,finding_id=row["id"],run_id=run["id"]))
        self.event(tx,actor,now,"FINDING_REPRODUCED",row["id"],row["version"],"MISMATCH",[item.mismatch])

    @staticmethod
    def finding_view(row):
        return {k:v for k,v in row.items() if k not in {"expected_json","actual_json"}} | dict(
            expected=json.loads(row["expected_json"]),actual=json.loads(row["actual_json"]),source="SYNTHETIC",
            reproduction_reference=f"/v1/alerts/{row['id']}",
            reproduction_steps=["Run the full pinned corpus against the exact candidate artifact hash.",
                f"Inspect scenario {row['scenario_id']} version {row['scenario_version']} in its restricted run results.",
                "Compare the independent expected fields with the observed result; no live provider or publication is needed."],
            severity_rationale="Unauthorized progression" if row["severity"]=="HIGH" else "Regression/availability or diagnostic contract mismatch")

    def list(self,token,kind,limit=25,before=None,filters=None):
        table={"runs":"security_runs","findings":"security_findings","candidates":"security_candidates","audit":"security_events"}[kind]
        with self.cases.repository.transaction() as tx:
            actor,now=self.auth(tx,token)
            keys={"tenant_id":actor["tenant_id"]}|{k:v for k,v in (filters or {}).items() if v is not None}
            rows=tx.page(table,keys,limit+1,before)
            visible=rows[:limit]
            items=[self.run_view(tx,row,now) if kind=="runs" else self.finding_view(row) if kind=="findings" else
                self.candidate_view(row) if kind=="candidates" else {k:v for k,v in row.items() if k!="reasons_json"}|{"reason_codes":json.loads(row["reasons_json"])} for row in visible]
            self.event(tx,actor,now,"ENGINEERING_LIST_READ",table)
            return dict(items=items,next_cursor=visible[-1]["id"] if len(rows)>limit else None)

    def get(self,token,kind,identifier):
        table={"run":"security_runs","finding":"security_findings","candidate":"security_candidates","gate":"security_gates"}[kind]
        with self.cases.repository.transaction() as tx:
            actor,now=self.auth(tx,token)
            row=self.scoped(tx,table,actor,identifier)
            self.event(tx,actor,now,"ENGINEERING_RECORD_READ",identifier)
            if kind=="run":return self.run_view(tx,row,now)
            if kind=="candidate":return self.candidate_view(row)
            if kind=="gate":return self.gate_view(tx,row)
            result=self.finding_view(row)
            occurrences=tx.page("security_occurrences",{"tenant_id":actor["tenant_id"],"finding_id":identifier},101)
            proposals=tx.page("security_proposals",{"tenant_id":actor["tenant_id"],"finding_id":identifier},101)
            result.update(occurrences_history=occurrences[:100],proposals=proposals[:100],history_truncated=len(occurrences)>100 or len(proposals)>100)
            result["run_references"]=[f"/v1/redteam/runs/{item['run_id']}" for item in occurrences[:100]]
            return result

    def triage(self,token,identifier,request):
        with self.cases.repository.transaction() as tx:
            actor,now=self.auth(tx,token)
            row=self.scoped(tx,"security_findings",actor,identifier)
            self.version(row,request.expected_version)
            if request.status=="VERIFIED":
                gate=self.scoped(tx,"security_gates",actor,request.gate_id)
                proposal=tx.get("security_proposals",id=gate["proposal_id"],tenant_id=actor["tenant_id"])
                if gate["decision"]!="READY_FOR_MANUAL_RELEASE" or not self.gate_view(tx,gate)["current_binding_valid"] or not proposal or proposal["finding_id"]!=identifier:
                    raise AppError(409,"VERIFIED_GATE_REQUIRED","Use the current accepted remediation gate for this finding.")
            updates=dict(status=request.status,version=row["version"]+1)
            tx.change("security_findings",dict(id=identifier,tenant_id=actor["tenant_id"],version=row["version"]),updates)
            self.event(tx,actor,now,"FINDING_TRIAGED",identifier,updates["version"],request.status,[request.reason])
            return self.finding_view(row|updates)

    def propose(self,token,identifier,request):
        with self.cases.repository.transaction() as tx:
            actor,now=self.auth(tx,token)
            finding=self.scoped(tx,"security_findings",actor,identifier)
            self.version(finding,request.expected_version)
            candidate=self.scoped(tx,"security_candidates",actor,request.candidate_id)
            self.version(candidate,request.expected_candidate_version)
            if not self.candidate_view(candidate)["current_binding_valid"]:raise conflict()
            row=dict(id=uid(),tenant_id=actor["tenant_id"],created_at=now,finding_id=identifier,candidate_id=candidate["id"],
                candidate_version=candidate["version"],artifact_sha256=candidate["artifact_sha256"],author_id=actor["id"],remediation=request.remediation)
            tx.add("security_proposals",row)
            tx.change("security_findings",dict(id=identifier,tenant_id=actor["tenant_id"],version=finding["version"]),dict(version=finding["version"]+1,status="REMEDIATION_PROPOSED"))
            self.event(tx,actor,now,"REMEDIATION_PROPOSED",row["id"])
            return row

    def matching_run(self,tx,actor,candidate,run_id):
        run=self.scoped(tx,"security_runs",actor,run_id)
        result=tx.get("security_results",tenant_id=actor["tenant_id"],run_id=run_id)
        _,_,corpus=load_corpus()
        if not result or result["status"]!="COMPLETE" or run["candidate_id"]!=candidate["id"] or run["candidate_version"]!=candidate["version"] or run["artifact_sha256"]!=candidate["artifact_sha256"] or run["corpus_sha256"]!=corpus["sha256"] or not self.candidate_view(candidate)["current_binding_valid"]:
            raise AppError(409,"CURRENT_COMPLETE_RUN_REQUIRED","Run the complete current corpus against this exact candidate revision.")
        return run,json.loads(result["summary_json"])

    def review(self,token,identifier,request):
        with self.cases.repository.transaction() as tx:
            actor,now=self.auth(tx,token)
            candidate=self.scoped(tx,"security_candidates",actor,identifier)
            self.version(candidate,request.expected_version)
            if candidate["review_revision"]!=request.expected_review_version:raise conflict()
            proposal=self.scoped(tx,"security_proposals",actor,request.proposal_id)
            if (proposal["candidate_id"],proposal["candidate_version"],proposal["artifact_sha256"])!=(identifier,candidate["version"],candidate["artifact_sha256"]):raise conflict()
            if actor["id"] in {proposal["author_id"],candidate["author_id"]}:
                raise AppError(403,"INDEPENDENT_ENGINEERING_REVIEW_REQUIRED","A different authenticated engineer must review this exact artifact.")
            run,summary=self.matching_run(tx,actor,candidate,request.run_id)
            row=dict(id=uid(),tenant_id=actor["tenant_id"],created_at=now,proposal_id=proposal["id"],candidate_id=identifier,
                candidate_version=candidate["version"],artifact_sha256=candidate["artifact_sha256"],run_id=run["id"],corpus_sha256=run["corpus_sha256"],
                reviewer_id=actor["id"],decision=request.decision,reason=request.reason)
            row["review_revision"]=candidate["review_revision"]+1
            tx.add("security_reviews",row)
            tx.change("security_candidates",dict(id=identifier,tenant_id=actor["tenant_id"],version=candidate["version"],
                review_revision=candidate["review_revision"]),dict(review_revision=row["review_revision"]))
            self.event(tx,actor,now,"CANDIDATE_REVIEWED",row["id"],candidate["version"],request.decision,[request.reason])
            return row

    def gate_view(self,tx,row):
        candidate=tx.get("security_candidates",id=row["candidate_id"],tenant_id=row["tenant_id"])
        _,_,corpus=load_corpus()
        run=tx.get("security_runs",id=row["run_id"],tenant_id=row["tenant_id"])
        review=tx.get("security_reviews",id=row["review_id"],tenant_id=row["tenant_id"]) if row["review_id"] else None
        reviewer=tx.get("users",id=review["reviewer_id"],tenant_id=row["tenant_id"],active=True) if review else None
        valid=bool(candidate and candidate["version"]==row["candidate_version"] and candidate["artifact_sha256"]==row["artifact_sha256"] and
            self.candidate_view(candidate)["current_binding_valid"] and run["corpus_sha256"]==corpus["sha256"] and
            (row["decision"]!="READY_FOR_MANUAL_RELEASE" or (reviewer and reviewer["role"]=="ENGINEER" and review["review_revision"]==candidate["review_revision"])))
        return {k:v for k,v in row.items() if k!="reasons_json"}|dict(
            historical_decision=row["decision"],decision=row["decision"] if valid else "BLOCKED",
            reason_codes=json.loads(row["reasons_json"])+([] if valid else ["ARTIFACT_OR_REVIEW_CHANGED"]),
            current_binding_valid=valid,published=False)

    def gate(self,token,identifier,request):
        with self.cases.repository.transaction() as tx:
            actor,now=self.auth(tx,token)
            candidate=self.scoped(tx,"security_candidates",actor,identifier)
            self.version(candidate,request.expected_version)
            run,summary=self.matching_run(tx,actor,candidate,request.run_id)
            reasons=[]
            if summary["false_approvals"] or summary["review_bypasses"]:reasons.append("FALSE_APPROVAL_PRESENT")
            if summary["regression_failures"] or summary["unevaluable"] or summary["total_executed"]!=run["scenario_count"]:reasons.append("MANDATORY_REGRESSION_FAILED")
            if summary["false_rejections"] or summary["true_negative"]<1 or summary["review_abstentions"]:reasons.append("VALID_CASE_REQUIREMENTS_FAILED")
            review=self.scoped(tx,"security_reviews",actor,request.review_id) if request.review_id else None
            proposal=None
            if review:
                reviewer=tx.get("users",id=review["reviewer_id"],tenant_id=actor["tenant_id"],active=True)
                proposal=tx.get("security_proposals",id=review["proposal_id"],tenant_id=actor["tenant_id"])
                if (review["candidate_id"],review["candidate_version"],review["artifact_sha256"],review["run_id"],review["corpus_sha256"],review["decision"])!=(identifier,candidate["version"],candidate["artifact_sha256"],run["id"],run["corpus_sha256"],"APPROVE") or not reviewer or reviewer["role"]!="ENGINEER" or review["review_revision"]!=candidate["review_revision"]:
                    reasons.append("HUMAN_REVIEW_INVALID")
            else:reasons.append("HUMAN_REVIEW_REQUIRED")
            row=dict(id=uid(),tenant_id=actor["tenant_id"],created_at=now,candidate_id=identifier,candidate_version=candidate["version"],
                artifact_sha256=candidate["artifact_sha256"],run_id=run["id"],review_id=review["id"] if review else None,
                proposal_id=proposal["id"] if proposal else None,actor_id=actor["id"],decision="BLOCKED" if reasons else "READY_FOR_MANUAL_RELEASE",reasons_json=canonical(reasons))
            tx.add("security_gates",row)
            self.event(tx,actor,now,"RELEASE_GATE_EVALUATED",row["id"],candidate["version"],row["decision"],reasons)
            return self.gate_view(tx,row)

    def suggest(self,token):
        with self.cases.repository.transaction() as tx:
            actor,now=self.auth(tx,token)
            self.event(tx,actor,now,"SUGGESTION_BLOCKED","DISABLED",outcome="BLOCKED",reasons=["GEMINI_FROZEN"])
        return dict(status="BLOCKED",source="DISABLED",reason_codes=["GEMINI_FROZEN"],candidates=[])
