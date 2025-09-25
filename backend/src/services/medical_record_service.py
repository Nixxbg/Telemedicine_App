"""
Medical Record service for CRUD operations and versioning management

This service handles:
- Medical record creation, reading, updating, and deletion
- Version management and audit trail
- Patient and doctor access control
- Medical record history tracking
- Data retention policies
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.medical_record import (
    ChangeUserType,
    MedicalRecord,
    MedicalRecordVersion,
    RecordType,
)
from src.models.patient import Patient
from src.models.user import UserType


class MedicalRecordService:
    """Service for medical record management with versioning"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_medical_record(
        self,
        patient_id: UUID,
        record_type: RecordType,
        title: str,
        data: Dict[str, Any],
        created_by_user_id: UUID,
        created_by_user_type: UserType,
        change_reason: Optional[str] = None,
    ) -> MedicalRecord:
        """
        Create a new medical record with initial version

        Args:
            patient_id: Patient's user ID
            record_type: Type of medical record
            title: Record title/description
            data: Medical record data
            created_by_user_id: User who created the record
            created_by_user_type: Type of user who created the record
            change_reason: Optional reason for creation

        Returns:
            Created MedicalRecord object

        Raises:
            HTTPException: If patient not found or access denied
        """
        # Verify patient exists
        patient = await self._get_patient_by_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        # Verify access permissions
        await self._check_record_access(
            patient_id, created_by_user_id, created_by_user_type
        )

        # Create medical record
        medical_record = MedicalRecord(
            patient_id=patient_id,
            record_type=record_type,
            title=title,
            current_version=1,
            is_active=True,
        )
        self.session.add(medical_record)
        await self.session.flush()  # Get the ID

        # Create initial version
        change_user_type = (
            ChangeUserType.PATIENT
            if created_by_user_type == UserType.PATIENT
            else ChangeUserType.DOCTOR
        )

        version = MedicalRecordVersion(
            medical_record_id=medical_record.id,
            changed_by_user_id=created_by_user_id,
            version_number=1,
            data=data,
            change_reason=change_reason or "Initial creation",
            changed_by_user_type=change_user_type,
        )
        self.session.add(version)

        await self.session.commit()
        await self.session.refresh(medical_record)
        return medical_record

    async def get_medical_record(
        self, record_id: UUID, requesting_user_id: UUID, requesting_user_type: UserType
    ) -> Optional[MedicalRecord]:
        """
        Get medical record by ID with access control

        Args:
            record_id: Medical record ID
            requesting_user_id: User requesting the record
            requesting_user_type: Type of requesting user

        Returns:
            MedicalRecord object or None if not found/no access
        """
        stmt = (
            select(MedicalRecord)
            .options(
                selectinload(MedicalRecord.patient),
                selectinload(MedicalRecord.versions).selectinload(
                    MedicalRecordVersion.changed_by_user
                ),
            )
            .where(
                and_(MedicalRecord.id == record_id, MedicalRecord.is_active.is_(True))
            )
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            return None

        # Check access permissions
        try:
            await self._check_record_access(
                record.patient_id, requesting_user_id, requesting_user_type
            )
        except HTTPException:
            return None

        return record

    async def get_patient_medical_records(
        self,
        patient_id: UUID,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
        record_type: Optional[RecordType] = None,
        include_inactive: bool = False,
    ) -> List[MedicalRecord]:
        """
        Get all medical records for a patient

        Args:
            patient_id: Patient's user ID
            requesting_user_id: User requesting the records
            requesting_user_type: Type of requesting user
            record_type: Optional filter by record type
            include_inactive: Whether to include inactive records

        Returns:
            List of MedicalRecord objects

        Raises:
            HTTPException: If access denied
        """
        # Check access permissions
        await self._check_record_access(
            patient_id, requesting_user_id, requesting_user_type
        )

        # Build query
        conditions = [MedicalRecord.patient_id == patient_id]
        if not include_inactive:
            conditions.append(MedicalRecord.is_active.is_(True))
        if record_type:
            conditions.append(MedicalRecord.record_type == record_type)

        stmt = (
            select(MedicalRecord)
            .options(
                selectinload(MedicalRecord.versions).selectinload(
                    MedicalRecordVersion.changed_by_user
                )
            )
            .where(and_(*conditions))
            .order_by(desc(MedicalRecord.updated_at))
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_medical_record(
        self,
        record_id: UUID,
        data: Dict[str, Any],
        updated_by_user_id: UUID,
        updated_by_user_type: UserType,
        change_reason: Optional[str] = None,
        title: Optional[str] = None,
    ) -> MedicalRecord:
        """
        Update medical record (creates new version)

        Args:
            record_id: Medical record ID
            data: Updated medical record data
            updated_by_user_id: User making the update
            updated_by_user_type: Type of user making the update
            change_reason: Optional reason for update
            title: Optional new title

        Returns:
            Updated MedicalRecord object

        Raises:
            HTTPException: If record not found or access denied
        """
        # Get existing record
        record = await self.get_medical_record(
            record_id, updated_by_user_id, updated_by_user_type
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical record not found or access denied",
            )

        # Update record metadata
        record.increment_version()
        if title:
            record.title = title

        # Create new version
        change_user_type = (
            ChangeUserType.PATIENT
            if updated_by_user_type == UserType.PATIENT
            else ChangeUserType.DOCTOR
        )

        version = MedicalRecordVersion(
            medical_record_id=record.id,
            changed_by_user_id=updated_by_user_id,
            version_number=record.current_version,
            data=data,
            change_reason=change_reason or "Record update",
            changed_by_user_type=change_user_type,
        )
        self.session.add(version)

        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_record_versions(
        self,
        record_id: UUID,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
        limit: Optional[int] = None,
    ) -> List[MedicalRecordVersion]:
        """
        Get all versions of a medical record

        Args:
            record_id: Medical record ID
            requesting_user_id: User requesting the versions
            requesting_user_type: Type of requesting user
            limit: Optional limit on number of versions returned

        Returns:
            List of MedicalRecordVersion objects (newest first)

        Raises:
            HTTPException: If record not found or access denied
        """
        # First verify access to the record
        record = await self.get_medical_record(
            record_id, requesting_user_id, requesting_user_type
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical record not found or access denied",
            )

        # Get versions
        stmt = (
            select(MedicalRecordVersion)
            .options(selectinload(MedicalRecordVersion.changed_by_user))
            .where(MedicalRecordVersion.medical_record_id == record_id)
            .order_by(desc(MedicalRecordVersion.version_number))
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_record_version(
        self,
        record_id: UUID,
        version_number: int,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
    ) -> Optional[MedicalRecordVersion]:
        """
        Get specific version of a medical record

        Args:
            record_id: Medical record ID
            version_number: Version number to retrieve
            requesting_user_id: User requesting the version
            requesting_user_type: Type of requesting user

        Returns:
            MedicalRecordVersion object or None if not found

        Raises:
            HTTPException: If record not found or access denied
        """
        # First verify access to the record
        record = await self.get_medical_record(
            record_id, requesting_user_id, requesting_user_type
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical record not found or access denied",
            )

        # Get specific version
        stmt = (
            select(MedicalRecordVersion)
            .options(selectinload(MedicalRecordVersion.changed_by_user))
            .where(
                and_(
                    MedicalRecordVersion.medical_record_id == record_id,
                    MedicalRecordVersion.version_number == version_number,
                )
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_delete_medical_record(
        self,
        record_id: UUID,
        deleted_by_user_id: UUID,
        deleted_by_user_type: UserType,
        delete_reason: Optional[str] = None,
    ) -> bool:
        """
        Soft delete medical record (mark as inactive)

        Args:
            record_id: Medical record ID
            deleted_by_user_id: User deleting the record
            deleted_by_user_type: Type of user deleting the record
            delete_reason: Optional reason for deletion

        Returns:
            True if successful, False if record not found

        Raises:
            HTTPException: If access denied
        """
        # Get existing record
        record = await self.get_medical_record(
            record_id, deleted_by_user_id, deleted_by_user_type
        )
        if not record:
            return False

        # Doctors can only soft delete their own additions, not patient data
        if deleted_by_user_type == UserType.DOCTOR:
            # Check if the latest version was created by a doctor
            latest_version = record.latest_version
            if latest_version and latest_version.is_patient_created:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Doctors cannot delete patient-entered medical data",
                )

        # Mark as inactive
        record.is_active = False

        # Create deletion audit version
        change_user_type = (
            ChangeUserType.PATIENT
            if deleted_by_user_type == UserType.PATIENT
            else ChangeUserType.DOCTOR
        )

        deletion_version = MedicalRecordVersion(
            medical_record_id=record.id,
            changed_by_user_id=deleted_by_user_id,
            version_number=record.current_version + 1,
            data={"deleted": True, "delete_reason": delete_reason},
            change_reason=delete_reason or "Record deletion",
            changed_by_user_type=change_user_type,
        )
        self.session.add(deletion_version)
        record.increment_version()

        await self.session.commit()
        return True

    async def get_medical_records_summary(
        self,
        patient_id: UUID,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
    ) -> Dict[str, Any]:
        """
        Get summary statistics for patient's medical records

        Args:
            patient_id: Patient's user ID
            requesting_user_id: User requesting the summary
            requesting_user_type: Type of requesting user

        Returns:
            Dictionary with summary statistics

        Raises:
            HTTPException: If access denied
        """
        # Check access permissions
        await self._check_record_access(
            patient_id, requesting_user_id, requesting_user_type
        )

        # Get all records
        records = await self.get_patient_medical_records(
            patient_id, requesting_user_id, requesting_user_type
        )

        # Calculate statistics
        summary: Dict[str, Any] = {
            "total_records": len(records),
            "by_type": {},
            "recent_updates": [],
            "version_counts": {},
        }

        for record in records:
            # Count by type
            record_type = record.record_type.value
            summary["by_type"][record_type] = summary["by_type"].get(record_type, 0) + 1

            # Track version counts
            version_count = record.current_version
            summary["version_counts"][str(record.id)] = version_count

            # Add to recent updates (last 5)
            if len(summary["recent_updates"]) < 5:
                summary["recent_updates"].append(
                    {
                        "id": str(record.id),
                        "title": record.title,
                        "type": record_type,
                        "current_version": version_count,
                        "last_updated": record.updated_at.isoformat(),
                    }
                )

        # Sort recent updates by date
        summary["recent_updates"].sort(key=lambda x: x["last_updated"], reverse=True)

        return summary

    async def _get_patient_by_id(self, patient_id: UUID) -> Optional[Patient]:
        """Get patient by ID"""
        stmt = select(Patient).where(Patient.user_id == patient_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_record_access(
        self, patient_id: UUID, user_id: UUID, user_type: UserType
    ) -> None:
        """
        Check if user has access to patient's medical records

        Args:
            patient_id: Patient's user ID
            user_id: User requesting access
            user_type: Type of user requesting access

        Raises:
            HTTPException: If access denied
        """
        if user_type == UserType.PATIENT:
            # Patients can only access their own records
            if patient_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Patients can only access their own medical records",
                )
        elif user_type == UserType.DOCTOR:
            # Doctors can access records of patients they have appointments with
            # For now, we'll implement a basic check
            # In a full implementation, you'd check for active
            # appointments/relationships

            # TODO: Implement proper doctor-patient relationship check
            # For now, allow all doctors to access (should be restricted in production)
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user type for medical record access",
            )
