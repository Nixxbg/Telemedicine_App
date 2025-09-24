"""
User model - Base authentication and profile entity
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.doctor import Doctor
    from src.models.message import Message
    from src.models.patient import Patient


class UserType(str, enum.Enum):
    """User type enumeration"""

    PATIENT = "patient"
    DOCTOR = "doctor"


class User(Base):
    """
    Base user model for authentication and common profile data

    This model serves as the base for both Patient and Doctor entities,
    providing common authentication fields and user type discrimination.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )

    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # User type discrimination
    user_type: Mapped[UserType] = mapped_column(Enum(UserType), nullable=False)

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    patient: Mapped[Optional["Patient"]] = relationship(
        "Patient",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select",
    )

    doctor: Mapped[Optional["Doctor"]] = relationship(
        "Doctor",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select",
    )

    sent_messages: Mapped[list["Message"]] = relationship(
        "Message",
        foreign_keys="Message.sender_id",
        back_populates="sender",
        lazy="select",
    )
    received_messages: Mapped[list["Message"]] = relationship(
        "Message",
        foreign_keys="Message.recipient_id",
        back_populates="recipient",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, user_type={self.user_type})>"

    @property
    def is_patient(self) -> bool:
        """Check if user is a patient"""
        return self.user_type == UserType.PATIENT

    @property
    def is_doctor(self) -> bool:
        """Check if user is a doctor"""
        return self.user_type == UserType.DOCTOR
