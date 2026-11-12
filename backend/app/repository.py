"""SQLAlchemy SQLite adapter and transaction contract for a future Firestore adapter.

The service uses the UnitOfWork interface, never SQLAlchemy or SQL directly.
Firestore must implement the same atomic reads, CAS writes and append-only events;
it cannot replace a transaction with several independent document writes.
"""

from contextlib import contextmanager, AbstractContextManager
from pathlib import Path
from typing import Protocol, Any

from sqlalchemy import (
    MetaData, Table, Column, String, Integer, Float, Boolean, ForeignKey,
    ForeignKeyConstraint, UniqueConstraint, CheckConstraint, create_engine, event,
    select, insert, update,
)
from sqlalchemy.exc import OperationalError

from .errors import AppError, conflict

metadata = MetaData()
tenants = Table("tenants", metadata, Column("id", String, primary_key=True))
users = Table("users", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, ForeignKey("tenants.id"), nullable=False),
    Column("username", String, nullable=False), Column("role", String, nullable=False),
    Column("password_hash", String, nullable=False), Column("active", Boolean, nullable=False),
    UniqueConstraint("tenant_id", "username"), UniqueConstraint("tenant_id", "id"),
    CheckConstraint("role IN ('CONTRACTOR','MANAGER','ENGINEER','SERVICE_AGENT')"))
sessions = Table("sessions", metadata,
    Column("id", String, primary_key=True), Column("token_hash", String, unique=True, nullable=False),
    Column("user_id", String, ForeignKey("users.id"), nullable=False),
    Column("expires_at", Float, nullable=False), Column("revoked", Boolean, nullable=False))
auth_limits = Table("auth_limits", metadata,
    Column("id", String, primary_key=True), Column("attempts", Integer, nullable=False),
    Column("resets_at", Float, nullable=False))
jobs = Table("jobs", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, ForeignKey("tenants.id"), nullable=False),
    Column("asset_id", String, nullable=False), Column("contractor_id", String, nullable=False),
    Column("engineer_id", String, nullable=False), Column("service_agent_id", String, nullable=False),
    Column("version", Integer, nullable=False), UniqueConstraint("tenant_id", "id"),
    *[ForeignKeyConstraint(["tenant_id", col], ["users.tenant_id", "users.id"])
      for col in ("contractor_id", "engineer_id", "service_agent_id")])
policies = Table("policies", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False),
    Column("job_id", String, nullable=False), Column("version", String, nullable=False),
    Column("config_json", String, nullable=False), Column("author_id", String, nullable=False),
    Column("reviewer_id", String, nullable=False), Column("review_reference", String, nullable=False),
    UniqueConstraint("tenant_id", "job_id", "version"),
    ForeignKeyConstraint(["tenant_id", "job_id"], ["jobs.tenant_id", "jobs.id"]))
cases = Table("cases", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False),
    Column("job_id", String, nullable=False), Column("policy_version", String, nullable=False),
    Column("invoice_amount_paise", Integer, nullable=False), Column("version", Integer, nullable=False),
    Column("evidence_version", Integer, nullable=False), Column("evidence_id", String),
    Column("challenge_id", String), Column("approval_id", String),
    UniqueConstraint("tenant_id", "id"),
    CheckConstraint("version > 0 AND evidence_version >= 0 AND invoice_amount_paise > 0"),
    ForeignKeyConstraint(["tenant_id", "job_id"], ["jobs.tenant_id", "jobs.id"]),
    ForeignKeyConstraint(["tenant_id", "job_id", "policy_version"], ["policies.tenant_id", "policies.job_id", "policies.version"]))
challenges = Table("challenges", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False),
    Column("case_id", String, nullable=False), Column("job_id", String, nullable=False),
    Column("asset_id", String, nullable=False), Column("evidence_session_id", String, unique=True, nullable=False),
    Column("auth_session_id", String, ForeignKey("sessions.id"), nullable=False),
    Column("actor_id", String, ForeignKey("users.id"), nullable=False), Column("token", String, unique=True, nullable=False),
    Column("created_at", Float, nullable=False), Column("expires_at", Float, nullable=False),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
evidence = Table("evidence", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False),
    Column("case_id", String, nullable=False), Column("challenge_id", String, ForeignKey("challenges.id"), nullable=False),
    Column("version", Integer, nullable=False), Column("sha256", String, nullable=False),
    Column("observation_json", String, nullable=False), Column("artifact_mode", String, nullable=False),
    Column("submitted_by", String, ForeignKey("users.id"), nullable=False),
    UniqueConstraint("tenant_id", "case_id", "version"),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
approvals = Table("approvals", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False),
    Column("case_id", String, nullable=False), Column("reviewer_id", String, ForeignKey("users.id"), nullable=False),
    Column("reviewed_case_version", Integer, nullable=False), Column("effective_case_version", Integer, nullable=False),
    Column("binding_json", String, nullable=False), Column("binding_sha256", String, nullable=False),
    Column("created_at", Float, nullable=False),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
decision_events = Table("decision_events", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False),
    Column("case_id", String, nullable=False), Column("actor_id", String, nullable=False),
    Column("event_type", String, nullable=False), Column("case_version", Integer, nullable=False),
    Column("evidence_version", Integer, nullable=False), Column("evidence_sha256", String),
    Column("policy_version", String, nullable=False), Column("action", String),
    Column("decision", String), Column("reason_codes_json", String, nullable=False), Column("created_at", Float, nullable=False),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
