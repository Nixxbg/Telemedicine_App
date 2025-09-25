"""
Contract tests for POST /api/v1/appointments endpoint

These tests validate the appointment creation API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.

Tests appointment booking functionality for patients with various scenarios.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestAppointmentsCreate:
    """Contract tests for appointment creation endpoint"""

    @pytest.fixture
    def valid_patient_token(self):
        """Valid JWT token for authenticated patient"""
        return "Bearer valid_patient_jwt_token_here"

    @pytest.fixture
    def valid_doctor_token(self):
        """Valid JWT token for authenticated doctor"""
        return "Bearer valid_doctor_jwt_token_here"

    @pytest.fixture
    def invalid_token(self):
        """Invalid JWT token"""
        return "Bearer invalid_jwt_token_here"

    @pytest.fixture
    def expired_token(self):
        """Expired JWT token"""
        return "Bearer expired_jwt_token_here"

    @pytest.fixture
    def valid_appointment_data(self):
        """Valid appointment creation data"""
        return {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-09-15T14:00:00Z",
            "scheduled_end": "2025-09-15T14:30:00Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Regular check-up and blood pressure monitoring",
        }

    @pytest.fixture
    def follow_up_appointment_data(self):
        """Valid follow-up appointment data"""
        return {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-09-20T10:00:00Z",
            "scheduled_end": "2025-09-20T10:30:00Z",
            "appointment_type": "follow_up",
            "reason_for_visit": "Follow-up on medication effectiveness",
        }

    def test_create_appointment_success_consultation(
        self, valid_patient_token, valid_appointment_data
    ):
        """
        Contract Test: POST /api/v1/appointments
        Success case: Patient books consultation appointment
        Expected: 201 Created with Appointment schema
        """
        headers = {"Authorization": valid_patient_token}
        response = client.post(
            "/api/v1/appointments", headers=headers, json=valid_appointment_data
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 201

        # Validate response schema according to OpenAPI spec
        data = response.json()
        assert "id" in data
        assert "patient_id" in data
        assert "doctor_id" in data
        assert "scheduled_start" in data
        assert "scheduled_end" in data
        assert "status" in data
        assert "appointment_type" in data
        assert "reason_for_visit" in data
        assert "preparation_notes" in data
        assert "cost" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Validate specific values
        assert data["doctor_id"] == valid_appointment_data["doctor_id"]
        assert data["scheduled_start"] == valid_appointment_data["scheduled_start"]
        assert data["scheduled_end"] == valid_appointment_data["scheduled_end"]
        assert data["appointment_type"] == valid_appointment_data["appointment_type"]
        assert data["reason_for_visit"] == valid_appointment_data["reason_for_visit"]
        assert data["status"] == "scheduled"  # Default status for new appointments
        assert data["cost"] == 0.00  # v1 cost is always 0.00

    def test_create_appointment_success_follow_up(
        self, valid_patient_token, follow_up_appointment_data
    ):
        """
        Contract Test: POST /api/v1/appointments
        Success case: Patient books follow-up appointment
        Expected: 201 Created with Appointment schema
        """
        headers = {"Authorization": valid_patient_token}
        response = client.post(
            "/api/v1/appointments", headers=headers, json=follow_up_appointment_data
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 201

        data = response.json()
        assert data["appointment_type"] == "follow_up"
        assert data["status"] == "scheduled"

    def test_create_appointment_success_urgent(self, valid_patient_token):
        """
        Contract Test: POST /api/v1/appointments
        Success case: Patient books urgent appointment
        Expected: 201 Created with Appointment schema
        """
        headers = {"Authorization": valid_patient_token}
        urgent_data = {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-09-14T09:00:00Z",
            "scheduled_end": "2025-09-14T09:30:00Z",
            "appointment_type": "urgent",
            "reason_for_visit": "Severe headache and dizziness",
        }
        response = client.post(
            "/api/v1/appointments", headers=headers, json=urgent_data
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 201

        data = response.json()
        assert data["appointment_type"] == "urgent"
        assert data["status"] == "scheduled"

    def test_create_appointment_validation_error_missing_required_fields(
        self, valid_patient_token
    ):
        """
        Contract Test: POST /api/v1/appointments
        Validation error: Missing required fields
        Expected: 400 Bad Request with ErrorResponse schema
        """
        headers = {"Authorization": valid_patient_token}

        # Missing doctor_id
        invalid_data = {
            "scheduled_start": "2025-09-15T14:00:00Z",
            "scheduled_end": "2025-09-15T14:30:00Z",
            "appointment_type": "consultation",
        }
        response = client.post(
            "/api/v1/appointments", headers=headers, json=invalid_data
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_appointment_validation_error_invalid_doctor_id(
        self, valid_patient_token
    ):
        """
        Contract Test: POST /api/v1/appointments
        Validation error: Invalid doctor UUID format
        Expected: 400 Bad Request with ErrorResponse schema
        """
        headers = {"Authorization": valid_patient_token}
        invalid_data = {
            "doctor_id": "invalid-doctor-id",
            "scheduled_start": "2025-09-15T14:00:00Z",
            "scheduled_end": "2025-09-15T14:30:00Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Regular check-up",
        }
        response = client.post(
            "/api/v1/appointments", headers=headers, json=invalid_data
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_appointment_validation_error_invalid_times(
        self, valid_patient_token
    ):
        """
        Contract Test: POST /api/v1/appointments
        Validation error: End time before start time
        Expected: 400 Bad Request with ErrorResponse schema
        """
        headers = {"Authorization": valid_patient_token}
        invalid_data = {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-09-15T14:30:00Z",
            "scheduled_end": "2025-09-15T14:00:00Z",  # End before start
            "appointment_type": "consultation",
            "reason_for_visit": "Regular check-up",
        }
        response = client.post(
            "/api/v1/appointments", headers=headers, json=invalid_data
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_appointment_validation_error_past_date(self, valid_patient_token):
        """
        Contract Test: POST /api/v1/appointments
        Validation error: Appointment in the past
        Expected: 400 Bad Request with ErrorResponse schema
        """
        headers = {"Authorization": valid_patient_token}
        invalid_data = {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2024-09-15T14:00:00Z",  # Past date
            "scheduled_end": "2024-09-15T14:30:00Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Regular check-up",
        }
        response = client.post(
            "/api/v1/appointments", headers=headers, json=invalid_data
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_appointment_business_error_doctor_not_available(
        self, valid_patient_token
    ):
        """
        Contract Test: POST /api/v1/appointments
        Business error: Doctor not available at requested time
        Expected: 400 Bad Request with scheduling_conflict error
        """
        headers = {"Authorization": valid_patient_token}
        conflict_data = {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-09-15T12:00:00Z",  # Time when doctor is busy
            "scheduled_end": "2025-09-15T12:30:00Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Regular check-up",
        }
        response = client.post(
            "/api/v1/appointments", headers=headers, json=conflict_data
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

        data = response.json()
        assert data["error"] == "scheduling_conflict"
        assert "available_slots" in data["details"]

    def test_create_appointment_business_error_appointment_limit(
        self, valid_patient_token
    ):
        """
        Contract Test: POST /api/v1/appointments
        Business error: Patient has reached appointment limit
        Expected: 400 Bad Request with appointment_limit error
        """
        headers = {"Authorization": valid_patient_token}
        limit_data = {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-10-15T14:00:00Z",
            "scheduled_end": "2025-10-15T14:30:00Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Regular check-up",
        }
        response = client.post("/api/v1/appointments", headers=headers, json=limit_data)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

        data = response.json()
        assert data["error"] == "appointment_limit"
        assert "maximum number of future appointments" in data["message"]

    def test_create_appointment_authentication_error_no_token(self):
        """
        Contract Test: POST /api/v1/appointments
        Authentication error: No authorization header
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        valid_data = {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-09-15T14:00:00Z",
            "scheduled_end": "2025-09-15T14:30:00Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Regular check-up",
        }
        response = client.post("/api/v1/appointments", json=valid_data)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_appointment_authentication_error_invalid_token(self, invalid_token):
        """
        Contract Test: POST /api/v1/appointments
        Authentication error: Invalid JWT token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": invalid_token}
        valid_data = {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-09-15T14:00:00Z",
            "scheduled_end": "2025-09-15T14:30:00Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Regular check-up",
        }
        response = client.post("/api/v1/appointments", headers=headers, json=valid_data)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_appointment_authentication_error_expired_token(self, expired_token):
        """
        Contract Test: POST /api/v1/appointments
        Authentication error: Expired JWT token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": expired_token}
        valid_data = {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-09-15T14:00:00Z",
            "scheduled_end": "2025-09-15T14:30:00Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Regular check-up",
        }
        response = client.post("/api/v1/appointments", headers=headers, json=valid_data)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_appointment_authorization_error_doctor_token(
        self, valid_doctor_token
    ):
        """
        Contract Test: POST /api/v1/appointments
        Authorization error: Doctor attempting to book appointment
        Expected: 403 Forbidden with ErrorResponse schema
        """
        headers = {"Authorization": valid_doctor_token}
        valid_data = {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-09-15T14:00:00Z",
            "scheduled_end": "2025-09-15T14:30:00Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Regular check-up",
        }
        response = client.post("/api/v1/appointments", headers=headers, json=valid_data)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 403

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_appointment_validation_error_invalid_appointment_type(
        self, valid_patient_token
    ):
        """
        Contract Test: POST /api/v1/appointments
        Validation error: Invalid appointment type
        Expected: 400 Bad Request with ErrorResponse schema
        """
        headers = {"Authorization": valid_patient_token}
        invalid_data = {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-09-15T14:00:00Z",
            "scheduled_end": "2025-09-15T14:30:00Z",
            "appointment_type": "invalid_type",  # Invalid type
            "reason_for_visit": "Regular check-up",
        }
        response = client.post(
            "/api/v1/appointments", headers=headers, json=invalid_data
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_appointment_validation_error_reason_too_long(
        self, valid_patient_token
    ):
        """
        Contract Test: POST /api/v1/appointments
        Validation error: Reason for visit exceeds max length
        Expected: 400 Bad Request with ErrorResponse schema
        """
        headers = {"Authorization": valid_patient_token}
        long_reason = "A" * 1001  # Exceeds 1000 character limit
        invalid_data = {
            "doctor_id": "123e4567-e89b-12d3-a456-426614174001",
            "scheduled_start": "2025-09-15T14:00:00Z",
            "scheduled_end": "2025-09-15T14:30:00Z",
            "appointment_type": "consultation",
            "reason_for_visit": long_reason,
        }
        response = client.post(
            "/api/v1/appointments", headers=headers, json=invalid_data
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data
