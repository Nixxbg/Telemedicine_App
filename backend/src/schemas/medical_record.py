"""Medical record request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from src.models.medical_record import ChangeUserType, RecordType

NonEmptyStr = Annotated[str, Field(min_length=1)]
TitleStr = Annotated[str, Field(min_length=1, max_length=200)]


class MedicalRecordCreateRequest(BaseModel):
    """Schema for creating a medical record."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    record_type: RecordType
    title: TitleStr
    data: Annotated[dict[str, Any], Field(min_length=1)]
    change_reason: NonEmptyStr | None = Field(default=None, max_length=500)

    @field_validator("data")
    @classmethod
    def validate_data(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Ensure medical record data is not empty."""
        if not value:
            raise ValueError("Medical record data cannot be empty")
        return value

    @field_validator("change_reason")
    @classmethod
    def validate_change_reason(cls, value: str | None) -> str | None:
        """Ensure change reason, when provided, is meaningful."""
        if value is None:
            return value
        if not value.strip():
            raise ValueError("Change reason cannot be blank")
        return value.strip()


class MedicalRecordUpdateRequest(BaseModel):
    """Schema for updating a medical record."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    title: TitleStr
    data: Annotated[dict[str, Any], Field(min_length=1)]
    change_reason: NonEmptyStr | None = Field(default=None, max_length=500)

    @field_validator("data")
    @classmethod
    def validate_data(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Ensure updated medical record data is not empty."""
        if not value:
            raise ValueError("Medical record data cannot be empty")
        return value

    @field_validator("change_reason")
    @classmethod
    def validate_change_reason(cls, value: str | None) -> str | None:
        """Ensure change reason, when provided, is meaningful."""
        if value is None:
            return value
        if not value.strip():
            raise ValueError("Change reason cannot be blank")
        return value.strip()


class MedicalRecordResponse(BaseModel):
    """Response schema for a medical record with latest version data."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    patient_id: UUID
    record_type: RecordType
    title: str
    current_version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    current_data: dict[str, Any]


class MedicalRecordListResponse(BaseModel):
    """Paginated list of medical records."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    records: list[MedicalRecordResponse]
    total_count: int
    limit: int
    offset: int


class MedicalRecordVersionResponse(BaseModel):
    """Response schema for a medical record version entry."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    medical_record_id: UUID
    version_number: int
    data: dict[str, Any]
    change_reason: str
    changed_by_user_id: UUID
    changed_by_user_type: ChangeUserType
    created_at: datetime


class MedicalRecordVersionsResponse(BaseModel):
    """List of versions available for a medical record."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    record_id: UUID
    total_versions: int
    versions: list[MedicalRecordVersionResponse]


class MedicalRecordValidationError(ValueError):
    """Domain-specific validation error for medical record payloads."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


def validate_medical_record_payload(
    payload: dict[str, Any],
    *,
    schema: type[MedicalRecordCreateRequest] | type[MedicalRecordUpdateRequest],
) -> MedicalRecordCreateRequest | MedicalRecordUpdateRequest:
    """Validate raw request payload against the provided schema.

    Raises a :class:`MedicalRecordValidationError` for predictable 400 responses
    instead of FastAPI's default 422 validation errors.
    """

    try:
        return schema.model_validate(payload)
    except ValidationError as exc:  # pragma: no cover - exercised in contract tests
        first_error = exc.errors()[0]
        field = ".".join(
            str(loc) for loc in first_error.get("loc", []) if loc != "body"
        )
        message = first_error.get("msg", "Invalid medical record payload")
        raise MedicalRecordValidationError(message, field=field or None) from exc
