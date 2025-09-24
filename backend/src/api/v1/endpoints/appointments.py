"""
Appointments API endpoints.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.models.appointment import Appointment, AppointmentStatus, AppointmentType
from src.models.user import User, UserType
from src.schemas import (
    AppointmentCreateRequest,
    AppointmentResponse,
    AppointmentsResponse,
    AppointmentStatusUpdateRequest,
    DoctorAvailabilityResponse,
    DoctorAvailabilitySlot,
    DoctorSummary,
    PatientSummary,
)
from src.services.appointment_service import AppointmentService
from src.services.auth_service import AuthService

router = APIRouter()
doctors_router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=False)


def http_error(
    status_code: int,
    error: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> HTTPException:
    """Create a structured :class:`HTTPException` matching the API contract."""

    payload: dict[str, Any] = {"error": error, "message": message}
    if details is not None:
        payload["details"] = details
    return HTTPException(status_code=status_code, detail=payload)


def map_http_exception(
    exc: HTTPException, default_error: str | None = None
) -> HTTPException:
    """Normalize service-level exceptions into contract-compliant errors."""

    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return exc

    message = str(detail)
    error = default_error
    if error is None:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            error = "authentication_error"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            error = "authorization_error"
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            error = "not_found"
        elif exc.status_code == status.HTTP_409_CONFLICT:
            error = "scheduling_conflict"
        else:
            error = "validation_error" if exc.status_code < 500 else "server_error"

    return http_error(exc.status_code, error, message)


async def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthService:
    """Provide an instance of :class:`AuthService` via dependency injection."""

    return AuthService(session)


async def get_appointment_service(
    session: AsyncSession = Depends(get_async_session),
) -> AppointmentService:
    """Provide an instance of :class:`AppointmentService` via dependency injection."""

    return AppointmentService(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Authenticate the current request and return the associated user."""

    if (
        not credentials
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials.strip()
    ):
        raise http_error(
            status.HTTP_401_UNAUTHORIZED,
            "authentication_error",
            "Missing or invalid authentication token",
        )

    token = credentials.credentials.strip()

    try:
        return await auth_service.get_current_user(token)
    except HTTPException as exc:  # pragma: no cover - delegated error mapping
        raise map_http_exception(exc, default_error="authentication_error") from exc


def require_field(value: Any, field_name: str) -> None:
    """Ensure a required field is present and not empty."""

    if value is None:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            f"{field_name} is required",
            details={"field": field_name, "code": "missing_field"},
        )

    if isinstance(value, str) and not value.strip():
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            f"{field_name} cannot be blank",
            details={"field": field_name, "code": "empty_field"},
        )


