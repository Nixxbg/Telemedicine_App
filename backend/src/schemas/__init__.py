"""Schemas package exports."""

from src.schemas.auth import (  # noqa: F401
    AuthenticationResponse,
    DoctorProfile,
    DoctorRegistrationRequest,
    ErrorResponse,
    LoginRequest,
    PatientProfile,
    PatientRegistrationRequest,
    RefreshTokenRequest,
    TokenResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)
from src.schemas.medical_record import (  # noqa: F401
    MedicalRecordCreateRequest,
    MedicalRecordListResponse,
    MedicalRecordResponse,
    MedicalRecordUpdateRequest,
    MedicalRecordValidationError,
    MedicalRecordVersionResponse,
    MedicalRecordVersionsResponse,
    validate_medical_record_payload,
)
