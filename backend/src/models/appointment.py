"""
Appointment model - Scheduled consultations between patients and doctors
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.doctor import Doctor
    from src.models.message import Message
    from src.models.patient import Patient


class AppointmentStatus(str, enum.Enum):
    """Appointment status enumeration"""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AppointmentType(str, enum.Enum):
    """Appointment type enumeration"""

    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    URGENT = "urgent"


class Appointment(Base):
    """
    Scheduled consultations between patients and doctors

    This model represents appointments with status tracking,
    scheduling information, and relationships to participants.
    """

    __tablename__ = "appointments"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )

    # Foreign keys
    patient_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("patients.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doctor_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("doctors.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Scheduling information
    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Appointment metadata
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
        index=True,
    )
    appointment_type: Mapped[AppointmentType] = mapped_column(
        Enum(AppointmentType), default=AppointmentType.CONSULTATION, nullable=False
    )

    # Appointment details
    reason_for_visit: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preparation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cost (free for v1)
    cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )

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

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="appointments", lazy="select"
    )

    doctor: Mapped["Doctor"] = relationship(
        "Doctor", back_populates="appointments", lazy="select"
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="appointment",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Appointment(id={self.id}, patient_id={self.patient_id}, "
            f"doctor_id={self.doctor_id}, status={self.status})>"
        )

    @property
    def duration_minutes(self) -> int:
        """Get appointment duration in minutes"""
        delta = self.scheduled_end - self.scheduled_start
        return int(delta.total_seconds() / 60)

    @property
    def is_future(self) -> bool:
        """Check if appointment is in the future"""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        return self.scheduled_start > now

    @property
    def is_past(self) -> bool:
        """Check if appointment is in the past"""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        return self.scheduled_end < now

    @property
    def is_active(self) -> bool:
        """Check if appointment is currently active"""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        return (
            self.scheduled_start <= now <= self.scheduled_end
            and self.status == AppointmentStatus.IN_PROGRESS
        )

    def can_be_cancelled(self) -> bool:
        """Check if appointment can be cancelled"""
        return self.status in [AppointmentStatus.SCHEDULED] and self.is_future

    def can_start(self) -> bool:
        """Check if appointment can be started"""
        return self.status == AppointmentStatus.SCHEDULED and not self.is_past

    def can_complete(self) -> bool:
        """Check if appointment can be completed"""
        return self.status == AppointmentStatus.IN_PROGRESS
