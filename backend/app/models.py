"""Typed data boundary. Observation data carries no authorization fields."""

from datetime import date, datetime
from enum import Enum, IntEnum
import math
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class DataModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")


class Permission(IntEnum):
    L0 = 0
    L1 = 1
    L2 = 2
    L3 = 3


class InspectionStatus(str, Enum):
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    OBSERVATION_PENDING = "OBSERVATION_PENDING"
    EVIDENCE_COMPLETE = "EVIDENCE_COMPLETE"
    SAFETY_ALERT = "SAFETY_ALERT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED_BY_HUMAN = "APPROVED_BY_HUMAN"


class Action(str, Enum):
    CREATE_DRAFT = "create_draft"
    REQUEST_EVIDENCE = "request_evidence"
    RECORD_PROVISIONAL_VISIT = "record_provisional_visit"
    PREPARE_INVOICE = "prepare_invoice"
    COMPLETE_SIMULATED_ACTION = "complete_simulated_action"


class Outcome(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class Reason(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_POLICY = "INVALID_POLICY"
    INVALID_CONTEXT = "INVALID_CONTEXT"
    INVALID_OBSERVATION = "INVALID_OBSERVATION"
    POLICY_CONTEXT_MISMATCH = "POLICY_CONTEXT_MISMATCH"
    OBSERVATION_MISSING = "OBSERVATION_MISSING"
    ASSET_MISMATCH = "ASSET_MISMATCH"
    CHALLENGE_MISMATCH = "CHALLENGE_MISMATCH"
    CHALLENGE_EXPIRED = "CHALLENGE_EXPIRED"
    UNCERTAIN_OBSERVATION = "UNCERTAIN_OBSERVATION"
    PRESSURE_MISSING = "PRESSURE_MISSING"
    UNIT_UNSUPPORTED = "UNIT_UNSUPPORTED"
    PRESSURE_OUT_OF_RANGE = "PRESSURE_OUT_OF_RANGE"
    EQUIPMENT_STATUS_MISSING = "EQUIPMENT_STATUS_MISSING"
    EQUIPMENT_STATUS_MISMATCH = "EQUIPMENT_STATUS_MISMATCH"
    CALIBRATION_MISSING = "CALIBRATION_MISSING"
    CALIBRATION_EXPIRED = "CALIBRATION_EXPIRED"
    EVIDENCE_SATISFIES_POLICY = "EVIDENCE_SATISFIES_POLICY"
    PERMISSION_INSUFFICIENT = "PERMISSION_INSUFFICIENT"
    HUMAN_APPROVAL_NOT_IMPLEMENTED = "HUMAN_APPROVAL_NOT_IMPLEMENTED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def finite_nonnegative(value: object) -> float:
    # Deliberately reject booleans and numeric strings; never coerce them to safety data.
    if type(value) not in (int, float):
        raise ValueError("Expected a numeric measurement")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError("Measurement is too large") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError("Measurement must be finite and nonnegative")
    return number


class Observation(DataModel):
    artifact_mode: Literal["SYNTHETIC", "MOCK_AI", "LIVE_GEMINI", "RECORDED_LIVE"]
    asset_id_observed: str | None = None
    challenge_text_observed: str | None = None
    pressure_value: float | None = None
    pressure_unit: str | None = None
    equipment_status: Literal["RUNNING", "OFF", "UNKNOWN"] | None = None
    calibration_expiry_date: date | None = None
    uncertain_fields: tuple[str, ...] = ()

    @field_validator("pressure_value", mode="before")
    @classmethod
    def validate_pressure(cls, value: object) -> float | None:
        return None if value is None else finite_nonnegative(value)

    @field_validator("calibration_expiry_date", mode="before")
    @classmethod
    def validate_expiry(cls, value: object) -> date | None:
        if value is None or type(value) is date:
            return value
        if type(value) is str:
            return date.fromisoformat(value)
        raise ValueError("Expected an ISO date")


class Policy(DataModel):
    policy_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    asset_id_expected: str = Field(min_length=1)
    classification: Literal["FICTIONAL_NOT_INDUSTRIAL_SAFETY_GUIDANCE"]
    pressure_unit: Literal["PSI", "BAR"]
    pressure_min: float
    pressure_max: float
    minimum_inclusive: bool = Field(strict=True)
    maximum_inclusive: bool = Field(strict=True)
    required_equipment_status: Literal["RUNNING", "OFF"]

    @field_validator("policy_id", "version", "tenant_id", "job_id", "asset_id_expected")
    @classmethod
    def validate_nonblank(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("Configuration identifiers must be nonblank and exact")
        return value

    @field_validator("pressure_min", "pressure_max", mode="before")
    @classmethod
    def validate_bound(cls, value: object) -> float:
        return finite_nonnegative(value)

    @model_validator(mode="after")
    def validate_range(self) -> "Policy":
        if self.pressure_min >= self.pressure_max:
            raise ValueError("Pressure minimum must be below maximum")
        if self.asset_id_expected.strip().upper() in {"N/A", "NA", "UNKNOWN", "NONE", "NULL", "-"}:
            raise ValueError("Expected asset cannot be a placeholder")
        return self


class EvaluationContext(DataModel):
    """Trusted caller input, never model output. No challenge issuance in Phase 00."""

    tenant_id: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    asset_id_expected: str = Field(min_length=1)
    approved_policy_version: str = Field(min_length=1)
    expected_challenge: str = Field(min_length=1)
    challenge_expires_at: AwareDatetime
    evaluated_at: AwareDatetime

    @field_validator("tenant_id", "job_id", "asset_id_expected", "approved_policy_version", "expected_challenge")
    @classmethod
    def validate_nonblank(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("Trusted context identifiers must be nonblank and exact")
        return value

    @field_validator("challenge_expires_at", "evaluated_at", mode="before")
    @classmethod
    def require_datetime(cls, value: object) -> object:
        if not isinstance(value, (datetime, str)):
            raise ValueError("Expected an aware datetime")
        return value


class Decision(DataModel):
    decision: Outcome
    inspection_status: InspectionStatus
    max_permission: Permission
    reason_codes: tuple[Reason, ...]
    guidance: str
