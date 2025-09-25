"""
Appointment service for booking, scheduling, and availability management

This service handles:
- Appointment booking and scheduling
- Doctor availability management
- Appointment status updates and cancellations
- Schedule conflict resolution
- Appointment history and filtering
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.appointment import Appointment, AppointmentStatus, AppointmentType
from src.models.doctor import Doctor
from src.models.patient import Patient
from src.models.user import UserType


class AppointmentService:
    """Service for appointment booking and management"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_appointment(
        self,
        patient_id: UUID,
        doctor_id: UUID,
        scheduled_start: datetime,
        scheduled_end: datetime,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
        appointment_type: AppointmentType = AppointmentType.CONSULTATION,
        reason_for_visit: Optional[str] = None,
        preparation_notes: Optional[str] = None,
    ) -> Appointment:
        """
        Create a new appointment

        Args:
            patient_id: Patient's user ID
            doctor_id: Doctor's user ID
            scheduled_start: Appointment start time
            scheduled_end: Appointment end time
            appointment_type: Type of appointment
            reason_for_visit: Reason for the visit
            preparation_notes: Preparation instructions
            requesting_user_id: User creating the appointment
            requesting_user_type: Type of user creating the appointment

        Returns:
            Created Appointment object

        Raises:
            HTTPException: If validation fails or access denied
        """
        # Validate access permissions
        await self._check_appointment_creation_access(
            patient_id, doctor_id, requesting_user_id, requesting_user_type
        )

        # Validate appointment time
        await self._validate_appointment_time(scheduled_start, scheduled_end)

        # Check doctor availability
        await self._check_doctor_availability(doctor_id, scheduled_start, scheduled_end)

        # Check for scheduling conflicts
        await self._check_scheduling_conflicts(
            patient_id, doctor_id, scheduled_start, scheduled_end
        )

        # Create appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            appointment_type=appointment_type,
            reason_for_visit=reason_for_visit,
            preparation_notes=preparation_notes,
            status=AppointmentStatus.SCHEDULED,
        )

        self.session.add(appointment)
        await self.session.commit()
        await self.session.refresh(appointment)
        return appointment

    async def get_appointment(
        self,
        appointment_id: UUID,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
    ) -> Optional[Appointment]:
        """
        Get appointment by ID with access control

        Args:
            appointment_id: Appointment ID
            requesting_user_id: User requesting the appointment
            requesting_user_type: Type of requesting user

        Returns:
            Appointment object or None if not found/no access
        """
        stmt = (
            select(Appointment)
            .options(
                selectinload(Appointment.patient).selectinload(Patient.user),
                selectinload(Appointment.doctor).selectinload(Doctor.user),
            )
            .where(Appointment.id == appointment_id)
        )
        result = await self.session.execute(stmt)
        appointment = result.scalar_one_or_none()

        if not appointment:
            return None

        # Check access permissions
        if not await self._has_appointment_access(
            appointment, requesting_user_id, requesting_user_type
        ):
            return None

        return appointment

    async def get_patient_appointments(
        self,
        patient_id: UUID,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
        status_filter: Optional[AppointmentStatus] = None,
        include_past: bool = True,
        limit: Optional[int] = None,
    ) -> List[Appointment]:
        """
        Get appointments for a patient

        Args:
            patient_id: Patient's user ID
            requesting_user_id: User requesting appointments
            requesting_user_type: Type of requesting user
            status_filter: Optional status filter
            include_past: Whether to include past appointments
            limit: Optional limit on results

        Returns:
            List of Appointment objects

        Raises:
            HTTPException: If access denied
        """
        # Check access permissions
        await self._check_patient_access(
            patient_id, requesting_user_id, requesting_user_type
        )

        # Build query conditions
        conditions = [Appointment.patient_id == patient_id]
        if status_filter:
            conditions.append(Appointment.status == status_filter)
        if not include_past:
            conditions.append(Appointment.scheduled_start > datetime.now(timezone.utc))

        stmt = (
            select(Appointment)
            .options(
                selectinload(Appointment.doctor).selectinload(Doctor.user),
            )
            .where(and_(*conditions))
            .order_by(desc(Appointment.scheduled_start))
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_doctor_appointments(
        self,
        doctor_id: UUID,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
        status_filter: Optional[AppointmentStatus] = None,
        date_filter: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Appointment]:
        """
        Get appointments for a doctor

        Args:
            doctor_id: Doctor's user ID
            requesting_user_id: User requesting appointments
            requesting_user_type: Type of requesting user
            status_filter: Optional status filter
            date_filter: Optional date filter (appointments on specific date)
            limit: Optional limit on results

        Returns:
            List of Appointment objects

        Raises:
            HTTPException: If access denied
        """
        # Check access permissions
        await self._check_doctor_access(
            doctor_id, requesting_user_id, requesting_user_type
        )

        # Build query conditions
        conditions = [Appointment.doctor_id == doctor_id]
        if status_filter:
            conditions.append(Appointment.status == status_filter)
        if date_filter:
            start_of_day = date_filter.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_of_day = start_of_day + timedelta(days=1)
            conditions.append(
                and_(
                    Appointment.scheduled_start >= start_of_day,
                    Appointment.scheduled_start < end_of_day,
                )
            )

        stmt = (
            select(Appointment)
            .options(
                selectinload(Appointment.patient).selectinload(Patient.user),
            )
            .where(and_(*conditions))
            .order_by(Appointment.scheduled_start)
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_appointment_status(
        self,
        appointment_id: UUID,
        new_status: AppointmentStatus,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
    ) -> Appointment:
        """
        Update appointment status

        Args:
            appointment_id: Appointment ID
            new_status: New status to set
            requesting_user_id: User updating the status
            requesting_user_type: Type of user updating the status

        Returns:
            Updated Appointment object

        Raises:
            HTTPException: If appointment not found, access denied,
                or invalid transition
        """
        appointment = await self.get_appointment(
            appointment_id, requesting_user_id, requesting_user_type
        )
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found or access denied",
            )

        # Validate status transition
        await self._validate_status_transition(
            appointment, new_status, requesting_user_type
        )

        appointment.status = new_status
        await self.session.commit()
        await self.session.refresh(appointment)
        return appointment

    async def cancel_appointment(
        self,
        appointment_id: UUID,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
        cancellation_reason: Optional[str] = None,
    ) -> Appointment:
        """
        Cancel an appointment

        Args:
            appointment_id: Appointment ID
            requesting_user_id: User canceling the appointment
            requesting_user_type: Type of user canceling the appointment
            cancellation_reason: Optional reason for cancellation

        Returns:
            Cancelled Appointment object

        Raises:
            HTTPException: If appointment cannot be cancelled
        """
        appointment = await self.get_appointment(
            appointment_id, requesting_user_id, requesting_user_type
        )
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found or access denied",
            )

        if not appointment.can_be_cancelled():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment cannot be cancelled",
            )

        appointment.status = AppointmentStatus.CANCELLED
        # In a full implementation, you might want to store cancellation_reason
        await self.session.commit()
        await self.session.refresh(appointment)
        return appointment

    async def reschedule_appointment(
        self,
        appointment_id: UUID,
        new_scheduled_start: datetime,
        new_scheduled_end: datetime,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
    ) -> Appointment:
        """
        Reschedule an appointment

        Args:
            appointment_id: Appointment ID
            new_scheduled_start: New start time
            new_scheduled_end: New end time
            requesting_user_id: User rescheduling the appointment
            requesting_user_type: Type of user rescheduling the appointment

        Returns:
            Updated Appointment object

        Raises:
            HTTPException: If appointment cannot be rescheduled or time conflicts
        """
        appointment = await self.get_appointment(
            appointment_id, requesting_user_id, requesting_user_type
        )
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found or access denied",
            )

        if appointment.status != AppointmentStatus.SCHEDULED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only scheduled appointments can be rescheduled",
            )

        # Validate new appointment time
        await self._validate_appointment_time(new_scheduled_start, new_scheduled_end)

        # Check doctor availability for new time
        await self._check_doctor_availability(
            appointment.doctor_id, new_scheduled_start, new_scheduled_end
        )

        # Check for scheduling conflicts (excluding current appointment)
        await self._check_scheduling_conflicts(
            appointment.patient_id,
            appointment.doctor_id,
            new_scheduled_start,
            new_scheduled_end,
            exclude_appointment_id=appointment.id,
        )

        # Update appointment times
        appointment.scheduled_start = new_scheduled_start
        appointment.scheduled_end = new_scheduled_end

        await self.session.commit()
        await self.session.refresh(appointment)
        return appointment

    async def get_doctor_availability_slots(
        self,
        doctor_id: UUID,
        date: datetime,
        slot_duration_minutes: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get available time slots for a doctor on a specific date

        Args:
            doctor_id: Doctor's user ID
            date: Date to check availability
            slot_duration_minutes: Duration of each slot in minutes

        Returns:
            List of available time slots

        Raises:
            HTTPException: If doctor not found
        """
        # Verify doctor exists
        doctor = await self._get_doctor_by_id(doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found",
            )

        # For v1, use simple availability: 9 AM to 5 PM, excluding existing appointments
        start_of_day = date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=17, minute=0, second=0, microsecond=0)

        # Get existing appointments for the day
        existing_appointments = await self.get_doctor_appointments(
            doctor_id,
            doctor_id,  # Doctor can see their own appointments
            UserType.DOCTOR,
            date_filter=date,
        )

        # Generate all possible slots and collect only the available ones
        slots: list[dict[str, Any]] = []
        current_time = start_of_day
        now = datetime.now(timezone.utc)
        while current_time + timedelta(minutes=slot_duration_minutes) <= end_of_day:
            slot_end = current_time + timedelta(minutes=slot_duration_minutes)

            # Prevent offering slots that have already started
            if slot_end <= now:
                current_time += timedelta(minutes=slot_duration_minutes)
                continue

            is_available = True
            for appointment in existing_appointments:
                if appointment.status in [
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.IN_PROGRESS,
                ]:
                    if (
                        current_time < appointment.scheduled_end
                        and slot_end > appointment.scheduled_start
                    ):
                        is_available = False
                        break

            if is_available:
                slots.append(
                    {
                        "start_time": current_time.isoformat(),
                        "end_time": slot_end.isoformat(),
                        "is_available": True,
                        "duration_minutes": slot_duration_minutes,
                    }
                )

            current_time += timedelta(minutes=slot_duration_minutes)

        return slots

    async def get_doctor_availability_range(
        self,
        doctor_id: UUID,
        from_date: date,
        to_date: date,
        slot_duration_minutes: int,
    ) -> tuple[Doctor, List[Dict[str, Any]]]:
        """Aggregate availability slots for a doctor across a date range."""

        doctor = await self._get_doctor_by_id(doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found",
            )

        all_slots: List[Dict[str, Any]] = []
        current_day = from_date
        today = datetime.now(timezone.utc).date()
        while current_day <= to_date:
            if current_day < today:
                current_day += timedelta(days=1)
                continue

            day_start = datetime(
                year=current_day.year,
                month=current_day.month,
                day=current_day.day,
                tzinfo=timezone.utc,
            )
            day_slots = await self.get_doctor_availability_slots(
                doctor_id,
                day_start,
                slot_duration_minutes=slot_duration_minutes,
            )
            all_slots.extend(day_slots)
            current_day += timedelta(days=1)

        return doctor, all_slots

    async def _validate_appointment_time(
        self, scheduled_start: datetime, scheduled_end: datetime
    ) -> None:
        """Validate appointment scheduling times"""
        now = datetime.now(timezone.utc)

        if scheduled_start <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment cannot be scheduled in the past",
            )

        if scheduled_end <= scheduled_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment end time must be after start time",
            )

        duration = scheduled_end - scheduled_start
        if duration.total_seconds() < 900:  # 15 minutes minimum
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment must be at least 15 minutes long",
            )

        if duration.total_seconds() > 7200:  # 2 hours maximum
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment cannot be longer than 2 hours",
            )

    async def _check_doctor_availability(
        self, doctor_id: UUID, scheduled_start: datetime, scheduled_end: datetime
    ) -> None:
        """Check if doctor is available during the requested time"""
        doctor = await self._get_doctor_by_id(doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found",
            )

        if not doctor.is_accepting_patients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor is not currently accepting new patients",
            )

        # For v1, assume doctors are available 9 AM to 5 PM
        start_hour = scheduled_start.hour
        end_hour = scheduled_end.hour

        if start_hour < 9 or end_hour > 17:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointments are only available between 9 AM and 5 PM",
            )

    async def _check_scheduling_conflicts(
        self,
        patient_id: UUID,
        doctor_id: UUID,
        scheduled_start: datetime,
        scheduled_end: datetime,
        exclude_appointment_id: Optional[UUID] = None,
    ) -> None:
        """Check for scheduling conflicts"""
        # Check for doctor conflicts
        conditions = [
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_(
                [
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.IN_PROGRESS,
                ]
            ),
            or_(
                and_(
                    Appointment.scheduled_start < scheduled_end,
                    Appointment.scheduled_end > scheduled_start,
                )
            ),
        ]

        if exclude_appointment_id:
            conditions.append(Appointment.id != exclude_appointment_id)

        stmt = select(Appointment).where(and_(*conditions))
        result = await self.session.execute(stmt)
        conflicting_appointments = list(result.scalars().all())

        if conflicting_appointments:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Doctor is not available during the requested time",
            )

    async def _check_appointment_creation_access(
        self,
        patient_id: UUID,
        doctor_id: UUID,
        requesting_user_id: UUID,
        requesting_user_type: UserType,
    ) -> None:
        """Check if user can create appointment"""
        if requesting_user_type == UserType.PATIENT:
            if patient_id != requesting_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Patients can only create appointments for themselves",
                )
        elif requesting_user_type == UserType.DOCTOR:
            if doctor_id != requesting_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Doctors can only create appointments for themselves",
                )

    async def _has_appointment_access(
        self, appointment: Appointment, user_id: UUID, user_type: UserType
    ) -> bool:
        """Check if user has access to appointment"""
        if user_type == UserType.PATIENT:
            return appointment.patient_id == user_id
        elif user_type == UserType.DOCTOR:
            return appointment.doctor_id == user_id
        return False

    async def _check_patient_access(
        self, patient_id: UUID, requesting_user_id: UUID, requesting_user_type: UserType
    ) -> None:
        """Check access to patient appointments"""
        if requesting_user_type == UserType.PATIENT:
            if patient_id != requesting_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Patients can only access their own appointments",
                )

    async def _check_doctor_access(
        self, doctor_id: UUID, requesting_user_id: UUID, requesting_user_type: UserType
    ) -> None:
        """Check access to doctor appointments"""
        if requesting_user_type == UserType.DOCTOR:
            if doctor_id != requesting_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Doctors can only access their own appointments",
                )

    async def _validate_status_transition(
        self,
        appointment: Appointment,
        new_status: AppointmentStatus,
        requesting_user_type: UserType,
    ) -> None:
        """Validate appointment status transitions"""
        current_status = appointment.status

        # Define valid transitions
        valid_transitions = {
            AppointmentStatus.SCHEDULED: [
                AppointmentStatus.IN_PROGRESS,
                AppointmentStatus.CANCELLED,
            ],
            AppointmentStatus.IN_PROGRESS: [
                AppointmentStatus.COMPLETED,
                AppointmentStatus.CANCELLED,
            ],
            AppointmentStatus.COMPLETED: [],  # Terminal state
            AppointmentStatus.CANCELLED: [],  # Terminal state
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from {current_status} to {new_status}",
            )

    async def _get_doctor_by_id(self, doctor_id: UUID) -> Optional[Doctor]:
        """Get doctor by user ID"""
        stmt = select(Doctor).where(Doctor.user_id == doctor_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
