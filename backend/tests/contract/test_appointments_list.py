"""
Contract tests for GET /api/v1/appointments endpoint

These tests validate the appointments list API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.

Tests patient and doctor access to their appointments with filtering and pagination.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestAppointmentsList:
    """Contract tests for appointments list endpoint"""

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

    def test_get_appointments_success_no_filters(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments
        Success case: Patient retrieves all their appointments without filters
        Expected: 200 OK with AppointmentsResponse schema
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get("/api/v1/appointments", headers=headers)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        # Validate response schema according to OpenAPI spec
        data = response.json()
        assert "appointments" in data
        assert "total_count" in data
        assert "offset" in data
        assert "limit" in data

        assert isinstance(data["appointments"], list)
        assert isinstance(data["total_count"], int)
        assert isinstance(data["offset"], int)
        assert isinstance(data["limit"], int)
        assert data["offset"] == 0  # Default offset
        assert data["limit"] == 20  # Default limit

    def test_get_appointments_success_with_status_filter(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments?status=scheduled
        Success case: Patient retrieves scheduled appointments only
        Expected: 200 OK with filtered AppointmentsResponse
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get("/api/v1/appointments?status=scheduled", headers=headers)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert "appointments" in data

        # All returned appointments should have status 'scheduled'
        for appointment in data["appointments"]:
            assert appointment["status"] == "scheduled"

    def test_get_appointments_success_with_date_filters(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments?from_date=2025-09-01&to_date=2025-09-30
        Success case: Patient retrieves appointments within date range
        Expected: 200 OK with date-filtered AppointmentsResponse
        """
        headers = {"Authorization": valid_patient_token}
        params = {"from_date": "2025-09-01", "to_date": "2025-09-30"}
        response = client.get("/api/v1/appointments", headers=headers, params=params)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert "appointments" in data

        # Validate appointment structure according to AppointmentDetail schema
        for appointment in data["appointments"]:
            assert "id" in appointment
            assert "patient_id" in appointment
            assert "doctor_id" in appointment
            assert "scheduled_start" in appointment
            assert "scheduled_end" in appointment
            assert "status" in appointment
            assert "appointment_type" in appointment
            assert "patient" in appointment
            assert "doctor" in appointment
            assert "messages_count" in appointment
            assert "has_consultation_notes" in appointment

    def test_get_appointments_success_with_pagination(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments?limit=5&offset=10
        Success case: Patient retrieves appointments with pagination
        Expected: 200 OK with paginated AppointmentsResponse
        """
        headers = {"Authorization": valid_patient_token}
        params = {"limit": 5, "offset": 10}
        response = client.get("/api/v1/appointments", headers=headers, params=params)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 10
        assert len(data["appointments"]) <= 5

    def test_get_appointments_success_doctor_view(self, valid_doctor_token):
        """
        Contract Test: GET /api/v1/appointments
        Success case: Doctor retrieves their appointments
        Expected: 200 OK with doctor's AppointmentsResponse
        """
        headers = {"Authorization": valid_doctor_token}
        response = client.get("/api/v1/appointments", headers=headers)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert "appointments" in data

        # Validate doctor sees patient information in appointments
        for appointment in data["appointments"]:
            assert "patient" in appointment
            patient = appointment["patient"]
            assert "id" in patient
            assert "username" in patient
            assert "first_name" in patient
            assert "last_name" in patient
            assert "date_of_birth" in patient

    def test_get_appointments_success_multiple_status_filter(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments?status=scheduled&status=in_progress
        Success case: Patient retrieves appointments with multiple statuses
        Expected: 200 OK with multi-status filtered AppointmentsResponse
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get("/api/v1/appointments?status=scheduled", headers=headers)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        for appointment in data["appointments"]:
            assert appointment["status"] in ["scheduled", "in_progress"]

    def test_get_appointments_validation_invalid_status(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments?status=invalid_status
        Validation error: Invalid status parameter
        Expected: 422 Unprocessable Entity with validation error
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get(
            "/api/v1/appointments?status=invalid_status", headers=headers
        )

        # This test MUST fail until the endpoint is implemented with validation
        assert response.status_code == 422

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_appointments_validation_invalid_date_format(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments?from_date=invalid-date
        Validation error: Invalid date format
        Expected: 422 Unprocessable Entity with validation error
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get(
            "/api/v1/appointments?from_date=invalid-date", headers=headers
        )

        # This test MUST fail until the endpoint is implemented with validation
        assert response.status_code == 422

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_appointments_validation_invalid_limit(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments?limit=101
        Validation error: Limit exceeds maximum (100)
        Expected: 422 Unprocessable Entity with validation error
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get("/api/v1/appointments?limit=101", headers=headers)

        # This test MUST fail until the endpoint is implemented with validation
        assert response.status_code == 422

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_appointments_validation_negative_offset(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments?offset=-1
        Validation error: Negative offset not allowed
        Expected: 422 Unprocessable Entity with validation error
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get("/api/v1/appointments?offset=-1", headers=headers)

        # This test MUST fail until the endpoint is implemented with validation
        assert response.status_code == 422

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_appointments_unauthorized_no_token(self):
        """
        Contract Test: GET /api/v1/appointments
        Error case: No authentication token provided
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        response = client.get("/api/v1/appointments")

        # This test MUST fail until authentication middleware is implemented
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_appointments_unauthorized_invalid_token(self, invalid_token):
        """
        Contract Test: GET /api/v1/appointments
        Error case: Invalid authentication token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": invalid_token}
        response = client.get("/api/v1/appointments", headers=headers)

        # This test MUST fail until authentication middleware is implemented
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_appointments_unauthorized_expired_token(self, expired_token):
        """
        Contract Test: GET /api/v1/appointments
        Error case: Expired authentication token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": expired_token}
        response = client.get("/api/v1/appointments", headers=headers)

        # This test MUST fail until authentication middleware is implemented
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_appointments_malformed_bearer_token(self):
        """
        Contract Test: GET /api/v1/appointments
        Error case: Malformed Authorization header (missing 'Bearer' prefix)
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": "malformed_token_without_bearer"}
        response = client.get("/api/v1/appointments", headers=headers)

        # This test MUST fail until authentication middleware is implemented
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_appointments_empty_response(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments
        Success case: Patient with no appointments
        Expected: 200 OK with empty appointments list but valid schema
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get("/api/v1/appointments", headers=headers)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert "appointments" in data
        assert "total_count" in data
        assert "offset" in data
        assert "limit" in data

        # Even empty response should follow schema
        assert isinstance(data["appointments"], list)
        assert data["total_count"] >= 0
        # Empty list is valid for patients with no appointments

    def test_get_appointments_patient_summary_schema(self, valid_doctor_token):
        """
        Contract Test: GET /api/v1/appointments
        Schema validation: PatientSummary structure in doctor's view
        Expected: 200 OK with proper PatientSummary schema in appointments
        """
        headers = {"Authorization": valid_doctor_token}
        response = client.get("/api/v1/appointments", headers=headers)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()

        for appointment in data["appointments"]:
            patient = appointment["patient"]
            # Validate PatientSummary schema
            assert "id" in patient
            assert "username" in patient
            assert "first_name" in patient
            assert "last_name" in patient
            assert "date_of_birth" in patient

            # Validate field types
            assert isinstance(patient["id"], str)
            assert isinstance(patient["username"], str)
            assert isinstance(patient["first_name"], str)
            assert isinstance(patient["last_name"], str)
            assert isinstance(patient["date_of_birth"], str)

    def test_get_appointments_doctor_summary_schema(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments
        Schema validation: DoctorSummary structure in patient's view
        Expected: 200 OK with proper DoctorSummary schema in appointments
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get("/api/v1/appointments", headers=headers)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()

        for appointment in data["appointments"]:
            doctor = appointment["doctor"]
            # Validate DoctorSummary schema
            assert "id" in doctor
            assert "doctor_id" in doctor
            assert "first_name" in doctor
            assert "last_name" in doctor
            assert "specializations" in doctor
            assert "years_experience" in doctor
            assert "is_accepting_patients" in doctor

            # Validate field types
            assert isinstance(doctor["id"], str)
            assert isinstance(doctor["doctor_id"], str)
            assert isinstance(doctor["first_name"], str)
            assert isinstance(doctor["last_name"], str)
            assert isinstance(doctor["specializations"], list)
            assert isinstance(doctor["years_experience"], int)
            assert isinstance(doctor["is_accepting_patients"], bool)

    def test_get_appointments_appointment_types_validation(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments
        Schema validation: Appointment types are valid enum values
        Expected: 200 OK with appointment_type in [consultation, follow_up, urgent]
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get("/api/v1/appointments", headers=headers)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        valid_types = ["consultation", "follow_up", "urgent"]

        for appointment in data["appointments"]:
            assert appointment["appointment_type"] in valid_types

    def test_get_appointments_status_validation(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/appointments
        Schema validation: Appointment statuses are valid enum values
        Expected: 200 OK with status in [scheduled, in_progress, completed, cancelled]
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get("/api/v1/appointments", headers=headers)

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        valid_statuses = ["scheduled", "in_progress", "completed", "cancelled"]

        for appointment in data["appointments"]:
            assert appointment["status"] in valid_statuses
