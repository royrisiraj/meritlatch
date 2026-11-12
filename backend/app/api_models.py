from enum import Enum

from pydantic import Field, SecretStr, field_validator

from .models import DataModel, Action


class Role(str, Enum):
    CONTRACTOR = "CONTRACTOR"
    MANAGER = "MANAGER"
    ENGINEER = "ENGINEER"
    SERVICE_AGENT = "SERVICE_AGENT"


class Login(DataModel):
    tenant_id: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=1, max_length=100)
    password: SecretStr = Field(min_length=1, max_length=256)


class JobCreate(DataModel):
    asset_id: str = Field(min_length=1, max_length=100)
    contractor_id: str = Field(min_length=1, max_length=100)
    engineer_id: str = Field(min_length=1, max_length=100)
    service_agent_id: str = Field(min_length=1, max_length=100)
    policy_id: str | None = Field(default=None, min_length=1, max_length=100)
    policy_version: str | None = Field(default=None, min_length=1, max_length=100)
    invoice_amount_paise: int = Field(default=500000, strict=True, gt=0, le=100000000)


class CaseCreate(DataModel):
    job_id: str = Field(min_length=1, max_length=100)
    invoice_amount_paise: int | None = Field(default=None, strict=True, gt=0, le=100000000)
    policy_version: str | None = Field(default=None, min_length=1, max_length=100)


class Versioned(DataModel):
    expected_case_version: int = Field(strict=True, ge=1)


class ChallengeRequest(Versioned):
    case_id: str = Field(min_length=1, max_length=100)


class ActionRequest(Versioned):
    action: Action


class InvoiceChange(Versioned):
    invoice_amount_paise: int = Field(strict=True, gt=0, le=100000000)


class PolicyChange(Versioned):
    policy_version: str = Field(min_length=1, max_length=100)


class AssignmentChange(DataModel):
    expected_job_version: int = Field(strict=True, ge=1)
    contractor_id: str = Field(min_length=1, max_length=100)
