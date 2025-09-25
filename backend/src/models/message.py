"""
Message model - Secure text-based communication between patients and doctors
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.appointment import Appointment
    from src.models.user import User


class MessageType(str, enum.Enum):
    """Message type enumeration"""

    TEXT = "text"
    SYSTEM_NOTIFICATION = "system_notification"


class Message(Base):
    """
    Secure text-based communication between patients and doctors

    This model represents messages exchanged between users, with optional
    appointment context and read status tracking.
    """

    __tablename__ = "messages"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )

    # Foreign keys
    sender_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipient_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appointment_id: Mapped[Optional[UUID]] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Message content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType), default=MessageType.TEXT, nullable=False
    )

    # Read status
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )

    # Timestamps
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    sender: Mapped["User"] = relationship(
        "User", foreign_keys=[sender_id], back_populates="sent_messages", lazy="select"
    )

    recipient: Mapped["User"] = relationship(
        "User",
        foreign_keys=[recipient_id],
        back_populates="received_messages",
        lazy="select",
    )

    appointment: Mapped[Optional["Appointment"]] = relationship(
        "Appointment", back_populates="messages", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id}, sender_id={self.sender_id}, "
            f"recipient_id={self.recipient_id}, type={self.message_type})>"
        )

    @property
    def is_system_message(self) -> bool:
        """Check if message is a system notification"""
        return self.message_type == MessageType.SYSTEM_NOTIFICATION

    @property
    def is_text_message(self) -> bool:
        """Check if message is a regular text message"""
        return self.message_type == MessageType.TEXT

    @property
    def content_preview(self) -> str:
        """Get a preview of the message content (first 100 characters)"""
        if len(self.content) <= 100:
            return self.content
        return f"{self.content[:97]}..."

    def mark_as_read(self) -> None:
        """Mark message as read with current timestamp"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()

    def is_valid_length(self) -> bool:
        """Check if message content is within valid length (max 2000 chars)"""
        return len(self.content.strip()) > 0 and len(self.content) <= 2000

    def can_be_read_by(self, user_id: UUID) -> bool:
        """Check if a user can read this message"""
        return user_id in [self.sender_id, self.recipient_id]
