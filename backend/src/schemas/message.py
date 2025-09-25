"""Messaging request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.appointment import AppointmentStatus, AppointmentType
from src.models.message import MessageType
from src.models.user import UserType

NonEmptyContent = Annotated[str, Field(min_length=1, max_length=2000)]


class SendMessageRequest(BaseModel):
    """Schema for sending a new message."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    recipient_id: UUID
    content: NonEmptyContent
    appointment_id: UUID | None = None


class UpdateMessageRequest(BaseModel):
    """Schema for updating a message (e.g., marking as read)."""

    model_config = ConfigDict(extra="forbid")

    is_read: bool | None = None


class UserSummary(BaseModel):
    """Compact representation of a user for messaging responses."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: UUID
    user_type: UserType
    first_name: str
    last_name: str
    username: str | None = None
    doctor_id: str | None = None


class AppointmentSummary(BaseModel):
    """Minimal appointment details used in messaging context."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: UUID
    scheduled_start: datetime
    status: AppointmentStatus
    appointment_type: AppointmentType


class Message(BaseModel):
    """Base message schema returned by the API."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: UUID
    sender_id: UUID
    recipient_id: UUID
    appointment_id: UUID | None = None
    content: str
    message_type: MessageType
    is_read: bool
    sent_at: datetime
    read_at: datetime | None = None


class MessageDetail(Message):
    """Message schema enriched with participant summaries."""

    sender: UserSummary
    recipient: UserSummary
    appointment: AppointmentSummary | None = None


class MessagesResponse(BaseModel):
    """Paginated response containing messages for a user."""

    model_config = ConfigDict(extra="ignore")

    messages: list[MessageDetail]
    total_count: int
    unread_count: int
    offset: int
    limit: int


class Conversation(BaseModel):
    """Conversation summary for the conversation list endpoint."""

    model_config = ConfigDict(extra="ignore")

    conversation_id: UUID
    participant: UserSummary
    appointment: AppointmentSummary | None = None
    last_message: Message
    unread_count: int
    total_messages: int
    last_activity: datetime


class ConversationsResponse(BaseModel):
    """Paginated response containing user conversations."""

    model_config = ConfigDict(extra="ignore")

    conversations: list[Conversation]
    total_count: int
    offset: int
    limit: int


class SuccessResponse(BaseModel):
    """Generic success payload for messaging endpoints."""

    model_config = ConfigDict(extra="ignore")

    message: str