action_runs = Table("action_runs", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False),
    Column("case_id", String, nullable=False), Column("action", String, nullable=False),
    Column("binding_sha256", String, nullable=False), Column("actor_id", String, nullable=False),
    Column("created_at", Float, nullable=False), UniqueConstraint("case_id", "action", "binding_sha256"),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
migrations = Table("schema_migrations", metadata, Column("version", Integer, primary_key=True))
media_migrations = Table("media_schema_migrations", metadata, Column("version", Integer, primary_key=True))
media_uploads = Table("media_uploads", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False),
    Column("case_id", String, nullable=False), Column("evidence_id", String, ForeignKey("evidence.id"), unique=True, nullable=False),
    Column("storage_key", String, unique=True, nullable=False), Column("sha256", String, nullable=False),
    Column("provider_sha256", String, nullable=False), Column("mime_type", String, nullable=False),
    Column("byte_size", Integer, nullable=False), Column("width", Integer, nullable=False), Column("height", Integer, nullable=False),
    Column("provenance_json", String, nullable=False), Column("provider_mode", String, nullable=False),
    Column("accepted_case_version", Integer, nullable=False), Column("created_at", Float, nullable=False),
    UniqueConstraint("tenant_id", "sha256"),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
media_analyses = Table("media_analyses", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False),
    Column("case_id", String, nullable=False), Column("evidence_id", String, ForeignKey("evidence.id"), unique=True, nullable=False),
    Column("status", String, nullable=False), Column("observation_json", String), Column("reason_code", String),
    Column("model_id", String, nullable=False), Column("model_version", String),
    Column("elapsed_seconds", Float, nullable=False), Column("created_at", Float, nullable=False),
    CheckConstraint("status IN ('SUCCESS','FAILED','STALE')"),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
TABLES = {t.name: t for t in metadata.tables.values()}


class UnitOfWork(Protocol):
    def get(self, table: str, **keys) -> dict | None: ...
    def find(self, table: str, **keys) -> list[dict]: ...
    def add(self, table: str, values: dict) -> None: ...
    def change(self, table: str, keys: dict, values: dict) -> None: ...
    def cas_case(self, case: dict, expected: int, values: dict) -> dict: ...


class Repository(Protocol):
    def transaction(self) -> AbstractContextManager[UnitOfWork]: ...


class SQLiteUnitOfWork:
    def __init__(self, connection):
        self.connection = connection

    def find(self, table, **keys):
        t = TABLES[table]
        stmt = select(t).where(*(t.c[k] == v for k, v in keys.items()))
        return [dict(row) for row in self.connection.execute(stmt).mappings()]

    def get(self, table, **keys):
        rows = self.find(table, **keys)
        return rows[0] if rows else None

    def add(self, table, values):
        self.connection.execute(insert(TABLES[table]).values(**values))

    def change(self, table, keys, values):
        if table in {"policies", "approvals", "evidence", "challenges", "decision_events", "action_runs", "media_uploads", "media_analyses"}:
            raise ValueError("Append-only table cannot be changed")
        t = TABLES[table]
        result = self.connection.execute(update(t).where(*(t.c[k] == v for k, v in keys.items())).values(**values))
        if result.rowcount != 1:
            raise conflict()

    def cas_case(self, case, expected, values):
        self.change("cases", {"id": case["id"], "tenant_id": case["tenant_id"], "version": expected},
                    {**values, "version": expected + 1})
        return {**case, **values, "version": expected + 1}


class SQLiteRepository:
    def __init__(self, path: Path):
        path = Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine("sqlite+pysqlite:///" + path.as_posix(),
                                    connect_args={"check_same_thread": False, "timeout": 5})

        @event.listens_for(self.engine, "connect")
        def configure(dbapi_connection, connection_record):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")
            dbapi_connection.execute("PRAGMA busy_timeout=5000")

        self.migrate()

    def migrate(self):
        # Version 1 is an explicit initial migration, idempotent on a new/local DB.
        with self.engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            conn.commit()
            conn.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                metadata.create_all(conn)
                versions = list(conn.execute(select(migrations.c.version)).scalars())
                if versions and versions != [1]:
                    raise ValueError("Unsupported database schema version; restore a compatible database.")
                if not versions:
                    conn.execute(insert(migrations).values(version=1))
                media_versions = list(conn.execute(select(media_migrations.c.version)).scalars())
                if media_versions and media_versions != [1]:
                    raise ValueError("Unsupported media schema version; restore a compatible database.")
                if not media_versions:
                    conn.execute(insert(media_migrations).values(version=1))
                for name in ("policies", "approvals", "evidence", "challenges", "decision_events", "action_runs", "media_uploads", "media_analyses"):
                    for operation in ("UPDATE", "DELETE"):
                        conn.exec_driver_sql(f"CREATE TRIGGER IF NOT EXISTS {name}_no_{operation.lower()} "
                            f"BEFORE {operation} ON {name} BEGIN SELECT RAISE(ABORT, 'append-only record'); END")
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    @contextmanager
    def transaction(self):
        with self.engine.connect() as conn:
            try:
                conn.exec_driver_sql("BEGIN IMMEDIATE")
                yield SQLiteUnitOfWork(conn)
                conn.commit()
            except OperationalError as exc:
                conn.rollback()
                raise AppError(409, "DATABASE_CONFLICT", "The database is busy; reload state and retry.") from exc
            except Exception:
                conn.rollback()
                raise

    def close(self):
        self.engine.dispose()
