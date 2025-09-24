"""Medical records API endpoints."""

from __future__ import annotations

from json import JSONDecodeError
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.models.medical_record import MedicalRecord, MedicalRecordVersion, RecordType
from src.models.user import User, UserType
from src.schemas import (
    MedicalRecordCreateRequest,
    MedicalRecordListResponse,
    MedicalRecordResponse,
    MedicalRecordUpdateRequest,
    MedicalRecordValidationError,
    MedicalRecordVersionResponse,
    MedicalRecordVersionsResponse,
    validate_medical_record_payload,
)
from src.services.auth_service import AuthService
from src.services.medical_record_service import MedicalRecordService

router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=False)


def http_error(
    status_code: int, error: str, message: str, details: dict[str, Any] | None = None
) -> HTTPException:
    """Create an :class:`HTTPException` with consistent error payload."""

    payload: dict[str, Any] = {"error": error, "message": message}
    if details:
        payload["details"] = details
    return HTTPException(status_code=status_code, detail=payload)


def map_http_exception(
    exc: HTTPException, default_error: str | None = None
) -> HTTPException:
    """Map service-level :class:`HTTPException` into API error format."""

    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return exc

    message = str(detail)
    error = default_error
    if error is None:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            error = "not_found"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            error = "authorization_error"
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            error = "authentication_error"
        else:
            error = "server_error"

    return http_error(exc.status_code, error, message)


def to_validation_exception(error: MedicalRecordValidationError) -> HTTPException:
    """Convert a domain validation error into an HTTP exception."""

    field = error.field or "payload"
    message = f"{field}: {error}"
    details = {"field": error.field, "message": str(error)} if error.field else None
    return http_error(
        status.HTTP_400_BAD_REQUEST,
        "validation_error",
        message,
        details=details,
    )


async def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthService:
    """FastAPI dependency returning an :class:`AuthService` instance."""

    return AuthService(session)


async def get_medical_record_service(
    session: AsyncSession = Depends(get_async_session),
) -> MedicalRecordService:
    """FastAPI dependency returning a :class:`MedicalRecordService` instance."""

    return MedicalRecordService(session)


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


def to_medical_record_response(record: MedicalRecord) -> MedicalRecordResponse:
    """Convert a :class:`MedicalRecord` ORM entity into a response schema."""

    latest_version = record.latest_version
    current_data = latest_version.data if latest_version else {}
    return MedicalRecordResponse(
        id=record.id,
        patient_id=record.patient_id,
        record_type=record.record_type,
        title=record.title,
        current_version=record.current_version,
        is_active=record.is_active,
        created_at=record.created_at,
        updated_at=record.updated_at,
        current_data=current_data,
    )


def to_version_response(version: MedicalRecordVersion) -> MedicalRecordVersionResponse:
    """Convert a :class:`MedicalRecordVersion` ORM entity into a response schema."""

    return MedicalRecordVersionResponse(
        id=version.id,
        medical_record_id=version.medical_record_id,
        version_number=version.version_number,
        data=version.data,
        change_reason=version.change_reason or "",
        changed_by_user_id=version.changed_by_user_id,
        changed_by_user_type=version.changed_by_user_type,
        created_at=version.created_at,
    )


