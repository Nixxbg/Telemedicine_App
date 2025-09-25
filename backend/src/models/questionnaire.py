"""
QuestionnaireProgress model - Tracks completion status of medical history questionnaire
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.patient import Patient


class QuestionnaireProgress(Base):
    """
    Tracks completion status of medical history questionnaire sections

    This model tracks which sections of the patient onboarding questionnaire
    have been completed, allowing for partial completion and session persistence.
    """

    __tablename__ = "questionnaire_progress"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )

    # Foreign key (one-to-one with Patient)
    patient_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("patients.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Questionnaire section completion status
    family_history_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    current_conditions_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    past_procedures_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    medications_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    allergies_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    drug_resistance_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    personal_info_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    emergency_contacts_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Calculated completion percentage
    overall_completion_percentage: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # Timestamp
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="questionnaire_progress", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<QuestionnaireProgress(id={self.id}, patient_id={self.patient_id}, "
            f"completion={self.overall_completion_percentage}%)>"
        )

    @property
    def completed_sections(self) -> list[str]:
        """Get list of completed section names"""
        sections = []
        if self.family_history_completed:
            sections.append("family_history")
        if self.current_conditions_completed:
            sections.append("current_conditions")
        if self.past_procedures_completed:
            sections.append("past_procedures")
        if self.medications_completed:
            sections.append("medications")
        if self.allergies_completed:
            sections.append("allergies")
        if self.drug_resistance_completed:
            sections.append("drug_resistance")
        if self.personal_info_completed:
            sections.append("personal_info")
        if self.emergency_contacts_completed:
            sections.append("emergency_contacts")
        return sections

    @property
    def incomplete_sections(self) -> list[str]:
        """Get list of incomplete section names"""
        all_sections = [
            "family_history",
            "current_conditions",
            "past_procedures",
            "medications",
            "allergies",
            "drug_resistance",
            "personal_info",
            "emergency_contacts",
        ]
        completed = self.completed_sections
        return [section for section in all_sections if section not in completed]

    @property
    def is_fully_completed(self) -> bool:
        """Check if all questionnaire sections are completed"""
        return self.overall_completion_percentage == 100

    def calculate_completion_percentage(self) -> int:
        """Calculate and update completion percentage based on completed sections"""
        total_sections = 8
        completed_count = len(self.completed_sections)
        percentage = int((completed_count / total_sections) * 100)
        self.overall_completion_percentage = percentage
        return percentage

    def mark_section_complete(self, section_name: str) -> bool:
        """
        Mark a specific section as complete

        Args:
            section_name: Name of the section to mark complete

        Returns:
            bool: True if section was successfully marked, False if invalid section
        """
        section_mapping = {
            "family_history": "family_history_completed",
            "current_conditions": "current_conditions_completed",
            "past_procedures": "past_procedures_completed",
            "medications": "medications_completed",
            "allergies": "allergies_completed",
            "drug_resistance": "drug_resistance_completed",
            "personal_info": "personal_info_completed",
            "emergency_contacts": "emergency_contacts_completed",
        }

        if section_name not in section_mapping:
            return False

        setattr(self, section_mapping[section_name], True)
        self.calculate_completion_percentage()
        return True

    def get_next_incomplete_section(self) -> str | None:
        """Get the next incomplete section in logical order"""
        section_order = [
            "personal_info",
            "emergency_contacts",
            "family_history",
            "current_conditions",
            "past_procedures",
            "medications",
            "allergies",
            "drug_resistance",
        ]

        for section in section_order:
            if section in self.incomplete_sections:
                return section
        return None
