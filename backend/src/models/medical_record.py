"""
Medical Record models - Core medical information with versioning support
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID as PostgreSQL_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.patient import Patient
    from src.models.user import User


class RecordType(str, enum.Enum):
    """Medical record type enumeration"""

    MEDICAL_HISTORY = "medical_history"
    MEDICATION = "medication"
    ALLERGY = "allergy"
    PROCEDURE = "procedure"


class ChangeUserType(str, enum.Enum):
    """User type who made the change"""

    PATIENT = "patient"
    DOCTOR = "doctor"


class MedicalRecord(Base):
    """
    Core medical information container with versioning support

    This model represents a medical record that can be versioned.
    Each update creates a new version while preserving history.
    """

    __tablename__ = "medical_records"

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

    # Record metadata
    record_type: Mapped[RecordType] = mapped_column(Enum(RecordType), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
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

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="medical_records", lazy="select"
    )

    versions: Mapped[list["MedicalRecordVersion"]] = relationship(
        "MedicalRecordVersion",
        back_populates="medical_record",
        cascade="all, delete-orphan",
        order_by="MedicalRecordVersion.version_number.desc()",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<MedicalRecord(id={self.id}, title={self.title}, "
            f"type={self.record_type}, version={self.current_version})>"
        )

    @property
    def latest_version(self) -> Optional["MedicalRecordVersion"]:
        """Get the latest version of this record"""
        return self.versions[0] if self.versions else None

    def increment_version(self) -> int:
        """Increment version number and return new version"""
        self.current_version += 1
        return self.current_version


class MedicalRecordVersion(Base):
    """
    Immutable snapshots of medical record changes with audit trail

    This model stores the complete state of a medical record at a specific
    point in time, providing an audit trail of all changes.
    """

    __tablename__ = "medical_record_versions"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )

    # Foreign keys
    medical_record_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("medical_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    changed_by_user_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Version information
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by_user_type: Mapped[ChangeUserType] = mapped_column(
        Enum(ChangeUserType), nullable=False
    )

    # Timestamp (immutable)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    medical_record: Mapped["MedicalRecord"] = relationship(
        "MedicalRecord", back_populates="versions", lazy="select"
    )

    changed_by_user: Mapped["User"] = relationship("User", lazy="select")

    def __repr__(self) -> str:
        return (
            f"<MedicalRecordVersion(id={self.id}, "
            f"record_id={self.medical_record_id}, "
            f"version={self.version_number})>"
        )

    @property
    def is_patient_created(self) -> bool:
        """Check if this version was created by a patient"""
        return self.changed_by_user_type == ChangeUserType.PATIENT

    @property
    def is_doctor_created(self) -> bool:
        """Check if this version was created by a doctor"""
        return self.changed_by_user_type == ChangeUserType.DOCTOR
