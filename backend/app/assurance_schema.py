"""Additive security-plane tables, separate from operational cases and policies."""

from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, ForeignKeyConstraint, UniqueConstraint


def register(metadata):
    Table("security_schema_migrations",metadata,Column("version",Integer,primary_key=True))
    def table(name,*fields,extras=()):
        return Table(name,metadata,Column("id",String,primary_key=True),
            Column("tenant_id",String,ForeignKey("tenants.id"),nullable=False),
            Column("created_at",Float,nullable=False),*fields,UniqueConstraint("tenant_id","id"),*extras)
    def text(name): return Column(name,String,nullable=False)
    def integer(name): return Column(name,Integer,nullable=False)
    table("security_candidates",text("profile"),integer("version"),integer("review_revision"),text("artifact_sha256"),text("software_revision"),text("author_id"))
    table("security_runs",text("candidate_id"),integer("candidate_version"),text("artifact_sha256"),text("software_revision"),
        text("corpus_id"),text("corpus_version"),text("corpus_sha256"),integer("scenario_count"),text("actor_id"),
        text("key_hash"),text("request_hash"),text("trigger"),
        extras=(UniqueConstraint("tenant_id","actor_id","key_hash"),
            ForeignKeyConstraint(["tenant_id","candidate_id"],["security_candidates.tenant_id","security_candidates.id"])))
    table("security_results",text("run_id"),text("status"),text("summary_json"),text("results_json"),
        Column("elapsed_seconds",Float,nullable=False),Column("error_code",String),
        extras=(UniqueConstraint("run_id"),ForeignKeyConstraint(["tenant_id","run_id"],["security_runs.tenant_id","security_runs.id"])))
    table("security_findings",text("fingerprint"),integer("version"),text("status"),text("severity"),text("mismatch"),
        text("scenario_id"),integer("scenario_version"),text("candidate_id"),text("artifact_sha256"),text("policy_id"),text("policy_version"),
        text("corpus_sha256"),text("expected_json"),text("actual_json"),text("owner_id"),
        Column("first_seen",Float,nullable=False),Column("last_seen",Float,nullable=False),integer("occurrences"),
        extras=(UniqueConstraint("tenant_id","fingerprint"),))
    table("security_occurrences",text("finding_id"),text("run_id"),
        extras=(UniqueConstraint("finding_id","run_id"),
            ForeignKeyConstraint(["tenant_id","finding_id"],["security_findings.tenant_id","security_findings.id"]),
            ForeignKeyConstraint(["tenant_id","run_id"],["security_runs.tenant_id","security_runs.id"])))
    table("security_proposals",text("finding_id"),text("candidate_id"),integer("candidate_version"),text("artifact_sha256"),
        text("author_id"),text("remediation"),
        extras=(ForeignKeyConstraint(["tenant_id","finding_id"],["security_findings.tenant_id","security_findings.id"]),
                ForeignKeyConstraint(["tenant_id","candidate_id"],["security_candidates.tenant_id","security_candidates.id"])))
    table("security_reviews",text("proposal_id"),text("candidate_id"),integer("candidate_version"),text("artifact_sha256"),
        text("run_id"),text("corpus_sha256"),integer("review_revision"),text("reviewer_id"),text("decision"),text("reason"),
        extras=(ForeignKeyConstraint(["tenant_id","proposal_id"],["security_proposals.tenant_id","security_proposals.id"]),
                ForeignKeyConstraint(["tenant_id","run_id"],["security_runs.tenant_id","security_runs.id"])))
    table("security_gates",text("candidate_id"),integer("candidate_version"),text("artifact_sha256"),text("run_id"),
        Column("review_id",String),Column("proposal_id",String),text("actor_id"),text("decision"),text("reasons_json"),
        extras=(ForeignKeyConstraint(["tenant_id","candidate_id"],["security_candidates.tenant_id","security_candidates.id"]),
                ForeignKeyConstraint(["tenant_id","run_id"],["security_runs.tenant_id","security_runs.id"])))
    table("security_events",text("actor_id"),text("action"),text("subject_id"),integer("subject_version"),text("outcome"),text("reasons_json"))
    return {"security_runs","security_results","security_occurrences","security_proposals","security_reviews","security_gates","security_events"}