@router.get("/", response_model=MedicalRecordListResponse)
async def list_medical_records(
    current_user: User = Depends(get_current_user),
    record_type: RecordType | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    patient_id: UUID | None = Query(default=None),
    service: MedicalRecordService = Depends(get_medical_record_service),
) -> MedicalRecordListResponse:
    """Return a paginated list of medical records for the authenticated context."""

    if current_user.user_type == UserType.PATIENT:
        target_patient_id = current_user.id
        if patient_id is not None and patient_id != current_user.id:
            raise http_error(
                status.HTTP_403_FORBIDDEN,
                "authorization_error",
                "Patients can only view their own medical records",
            )
    elif current_user.user_type == UserType.DOCTOR:
        if patient_id is None:
            raise http_error(
                status.HTTP_400_BAD_REQUEST,
                "validation_error",
                "Doctors must specify patient_id to view medical records",
            )
        target_patient_id = patient_id
    else:  # pragma: no cover - defensive guard
        raise http_error(
            status.HTTP_403_FORBIDDEN,
            "authorization_error",
            "Unsupported user type for medical record access",
        )

    try:
        records = await service.get_patient_medical_records(
            target_patient_id,
            current_user.id,
            current_user.user_type,
            record_type=record_type,
        )
    except HTTPException as exc:
        raise map_http_exception(exc) from exc

    total_count = len(records)
    if offset >= total_count:
        paginated_records = []
    else:
        paginated_records = records[offset : offset + limit]

    response_records = [
        to_medical_record_response(record) for record in paginated_records
    ]

    return MedicalRecordListResponse(
        records=response_records,
        total_count=total_count,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medical_record(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: MedicalRecordService = Depends(get_medical_record_service),
) -> MedicalRecordResponse:
    """Create a new medical record for the authenticated patient."""

    if current_user.user_type != UserType.PATIENT:
        raise http_error(
            status.HTTP_403_FORBIDDEN,
            "authorization_error",
            "Only patients can create medical records",
        )

    try:
        payload = await request.json()
    except JSONDecodeError as error:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "Request body must be valid JSON",
        ) from error

    if not isinstance(payload, dict):
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "Request payload must be a JSON object",
        )

    try:
        validated = cast(
            MedicalRecordCreateRequest,
            validate_medical_record_payload(payload, schema=MedicalRecordCreateRequest),
        )
    except MedicalRecordValidationError as error:
        raise to_validation_exception(error) from error

    try:
        record = await service.create_medical_record(
            patient_id=current_user.id,
            record_type=validated.record_type,
            title=validated.title,
            data=validated.data,
            created_by_user_id=current_user.id,
            created_by_user_type=current_user.user_type,
            change_reason=validated.change_reason,
        )
    except HTTPException as exc:
        raise map_http_exception(exc, default_error="validation_error") from exc

    fresh_record = await service.get_medical_record(
        record.id, current_user.id, current_user.user_type
    )
    if fresh_record is None:  # pragma: no cover - defensive guard
        raise http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "server_error",
            "Failed to load created medical record",
        )

    return to_medical_record_response(fresh_record)


@router.put("/{record_id}", response_model=MedicalRecordResponse)
async def update_medical_record(
    record_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: MedicalRecordService = Depends(get_medical_record_service),
) -> MedicalRecordResponse:
    """Update an existing medical record and create a new version."""

    try:
        record_uuid = UUID(record_id)
    except ValueError as error:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "Invalid record ID format",
        ) from error

    try:
        payload = await request.json()
    except JSONDecodeError as error:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "Request body must be valid JSON",
        ) from error

    if not isinstance(payload, dict):
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "Request payload must be a JSON object",
        )

    try:
        validated = cast(
            MedicalRecordUpdateRequest,
            validate_medical_record_payload(payload, schema=MedicalRecordUpdateRequest),
        )
    except MedicalRecordValidationError as error:
        raise to_validation_exception(error) from error

    try:
        await service.update_medical_record(
            record_id=record_uuid,
            data=validated.data,
            updated_by_user_id=current_user.id,
            updated_by_user_type=current_user.user_type,
            change_reason=validated.change_reason,
            title=validated.title,
        )
    except HTTPException as exc:
        raise map_http_exception(exc, default_error="validation_error") from exc

    fresh_record = await service.get_medical_record(
        record_uuid, current_user.id, current_user.user_type
    )
    if fresh_record is None:
        raise http_error(
            status.HTTP_404_NOT_FOUND,
            "not_found",
            "Medical record not found or access denied",
        )

    return to_medical_record_response(fresh_record)


@router.get(
    "/{record_id}/versions",
    response_model=MedicalRecordVersionsResponse,
)
async def list_medical_record_versions(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    limit: int | None = Query(default=None, ge=1, le=100),
    service: MedicalRecordService = Depends(get_medical_record_service),
) -> MedicalRecordVersionsResponse:
    """Return the version history for a medical record."""

    try:
        versions = await service.get_record_versions(
            record_id,
            current_user.id,
            current_user.user_type,
            limit=limit,
        )
    except HTTPException as exc:
        raise map_http_exception(exc) from exc

    version_responses = [to_version_response(version) for version in versions]

    return MedicalRecordVersionsResponse(
        record_id=record_id,
        total_versions=len(version_responses),
        versions=version_responses,
    )
