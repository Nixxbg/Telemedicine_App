"""
Models package - Database models for the telemedicine application

This package contains all SQLAlchemy models for the application,
including User, Patient, Doctor, MedicalRecord, Appointment, Message,
and QuestionnaireProgress models.
"""

from src.models.appointment import Appointment, AppointmentStatus, AppointmentType
from src.models.doctor import Doctor
from src.models.medical_record import (
    ChangeUserType,
    MedicalRecord,
    MedicalRecordVersion,
    RecordType,
)
from src.models.message import Message, MessageType
from src.models.patient import Patient
from src.models.questionnaire import QuestionnaireProgress
from src.models.user import User, UserType

__all__ = [
    # Core models
    "User",
    "Patient",
    "Doctor",
    "MedicalRecord",
    "MedicalRecordVersion",
    "Appointment",
    "Message",
    "QuestionnaireProgress",
    # Enums
    "UserType",
    "RecordType",
    "ChangeUserType",
    "AppointmentStatus",
    "AppointmentType",
    "MessageType",
]
