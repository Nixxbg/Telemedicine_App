"""Authentication request and response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from src.core.validation import (
    EnhancedValidationMixin,
    calculate_age_in_years,
    validate_emergency_contact,
)
from src.models.user import UserType

UsernameStr = Annotated[
    str,
    Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$"),
]
PasswordStr = Annotated[str, Field(min_length=8, max_length=128)]
DoctorIDStr = Annotated[
    str,
    Field(min_length=3, max_length=20, pattern=r"^[A-Z0-9]+$"),
]
PhoneNumberStr = Annotated[
    str,
    Field(pattern=r"^\+?[1-9]\d{1,14}$", max_length=16),
]


class PatientRegistrationRequest(EnhancedValidationMixin, BaseModel):
    """Schema for patient registration payload."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    email: EmailStr
    username: UsernameStr
    password: PasswordStr
    first_name: Annotated[str, Field(min_length=1, max_length=100)]
    last_name: Annotated[str, Field(min_length=1, max_length=100)]
    date_of_birth: date
    phone_number: PhoneNumberStr | None = Field(default=None)
    emergency_contact_name: Annotated[str | None, Field(default=None, max_length=200)]
    emergency_contact_phone: PhoneNumberStr | None = Field(default=None)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date) -> date:
        """Ensure date of birth is not in the future and patient is reasonable age."""
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")

        # Check if patient is too old (over 150 years)
        age = calculate_age_in_years(value)
        if age > 150:
            raise ValueError("Invalid date of birth: age cannot exceed 150 years")

        # Check if patient is too young (under 1 year for basic check)
        if age < 0:
            raise ValueError("Invalid date of birth")

        return value

    @model_validator(mode="after")
    def validate_emergency_contact_consistency(self) -> "PatientRegistrationRequest":
        """Validate emergency contact information is consistent."""
        validate_emergency_contact(
            self.emergency_contact_name, self.emergency_contact_phone
        )
        return self


class DoctorRegistrationRequest(BaseModel):
    """Schema for doctor registration payload."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    email: EmailStr
    doctor_id: DoctorIDStr
    password: PasswordStr
    first_name: Annotated[str, Field(min_length=1, max_length=100)]
    last_name: Annotated[str, Field(min_length=1, max_length=100)]
    specializations: Annotated[list[str], Field(min_length=1)]
    license_number: Annotated[str | None, Field(default=None, max_length=50)]
    bio: Annotated[str | None, Field(default=None, max_length=2000)]
    years_experience: Annotated[int | None, Field(default=None, ge=0)]

    @field_validator("specializations")
    @classmethod
    def validate_specializations(cls, value: list[str]) -> list[str]:
        """Ensure the list of specializations contains non-empty values."""
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("At least one specialization is required")
        return cleaned


class LoginRequest(BaseModel):
    """Schema for login requests."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    email: EmailStr
    password: PasswordStr


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token requests."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    refresh_token: Annotated[str, Field(min_length=1)]


class ValidationErrorDetail(BaseModel):
    """Details for individual field validation errors."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    field: str
    message: str
    code: str


class ValidationErrorResponse(BaseModel):
    """Response schema for validation errors."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    error: Literal["validation_error"] = "validation_error"
    message: str = "Request validation failed"
    details: list[ValidationErrorDetail]


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    error: str
    message: str
    details: dict[str, Any] | None = None


class PatientProfile(BaseModel):
    """Response schema for patient profile data."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    email: EmailStr
    user_type: Literal[UserType.PATIENT] = UserType.PATIENT
    username: str
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    phone_number: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    profile_completed: bool
    created_at: datetime


class DoctorProfile(BaseModel):
    """Response schema for doctor profile data."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    email: EmailStr
    user_type: Literal[UserType.DOCTOR] = UserType.DOCTOR
    doctor_id: str
    first_name: str
    last_name: str
    specializations: list[str]
    license_number: str | None = None
    bio: str | None = None
    years_experience: int | None = None
    is_accepting_patients: bool | None = None
    created_at: datetime


class TokenResponse(BaseModel):
    """Response schema for token refresh responses."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class AuthenticationResponse(TokenResponse):
    """Response schema for successful authentication operations."""

    refresh_token: str
    user: PatientProfile | DoctorProfile