def ensure_timezone(value: datetime) -> datetime:
    """Return a timezone-aware datetime, defaulting naive values to UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_patient_summary(appointment: Appointment) -> PatientSummary | None:
    """Build a patient summary payload from an appointment entity."""

    patient = getattr(appointment, "patient", None)
    if patient is None:
        return None

    return PatientSummary(
        id=patient.user_id,
        username=patient.username,
        first_name=patient.first_name,
        last_name=patient.last_name,
        date_of_birth=patient.date_of_birth,
    )


def to_doctor_summary(appointment: Appointment) -> DoctorSummary | None:
    """Build a doctor summary payload from an appointment entity."""

    doctor = getattr(appointment, "doctor", None)
    if doctor is None:
        return None

    specializations = doctor.specializations or []
    years_experience = doctor.years_experience or 0

    return DoctorSummary(
        id=doctor.user_id,
        doctor_id=doctor.doctor_id,
        first_name=doctor.first_name,
        last_name=doctor.last_name,
        specializations=list(specializations),
        years_experience=years_experience,
        is_accepting_patients=bool(doctor.is_accepting_patients),
    )


def to_appointment_response(
    appointment: Appointment,
    *,
    cancellation_reason: str | None = None,
) -> AppointmentResponse:
    """Convert an appointment ORM entity into a response schema."""

    messages = getattr(appointment, "messages", None)
    messages_count = len(messages) if messages else 0

    consultation_notes = getattr(appointment, "consultation_notes", None)
    has_consultation_notes = bool(consultation_notes)

    resolved_reason = getattr(appointment, "cancellation_reason", None)
    if resolved_reason is None:
        resolved_reason = cancellation_reason

    return AppointmentResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        scheduled_start=appointment.scheduled_start,
        scheduled_end=appointment.scheduled_end,
        status=appointment.status,
        appointment_type=appointment.appointment_type,
        reason_for_visit=appointment.reason_for_visit,
        preparation_notes=appointment.preparation_notes,
        cancellation_reason=resolved_reason,
        cost=float(appointment.cost) if appointment.cost is not None else 0.0,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        messages_count=messages_count,
        has_consultation_notes=has_consultation_notes,
        patient=to_patient_summary(appointment),
        doctor=to_doctor_summary(appointment),
    )


@router.get("/", response_model=AppointmentsResponse)
async def list_appointments(  # noqa: D401 - FastAPI generates schema docs
    current_user: User = Depends(get_current_user),
    status_filters: list[AppointmentStatus] | None = Query(
        default=None, alias="status"
    ),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: AppointmentService = Depends(get_appointment_service),
) -> AppointmentsResponse:
    """Return appointments for the authenticated user with optional filters."""

    if from_date and to_date and from_date > to_date:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "from_date cannot be after to_date",
        )

    if current_user.user_type == UserType.PATIENT:
        appointments = await service.get_patient_appointments(
            patient_id=current_user.id,
            requesting_user_id=current_user.id,
            requesting_user_type=current_user.user_type,
            status_filter=None,
            include_past=True,
            limit=None,
        )
    elif current_user.user_type == UserType.DOCTOR:
        appointments = await service.get_doctor_appointments(
            doctor_id=current_user.id,
            requesting_user_id=current_user.id,
            requesting_user_type=current_user.user_type,
            status_filter=None,
            date_filter=None,
            limit=None,
        )
    else:  # pragma: no cover - defensive guard
        raise http_error(
            status.HTTP_403_FORBIDDEN,
            "authorization_error",
            "Unsupported user type for appointments",
        )

    filtered: list[Appointment] = []
    for appointment in appointments:
        if status_filters and appointment.status not in status_filters:
            continue

        appointment_date = appointment.scheduled_start.date()
        if from_date and appointment_date < from_date:
            continue
        if to_date and appointment_date > to_date:
            continue

        filtered.append(appointment)

    total_count = len(filtered)
    if offset >= total_count:
        paginated: list[Appointment] = []
    else:
        paginated = filtered[offset : offset + limit]

    responses = [to_appointment_response(appointment) for appointment in paginated]

    return AppointmentsResponse(
        appointments=responses,
        total_count=total_count,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment(
    payload: AppointmentCreateRequest,
    current_user: User = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
) -> AppointmentResponse:
    """Book a new appointment for the authenticated patient."""

    if current_user.user_type != UserType.PATIENT:
        raise http_error(
            status.HTTP_403_FORBIDDEN,
            "authorization_error",
            "Only patients can create appointments",
        )

    require_field(payload.doctor_id, "doctor_id")
    require_field(payload.scheduled_start, "scheduled_start")
    require_field(payload.scheduled_end, "scheduled_end")
    require_field(payload.appointment_type, "appointment_type")

    try:
        doctor_uuid = UUID(str(payload.doctor_id))
    except ValueError as error:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "Invalid doctor ID format",
            details={"field": "doctor_id", "code": "invalid_format"},
        ) from error

    scheduled_start = ensure_timezone(payload.scheduled_start)  # type: ignore[arg-type]
    scheduled_end = ensure_timezone(payload.scheduled_end)  # type: ignore[arg-type]

    try:
        appointment_type = AppointmentType(str(payload.appointment_type))
    except ValueError as error:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "Invalid appointment type",
            details={"field": "appointment_type", "code": "invalid_choice"},
        ) from error

    now = datetime.now(timezone.utc)
    existing_future = await service.get_patient_appointments(
        patient_id=current_user.id,
        requesting_user_id=current_user.id,
        requesting_user_type=current_user.user_type,
        status_filter=None,
        include_past=False,
        limit=None,
    )

    active_future = [
        appointment
        for appointment in existing_future
        if appointment.scheduled_start >= now
        and appointment.status == AppointmentStatus.SCHEDULED
    ]

    if len(active_future) >= 3:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "appointment_limit",
            "Patient has reached the maximum number of future appointments",
        )

    try:
        appointment = await service.create_appointment(
            patient_id=current_user.id,
            doctor_id=doctor_uuid,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            appointment_type=appointment_type,
            reason_for_visit=payload.reason_for_visit,
            preparation_notes=payload.preparation_notes,
            requesting_user_id=current_user.id,
            requesting_user_type=current_user.user_type,
        )
    except HTTPException as exc:
        if exc.status_code == status.HTTP_409_CONFLICT:
            duration_minutes = int(
                (scheduled_end - scheduled_start).total_seconds() // 60
            )
            availability = await service.get_doctor_availability_slots(
                doctor_uuid,
                scheduled_start,
                slot_duration_minutes=max(duration_minutes, 15),
            )
            raise http_error(
                status.HTTP_400_BAD_REQUEST,
                "scheduling_conflict",
                str(exc.detail),
                details={"available_slots": availability},
            ) from exc

        raise map_http_exception(exc) from exc

    fresh = await service.get_appointment(
        appointment.id, current_user.id, current_user.user_type
    )
    if fresh is None:  # pragma: no cover - defensive guard
        raise http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "server_error",
            "Failed to load created appointment",
        )

    return to_appointment_response(fresh)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: UUID,
    payload: AppointmentStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
) -> AppointmentResponse:
    """Update the status of an appointment (including cancellation)."""

    if payload.status == AppointmentStatus.CANCELLED:
        try:
            appointment = await service.cancel_appointment(
                appointment_id,
                current_user.id,
                current_user.user_type,
                cancellation_reason=payload.cancellation_reason,
            )
        except HTTPException as exc:
            raise map_http_exception(exc) from exc

        return to_appointment_response(
            appointment, cancellation_reason=payload.cancellation_reason
        )

    try:
        appointment = await service.update_appointment_status(
            appointment_id,
            payload.status,
            current_user.id,
            current_user.user_type,
        )
    except HTTPException as exc:
        raise map_http_exception(exc) from exc

    return to_appointment_response(appointment)


@doctors_router.get(
    "/{doctor_id}/availability",
    response_model=DoctorAvailabilityResponse,
)
async def get_doctor_availability(
    doctor_id: UUID,
    from_date: date = Query(...),
    to_date: date = Query(...),
    appointment_duration: int = Query(default=30, ge=15, le=120),
    current_user: User = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
) -> DoctorAvailabilityResponse:
    """Return availability slots for a doctor within a date range."""

    if current_user.user_type not in {UserType.PATIENT, UserType.DOCTOR}:
        raise http_error(
            status.HTTP_403_FORBIDDEN,
            "authorization_error",
            "Only patients and doctors can view doctor availability",
        )

    if from_date > to_date:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "from_date cannot be after to_date",
        )

    try:
        doctor, slots = await service.get_doctor_availability_range(
            doctor_id,
            from_date,
            to_date,
            slot_duration_minutes=appointment_duration,
        )
    except HTTPException as exc:
        raise map_http_exception(exc) from exc

    availability_slots = [DoctorAvailabilitySlot.model_validate(slot) for slot in slots]

    return DoctorAvailabilityResponse(
        doctor_id=doctor.user_id,
        doctor_name=doctor.display_name,
        from_date=from_date,
        to_date=to_date,
        appointment_duration_minutes=appointment_duration,
        available_slots=availability_slots,
    )
