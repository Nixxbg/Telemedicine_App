"""Database seeding helpers for deterministic test scenarios.

This module populates the in-memory development database with a
stable dataset used by the contract tests. The dataset mirrors the
expectations defined in the OpenAPI contracts and pytest suites,
providing reference users, doctors, patients, medical records, and
appointments.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Sequence

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import async_session_factory
from src.core.reference_data import (
    APPOINTMENT_ID,
    CONFLICT_APPOINTMENT_ID,
    DOCTOR_USER_ID,
    FOLLOW_UP_APPOINTMENT_ID,
    MEDICAL_RECORD_ID,
    OTHER_PATIENT_USER_ID,
    PATIENT_USER_ID,
    URGENT_APPOINTMENT_ID,
)
from src.models.appointment import (
    Appointment,
    AppointmentStatus,
    AppointmentType,
)
from src.models.doctor import Doctor
from src.models.medical_record import (
    ChangeUserType,
    MedicalRecord,
    MedicalRecordVersion,
    RecordType,
)
from src.models.patient import Patient
from src.models.user import User, UserType

# Predefined bcrypt password hash (hash for "Password123!")
PASSWORD_HASH = bcrypt.hashpw(b"Password123!", bcrypt.gensalt()).decode("utf-8")


async def _has_existing_users(session: AsyncSession) -> bool:
    """Check whether the reference seed data already exists."""

    result = await session.execute(select(User.id).limit(1))
    return result.scalar_one_or_none() is not None


async def seed_reference_data() -> None:
    """Populate the database with a deterministic reference dataset.

    The contract tests rely on known identifiers, timestamps, and entity
    relationships. Seeding occurs once during application start-up after
    the schema has been (re)created.
    """

    async with async_session_factory() as session:
        if await _has_existing_users(session):
            return

        await _seed_users(session)
        await _seed_patients(session)
        await _seed_doctors(session)
        await _seed_medical_records(session)
        await _seed_appointments(session)
        await session.commit()


async def _seed_users(session: AsyncSession) -> None:
    """Create reference user accounts for contract tests."""

    users: Sequence[User] = (
        User(
            id=PATIENT_USER_ID,
            email="patient@example.com",
            password_hash=PASSWORD_HASH,
            user_type=UserType.PATIENT,
            is_active=True,
        ),
        User(
            id=OTHER_PATIENT_USER_ID,
            email="other.patient@example.com",
            password_hash=PASSWORD_HASH,
            user_type=UserType.PATIENT,
            is_active=True,
        ),
        User(
            id=DOCTOR_USER_ID,
            email="doctor@example.com",
            password_hash=PASSWORD_HASH,
            user_type=UserType.DOCTOR,
            is_active=True,
        ),
    )

    session.add_all(users)


async def _seed_patients(session: AsyncSession) -> None:
    """Insert patient profiles linked to the reference users."""

    patients: Sequence[Patient] = (
        Patient(
            user_id=PATIENT_USER_ID,
            username="primary_patient",
            first_name="Alex",
            last_name="Johnson",
            date_of_birth=date(1990, 5, 15),
            phone_number="+15555550100",
            emergency_contact_name="Taylor Johnson",
            emergency_contact_phone="+15555550999",
            profile_completed=True,
        ),
        Patient(
            user_id=OTHER_PATIENT_USER_ID,
            username="secondary_patient",
            first_name="Jamie",
            last_name="Rivera",
            date_of_birth=date(1992, 8, 21),
            profile_completed=True,
        ),
    )

    session.add_all(patients)


async def _seed_doctors(session: AsyncSession) -> None:
    """Insert doctor profile referenced by the contract tests."""

    doctor = Doctor(
        user_id=DOCTOR_USER_ID,
        doctor_id="DOC001",
        first_name="Morgan",
        last_name="Reed",
        specializations=["internal_medicine", "cardiology"],
        license_number="LIC-12345",
        years_experience=12,
        bio="Board-certified in internal medicine with cardiology focus.",
        is_accepting_patients=True,
    )

    session.add(doctor)


async def _seed_medical_records(session: AsyncSession) -> None:
    """Create medical records with initial version history."""

    record = MedicalRecord(
        id=MEDICAL_RECORD_ID,
        patient_id=PATIENT_USER_ID,
        record_type=RecordType.MEDICATION,
        title="Blood Pressure Medication",
        current_version=1,
        is_active=True,
    )
    session.add(record)
    await session.flush()

    version = MedicalRecordVersion(
        medical_record_id=record.id,
        version_number=1,
        data={
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily",
            "start_date": "2025-01-01",
            "prescribing_doctor": "Dr. Morgan Reed",
            "notes": "Initial prescription for hypertension management.",
        },
        change_reason="Initial record",
        changed_by_user_id=PATIENT_USER_ID,
        changed_by_user_type=ChangeUserType.PATIENT,
    )
    session.add(version)


async def _seed_appointments(session: AsyncSession) -> None:
    """Create a set of appointments covering multiple test scenarios."""

    base_date = datetime(2025, 9, 15, tzinfo=timezone.utc)

    appointments: Sequence[Appointment] = (
        Appointment(
            id=APPOINTMENT_ID,
            patient_id=PATIENT_USER_ID,
            doctor_id=DOCTOR_USER_ID,
            scheduled_start=base_date + timedelta(hours=14),
            scheduled_end=base_date + timedelta(hours=14, minutes=30),
            appointment_type=AppointmentType.CONSULTATION,
            status=AppointmentStatus.SCHEDULED,
            reason_for_visit="Routine blood pressure check",
            preparation_notes="Bring log of home readings.",
        ),
        Appointment(
            id=CONFLICT_APPOINTMENT_ID,
            patient_id=PATIENT_USER_ID,
            doctor_id=DOCTOR_USER_ID,
            scheduled_start=base_date + timedelta(hours=12),
            scheduled_end=base_date + timedelta(hours=12, minutes=30),
            appointment_type=AppointmentType.CONSULTATION,
            status=AppointmentStatus.SCHEDULED,
            reason_for_visit="Cardiology follow up",
        ),
        Appointment(
            id=FOLLOW_UP_APPOINTMENT_ID,
            patient_id=PATIENT_USER_ID,
            doctor_id=DOCTOR_USER_ID,
            scheduled_start=base_date + timedelta(days=5, hours=10),
            scheduled_end=base_date + timedelta(days=5, hours=10, minutes=30),
            appointment_type=AppointmentType.FOLLOW_UP,
            status=AppointmentStatus.COMPLETED,
            reason_for_visit="Medication effectiveness review",
        ),
        Appointment(
            id=URGENT_APPOINTMENT_ID,
            patient_id=OTHER_PATIENT_USER_ID,
            doctor_id=DOCTOR_USER_ID,
            scheduled_start=base_date + timedelta(days=1, hours=9),
            scheduled_end=base_date + timedelta(days=1, hours=9, minutes=30),
            appointment_type=AppointmentType.URGENT,
            status=AppointmentStatus.CANCELLED,
        ),
    )

    for appointment in appointments:
        appointment.cost = Decimal("0.00")

    session.add_all(appointments)
