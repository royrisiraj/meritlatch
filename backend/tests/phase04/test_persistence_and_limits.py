from dataclasses import replace
import json
import subprocess

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,insert,select
from sqlalchemy.exc import IntegrityError

from backend.app.api import create_app
from backend.app.assurance_corpus import CORPUS_ROOT,load_corpus
from backend.app.assurance_service import isolated_run
from backend.app.repository import metadata


def test_restart_preserves_runs_findings_review_and_current_gate(fast):
    _,_,finding,safe,run,proposal,review=fast.correction()
    gate=fast.gate(safe,run,review).json()
    fast.service.repository.close()
    app=create_app(fast.app.state.settings,clock=fast.clock)
    with TestClient(app) as client:
        saved=client.get(f"/v1/redteam/runs/{run['id']}",headers=fast.headers("a_engineer")).json()
        assert saved["status"]=="COMPLETE" and saved["summary"]["passed"]==38
        current=client.get(f"/v1/redteam/release-gates/{gate['id']}",headers=fast.headers("a_engineer")).json()
        assert current["decision"]=="READY_FOR_MANUAL_RELEASE" and current["current_binding_valid"]
        details=client.get(f"/v1/alerts/{finding['id']}",headers=fast.headers("a_engineer")).json()
        assert details["proposals"][0]["id"]==proposal["id"] and details["run_references"]


@pytest.mark.parametrize("table",["security_runs","security_results","security_occurrences","security_proposals","security_reviews","security_gates","security_events"])
def test_security_histories_reject_ordinary_rewrites(sec,table):
    with sec.service.repository.transaction() as tx:
        with pytest.raises(ValueError,match="Append-only"):
            tx.change(table,{"id":"any"},{})
    sec.candidate()
    if table=="security_events":
        with pytest.raises(IntegrityError,match="append-only record"):
            with sec.service.repository.engine.begin() as connection:
                connection.exec_driver_sql("DELETE FROM security_events")


def test_security_migration_is_additive_idempotent_and_rejects_unknown_version(sec):
    repo=sec.service.repository
    repo.migrate()
    repo.migrate()
    with repo.transaction() as tx:
        for namespace in ("schema_migrations","media_schema_migrations","workflow_schema_migrations","security_schema_migrations"):
            assert tx.find(namespace)==[{"version":1}]
        tx.change("security_schema_migrations",{"version":1},{"version":999})
    with pytest.raises(ValueError,match="Unsupported security schema"):
        repo.migrate()


def test_upgrade_from_phase03_preserves_cases_and_adds_empty_security_plane(sec,tmp_path):
    _,case=sec.new()
    path=tmp_path/"phase03.sqlite"
    engine=create_engine("sqlite:///"+path.as_posix())
    tables=[table for table in metadata.sorted_tables if not table.name.startswith("security_")]
    with sec.service.repository.engine.connect() as source,engine.begin() as destination:
        metadata.create_all(destination,tables=tables)
        for table in tables:
            rows=[dict(row) for row in source.execute(select(table)).mappings()]
            if rows:destination.execute(insert(table),rows)
    engine.dispose()
    app=create_app(replace(sec.app.state.settings,database_path=path),clock=sec.clock)
    with TestClient(app) as client:
        result=client.get(f"/v1/cases/{case['id']}",headers=sec.headers("a_engineer"))
        assert result.status_code==200 and result.json()["version"]==case["version"]
        assert client.get("/v1/alerts",headers=sec.headers("a_engineer")).json()["items"]==[]


def test_reference_file_edits_without_manifest_update_fail_closed(monkeypatch,tmp_path):
    import backend.app.assurance_corpus as corpus
    for name in ("scenarios_v1.json","labels_v1.json","manifest_v1.json"):
        (tmp_path/name).write_bytes((CORPUS_ROOT/name).read_bytes())
    labels=json.loads((tmp_path/"labels_v1.json").read_text())
    labels["labels"][0]["expected"]["decision"]="DENY"
    (tmp_path/"labels_v1.json").write_text(json.dumps(labels))
    monkeypatch.setattr(corpus,"CORPUS_ROOT",tmp_path)
    with pytest.raises(ValueError,match="manifest"):
        load_corpus()


def test_tenant_run_rate_limit_and_known_replay_remain_bounded(fast):
    candidate=fast.candidate()
    for i in range(10):
        assert fast.run(candidate,operation=f"bounded_operation_{i:04d}").status_code==200
    assert fast.run(candidate,operation="bounded_operation_0010").status_code==429
    assert fast.run(candidate,operation="bounded_operation_0000").json()["operation_replayed"] is True


def test_isolated_subprocess_has_fixed_command_timeout_and_no_user_keys(monkeypatch):
    import backend.app.assurance_service as service
    monkeypatch.setenv("GEMINI_API_KEY","PRIVATE_DUMMY_USER_KEY_NOT_REAL")
    monkeypatch.setenv("GOOGLE_API_KEY","PRIVATE_DUMMY_USER_KEY_NOT_REAL")
    calls=[]
    def process(command,**kwargs):
        calls.append((command,kwargs))
        raise subprocess.TimeoutExpired(command,kwargs["timeout"])
    monkeypatch.setattr(service.subprocess,"run",process)
    data,error,elapsed=isolated_run({"profile":"SAFE_BASELINE"})
    assert data is None and error=="RUN_TIMEOUT"
    command,options=calls[0]
    assert command[1:]==["-m","backend.app.assurance_worker"] and options["shell"] is False
    assert options["timeout"]==20 and options["env"]["SENTINEL_PROVIDER_MODE"]=="DISABLED"
    assert "GEMINI_API_KEY" not in options["env"] and "GOOGLE_API_KEY" not in options["env"]
    assert "PRIVATE_DUMMY_USER_KEY_NOT_REAL" not in str(options)


def test_unexpected_worker_exception_is_redacted_and_persists_failed_run(sec,monkeypatch):
    def fail(request):raise RuntimeError("PRIVATE_UNTRUSTED_MARKER")
    monkeypatch.setattr(sec.app.state.assurance,"runner",fail)
    candidate=sec.candidate()
    result=sec.run(candidate)
    assert result.status_code==200 and result.json()["status"]=="FAILED"
    assert result.json()["error_code"]=="ISOLATED_EXECUTION_FAILED"
    assert result.json()["summary"]["unevaluable"]==38
    assert "PRIVATE_UNTRUSTED_MARKER" not in result.text
    assert sec.gate(candidate,result.json()).status_code==409


def test_changed_corpus_or_disabled_reviewer_invalidates_ready_gate(fast,monkeypatch):
    import backend.app.assurance_service as service
    _,_,_,candidate,run,_,review=fast.correction()
    gate=fast.gate(candidate,run,review).json()
    with fast.service.repository.transaction() as tx:
        tx.change("users",{"id":fast.ids["a_reviewer"],"tenant_id":"a"},{"active":False})
    assert fast.request("GET",f"/v1/redteam/release-gates/{gate['id']}").json()["decision"]=="BLOCKED"
    with fast.service.repository.transaction() as tx:
        tx.change("users",{"id":fast.ids["a_reviewer"],"tenant_id":"a"},{"active":True})
    original=service.load_corpus
    def changed():
        scenarios,labels,corpus=original()
        return scenarios,labels,corpus|{"sha256":"0"*64}
    monkeypatch.setattr(service,"load_corpus",changed)
    assert fast.gate(candidate,run,review).status_code==409
    assert fast.request("GET",f"/v1/redteam/release-gates/{gate['id']}").json()["decision"]=="BLOCKED"
