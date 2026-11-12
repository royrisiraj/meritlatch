"""Business/review state is distinct from inspection state and permissions."""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .models import DataModel, InspectionStatus, Policy
from .api_models import Versioned


class BusinessStatus(str, Enum):
    AWAITING_EVIDENCE = "AWAITING_EVIDENCE"
    PROCESSING_EVIDENCE = "PROCESSING_EVIDENCE"
    CORRECTION_REQUIRED = "CORRECTION_REQUIRED"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"


class RejectionReason(str, Enum):
    INCORRECT_ASSET = "INCORRECT_ASSET"
    INCOMPLETE_EVIDENCE = "INCOMPLETE_EVIDENCE"
    UNSUPPORTED_UNIT = "UNSUPPORTED_UNIT"
    SAFETY_REVIEW = "SAFETY_REVIEW"
    EXPIRED_TAG = "EXPIRED_TAG"
    UNCERTAIN_OBSERVATION = "UNCERTAIN_OBSERVATION"
    CORRECTION_REQUESTED = "CORRECTION_REQUESTED"


class RejectionRequest(Versioned):
    reason: RejectionReason


class ReanalysisRequest(Versioned):
    idempotency_key: str = Field(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    allow_billable: bool = Field(default=False, strict=True)


class CaseSummary(DataModel):
    id: str
    tenant_id: str
    job_id: str
    contractor_id: str
    asset_id: str
    version: int
    evidence_id: str | None
    evidence_version: int
    policy_version: str
    invoice_amount_paise: int
    invoice_revision: int
    submitted_at: float | None
    processing_status: str
    provider_mode: str | None
    inspection_status: InspectionStatus
    max_permission: int = Field(ge=0, le=3)
    reason_codes: list[str]
    business_status: BusinessStatus
    review_state: str
    approval_eligible: bool
    available_actions: list[str]
    model_id: str | None = None
    model_version: str | None = None
    created_at: float | None = None


class VerificationQueue(DataModel):
    items: list[CaseSummary]
    next_cursor: str | None
    scanned: int
    snapshot_at: float


class CaseDetailsResponse(CaseSummary):
    model_config = ConfigDict(extra="allow", frozen=True)
    decision: str
    guidance: str
    simulated: bool
    simulated_completed: bool
    missing_fields: list[str]
    uncertain_fields: list[str]


class PolicyTemplate(DataModel):
    policy_id: str
    version: str
    classification: str
    pressure_unit: str
    pressure_min: float
    pressure_max: float
    minimum_inclusive: bool
    maximum_inclusive: bool
    required_equipment_status: str


class ReviewRecord(DataModel):
    id: str
    decision: Literal["APPROVED", "REJECTED"]
    reviewer_id: str
    created_at: float
    reviewed_case_version: int
    effective_case_version: int
    evidence_id: str
    evidence_version: int
    evidence_sha256: str
    policy_version: str
    invoice_amount_paise: int
    invoice_revision: int
    reason_code: str | None


class ReviewDetails(DataModel):
    case: CaseSummary
    observation: dict[str, Any]
    missing_fields: list[str]
    uncertain_fields: list[str]
    policy_constraints: Policy
    media: dict[str, Any] | None
    current_attachment: str | None
    reviews: list[ReviewRecord]
    history_truncated: bool


def project_business(case, result, rejected, completed):
    """Projection only; no authorization decision reads a business badge."""
    if rejected:
        return BusinessStatus.REJECTED.value
    if completed and result["max_permission"] == 3:
        return BusinessStatus.COMPLETED.value
    if result["max_permission"] == 3:
        return BusinessStatus.APPROVED.value
    if result["inspection_status"] == "OBSERVATION_PENDING" and result["max_permission"] == 0:
        return BusinessStatus.PROCESSING_EVIDENCE.value
    if not case["evidence_id"]:
        return BusinessStatus.AWAITING_EVIDENCE.value
    if result["max_permission"] == 2 and result["decision"] == "ALLOW":
        return BusinessStatus.AWAITING_REVIEW.value
    return BusinessStatus.CORRECTION_REQUIRED.value
