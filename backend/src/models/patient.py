"""
Patient model - Patient-specific profile information and medical data ownership
"""

from datetime import date
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.appointment import Appointment
    from src.models.medical_record import MedicalRecord
    from src.models.questionnaire import QuestionnaireProgress
    from src.models.user import User


class Patient(Base):
    """
    Patient model extending User with patient-specific profile information

    This model contains patient-specific data including personal information,
    emergency contacts, and profile completion status.
    """

    __tablename__ = "patients"

    # Primary key - references User.id
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    # Patient-specific identifiers
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # Personal information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    # Contact information
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Emergency contact information
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True
    )
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )

    # Profile completion status
    profile_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="patient", lazy="select")

    medical_records: Mapped[list["MedicalRecord"]] = relationship(
        "MedicalRecord",
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy="select",
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        foreign_keys="Appointment.patient_id",
        back_populates="patient",
        lazy="select",
    )

    questionnaire_progress: Mapped[Optional["QuestionnaireProgress"]] = relationship(
        "QuestionnaireProgress",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Patient(user_id={self.user_id}, username={self.username}, "
            f"name={self.first_name} {self.last_name})>"
        )

    @property
    def full_name(self) -> str:
        """Get patient's full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def has_emergency_contact(self) -> bool:
        """Check if patient has emergency contact information"""
        return bool(self.emergency_contact_name and self.emergency_contact_phone)

    def calculate_age(self) -> int:
        """Calculate patient's current age"""
        from datetime import date

        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )
