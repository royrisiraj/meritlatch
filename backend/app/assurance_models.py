"""Typed offline assurance contracts. No observations or badges confer authority."""

from enum import Enum
from typing import Any, Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from .api_models import Role
from .models import Action, DataModel, EvaluationContext, InspectionStatus, Outcome, Reason


class Profile(str, Enum):
    SAFE = "SAFE_BASELINE"
    WEAK = "WEAK_TEST_ONLY"
    STRICT = "OVERRESTRICTIVE_TEST_ONLY"


class ActorContext(DataModel):
    role: Role
    tenant_id: str = Field(max_length=100)
    assigned: bool = True
    authenticated: bool = True


class Scenario(DataModel):
    id: str = Field(pattern=r"^[A-Z][A-Z0-9_-]{2,63}$")
    version: int = Field(ge=1, le=999)
    source: Literal["SYNTHETIC", "HUMAN_LABELED"]
    review_state: Literal["SPECIFICATION_REFERENCE", "HUMAN_REVIEWED", "PENDING_REVIEW"]
    reviewer: str | None = Field(default=None, max_length=100)
    policy_id: str
    policy_version: str
    category: str = Field(pattern=r"^[A-Z0-9_]{2,64}$")
    target: Literal["POLICY", "API", "APPROVAL_BINDING"]
    operation: str = Field(pattern=r"^[A-Z_]{2,64}$")
    actor: ActorContext
    observation: dict[str, Any] | None
    context: EvaluationContext
    action: Action
    numeric_variant: Literal["NONE", "NAN", "INFINITY"] = "NONE"
    risk: Literal["HIGH", "MEDIUM", "LOW"]
    rationale: str = Field(min_length=1, max_length=300)
    steps: tuple[str, ...] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def provenance(self):
        if self.review_state == "PENDING_REVIEW":
            raise ValueError("Unlabeled candidates cannot enter the reference corpus")
        if self.source == "HUMAN_LABELED" and (self.review_state != "HUMAN_REVIEWED" or not self.reviewer):
            raise ValueError("Human-labeled sources require recorded independent review")
        if self.context.tenant_id != "synthetic-org-a" or self.context.job_id != "synthetic-job-001":
            raise ValueError("Only the fixed fictional assurance scope is permitted")
        if self.observation and (len(self.observation) > 16 or len(str(self.observation)) > 4096):
            raise ValueError("Observation fixture exceeds its bound")
        if any(len(step) > 250 for step in self.steps):
            raise ValueError("Reproduction reference too long")
        return self


class Expected(DataModel):
    decision: Outcome
    inspection_status: InspectionStatus | None = None
    max_permission: int | None = Field(default=None, ge=0, le=3)
    http_status: int | None = Field(default=None, ge=100, le=599)
    required_reasons: tuple[str, ...] = ()


class Label(DataModel):
    scenario_id: str
    scenario_version: int
    basis: Literal["MASTER_BOOK_SPECIFICATION", "HUMAN_REVIEWED"]
    reference: str = Field(min_length=1, max_length=200)
    mandatory: bool = True
    expected: Expected


class Observed(DataModel):
    decision: Outcome | None
    inspection_status: InspectionStatus | None = None
    max_permission: int | None = Field(default=None, ge=0, le=3)
    http_status: int | None = Field(default=None, ge=100, le=599)
    reason_codes: tuple[str, ...] = Field(default=(), max_length=32)
    error_code: Literal["EXECUTION_ERROR", "RUN_TIMEOUT", "INCOMPLETE_RUN"] | None = None

    @field_validator("reason_codes")
    @classmethod
    def safe_codes(cls, values):
        allowed = {item.value for item in Reason} | {"ROLE_FORBIDDEN", "NOT_FOUND", "EXACT_DUPLICATE", "VERSION_CONFLICT"}
        if not set(values) <= allowed:
            raise ValueError("Unrecognized output reason; raw messages are not evidence")
        return values


class ScenarioResult(DataModel):
    scenario_id: str
    scenario_version: int
    target: str
    mandatory: bool
    expected: Expected
    actual: Observed
    passed: bool
    mismatch: str | None
    risk: str


