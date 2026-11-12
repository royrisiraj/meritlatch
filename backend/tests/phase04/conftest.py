import secrets
import shutil
from copy import deepcopy
from threading import Lock

import pytest
from fastapi.testclient import TestClient

from backend.app.api import create_app
from backend.app.settings import Settings
from backend.tests.phase01.conftest import account_template, Clock, World
from backend.tests.phase02.conftest import no_external_connections
from backend.app.assurance_corpus import artifact,load_corpus
from backend.app.assurance_service import isolated_run


class SecurityWorld(World):
    def request(self,method,path,key="a_engineer",data=None):
        return super().request(method,path,key,data)

    def candidate(self,profile="SAFE_BASELINE",key="a_engineer"):
        result=self.request("POST","/v1/redteam/candidates",key,{"profile":profile})
        assert result.status_code==201,result.text
        return result.json()

    def run(self,candidate,key="a_engineer",operation=None):
        return self.request("POST","/v1/redteam/run",key,dict(candidate_id=candidate["id"],
            expected_candidate_version=candidate["version"],idempotency_key=operation or secrets.token_urlsafe(20)))

    def findings(self):
        return self.request("GET","/v1/alerts?limit=50").json()["items"]

    def proposal(self,finding,candidate):
        return self.request("POST",f"/v1/alerts/{finding['id']}/remediations",data=dict(expected_version=finding["version"],
            candidate_id=candidate["id"],expected_candidate_version=candidate["version"],remediation="RESTORE_BASELINE_BOUNDS"))

    def review(self,candidate,run,proposal,key="a_reviewer",**extra):
        return self.request("POST",f"/v1/redteam/candidates/{candidate['id']}/reviews",key,dict(expected_version=candidate["version"],
            proposal_id=proposal["id"],run_id=run["id"],decision="APPROVE",reason="REGRESSION_REVIEWED",**extra))

    def gate(self,candidate,run,review=None):
        return self.request("POST",f"/v1/redteam/candidates/{candidate['id']}/release-gate",data=dict(
            expected_version=candidate["version"],run_id=run["id"],review_id=review["id"] if review else None))

    def correction(self):
        weak=self.candidate("WEAK_TEST_ONLY")
        weakrun=self.run(weak).json()
        finding=next(item for item in self.findings() if item["scenario_id"]=="A02")
        safe=self.candidate()
        saferun=self.run(safe).json()
        proposal=self.proposal(finding,safe).json()
        review=self.review(safe,saferun,proposal).json()
        return weak,weakrun,finding,safe,saferun,proposal,review


@pytest.fixture
def sec(tmp_path,account_template):
    template,ids,passwords,tokens=account_template
    path=tmp_path/"assurance.sqlite"
    shutil.copy2(template,path)
    clock=Clock()
    app=create_app(Settings(database_path=path,environment="test",allow_synthetic=True,media_root=tmp_path/"private"),clock=clock)
    with TestClient(app,raise_server_exceptions=False) as client:
        yield SecurityWorld(app,client,ids,passwords,tokens,clock)


@pytest.fixture(scope="session")
def executed_fixtures():
    """Cache actual isolated executions for parent API concurrency/CRUD tests.

    The TCP smoke always uses fresh workers. Cached outputs remain SYNTHETIC,
    not fabricated expected answers, and parent recomputes all oracle comparisons.
    """
    bank,lock={},Lock()
    def run(request):
        key=(request["profile"],request["version"])
        with lock:
            if key not in bank:
                value=artifact(*key)
                _,_,corpus=load_corpus()
                data,error,elapsed=isolated_run(dict(profile=key[0],version=key[1],artifact_sha256=value["sha256"],corpus_sha256=corpus["sha256"]))
                assert error is None
                bank[key]=(data,error,elapsed)
            data,error,elapsed=bank[key]
            assert data["artifact"]["sha256"]==request["artifact_sha256"]
            assert data["corpus"]["sha256"]==request["corpus_sha256"]
            return deepcopy(data),error,elapsed
    return run


@pytest.fixture
def fast(sec,executed_fixtures,monkeypatch):
    monkeypatch.setattr(sec.app.state.assurance,"runner",executed_fixtures)
    return sec
