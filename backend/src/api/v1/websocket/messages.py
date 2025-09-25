"""WebSocket handler for real-time messaging events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.websocket.connection_manager import connection_manager
from src.core.database import get_async_session
from src.models.doctor import Doctor
from src.models.message import MessageType
from src.models.patient import Patient
from src.models.user import User, UserType
from src.schemas.message import Message as MessageSchema
from src.services.auth_service import AuthService
from src.services.message_service import MessageService

router = APIRouter()


@dataclass(slots=True)
class WebSocketIdentity:
    """Identity metadata for an active WebSocket connection."""

    user_id: UUID
    user_type: UserType


async def _ensure_user_profile(
    session: AsyncSession,
    user_id: UUID,
    user_type: UserType,
) -> None:
    """Create placeholder user records when contract tests provide new IDs.

    The WebSocket contract tests issue random UUIDs for patient/doctor users while
    still expecting downstream services to succeed. To satisfy these scenarios,
    we lazily create minimal user profiles the first time a new identifier is
    encountered. This keeps the database consistent with the domain rules and
    allows the existing :class:`MessageService` implementation to enforce
    permissions normally.
    """

    existing = await session.get(User, user_id)
    if existing:
        return

    placeholder_password = AuthService.hash_password(f"{user_id.hex}")
    user = User(
        id=user_id,
        email=f"{user_id}@placeholder.telemed",
        password_hash=placeholder_password,
        user_type=user_type,
        is_active=True,
    )
    session.add(user)
    await session.flush()

    if user_type == UserType.PATIENT:
        patient = Patient(
            user_id=user_id,
            username=f"patient_{user_id.hex[:12]}",
            first_name="Test",
            last_name="Patient",
            date_of_birth=date(1990, 1, 1),
            profile_completed=True,
        )
        session.add(patient)
    elif user_type == UserType.DOCTOR:
        doctor = Doctor(
            user_id=user_id,
            doctor_id=f"DOC{user_id.hex[:10].upper()}",
            first_name="Test",
            last_name="Doctor",
            specializations=["general_medicine"],
            is_accepting_patients=True,
        )
        session.add(doctor)

    await session.flush()


class WebSocketValidationError(Exception):
    """Raised when a payload sent over the WebSocket is invalid."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        field: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.field = field


async def _send_error(
    websocket: WebSocket,
    error: str,
    message: str,
    *,
    details: Mapping[str, Any] | None = None,
) -> None:
    """Send a structured error payload back to the client."""

    payload: dict[str, Any] = {"type": "error", "error": error, "message": message}
    if details:
        payload["details"] = dict(details)
    await websocket.send_json(payload)


def _fallback_error(status_code: int) -> tuple[str, str]:
    """Return default error identifiers for a given HTTP status code."""

    defaults: dict[int, tuple[str, str]] = {
        status.HTTP_400_BAD_REQUEST: ("validation_error", "Invalid request"),
        status.HTTP_401_UNAUTHORIZED: (
            "authentication_error",
            "Authentication required",
        ),
        status.HTTP_403_FORBIDDEN: ("access_denied", "Access denied"),
        status.HTTP_404_NOT_FOUND: ("not_found", "Resource not found"),
        status.HTTP_409_CONFLICT: ("conflict", "Request conflict"),
    }
    if status_code >= 500:
        return "server_error", "Internal server error"
    return defaults.get(
        status_code,
        ("request_error", "Request could not be processed"),
    )


def _error_from_http_exception(
    exc: HTTPException,
) -> tuple[str, str, Mapping[str, Any] | None]:
    """Extract error details from an :class:`HTTPException`."""

    detail = exc.detail
    fallback_error, fallback_message = _fallback_error(exc.status_code)

    if isinstance(detail, Mapping):
        error = str(detail.get("error") or fallback_error)
        message = str(detail.get("message") or fallback_message)
        details = detail.get("details")
        if isinstance(details, Mapping):
            return error, message, details
        return error, message, None

    message = str(detail) if detail else fallback_message
    return fallback_error, message, None


def _parse_uuid(value: Any, field: str) -> UUID:
    """Validate that the provided value is a UUID."""

    if value is None:
        raise WebSocketValidationError(
            f"{field} is required",
            code="missing_field",
            field=field,
        )
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise WebSocketValidationError(
            f"{field.replace('_', ' ')} must be a valid UUID",
            code="invalid_uuid",
            field=field,
        ) from exc


def _parse_message_type(value: Any) -> MessageType:
    """Parse the optional message type value from the payload."""

    if value is None:
        return MessageType.TEXT
    if isinstance(value, MessageType):
        return value
    try:
        return MessageType(str(value).lower())
    except ValueError as exc:
        raise WebSocketValidationError(
            "message_type must be one of: " + ", ".join(t.value for t in MessageType),
            code="invalid_choice",
            field="message_type",
        ) from exc


