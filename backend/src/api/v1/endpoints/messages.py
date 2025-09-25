"""Messaging API endpoints."""

from __future__ import annotations

import json
from typing import Any, Mapping, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.models.appointment import Appointment
from src.models.message import Message as MessageModel
from src.models.message import MessageType
from src.models.user import User, UserType
from src.schemas.message import (
    AppointmentSummary,
    Conversation,
    ConversationsResponse,
    MessageDetail,
    MessagesResponse,
    SendMessageRequest,
    SuccessResponse,
    UpdateMessageRequest,
    UserSummary,
)
from src.schemas.message import (
    Message as MessageSchema,
)
from src.services.auth_service import AuthService
from src.services.message_service import MessageService

router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=False)


def http_error(
    status_code: int,
    error: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> HTTPException:
    """Create a structured :class:`HTTPException` for contract compliance."""

    payload: dict[str, Any] = {"error": error, "message": message}
    if details:
        payload["details"] = details
    return HTTPException(status_code=status_code, detail=payload)


def map_http_exception(
    exc: HTTPException, default_error: str | None = None
) -> HTTPException:
    """Normalize service exceptions into API contract errors."""

    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return exc

    message = str(detail) if detail else "Request could not be processed"
    error = default_error
    if error is None:
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            error = "validation_error"
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            error = "authentication_error"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            error = "access_denied"
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            error = "not_found"
        else:
            error = "server_error" if exc.status_code >= 500 else "request_error"

    return http_error(exc.status_code, error, message)


def raise_validation_error(
    message: str,
    *,
    field: str | None = None,
    code: str | None = None,
) -> NoReturn:
    """Raise a contract-compliant validation error."""

    details: dict[str, Any] | None = None
    if field or code:
        details = {}
        if field:
            details["field"] = field
        if code:
            details["code"] = code

    raise http_error(
        status.HTTP_400_BAD_REQUEST,
        "validation_error",
        message,
        details,
    )


def _to_valid_uuid(value: Any, field: str) -> UUID:
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (TypeError, ValueError):
        raise_validation_error(
            f"{field.replace('_', ' ').title()} must be a valid UUID",
            field=field,
            code="invalid_uuid",
        )


def parse_uuid_param(value: Any, field: str) -> UUID | None:
    """Parse an optional UUID query parameter."""

    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return _to_valid_uuid(value, field)


def parse_int_param(
    value: Any,
    field: str,
    *,
    default: int,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Parse an integer query parameter with optional bounds."""

    raw = default if value is None else value
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        raise_validation_error(
            f"{field.replace('_', ' ').title()} must be an integer",
            field=field,
            code="invalid_integer",
        )

    if minimum is not None and parsed < minimum:
        raise_validation_error(
            f"{field.replace('_', ' ').title()} must be at least {minimum}",
            field=field,
            code="value_too_small",
        )

    if maximum is not None and parsed > maximum:
        raise_validation_error(
            f"{field.replace('_', ' ').title()} must be at most {maximum}",
            field=field,
            code="value_too_large",
        )

    return parsed


def parse_bool_param(value: Any, field: str, *, default: bool = False) -> bool:
    """Parse a boolean query parameter supporting multiple representations."""

    if value is None:
        return default
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False

    raise_validation_error(
        f"{field.replace('_', ' ').title()} must be a boolean value",
        field=field,
        code="invalid_boolean",
    )


def parse_sort_order(value: Any) -> str:
    """Parse the sort order query parameter."""

    default = "desc"
    if value is None:
        return default

    normalized = str(value).strip().lower()
    if normalized not in {"asc", "desc"}:
        raise_validation_error(
            "sort_order must be either 'asc' or 'desc'",
            field="sort_order",
            code="invalid_choice",
        )
    return normalized


def parse_message_type_param(value: Any) -> MessageType | None:
    """Parse the optional message type filter."""

    if value is None:
        return None
    if isinstance(value, MessageType):
        return value

    normalized = str(value).strip().lower()
    try:
        return MessageType(normalized)
    except ValueError:
        valid = ", ".join(sorted(item.value for item in MessageType))
        raise_validation_error(
            f"message_type must be one of: {valid}",
            field="message_type",
            code="invalid_choice",
        )


def parse_send_message_payload(payload: Mapping[str, Any]) -> SendMessageRequest:
    """Validate and normalize the send message request payload."""

    if not isinstance(payload, Mapping):
        raise_validation_error(
            "Request body must be a JSON object",
            code="invalid_body",
        )

    recipient_raw = payload.get("recipient_id")
    if recipient_raw is None:
        raise_validation_error(
            "recipient_id is required",
            field="recipient_id",
            code="missing_field",
        )
    recipient_id = _to_valid_uuid(recipient_raw, "recipient_id")

    content_raw = payload.get("content")
    if content_raw is None:
        raise_validation_error(
            "content is required",
            field="content",
            code="missing_field",
        )

    content = str(content_raw).strip()
    if not content:
        raise_validation_error(
            "Message content cannot be empty",
            field="content",
            code="empty",
        )
    if len(content) > 2000:
        raise_validation_error(
            "Message content cannot exceed 2000 characters",
            field="content",
            code="too_long",
        )

    appointment_raw = payload.get("appointment_id")
    appointment_id = None
    if appointment_raw is not None:
        appointment_id = _to_valid_uuid(appointment_raw, "appointment_id")

    return SendMessageRequest(
        recipient_id=recipient_id,
        content=content,
        appointment_id=appointment_id,
    )


async def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthService:
    """Provide an :class:`AuthService` instance via dependency injection."""

    return AuthService(session)


async def get_message_service(
    session: AsyncSession = Depends(get_async_session),
) -> MessageService:
    """Provide a :class:`MessageService` instance via dependency injection."""

    return MessageService(session)


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
    except HTTPException as exc:  # pragma: no cover - delegated to auth tests
        raise map_http_exception(exc, default_error="authentication_error") from exc


def to_user_summary(user: User) -> UserSummary:
    """Convert a :class:`User` ORM entity into a :class:`UserSummary`."""

    if user.user_type == UserType.PATIENT:
        patient = getattr(user, "patient", None)
        if not patient:
            raise http_error(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "server_error",
                "Patient profile is missing",
            )
        return UserSummary(
            id=user.id,
            user_type=user.user_type,
            first_name=patient.first_name,
            last_name=patient.last_name,
            username=patient.username,
        )

    if user.user_type == UserType.DOCTOR:
        doctor = getattr(user, "doctor", None)
        if not doctor:
            raise http_error(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "server_error",
                "Doctor profile is missing",
            )
        return UserSummary(
            id=user.id,
            user_type=user.user_type,
            first_name=doctor.first_name,
            last_name=doctor.last_name,
            doctor_id=doctor.doctor_id,
        )

    raise http_error(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "server_error",
        "Unsupported user type for messaging",
    )


def to_appointment_summary(
    appointment: Appointment | None,
) -> AppointmentSummary | None:
    """Convert an appointment ORM entity into a summary schema."""

    if appointment is None:
        return None
    return AppointmentSummary.model_validate(appointment)


def to_message_schema(message: MessageModel) -> MessageSchema:
    """Convert a message ORM entity into the base message schema."""

    return MessageSchema(
        id=message.id,
        sender_id=message.sender_id,
        recipient_id=message.recipient_id,
        appointment_id=message.appointment_id,
        content=message.content,
        message_type=message.message_type,
        is_read=message.is_read,
        sent_at=message.sent_at,
        read_at=message.read_at,
    )


def to_message_detail(message: MessageModel) -> MessageDetail:
    """Convert a message ORM entity into the detailed message schema."""

    return MessageDetail(
        id=message.id,
        sender_id=message.sender_id,
        recipient_id=message.recipient_id,
        appointment_id=message.appointment_id,
        content=message.content,
        message_type=message.message_type,
        is_read=message.is_read,
        sent_at=message.sent_at,
        read_at=message.read_at,
        sender=to_user_summary(message.sender),
        recipient=to_user_summary(message.recipient),
        appointment=to_appointment_summary(message.appointment),
    )


def to_conversation(payload: dict[str, Any]) -> Conversation:
    """Convert a conversation aggregate into the response schema."""

    latest_message: MessageModel = payload["latest_message"]
    partner: User = payload["partner"]
    appointment: Appointment | None = payload.get("appointment")

    return Conversation(
        conversation_id=payload["partner_id"],
        participant=to_user_summary(partner),
        appointment=to_appointment_summary(appointment),
        last_message=to_message_schema(latest_message),
        unread_count=payload["unread_count"],
        total_messages=payload["total_messages"],
        last_activity=latest_message.sent_at,
    )


@router.get("/", response_model=MessagesResponse)
async def list_messages(  # noqa: D401 - FastAPI generates schema docs
    appointment_id: str | None = Query(default=None),
    conversation_with: str | None = Query(default=None),
    message_type: str | None = Query(default=None),
    unread_only: bool | str | None = Query(default=None),
    limit: int | str | None = Query(default=50),
    offset: int | str | None = Query(default=0),
    sort_order: str | None = Query(default="desc"),
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
) -> MessagesResponse:
    """Return messages for the authenticated user with optional filters."""

    appointment_uuid = parse_uuid_param(appointment_id, "appointment_id")
    conversation_uuid = parse_uuid_param(conversation_with, "conversation_with")
    message_type_enum = parse_message_type_param(message_type)
    unread_only_flag = parse_bool_param(unread_only, "unread_only", default=False)
    limit_value = parse_int_param(limit, "limit", default=50, minimum=1, maximum=100)
    offset_value = parse_int_param(offset, "offset", default=0, minimum=0)
    sort_order_value = parse_sort_order(sort_order)

    messages, total_count, unread_count = await service.list_user_messages(
        current_user.id,
        appointment_id=appointment_uuid,
        conversation_with=conversation_uuid,
        message_type=message_type_enum,
        unread_only=unread_only_flag,
        limit=limit_value,
        offset=offset_value,
        sort_order=sort_order_value,
    )

    return MessagesResponse(
        messages=[to_message_detail(message) for message in messages],
        total_count=total_count,
        unread_count=unread_count,
        offset=offset_value,
        limit=limit_value,
    )


@router.post(
    "/",
    response_model=MessageDetail,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
) -> MessageDetail:
    """Send a message from the authenticated user to a recipient."""

    content_type = request.headers.get("content-type", "").lower()
    if "application/json" not in content_type:
        raise_validation_error(
            "Content-Type must be application/json",
            code="invalid_content_type",
        )

    try:
        raw_payload = await request.json()
    except (json.JSONDecodeError, ValueError):
        raise_validation_error(
            "Invalid JSON payload",
            code="invalid_json",
        )

    request_payload = parse_send_message_payload(raw_payload)

    try:
        created = await service.send_message(
            sender_id=current_user.id,
            recipient_id=request_payload.recipient_id,
            content=request_payload.content,
            sender_user_type=current_user.user_type,
            message_type=MessageType.TEXT,
            appointment_id=request_payload.appointment_id,
        )
    except HTTPException as exc:
        raise map_http_exception(exc) from exc

    fresh = await service.get_message(created.id, current_user.id)
    if not fresh:  # pragma: no cover - defensive guard
        raise http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "server_error",
            "Failed to load created message",
        )

    return to_message_detail(fresh)


@router.get("/{message_id}", response_model=MessageDetail)
async def get_message_detail(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
) -> MessageDetail:
    """Retrieve a specific message for the authenticated user."""

    message = await service.get_message(message_id, current_user.id)
    if not message:
        raise http_error(
            status.HTTP_404_NOT_FOUND,
            "not_found",
            "Message not found",
        )

    return to_message_detail(message)


@router.put("/{message_id}", response_model=MessageDetail)
async def update_message_read_state(
    message_id: UUID,
    payload: UpdateMessageRequest,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
) -> MessageDetail:
    """Update the read status of a message."""

    if payload.is_read is None:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "is_read is required",
        )

    message = await service.get_message(message_id, current_user.id)
    if not message:
        raise http_error(
            status.HTTP_404_NOT_FOUND,
            "not_found",
            "Message not found",
        )

    if message.recipient_id != current_user.id:
        raise http_error(
            status.HTTP_403_FORBIDDEN,
            "access_denied",
            "Only the message recipient can update read status",
        )

    if payload.is_read:
        updated = await service.mark_message_as_read(message_id, current_user.id)
        if not updated:
            raise http_error(
                status.HTTP_404_NOT_FOUND,
                "not_found",
                "Message not found",
            )
        message = updated
    else:
        if message.is_read:
            message.is_read = False
            message.read_at = None
            await service.session.commit()
            await service.session.refresh(message)

    return to_message_detail(message)


@router.get("/conversations", response_model=ConversationsResponse)
async def list_conversations(  # noqa: D401 - FastAPI generates schema docs
    current_user: User = Depends(get_current_user),
    include_archived: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    service: MessageService = Depends(get_message_service),
) -> ConversationsResponse:
    """Return conversations for the authenticated user."""

    # include_archived reserved for future enhancements
    _ = include_archived

    raw_conversations = await service.get_user_conversations(
        current_user.id, limit=None
    )
    total_count = len(raw_conversations)

    if offset >= total_count:
        sliced: list[dict[str, Any]] = []
    else:
        sliced = raw_conversations[offset : offset + limit]

    conversations = [to_conversation(entry) for entry in sliced]

    return ConversationsResponse(
        conversations=conversations,
        total_count=total_count,
        offset=offset,
        limit=limit,
    )


@router.put(
    "/conversations/{conversation_id}/mark-read",
    response_model=SuccessResponse,
)
async def mark_conversation_as_read(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
) -> SuccessResponse:
    """Mark all unread messages in a conversation as read."""

    if conversation_id == current_user.id:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "Cannot mark a conversation with yourself",
        )

    partner = await service.session.get(User, conversation_id)
    if not partner:
        raise http_error(
            status.HTTP_404_NOT_FOUND,
            "not_found",
            "Conversation not found",
        )

    try:
        # Ensure the requester has access to this conversation
        await service.get_conversation(
            current_user.id,
            conversation_id,
            current_user.id,
            limit=1,
        )
    except HTTPException as exc:
        raise map_http_exception(exc, default_error="access_denied") from exc

    updated = await service.mark_conversation_as_read(
        sender_id=conversation_id, recipient_id=current_user.id
    )

    message = (
        f"Marked {updated} messages as read"
        if updated
        else "No unread messages to mark"
    )

    return SuccessResponse(message=message)
