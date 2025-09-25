"""Appointment request and response schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.validation import (
    EnhancedValidationMixin,
    MedicalDataValidationError,
    sanitize_medical_text,
    validate_appointment_time_slot,
)
from src.models.appointment import AppointmentStatus, AppointmentType

UuidStr = Annotated[str, Field(min_length=1)]
ReasonStr = Annotated[str, Field(max_length=1000)]
CancellationReasonStr = Annotated[str, Field(max_length=500)]


class PatientSummary(BaseModel):
    """Summary information about a patient for appointment context."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    username: str
    first_name: str
    last_name: str
    date_of_birth: date


class DoctorSummary(BaseModel):
    """Summary information about a doctor for appointment context."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    doctor_id: str
    first_name: str
    last_name: str
    specializations: list[str]
    years_experience: Optional[int]
    is_accepting_patients: bool | None = None


class AppointmentCreateRequest(EnhancedValidationMixin, BaseModel):
    """Schema for creating a new appointment."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    doctor_id: UuidStr | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    appointment_type: str | None = None
    reason_for_visit: Optional[ReasonStr] = None
    preparation_notes: Optional[ReasonStr] = None

    @field_validator("reason_for_visit")
    @classmethod
    def validate_reason_for_visit(cls, value: str | None) -> str | None:
        """Sanitize reason for visit text."""
        if value is None:
            return value
        sanitized = sanitize_medical_text(value)
        if not sanitized.strip():
            raise ValueError("Reason for visit cannot be empty")
        return sanitized

    @field_validator("preparation_notes")
    @classmethod
    def validate_preparation_notes(cls, value: str | None) -> str | None:
        """Sanitize preparation notes text."""
        if value is None:
            return value
        sanitized = sanitize_medical_text(value)
        return sanitized if sanitized.strip() else None

    def validate_appointment_timing(self) -> None:
        """Validate appointment timing constraints."""
        if self.scheduled_start and self.scheduled_end:
            try:
                validate_appointment_time_slot(self.scheduled_start, self.scheduled_end)
            except MedicalDataValidationError as e:
                raise ValueError(e.message) from e


class AppointmentStatusUpdateRequest(BaseModel):
    """Schema for updating the status of an appointment."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    status: AppointmentStatus
    cancellation_reason: Optional[CancellationReasonStr] = None


class AppointmentResponse(BaseModel):
    """Detailed appointment information returned by the API."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    patient_id: UUID
    doctor_id: UUID
    scheduled_start: datetime
    scheduled_end: datetime
    status: AppointmentStatus
    appointment_type: AppointmentType
    reason_for_visit: Optional[str]
    preparation_notes: Optional[str]
    cancellation_reason: Optional[str] = None
    cost: float
    created_at: datetime
    updated_at: datetime
    messages_count: int
    has_consultation_notes: bool
    patient: Optional[PatientSummary] = None
    doctor: Optional[DoctorSummary] = None

    @field_validator("cost", mode="before")
    @classmethod
    def convert_decimal_to_float(cls, value: float | Decimal) -> float:
        """Ensure Decimal cost values are serialized as floats."""

        if isinstance(value, Decimal):
            return float(value)
        return float(value)


class AppointmentsResponse(BaseModel):
    """Paginated list of appointments for the authenticated user."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    appointments: list[AppointmentResponse]
    total_count: int
    offset: int
    limit: int


class DoctorAvailabilitySlot(BaseModel):
    """Represents a single availability window for a doctor."""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        from_attributes=True,
    )

    start_time: datetime
    end_time: datetime
    is_available: bool


class DoctorAvailabilityResponse(BaseModel):
    """Availability response structure for doctor schedule queries."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    doctor_id: UUID
    doctor_name: str
    from_date: date
    to_date: date
    appointment_duration_minutes: int
    available_slots: list[DoctorAvailabilitySlot]
