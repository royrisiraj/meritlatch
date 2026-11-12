"""SQLAlchemy SQLite adapter and transaction contract for a future Firestore adapter.

The service uses the UnitOfWork interface, never SQLAlchemy or SQL directly.
Firestore must implement the same atomic reads, CAS writes and append-only events;
it cannot replace a transaction with several independent document writes.
"""

from contextlib import contextmanager, AbstractContextManager
from pathlib import Path
import json
from uuid import uuid5, NAMESPACE_URL
from typing import Protocol, Any

from sqlalchemy import (
    MetaData, Table, Column, String, Integer, Float, Boolean, ForeignKey,
    ForeignKeyConstraint, UniqueConstraint, CheckConstraint, create_engine, event,
    select, insert, update, func, and_, or_,
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
workflow_migrations = Table("workflow_schema_migrations", metadata, Column("version", Integer, primary_key=True))
job_workflow = Table("job_workflow", metadata,
    Column("job_id", String, primary_key=True), Column("tenant_id", String, nullable=False),
    Column("policy_id", String, nullable=False), Column("policy_version", String, nullable=False),
    Column("invoice_amount_paise", Integer, nullable=False), Column("created_at", Float, nullable=False),
    ForeignKeyConstraint(["tenant_id", "job_id"], ["jobs.tenant_id", "jobs.id"]))
case_workflow = Table("case_workflow", metadata,
    Column("case_id", String, primary_key=True), Column("tenant_id", String, nullable=False),
    Column("created_at", Float), Column("invoice_revision", Integer, nullable=False),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
manager_reviews = Table("manager_reviews", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False), Column("case_id", String, nullable=False),
    Column("decision", String, nullable=False), Column("reviewer_id", String, ForeignKey("users.id"), nullable=False),
    Column("created_at", Float, nullable=False), Column("reviewed_case_version", Integer, nullable=False),
    Column("effective_case_version", Integer, nullable=False), Column("evidence_id", String, ForeignKey("evidence.id"), nullable=False),
    Column("evidence_version", Integer, nullable=False), Column("evidence_sha256", String, nullable=False),
    Column("policy_version", String, nullable=False), Column("invoice_amount_paise", Integer, nullable=False),
    Column("invoice_revision", Integer, nullable=False), Column("challenge_id", String, nullable=False),
    Column("reason_code", String), Column("internal_approval_id", String),
    CheckConstraint("decision IN ('APPROVED','REJECTED')"), UniqueConstraint("case_id", "effective_case_version"),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
workflow_events = Table("workflow_events", metadata,
    Column("sequence", Integer, primary_key=True, autoincrement=True),
    Column("event_id", String, ForeignKey("decision_events.id"), nullable=False, unique=True),
    Column("tenant_id", String, nullable=False), Column("case_id", String, nullable=False), Column("job_id", String, nullable=False),
    Column("business_status", String, nullable=False), Column("source_mode", String),
    Column("source_evidence_id", String),
    Column("review_reference", String), Column("completion_reference", String),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
job_events = Table("job_events", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False), Column("job_id", String, nullable=False),
    Column("actor_id", String, nullable=False), Column("job_version", Integer, nullable=False),
    Column("event_type", String, nullable=False), Column("created_at", Float, nullable=False),
    ForeignKeyConstraint(["tenant_id", "job_id"], ["jobs.tenant_id", "jobs.id"]))
submission_operations = Table("submission_operations", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False), Column("case_id", String, nullable=False),
    Column("actor_id", String, nullable=False), Column("auth_session_id", String, nullable=False),
    Column("key_hash", String, nullable=False), Column("request_sha256", String, nullable=False),
    Column("declared_type", String, nullable=False), Column("challenge_id", String, nullable=False),
    Column("evidence_session_id", String, nullable=False), Column("expected_case_version", Integer, nullable=False),
    Column("evidence_id", String, ForeignKey("evidence.id"), nullable=False), Column("created_at", Float, nullable=False),
    UniqueConstraint("tenant_id", "actor_id", "key_hash"),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
analysis_runs = Table("analysis_runs", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String, nullable=False), Column("case_id", String, nullable=False),
    Column("evidence_id", String, ForeignKey("evidence.id"), nullable=False), Column("actor_id", String, nullable=False),
    Column("auth_session_id", String, nullable=False), Column("key_hash", String, nullable=False),
    Column("expected_case_version", Integer, nullable=False), Column("started_case_version", Integer, nullable=False),
    Column("provider_mode", String, nullable=False), Column("model_id", String, nullable=False), Column("created_at", Float, nullable=False),
    UniqueConstraint("tenant_id", "actor_id", "key_hash"), UniqueConstraint("case_id", "started_case_version"),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
analysis_results = Table("analysis_results", metadata,
    Column("id", String, primary_key=True), Column("run_id", String, ForeignKey("analysis_runs.id"), nullable=False, unique=True),
    Column("tenant_id", String, nullable=False), Column("case_id", String, nullable=False),
    Column("evidence_id", String, ForeignKey("evidence.id"), nullable=False),
    Column("status", String, nullable=False), Column("observation_json", String), Column("reason_code", String),
    Column("model_id", String, nullable=False), Column("model_version", String),
    Column("elapsed_seconds", Float, nullable=False), Column("created_at", Float, nullable=False),
    CheckConstraint("status IN ('SUCCESS','FAILED','STALE')"),
    ForeignKeyConstraint(["tenant_id", "case_id"], ["cases.tenant_id", "cases.id"]))
TABLES = {t.name: t for t in metadata.tables.values()}
APPEND_ONLY = {"policies", "approvals", "evidence", "challenges", "decision_events", "action_runs", "media_uploads", "media_analyses",
               "manager_reviews", "workflow_events", "job_events", "submission_operations", "analysis_runs", "analysis_results"}


class UnitOfWork(Protocol):
    def get(self, table: str, **keys) -> dict | None: ...
    def find(self, table: str, **keys) -> list[dict]: ...
    def add(self, table: str, values: dict) -> None: ...
    def change(self, table: str, keys: dict, values: dict) -> None: ...
    def cas_case(self, case: dict, expected: int, values: dict) -> dict: ...
    def recent(self, table: str, keys: dict, order: str, limit: int) -> list[dict]: ...
    def case_page(self, tenant_id: str, cursor: str | None, limit: int, contractor_id: str | None) -> list[dict]: ...
    def audit_page(self, tenant_id: str, case_id: str, before: str | None, event_type: str | None, limit: int) -> list[dict]: ...


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
        t = TABLES[table]
        row = self.connection.execute(select(t).where(*(t.c[k] == v for k, v in keys.items())).limit(1)).mappings().first()
        return dict(row) if row else None

    def recent(self, table, keys, order, limit):
        t = TABLES[table]
        stmt = select(t).where(*(t.c[k] == v for k, v in keys.items())).order_by(t.c[order].desc(), t.c.id.desc()).limit(limit)
        return [dict(row) for row in self.connection.execute(stmt).mappings()]

    def case_page(self, tenant_id, cursor, limit, contractor_id=None):
        stamp = func.coalesce(case_workflow.c.created_at, 0)
        query = select(cases).outerjoin(case_workflow, cases.c.id == case_workflow.c.case_id).join(jobs, cases.c.job_id == jobs.c.id).where(cases.c.tenant_id == tenant_id)
        if contractor_id:
            query = query.where(jobs.c.contractor_id == contractor_id)
        if cursor:
            prior = self.get("cases", tenant_id=tenant_id, id=cursor)
            if not prior:
                from .errors import not_found
                raise not_found()
            previous = self.get("case_workflow", tenant_id=tenant_id, case_id=cursor)
            at = previous["created_at"] if previous and previous["created_at"] is not None else 0
            query = query.where(or_(stamp > at, and_(stamp == at, cases.c.id > cursor)))
        return [dict(row) for row in self.connection.execute(query.order_by(stamp, cases.c.id).limit(limit)).mappings()]

    def audit_page(self, tenant_id, case_id, before, event_type, limit):
        query = select(decision_events, workflow_events.c.job_id, workflow_events.c.business_status,
                       workflow_events.c.source_mode, workflow_events.c.source_evidence_id, workflow_events.c.review_reference, workflow_events.c.completion_reference).join(
                       workflow_events, decision_events.c.id == workflow_events.c.event_id).where(
                       decision_events.c.tenant_id == tenant_id, decision_events.c.case_id == case_id)
        if before:
            marker = self.get("workflow_events", tenant_id=tenant_id, case_id=case_id, event_id=before)
            if not marker:
                from .errors import not_found
                raise not_found()
            query = query.where(workflow_events.c.sequence < marker["sequence"])
        if event_type:
            query = query.where(decision_events.c.event_type == event_type)
        return [dict(row) for row in self.connection.execute(query.order_by(workflow_events.c.sequence.desc()).limit(limit)).mappings()]

    def add(self, table, values):
        self.connection.execute(insert(TABLES[table]).values(**values))

    def change(self, table, keys, values):
        if table in APPEND_ONLY:
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
                workflow_versions = list(conn.execute(select(workflow_migrations.c.version)).scalars())
                if workflow_versions and workflow_versions != [1]:
                    raise ValueError("Unsupported workflow schema version; restore a compatible database.")
                if not workflow_versions:
                    conn.execute(insert(workflow_migrations).values(version=1))
                # Backfill only additive metadata. Original history/approvals/media remain unchanged.
                for case in conn.execute(select(cases)).mappings():
                    found = conn.execute(select(case_workflow.c.case_id).where(case_workflow.c.case_id == case["id"])).first()
                    if not found:
                        created = conn.execute(select(func.min(decision_events.c.created_at)).where(decision_events.c.case_id == case["id"])).scalar()
                        revisions = conn.execute(select(func.count()).select_from(decision_events).where(decision_events.c.case_id == case["id"], decision_events.c.event_type == "INVOICE_CHANGED")).scalar()
                        conn.execute(insert(case_workflow).values(case_id=case["id"], tenant_id=case["tenant_id"], created_at=created, invoice_revision=1 + revisions))
                for approval in conn.execute(select(approvals)).mappings():
                    known = conn.execute(select(manager_reviews.c.id).where(manager_reviews.c.internal_approval_id == approval["id"])).first()
                    if not known:
                        binding = json.loads(approval["binding_json"])
                        revisions = conn.execute(select(func.count()).select_from(decision_events).where(decision_events.c.case_id == approval["case_id"], decision_events.c.event_type == "INVOICE_CHANGED", decision_events.c.case_version <= approval["reviewed_case_version"])).scalar()
                        conn.execute(insert(manager_reviews).values(id=str(uuid5(NAMESPACE_URL, "sentinel-legacy-review:" + approval["id"])),
                            tenant_id=approval["tenant_id"], case_id=approval["case_id"], decision="APPROVED", reviewer_id=approval["reviewer_id"],
                            created_at=approval["created_at"], reviewed_case_version=approval["reviewed_case_version"], effective_case_version=approval["effective_case_version"],
                            evidence_id=binding["evidence_id"], evidence_version=binding["evidence_version"], evidence_sha256=binding["evidence_sha256"],
                            policy_version=binding["policy_version"], invoice_amount_paise=binding["invoice_amount_paise"], invoice_revision=1 + revisions,
                            challenge_id=binding["challenge_id"], reason_code=None, internal_approval_id=approval["id"]))
                legacy = conn.execute(select(decision_events).outerjoin(workflow_events, decision_events.c.id == workflow_events.c.event_id).where(workflow_events.c.event_id.is_(None)).order_by(decision_events.c.created_at, decision_events.c.case_version, decision_events.c.id)).mappings().all()
                for row in legacy:
                    case = conn.execute(select(cases).where(cases.c.id == row["case_id"])).mappings().one()
                    ev = conn.execute(select(evidence).where(evidence.c.case_id == row["case_id"], evidence.c.version == row["evidence_version"])).mappings().first()
                    conn.execute(insert(workflow_events).values(event_id=row["id"], tenant_id=row["tenant_id"], case_id=row["case_id"], job_id=case["job_id"], business_status="LEGACY_RECORDED", source_mode=ev["artifact_mode"] if ev else None, source_evidence_id=ev["id"] if ev else None))
                for name in APPEND_ONLY:
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
