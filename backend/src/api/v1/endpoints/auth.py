"""Authentication API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_async_session
from src.models.user import User, UserType
from src.schemas import (
    AuthenticationResponse,
    DoctorProfile,
    DoctorRegistrationRequest,
    LoginRequest,
    PatientProfile,
    PatientRegistrationRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from src.services.auth_service import AuthService

router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=False)
ACCESS_TOKEN_LIFETIME_SECONDS = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


async def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthService:
    """FastAPI dependency that returns an :class:`AuthService` instance."""

    return AuthService(session)


def build_patient_profile(user: User) -> PatientProfile:
    """Construct a patient profile response from ORM entities."""

    patient = user.patient
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patient profile is missing",
        )

    return PatientProfile(
        id=user.id,
        email=user.email,
        username=patient.username,
        first_name=patient.first_name,
        last_name=patient.last_name,
        date_of_birth=patient.date_of_birth,
        phone_number=patient.phone_number,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_phone=patient.emergency_contact_phone,
        profile_completed=patient.profile_completed,
        created_at=user.created_at,
    )


def build_doctor_profile(user: User) -> DoctorProfile:
    """Construct a doctor profile response from ORM entities."""

    doctor = user.doctor
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Doctor profile is missing",
        )

    return DoctorProfile(
        id=user.id,
        email=user.email,
        doctor_id=doctor.doctor_id,
        first_name=doctor.first_name,
        last_name=doctor.last_name,
        specializations=doctor.specializations,
        license_number=doctor.license_number,
        bio=doctor.bio,
        years_experience=doctor.years_experience,
        is_accepting_patients=doctor.is_accepting_patients,
        created_at=user.created_at,
    )


def json_error(
    status_code: int,
    error: str,
    message: str,
    details: Any | None = None,
) -> JSONResponse:
    """Create a JSON error response following the API contract."""

    payload: dict[str, Any] = {"error": error, "message": message}
    if details is not None:
        payload["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


def map_http_exception(
    exc: HTTPException,
    default_error: str | None = None,
) -> JSONResponse:
    """Convert an :class:`HTTPException` into a contract-compliant response."""

    if isinstance(exc.detail, dict):
        payload = exc.detail
    else:
        message = str(exc.detail)
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            lower_message = message.lower()
            details: dict[str, str] | None = None
            if "email" in lower_message:
                details = {
                    "field": "email",
                    "message": message,
                    "code": "already_exists",
                }
            elif "username" in lower_message:
                details = {
                    "field": "username",
                    "message": message,
                    "code": "already_exists",
                }
            elif "doctor" in lower_message:
                details = {
                    "field": "doctor_id",
                    "message": message,
                    "code": "already_exists",
                }

            payload: dict[str, Any] = {"error": "validation_error", "message": message}
            if details is not None:
                payload["details"] = details
        else:
            error = default_error
            if error is None:
                if exc.status_code in {
                    status.HTTP_401_UNAUTHORIZED,
                    status.HTTP_403_FORBIDDEN,
                }:
                    error = "authentication_error"
                elif exc.status_code in {
                    status.HTTP_404_NOT_FOUND,
                    status.HTTP_409_CONFLICT,
                }:
                    error = "validation_error"
                else:
                    error = "server_error"
            payload = {"error": error, "message": message}

    return JSONResponse(status_code=exc.status_code, content=payload)


@router.post(
    "/register/patient",
    response_model=AuthenticationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_patient(
    payload: PatientRegistrationRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthenticationResponse | JSONResponse:
    """Register a new patient account."""

    try:
        user, _ = await service.register_patient(
            email=payload.email,
            password=payload.password,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            date_of_birth=payload.date_of_birth.isoformat(),
            phone_number=payload.phone_number,
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
        )
    except HTTPException as exc:  # pragma: no cover - handled via tests
        return map_http_exception(exc, default_error="validation_error")

    full_user = await service.get_user_by_id(user.id)
    if not full_user or not full_user.patient:
        return json_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "server_error",
            "Failed to load patient profile after registration",
        )

    access_token = service.create_access_token(full_user.id, full_user.user_type)
    refresh_token = service.create_refresh_token(full_user.id, full_user.user_type)

    return AuthenticationResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_LIFETIME_SECONDS,
        user=build_patient_profile(full_user),
    )


@router.post(
    "/register/doctor",
    response_model=AuthenticationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_doctor(
    payload: DoctorRegistrationRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthenticationResponse | JSONResponse:
    """Register a new doctor account."""

    try:
        user, _ = await service.register_doctor(
            email=payload.email,
            password=payload.password,
            doctor_id=payload.doctor_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            specializations=payload.specializations,
            license_number=payload.license_number,
            bio=payload.bio,
            years_experience=payload.years_experience,
            is_accepting_patients=True,
        )
    except HTTPException as exc:  # pragma: no cover - handled via tests
        return map_http_exception(exc, default_error="validation_error")

    full_user = await service.get_user_by_id(user.id)
    if not full_user or not full_user.doctor:
        return json_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "server_error",
            "Failed to load doctor profile after registration",
        )

    access_token = service.create_access_token(full_user.id, full_user.user_type)
    refresh_token = service.create_refresh_token(full_user.id, full_user.user_type)

    return AuthenticationResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_LIFETIME_SECONDS,
        user=build_doctor_profile(full_user),
    )


@router.post("/login", response_model=AuthenticationResponse)
async def login(
    payload: LoginRequest, service: AuthService = Depends(get_auth_service)
) -> AuthenticationResponse | JSONResponse:
    """Authenticate a doctor or patient using email and password."""

    user = await service.authenticate_user(
        email=payload.email,
        password=payload.password,
    )

    if not user:
        return json_error(
            status.HTTP_401_UNAUTHORIZED,
            "authentication_error",
            "Invalid email or password",
        )

    full_user = await service.get_user_by_id(user.id)
    if not full_user:
        return json_error(
            status.HTTP_401_UNAUTHORIZED,
            "authentication_error",
            "User not found or inactive",
        )

    access_token = service.create_access_token(full_user.id, full_user.user_type)
    refresh_token = service.create_refresh_token(full_user.id, full_user.user_type)

    if full_user.user_type == UserType.PATIENT and full_user.patient:
        user_profile = build_patient_profile(full_user)
    elif full_user.user_type == UserType.DOCTOR and full_user.doctor:
        user_profile = build_doctor_profile(full_user)
    else:  # pragma: no cover - defensive guard
        return json_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "server_error",
            "User profile is incomplete",
        )

    return AuthenticationResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_LIFETIME_SECONDS,
        user=user_profile,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse | JSONResponse:
    """Refresh the access token using a valid refresh token."""

    token = payload.refresh_token.strip()
    if not token:
        return json_error(
            status.HTTP_401_UNAUTHORIZED,
            "authentication_error",
            "Refresh token cannot be empty",
        )

    try:
        access_token, _ = await service.refresh_token(token)
    except HTTPException as exc:  # pragma: no cover - handled via tests
        return map_http_exception(exc, default_error="authentication_error")

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_LIFETIME_SECONDS,
    )


@router.get(
    "/me",
    response_model=PatientProfile | DoctorProfile,
)
async def current_user_profile(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    service: AuthService = Depends(get_auth_service),
) -> PatientProfile | DoctorProfile | JSONResponse:
    """Return the authenticated user's profile."""

    if (
        not credentials
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials
    ):
        return json_error(
            status.HTTP_401_UNAUTHORIZED,
            "authentication_error",
            "Missing or invalid authentication token",
        )

    token = credentials.credentials

    try:
        user = await service.get_current_user(token)
    except HTTPException as exc:  # pragma: no cover - handled via tests
        return map_http_exception(exc, default_error="authentication_error")

    full_user = await service.get_user_by_id(user.id)
    if not full_user:
        return json_error(
            status.HTTP_401_UNAUTHORIZED,
            "authentication_error",
            "User not found or inactive",
        )

    if full_user.user_type == UserType.PATIENT and full_user.patient:
        return build_patient_profile(full_user)

    if full_user.user_type == UserType.DOCTOR and full_user.doctor:
        return build_doctor_profile(full_user)

    return json_error(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "server_error",
        "User profile is incomplete",
    )