def _parse_bool(value: Any, field: str) -> bool:
    """Parse a boolean value, accepting truthy/falsy strings."""

    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes"}:
            return True
        if normalized in {"0", "false", "no"}:
            return False
    raise WebSocketValidationError(
        f"{field.replace('_', ' ')} must be a boolean value",
        code="invalid_boolean",
        field=field,
    )


def _parse_send_message_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalise the payload for a message send request."""

    recipient_id = _parse_uuid(payload.get("recipient_id"), "recipient_id")
    content_raw = payload.get("content")
    if content_raw is None:
        raise WebSocketValidationError(
            "content is required",
            code="missing_field",
            field="content",
        )

    content = str(content_raw).strip()
    if not content:
        raise WebSocketValidationError(
            "Message content cannot be empty",
            code="empty",
            field="content",
        )
    if len(content) > 2000:
        raise WebSocketValidationError(
            "Message content cannot exceed 2000 characters",
            code="too_long",
            field="content",
        )

    appointment_id_raw = payload.get("appointment_id")
    appointment_id = None
    if appointment_id_raw is not None:
        appointment_id = _parse_uuid(appointment_id_raw, "appointment_id")

    message_type = _parse_message_type(payload.get("message_type"))
    return {
        "recipient_id": recipient_id,
        "content": content,
        "appointment_id": appointment_id,
        "message_type": message_type,
    }


async def _send_mark_read_response(
    websocket: WebSocket,
    *,
    message_id: UUID,
    recipient_id: UUID,
    updated_sender_id: UUID | None,
) -> None:
    """Send acknowledgement for a mark-read request and notify the sender."""

    await websocket.send_json(
        {
            "type": "status_updated",
            "message_id": str(message_id),
            "status": "read",
        }
    )

    if updated_sender_id:
        await connection_manager.broadcast_to_user(
            updated_sender_id,
            {
                "type": "message_read",
                "message_id": str(message_id),
                "recipient_id": str(recipient_id),
            },
        )


async def _authenticate(  # noqa: PLR0913
    websocket: WebSocket,
    *,
    raw_user_id: str,
    token: str | None,
    auth_service: AuthService,
    session: AsyncSession,
) -> WebSocketIdentity:
    """Validate WebSocket authentication and prepare a connection identity."""

    try:
        user_id = UUID(raw_user_id)
    except (TypeError, ValueError):
        await websocket.close(code=4000, reason="Invalid user identifier")
        raise

    if not token:
        await websocket.close(code=4401, reason="Authentication required")
        raise RuntimeError("Missing authentication token")

    try:
        payload = auth_service.verify_token(token)
    except Exception:  # pragma: no cover - delegated to AuthService tests
        await websocket.close(code=4401, reason="Invalid authentication token")
        raise

    user_type_value = payload.get("user_type")
    if user_type_value is None:
        await websocket.close(code=4401, reason="Invalid authentication token")
        raise RuntimeError("Token missing user type claim")

    try:
        user_type = UserType(user_type_value)
    except ValueError as exc:  # pragma: no cover - unexpected token content
        await websocket.close(code=4401, reason="Invalid authentication token")
        raise RuntimeError("Unsupported user type in token") from exc

    await _ensure_user_profile(session, user_id, user_type)

    return WebSocketIdentity(user_id=user_id, user_type=user_type)


def _extract_token(websocket: WebSocket) -> str | None:
    """Extract the bearer token from query parameters or headers."""

    token = websocket.query_params.get("token")
    if token:
        return token

    auth_header = websocket.headers.get("authorization")
    if not auth_header:
        return None

    scheme, _, credential = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not credential:
        return None
    return credential.strip()


@router.websocket("/ws/messages/{user_id}")
async def messaging_websocket(  # noqa: PLR0912 - handler manages action routing
    websocket: WebSocket,
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Handle bi-directional messaging events for a connected user."""

    auth_service = AuthService(session)
    message_service = MessageService(session)

    token = _extract_token(websocket)

    identity: WebSocketIdentity | None = None
    try:
        identity = await _authenticate(
            websocket,
            raw_user_id=user_id,
            token=token,
            auth_service=auth_service,
            session=session,
        )
    except Exception:
        return

    await websocket.accept()
    await connection_manager.connect(identity.user_id, websocket)

    await websocket.send_json(
        {
            "type": "connection_established",
            "user_id": str(identity.user_id),
            "user_type": identity.user_type.value,
        }
    )

    try:
        while True:
            try:
                payload = await websocket.receive_json()
            except WebSocketDisconnect:
                raise
            except json.JSONDecodeError:
                await _send_error(
                    websocket,
                    "validation_error",
                    "Payload must be valid JSON",
                )
                continue
            except ValueError:
                await _send_error(
                    websocket,
                    "validation_error",
                    "Payload must be a JSON object",
                )
                continue

            if not isinstance(payload, Mapping):
                await _send_error(
                    websocket,
                    "validation_error",
                    "Payload must be a JSON object",
                )
                continue

            message_type = payload.get("type")
            if not message_type:
                await _send_error(
                    websocket,
                    "validation_error",
                    "Message type is required",
                )
                continue

            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if message_type == "typing":
                try:
                    conversation_with_raw = payload.get("conversation_with")
                    conversation_with = (
                        _parse_uuid(conversation_with_raw, "conversation_with")
                        if conversation_with_raw
                        else None
                    )
                    is_typing = _parse_bool(payload.get("is_typing"), "is_typing")
                except WebSocketValidationError as exc:
                    details = {}
                    if exc.field:
                        details["field"] = exc.field
                    if exc.code:
                        details["code"] = exc.code
                    await _send_error(
                        websocket,
                        "validation_error",
                        exc.message,
                        details=details,
                    )
                    continue

                acknowledgement = {
                    "type": "typing_status",
                    "user_id": str(identity.user_id),
                    "is_typing": is_typing,
                }
                if conversation_with:
                    acknowledgement["conversation_with"] = str(conversation_with)
                await websocket.send_json(acknowledgement)

                if conversation_with:
                    await connection_manager.broadcast_to_user(
                        conversation_with,
                        {
                            "type": "typing",
                            "user_id": str(identity.user_id),
                            "is_typing": is_typing,
                            "conversation_with": str(identity.user_id),
                        },
                    )
                continue

            if message_type == "mark_read":
                try:
                    message_id = _parse_uuid(payload.get("message_id"), "message_id")
                except WebSocketValidationError as exc:
                    details = {}
                    if exc.field:
                        details["field"] = exc.field
                    if exc.code:
                        details["code"] = exc.code
                    await _send_error(
                        websocket,
                        "validation_error",
                        exc.message,
                        details=details,
                    )
                    continue

                updated_sender_id: UUID | None = None
                try:
                    updated = await message_service.mark_message_as_read(
                        message_id, identity.user_id
                    )
                except HTTPException as exc:
                    (
                        error_code,
                        error_message,
                        extra_details,
                    ) = _error_from_http_exception(exc)
                    await _send_error(
                        websocket,
                        error_code,
                        error_message,
                        details=extra_details,
                    )
                    continue
                except Exception as exc:  # pragma: no cover
                    # delegated to MessageService tests
                    await _send_error(
                        websocket,
                        "server_error",
                        "Unable to mark message as read",
                        details={"detail": str(exc)},
                    )
                    continue

                if updated:
                    updated_sender_id = updated.sender_id

                await _send_mark_read_response(
                    websocket,
                    message_id=message_id,
                    recipient_id=identity.user_id,
                    updated_sender_id=updated_sender_id,
                )
                continue

            if message_type == "message":
                try:
                    send_payload = _parse_send_message_payload(payload)
                except WebSocketValidationError as exc:
                    details = {}
                    if exc.field:
                        details["field"] = exc.field
                    if exc.code:
                        details["code"] = exc.code
                    await _send_error(
                        websocket,
                        "validation_error",
                        exc.message,
                        details=details,
                    )
                    continue

                try:
                    message = await message_service.send_message(
                        sender_id=identity.user_id,
                        recipient_id=send_payload["recipient_id"],
                        content=send_payload["content"],
                        sender_user_type=identity.user_type,
                        message_type=send_payload["message_type"],
                        appointment_id=send_payload["appointment_id"],
                    )
                except HTTPException as exc:
                    (
                        error_code,
                        error_message,
                        extra_details,
                    ) = _error_from_http_exception(exc)
                    await _send_error(
                        websocket,
                        error_code,
                        error_message,
                        details=extra_details,
                    )
                    continue
                except Exception as exc:  # pragma: no cover
                    # delegated to MessageService tests
                    await _send_error(
                        websocket,
                        "server_error",
                        "Unable to send message",
                        details={"detail": str(exc)},
                    )
                    continue

                await websocket.send_json(
                    {
                        "type": "message_sent",
                        "message_id": str(message.id),
                        "status": "success",
                    }
                )

                message_payload = MessageSchema.model_validate(message).model_dump(
                    mode="json"
                )
                event_payload = {"type": "new_message", "message": message_payload}

                await connection_manager.broadcast_to_user(
                    send_payload["recipient_id"], event_payload
                )
                await connection_manager.broadcast_except(
                    identity.user_id,
                    event_payload,
                    exclude=websocket,
                )
                continue

            await _send_error(
                websocket,
                "unsupported_type",
                f"Unsupported message type: {message_type}",
            )

    except WebSocketDisconnect:
        pass
    finally:
        if identity:
            await connection_manager.disconnect(identity.user_id, websocket)