class Versioned(DataModel):
    expected_version: int = Field(strict=True, ge=1)


class CandidateCreate(DataModel):
    profile: Profile


class CandidateChange(Versioned):
    profile: Profile


class RunRequest(DataModel):
    candidate_id: str = Field(min_length=1, max_length=100)
    expected_candidate_version: int = Field(strict=True, ge=1)
    idempotency_key: str = Field(pattern=r"^[A-Za-z0-9_-]{16,128}$")
    trigger: Literal["PRE_RELEASE", "MANUAL_PERIODIC", "TARGETED_SYNTHETIC"] = "PRE_RELEASE"


class TriageRequest(Versioned):
    status: Literal["ACKNOWLEDGED", "IN_REVIEW", "DISMISSED", "VERIFIED"]
    reason: Literal["REPRODUCED", "NEEDS_CORRECTION", "LABEL_DISPUTED", "ACCEPTED_TEST_ONLY_RISK", "REGRESSION_VERIFIED"]
    gate_id: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def reasons(self):
        if self.status == "DISMISSED" and self.reason not in {"LABEL_DISPUTED", "ACCEPTED_TEST_ONLY_RISK"}:
            raise ValueError("Dismissal requires an explicit disposition")
        if self.status == "VERIFIED" and (not self.gate_id or self.reason != "REGRESSION_VERIFIED"):
            raise ValueError("Verification requires a current accepted gate")
        return self


class ProposalRequest(Versioned):
    candidate_id: str = Field(min_length=1, max_length=100)
    expected_candidate_version: int = Field(strict=True, ge=1)
    remediation: Literal["RESTORE_BASELINE_BOUNDS", "RESTORE_REQUIRED_CHECK", "REVIEW_BINDING_CONTROL"]


class ReviewRequest(Versioned):
    expected_review_version: int = Field(default=0, strict=True, ge=0)
    proposal_id: str = Field(min_length=1, max_length=100)
    run_id: str = Field(min_length=1, max_length=100)
    decision: Literal["APPROVE", "REJECT"]
    reason: Literal["REGRESSION_REVIEWED", "CANDIDATE_NOT_ACCEPTABLE"]

    @model_validator(mode="after")
    def reason_matches(self):
        if (self.decision == "APPROVE") != (self.reason == "REGRESSION_REVIEWED"):
            raise ValueError("Review decision/reason conflict")
        return self


class GateRequest(Versioned):
    run_id: str = Field(min_length=1, max_length=100)
    review_id: str | None = Field(default=None, max_length=100)


class Record(DataModel):
    """Bounded public records are explicitly assembled by the scoped service."""
    model_config = ConfigDict(extra="allow", frozen=True)
    id: str
    tenant_id: str


class Page(DataModel):
    items: list[Record]
    next_cursor: str | None


class CandidateRecord(Record):
    profile: Profile
    version: int
    review_revision: int
    artifact_sha256: str
    software_revision: str
    current_binding_valid: bool
    test_only: Literal[True]
    published: Literal[False]


class RunRecord(Record):
    candidate_id: str
    candidate_version: int
    artifact_sha256: str
    corpus_id: str
    corpus_version: str
    corpus_sha256: str
    scenario_count: int
    status: Literal["RUNNING", "INTERRUPTED", "COMPLETE", "FAILED", "STALE"]
    summary: dict[str, Any] | None
    results: list[ScenarioResult] = Field(max_length=64)


class FindingRecord(Record):
    scenario_id: str
    scenario_version: int
    version: int
    status: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    mismatch: str
    expected: Expected
    actual: Observed


class GateRecord(Record):
    candidate_id: str
    candidate_version: int
    artifact_sha256: str
    decision: Literal["BLOCKED", "READY_FOR_MANUAL_RELEASE"]
    reason_codes: list[str]
    current_binding_valid: bool
    published: Literal[False]


class SuggestionState(DataModel):
    status: Literal["BLOCKED"] = "BLOCKED"
    source: Literal["DISABLED"] = "DISABLED"
    reason_codes: tuple[str, ...] = ("GEMINI_FROZEN",)
    candidates: tuple = ()
