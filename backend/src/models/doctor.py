"""
Doctor model - Healthcare provider profiles with specializations and availability
"""

from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID as PostgreSQL_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.appointment import Appointment
    from src.models.user import User


class Doctor(Base):
    """
    Doctor model extending User with healthcare provider-specific information

    This model contains doctor-specific data including specializations,
    credentials, and professional information.
    """

    __tablename__ = "doctors"

    # Primary key - references User.id
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    # Doctor-specific identifier (pre-assigned for v1)
    doctor_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )

    # Personal information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Professional information
    specializations: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    license_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    credentials: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    years_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Consultation settings
    consultation_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),  # Free for v1
        nullable=False,
    )
    is_accepting_patients: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="doctor", lazy="select")

    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        foreign_keys="Appointment.doctor_id",
        back_populates="doctor",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Doctor(user_id={self.user_id}, doctor_id={self.doctor_id}, "
            f"name={self.first_name} {self.last_name})>"
        )

    @property
    def full_name(self) -> str:
        """Get doctor's full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def display_name(self) -> str:
        """Get doctor's display name with title"""
        return f"Dr. {self.full_name}"

    @property
    def primary_specialization(self) -> Optional[str]:
        """Get doctor's primary specialization"""
        return self.specializations[0] if self.specializations else None

    def has_specialization(self, specialization: str) -> bool:
        """Check if doctor has a specific specialization"""
        return specialization.lower() in [spec.lower() for spec in self.specializations]

    def get_years_experience_display(self) -> str:
        """Get formatted years of experience"""
        if not self.years_experience:
            return "Experience not specified"
        years = self.years_experience
        suffix = "s" if years != 1 else ""
        return f"{years} year{suffix}"
