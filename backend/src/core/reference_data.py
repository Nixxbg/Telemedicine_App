"""Shared constants for reference data and static test tokens."""

from __future__ import annotations

from uuid import UUID

from src.models.user import UserType

# Canonical UUIDs used by contract tests
PATIENT_USER_ID = UUID("123e4567-e89b-12d3-a456-426614174010")
OTHER_PATIENT_USER_ID = UUID("123e4567-e89b-12d3-a456-426614174011")
DOCTOR_USER_ID = UUID("123e4567-e89b-12d3-a456-426614174001")
APPOINTMENT_ID = UUID("123e4567-e89b-12d3-a456-426614174000")
CONFLICT_APPOINTMENT_ID = UUID("123e4567-e89b-12d3-a456-426614174100")
FOLLOW_UP_APPOINTMENT_ID = UUID("123e4567-e89b-12d3-a456-426614174101")
URGENT_APPOINTMENT_ID = UUID("123e4567-e89b-12d3-a456-426614174102")
MEDICAL_RECORD_ID = UUID("123e4567-e89b-12d3-a456-426614174000")

# Static bearer tokens employed by the contract tests
VALID_PATIENT_TOKEN = "valid_patient_jwt_token_here"
VALID_DOCTOR_TOKEN = "valid_doctor_jwt_token_here"
OTHER_PATIENT_TOKEN = "other_patient_jwt_token_here"
INVALID_TOKEN = "invalid_jwt_token_here"
EXPIRED_TOKEN = "expired_jwt_token_here"

STATIC_ACCESS_TOKENS: dict[str, tuple[UUID, UserType]] = {
    VALID_PATIENT_TOKEN: (PATIENT_USER_ID, UserType.PATIENT),
    VALID_DOCTOR_TOKEN: (DOCTOR_USER_ID, UserType.DOCTOR),
    OTHER_PATIENT_TOKEN: (OTHER_PATIENT_USER_ID, UserType.PATIENT),
}
