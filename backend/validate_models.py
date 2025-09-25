#!/usr/bin/env python3
"""
Model validation script - Test model definitions without database connection
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

from sqlalchemy.orm import declarative_base

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Create a real SQLAlchemy base for testing
TestBase = declarative_base()

# Mock the settings to avoid requiring environment variables
mock_settings = Mock()
mock_settings.DATABASE_URL = "postgresql+asyncpg://mock:mock@localhost/mock"


def validate_models():
    """Test that all models can be imported and their basic structure is correct"""

    try:
        # Mock the database imports to avoid connection requirements
        with (
            patch("src.core.config.settings", mock_settings),
            patch("sqlalchemy.ext.asyncio.create_async_engine"),
            patch("sqlalchemy.ext.asyncio.async_sessionmaker"),
        ):
            # Mock the Base class directly in the database module
            with patch("src.core.database.Base", TestBase):
                # Import individual model files to avoid database connection
                from src.models.appointment import Appointment, AppointmentStatus
                from src.models.doctor import Doctor
                from src.models.medical_record import (
                    MedicalRecord,
                    MedicalRecordVersion,
                    RecordType,
                )
                from src.models.message import Message, MessageType
                from src.models.patient import Patient
                from src.models.questionnaire import QuestionnaireProgress
                from src.models.user import User, UserType

        print("✅ All model imports successful")

        # Test enum values
        assert len(UserType.__members__) == 2
        assert UserType.PATIENT == "patient"
        assert UserType.DOCTOR == "doctor"
        print("✅ UserType enum validated")

        assert len(RecordType.__members__) == 4
        assert RecordType.MEDICAL_HISTORY == "medical_history"
        assert RecordType.MEDICATION == "medication"
        assert RecordType.ALLERGY == "allergy"
        assert RecordType.PROCEDURE == "procedure"
        print("✅ RecordType enum validated")

        assert len(AppointmentStatus.__members__) == 4
        assert AppointmentStatus.SCHEDULED == "scheduled"
        assert AppointmentStatus.IN_PROGRESS == "in_progress"
        assert AppointmentStatus.COMPLETED == "completed"
        assert AppointmentStatus.CANCELLED == "cancelled"
        print("✅ AppointmentStatus enum validated")

        assert len(MessageType.__members__) == 2
        assert MessageType.TEXT == "text"
        assert MessageType.SYSTEM_NOTIFICATION == "system_notification"
        print("✅ MessageType enum validated")

        # Test model class definitions exist and have correct table names
        expected_tables = {
            User: "users",
            Patient: "patients",
            Doctor: "doctors",
            MedicalRecord: "medical_records",
            MedicalRecordVersion: "medical_record_versions",
            Appointment: "appointments",
            Message: "messages",
            QuestionnaireProgress: "questionnaire_progress",
        }

        for model_class, expected_table_name in expected_tables.items():
            assert hasattr(model_class, "__tablename__"), (
                f"{model_class.__name__} missing __tablename__"
            )
            actual_table_name = model_class.__tablename__
            assert actual_table_name == expected_table_name, (
                f"{model_class.__name__} has wrong table name: "
                f"{actual_table_name} != {expected_table_name}"
            )

        print("✅ All model classes have correct table names defined")

        # Test that models inherit from Base properly
        for model_class in expected_tables.keys():
            assert issubclass(model_class, TestBase), (
                f"{model_class.__name__} doesn't inherit from Base"
            )

        print("✅ All models inherit from SQLAlchemy Base")

        print("\n🎉 All model validations passed!")
        return True

    except Exception as e:
        print(f"❌ Model validation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = validate_models()
    sys.exit(0 if success else 1)
