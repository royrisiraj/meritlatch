import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from backend.app.api import create_app
from backend.app.provisioning import provision_user, register_reviewed_policy
from backend.app.repository import SQLiteRepository, metadata
from backend.app.settings import Settings
from backend.testing import create_test_app


def test_cases_sessions_approval_and_idempotency_survive_application_restart(world):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    first = world.act(approved, "complete_simulated_action", execute=True).json()
    world.service.repository.close()
    reopened = create_test_app(world.app.state.settings.database_path, world.clock)
    with TestClient(reopened) as client:
        current = client.get(f"/v1/cases/{case['id']}", headers=world.headers()).json()
        assert current["max_permission"] == 3
        assert current["simulated_completed"] is True
        repeated = client.post(f"/v1/cases/{case['id']}/actions/execute", headers=world.headers("a_agent"),
            json=dict(expected_case_version=current["version"], action="complete_simulated_action")).json()
        assert repeated["receipt_id"] == first["receipt_id"]
        assert repeated["already_executed"] is True


@pytest.mark.parametrize("table", ["decision_events", "approvals", "evidence", "challenges", "policies", "action_runs"])
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_history_tables_reject_in_place_update_and_delete(world, table, operation):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    world.act(approved, "complete_simulated_action", execute=True)
    sql = f"UPDATE {table} SET id = id" if operation == "UPDATE" else f"DELETE FROM {table}"
    with pytest.raises(IntegrityError, match="append-only record"):
        with world.service.repository.engine.begin() as conn:
            conn.exec_driver_sql(sql)


def test_sqlite_enforces_foreign_keys_and_case_cas(world):
    job, case = world.new()
    with pytest.raises(IntegrityError):
        with world.service.repository.transaction() as tx:
            tx.add("jobs", dict(id="bad", tenant_id="a", asset_id="PUMP-042", version=1,
                contractor_id=world.ids["b_contractor"], engineer_id=world.ids["a_engineer"], service_agent_id=world.ids["a_agent"]))
    from backend.app.errors import AppError
    with pytest.raises(AppError) as exc:
        with world.service.repository.transaction() as tx:
            row = tx.get("cases", id=case["id"])
            tx.cas_case(row, 999, {"approval_id": None})
    assert exc.value.code == "VERSION_CONFLICT"


def test_migration_is_idempotent_and_unknown_future_schema_fails_closed(world):
    repository = world.service.repository
    repository.migrate()
    repository.migrate()
    with repository.transaction() as tx:
        assert tx.find("schema_migrations") == [{"version": 1}]
        tx.change("schema_migrations", {"version": 1}, {"version": 999})
    with pytest.raises(ValueError, match="Unsupported database schema"):
        repository.migrate()


def test_no_credentials_are_seeded_on_normal_startup(tmp_path):
    app = create_app(Settings(database_path=tmp_path / "empty.sqlite"))
    with TestClient(app):
        with app.state.service.repository.transaction() as tx:
            assert tx.find("users") == []
            assert tx.find("tenants") == []


def test_fixture_gate_rejects_production_and_env_enablement(monkeypatch):
    with pytest.raises(ValueError, match="local development/test"):
        Settings(environment="production")
    with pytest.raises(ValueError, match="internal test factory"):
        Settings(environment="development", allow_synthetic=True)
    monkeypatch.setenv("SENTINEL_ALLOW_SYNTHETIC", "true")
    with pytest.raises(ValueError, match="internal test factory"):
        Settings.from_env()


def test_offline_provisioning_does_not_overwrite_accounts_or_create_invalid_roles(world):
    with pytest.raises(ValueError, match="already exists"):
        provision_user(world.service.repository, "a", "manager", "MANAGER", "test-only-new-password")
    with pytest.raises(ValueError):
        provision_user(world.service.repository, "a", "attacker", "SUPER_ADMIN", "test-only-new-password")
    assert world.request("GET", "/v1/me").status_code == 200
