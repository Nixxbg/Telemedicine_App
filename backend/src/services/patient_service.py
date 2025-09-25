"""
Patient service for profile management and questionnaire progress tracking

This service handles:
- Patient profile management (personal info, emergency contacts)
- Medical questionnaire completion tracking
- Profile completion status updates
- Patient dashboard data aggregation
"""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.patient import Patient
from src.models.questionnaire import QuestionnaireProgress


class PatientService:
    """Service for patient profile and questionnaire management"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_patient_by_user_id(self, user_id: UUID) -> Optional[Patient]:
        """Get patient by user ID with relationships loaded"""
        stmt = (
            select(Patient)
            .options(
                selectinload(Patient.user),
                selectinload(Patient.questionnaire_progress),
                selectinload(Patient.medical_records),
                selectinload(Patient.appointments),
            )
            .where(Patient.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_patient_by_username(self, username: str) -> Optional[Patient]:
        """Get patient by username"""
        stmt = select(Patient).where(Patient.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_patient_profile(
        self,
        user_id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        emergency_contact_name: Optional[str] = None,
        emergency_contact_phone: Optional[str] = None,
    ) -> Patient:
        """
        Update patient profile information

        Args:
            user_id: Patient's user ID
            first_name: Updated first name
            last_name: Updated last name
            phone_number: Updated phone number
            emergency_contact_name: Updated emergency contact name
            emergency_contact_phone: Updated emergency contact phone

        Returns:
            Updated Patient object

        Raises:
            HTTPException: If patient not found
        """
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        # Update fields that are provided
        if first_name is not None:
            patient.first_name = first_name
        if last_name is not None:
            patient.last_name = last_name
        if phone_number is not None:
            patient.phone_number = phone_number
        if emergency_contact_name is not None:
            patient.emergency_contact_name = emergency_contact_name
        if emergency_contact_phone is not None:
            patient.emergency_contact_phone = emergency_contact_phone

        # Check if profile is now complete
        await self._update_profile_completion_status(patient)

        await self.session.commit()
        await self.session.refresh(patient)
        return patient

    async def update_patient_date_of_birth(
        self, user_id: UUID, date_of_birth: date
    ) -> Patient:
        """
        Update patient date of birth

        Args:
            user_id: Patient's user ID
            date_of_birth: New date of birth

        Returns:
            Updated Patient object

        Raises:
            HTTPException: If patient not found
        """
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        patient.date_of_birth = date_of_birth
        await self._update_profile_completion_status(patient)

        await self.session.commit()
        await self.session.refresh(patient)
        return patient

    async def get_or_create_questionnaire_progress(
        self, patient_id: UUID
    ) -> QuestionnaireProgress:
        """
        Get existing questionnaire progress or create new one

        Args:
            patient_id: Patient's user ID

        Returns:
            QuestionnaireProgress object
        """
        # Try to get existing progress
        stmt = select(QuestionnaireProgress).where(
            QuestionnaireProgress.patient_id == patient_id
        )
        result = await self.session.execute(stmt)
        progress = result.scalar_one_or_none()

        if not progress:
            # Create new progress record
            progress = QuestionnaireProgress(patient_id=patient_id)
            self.session.add(progress)
            await self.session.commit()
            await self.session.refresh(progress)

        return progress

    async def update_questionnaire_section(
        self, patient_id: UUID, section_name: str, completed: bool = True
    ) -> QuestionnaireProgress:
        """
        Update questionnaire section completion status

        Args:
            patient_id: Patient's user ID
            section_name: Name of the section to update
            completed: Whether section is completed (default: True)

        Returns:
            Updated QuestionnaireProgress object

        Raises:
            HTTPException: If invalid section name
        """
        progress = await self.get_or_create_questionnaire_progress(patient_id)

        # Map section names to progress attributes
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid section name: {section_name}",
            )

        # Update the section status
        setattr(progress, section_mapping[section_name], completed)
        progress.calculate_completion_percentage()

        await self.session.commit()
        await self.session.refresh(progress)

        # Update patient profile completion if questionnaire is complete
        if progress.is_fully_completed:
            patient = await self.get_patient_by_user_id(patient_id)
            if patient:
                await self._update_profile_completion_status(patient)
                await self.session.commit()

        return progress

    async def get_questionnaire_progress(
        self, patient_id: UUID
    ) -> QuestionnaireProgress:
        """
        Get questionnaire progress for patient

        Args:
            patient_id: Patient's user ID

        Returns:
            QuestionnaireProgress object
        """
        return await self.get_or_create_questionnaire_progress(patient_id)

    async def get_patient_dashboard_data(self, user_id: UUID) -> dict:
        """
        Get comprehensive dashboard data for patient

        Args:
            user_id: Patient's user ID

        Returns:
            Dictionary with patient dashboard data

        Raises:
            HTTPException: If patient not found
        """
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        questionnaire_progress = await self.get_questionnaire_progress(user_id)

        # Count appointments by status
        # (you'll need to implement this based on appointment model)
        upcoming_appointments_count = len(
            [
                appt
                for appt in patient.appointments
                if appt.status
                in ["scheduled", "confirmed"]  # Adjust based on your enum
            ]
        )

        # Count medical records
        medical_records_count = len(patient.medical_records)

        dashboard_data = {
            "patient": {
                "id": str(patient.user_id),
                "username": patient.username,
                "full_name": patient.full_name,
                "email": patient.user.email,
                "phone_number": patient.phone_number,
                "age": patient.calculate_age(),
                "profile_completed": patient.profile_completed,
                "has_emergency_contact": patient.has_emergency_contact,
                "last_login": (
                    patient.user.last_login.isoformat()
                    if patient.user.last_login
                    else None
                ),
            },
            "questionnaire": {
                "completion_percentage": (
                    questionnaire_progress.overall_completion_percentage
                ),
                "is_fully_completed": questionnaire_progress.is_fully_completed,
                "completed_sections": questionnaire_progress.completed_sections,
                "incomplete_sections": questionnaire_progress.incomplete_sections,
                "next_section": questionnaire_progress.get_next_incomplete_section(),
                "last_updated": questionnaire_progress.last_updated.isoformat(),
            },
            "summary": {
                "upcoming_appointments": upcoming_appointments_count,
                "medical_records": medical_records_count,
                "profile_completion_score": self._calculate_profile_completion_score(
                    patient, questionnaire_progress
                ),
            },
        }

        return dashboard_data

    async def check_username_availability(
        self, username: str, exclude_user_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if username is available

        Args:
            username: Username to check
            exclude_user_id: User ID to exclude from check (for updates)

        Returns:
            True if username is available, False if taken
        """
        stmt = select(Patient).where(Patient.username == username)
        if exclude_user_id:
            stmt = stmt.where(Patient.user_id != exclude_user_id)

        result = await self.session.execute(stmt)
        existing_patient = result.scalar_one_or_none()
        return existing_patient is None

    async def update_username(self, user_id: UUID, new_username: str) -> Patient:
        """
        Update patient username

        Args:
            user_id: Patient's user ID
            new_username: New username

        Returns:
            Updated Patient object

        Raises:
            HTTPException: If patient not found or username taken
        """
        # Check if username is available
        is_available = await self.check_username_availability(new_username, user_id)
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        patient.username = new_username
        await self.session.commit()
        await self.session.refresh(patient)
        return patient

    async def deactivate_patient(self, user_id: UUID) -> bool:
        """
        Deactivate patient account (via user account)

        Args:
            user_id: Patient's user ID

        Returns:
            True if successful, False if patient not found
        """
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            return False

        # Deactivate the user account
        patient.user.is_active = False
        await self.session.commit()
        return True

    async def _update_profile_completion_status(self, patient: Patient) -> None:
        """
        Update patient profile completion status based on filled fields

        Args:
            patient: Patient object to update
        """
        # Check required fields for profile completion
        required_fields = [
            patient.first_name,
            patient.last_name,
            patient.date_of_birth,
            patient.phone_number,
            patient.emergency_contact_name,
            patient.emergency_contact_phone,
        ]

        # Check if questionnaire is complete
        questionnaire_progress = await self.get_questionnaire_progress(patient.user_id)
        questionnaire_complete = questionnaire_progress.is_fully_completed

        # Profile is complete if all required fields are filled
        # and questionnaire is done
        profile_complete = (
            all(field is not None for field in required_fields)
            and questionnaire_complete
        )

        patient.profile_completed = profile_complete

    def _calculate_profile_completion_score(
        self, patient: Patient, questionnaire_progress: QuestionnaireProgress
    ) -> int:
        """
        Calculate overall profile completion score (0-100)

        Args:
            patient: Patient object
            questionnaire_progress: QuestionnaireProgress object

        Returns:
            Completion score as percentage
        """
        # Profile fields (40% weight)
        profile_fields = [
            patient.first_name,
            patient.last_name,
            patient.phone_number,
            patient.emergency_contact_name,
            patient.emergency_contact_phone,
        ]
        profile_score = sum(1 for field in profile_fields if field is not None)
        profile_percentage = (profile_score / len(profile_fields)) * 40

        # Questionnaire completion (60% weight)
        questionnaire_percentage = (
            questionnaire_progress.overall_completion_percentage / 100
        ) * 60

        return int(profile_percentage + questionnaire_percentage)
