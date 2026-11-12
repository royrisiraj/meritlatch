"""Untrusted observation contract. No policy/auth/storage or authority imports."""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Protocol

from pydantic import Field, field_validator

from .models import DataModel, Observation, finite_nonnegative


class VisualObservation(DataModel):
    asset_id_observed: str | None = Field(max_length=128)
    challenge_text_observed: str | None = Field(max_length=128)
    pressure_value: float | None
    pressure_unit: str | None = Field(max_length=20)
    equipment_status: Literal["RUNNING", "OFF", "UNKNOWN"] | None
    calibration_expiry_date: date | None
    uncertain_fields: tuple[str, ...] = Field(max_length=16)
    conflicting_fields: tuple[str, ...] = Field(max_length=16)

    @field_validator("pressure_value", mode="before")
    @classmethod
    def numeric(cls, value):
        return None if value is None else finite_nonnegative(value)

    @field_validator("calibration_expiry_date", mode="before")
    @classmethod
    def expiry(cls, value):
        return Observation.validate_expiry(value)

    @field_validator("uncertain_fields", "conflicting_fields")
    @classmethod
    def fields(cls, values):
        allowed = {"asset_id_observed", "challenge_text_observed", "pressure_value", "pressure_unit", "equipment_status", "calibration_expiry_date"}
        if not set(values) <= allowed:
            raise ValueError("Unknown uncertainty field")
        return values

    def observation(self, mode):
        fields = self.model_dump(exclude={"conflicting_fields"})
        fields["uncertain_fields"] = tuple(sorted(set(self.uncertain_fields) | set(self.conflicting_fields)))
        return Observation.model_validate({**fields, "artifact_mode": mode})


@dataclass(frozen=True)
class PerceptionInput:
    image_bytes: bytes = field(repr=False)
    mime_type: str
    evidence_id: str


@dataclass(frozen=True)
class PerceptionResult:
    fields: VisualObservation
    model_id: str
    model_version: str | None


class ProviderError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class PerceptionProvider(Protocol):
    mode: Literal["MOCK_AI", "LIVE_GEMINI"]
    model_id: str
    async def inspect(self, source: PerceptionInput) -> PerceptionResult: ...


class MockPerceptionProvider:
    mode = "MOCK_AI"
    model_id = "mock-observer-v1"

    def __init__(self, reply=None):
        # The normal explicit mock has UNKNOWN fields. Matching positive fixtures
        # are configured in internal tests/smoke only, never from HTTP or filenames.
        self.reply = reply or dict(asset_id_observed=None, challenge_text_observed=None, pressure_value=None,
            pressure_unit=None, equipment_status="UNKNOWN", calibration_expiry_date=None,
            uncertain_fields=["asset_id_observed", "challenge_text_observed", "pressure_value", "pressure_unit", "equipment_status", "calibration_expiry_date"], conflicting_fields=[])

    async def inspect(self, source):
        try:
            return PerceptionResult(VisualObservation.model_validate(self.reply), self.model_id, "mock-v1")
        except ValueError:
            raise ProviderError("PROVIDER_INVALID_OBSERVATION") from None
