from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from backend.app.api import create_app
from .conftest import visual_reply


def test_audit_has_scoped_actor_versions_source_and_public_review_receipt_refs(wf):
    job, case, ch = wf.ready()
    approved = wf.approve(case).json()
    receipt = wf.act(approved, "complete_simulated_action", execute=True).json()
    history = wf.review(case).json()["reviews"]
    rows = wf.request("GET", f"/v1/cases/{case['id']}/audit").json()
    approved_event = next(row for row in rows if row["event_type"] == "MANAGER_APPROVED_SIMULATION")
    assert approved_event["actor_id"] == wf.ids["a_manager"]
    assert approved_event["job_id"] == job["id"] and approved_event["tenant_id"] == "a"
    assert approved_event["review_reference"] == history[0]["id"]
    assert approved_event["source_mode"] == "MOCK_AI"
    assert approved_event["source_evidence_id"] == case["evidence_id"]
    assert approved_event["evidence_sha256"] == case["evidence_sha256"]
    assert approved_event["policy_version"] == case["policy_version"]
    assert approved_event["business_status"] == "APPROVED"
    completed = next(row for row in rows if row["event_type"] == "SIMULATED_ACTION_EXECUTED" and row["action"] == "complete_simulated_action")
    assert completed["completion_reference"] == receipt["receipt_id"]
    assert completed["business_status"] == "COMPLETED"
    assert ch["token"] not in str(rows) and ch["evidence_session_id"] not in str(rows)
    assert "binding_json" not in str(rows) and "internal_approval_id" not in str(rows)


def test_audit_filters_and_scoped_keyset_pagination(wf):
    _, case, _ = wf.ready()
    for _ in range(4): wf.review(case)
    first = wf.request("GET", f"/v1/cases/{case['id']}/audit?limit=2")
    assert first.status_code == 200 and len(first.json()) == 2
    cursor = first.headers["X-Audit-Next-Cursor"]
    second = wf.request("GET", f"/v1/cases/{case['id']}/audit?limit=2&before_event_id={cursor}")
    assert not ({row["id"] for row in first.json()} & {row["id"] for row in second.json()})
    filtered = wf.request("GET", f"/v1/cases/{case['id']}/audit?event_type=MANAGER_REVIEW_READ").json()
    assert len(filtered) == 4
    assert all(row["event_type"] == "MANAGER_REVIEW_READ" for row in filtered)
    assert wf.request("GET", f"/v1/cases/{case['id']}/audit?before_event_id=unrelated").status_code == 404


@pytest.mark.parametrize("table", ["manager_reviews", "workflow_events", "job_events", "submission_operations", "analysis_runs", "analysis_results"])
def test_workflow_history_cannot_be_edited_in_place(wf, table):
    job, case, ch = wf.ready()
    wf.reject(case)
    with wf.service.repository.transaction() as tx:
        with pytest.raises(ValueError, match="Append-only"):
            tx.change(table, {"id": "anything"}, {})
    if table in {"manager_reviews", "workflow_events", "job_events"}:
        with pytest.raises(IntegrityError, match="append-only record"):
            with wf.service.repository.engine.begin() as connection:
                connection.exec_driver_sql(f"DELETE FROM {table}")


def test_review_and_rejection_survive_restart_with_same_effective_authority(wf):
    job, case, ch = wf.ready()
    rejected = wf.reject(case, "UNCERTAIN_OBSERVATION").json()
    wf.service.repository.close()
    app = create_app(wf.app.state.settings, clock=wf.clock)
    with TestClient(app) as client:
        current = client.get(f"/v1/cases/{case['id']}", headers=wf.headers()).json()
        assert current["business_status"] == "REJECTED" and current["max_permission"] == 0
        details = client.get(f"/v1/cases/{case['id']}/review", headers=wf.headers()).json()
        assert details["reviews"][0]["reason_code"] == "UNCERTAIN_OBSERVATION"
        assert details["reviews"][0]["evidence_version"] == case["evidence_version"]
        assert client.post(f"/v1/cases/{case['id']}/approvals", headers=wf.headers(), json={"expected_case_version": current["version"]}).status_code == 409


def test_workflow_migration_is_idempotent_and_does_not_change_core_media_versions(wf):
    _, case, _ = wf.ready()
    approved = wf.approve(case).json()
    repo = wf.service.repository
    repo.migrate()
    repo.migrate()
    with repo.transaction() as tx:
        assert tx.find("schema_migrations") == [{"version": 1}]
        assert tx.find("media_schema_migrations") == [{"version": 1}]
        assert tx.find("workflow_schema_migrations") == [{"version": 1}]
        assert len(tx.find("manager_reviews", case_id=case["id"])) == 1
        tx.change("workflow_schema_migrations", {"version": 1}, {"version": 999})
    with pytest.raises(ValueError, match="Unsupported workflow schema"):
        repo.migrate()


def test_upgrade_preserves_phase02_approval_and_backfills_public_review_history(wf, tmp_path):
    from sqlalchemy import create_engine, insert, select
    from backend.app.repository import metadata
    job, case, ch = wf.ready()
    approved = wf.approve(case).json()
    new_tables = {"workflow_schema_migrations", "job_workflow", "case_workflow", "manager_reviews", "workflow_events", "job_events", "submission_operations", "analysis_runs", "analysis_results"}
    legacy_path = tmp_path / "phase02-format.sqlite"
    engine = create_engine("sqlite:///" + legacy_path.as_posix())
    tables = [table for table in metadata.sorted_tables if table.name not in new_tables]
    # Copy only baseline core/media records into a new test-owned Phase 02 schema.
    # Do not delete/edit source history or the user's database.
    with wf.service.repository.engine.connect() as source, engine.begin() as destination:
        metadata.create_all(destination, tables=tables)
        for table in tables:
            rows = [dict(row) for row in source.execute(select(table)).mappings()]
            if rows: destination.execute(insert(table), rows)
    engine.dispose()
    upgraded = create_app(replace(wf.app.state.settings, database_path=legacy_path), clock=wf.clock)
    with TestClient(upgraded) as client:
        current = client.get(f"/v1/cases/{case['id']}", headers=wf.headers()).json()
        assert current["max_permission"] == 3 and current["version"] == approved["version"]
        details = client.get(f"/v1/cases/{case['id']}/review", headers=wf.headers()).json()
        assert len(details["reviews"]) == 1
        review = details["reviews"][0]
        assert review["decision"] == "APPROVED" and review["reviewer_id"] == wf.ids["a_manager"]
        assert review["evidence_sha256"] == approved["evidence_sha256"]
        assert "internal_approval_id" not in review
        with upgraded.state.service.repository.transaction() as tx:
            assert len(tx.find("approvals", case_id=case["id"])) == 1
            assert len(tx.find("evidence", case_id=case["id"])) == 1
