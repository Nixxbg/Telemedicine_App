"""
Contract tests for PUT /api/v1/appointments/{id} endpoint - Cancellation functionality

These tests validate the appointment cancellation API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.

Tests appointment cancellation functionality for both patients and doctors.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestAppointmentsCancel:
    """Contract tests for appointment cancellation functionality"""

    @pytest.fixture
    def valid_patient_token(self):
        """Valid JWT token for authenticated patient"""
        return "Bearer valid_patient_jwt_token_here"

    @pytest.fixture
    def valid_doctor_token(self):
        """Valid JWT token for authenticated doctor"""
        return "Bearer valid_doctor_jwt_token_here"

    @pytest.fixture
    def other_patient_token(self):
        """Valid JWT token for different patient"""
        return "Bearer other_patient_jwt_token_here"

    @pytest.fixture
    def invalid_token(self):
        """Invalid JWT token"""
        return "Bearer invalid_jwt_token_here"

    @pytest.fixture
    def valid_appointment_id(self):
        """Valid appointment UUID"""
        return "123e4567-e89b-12d3-a456-426614174000"

    @pytest.fixture
    def nonexistent_appointment_id(self):
        """Nonexistent appointment UUID"""
        return "99999999-9999-9999-9999-999999999999"

    @pytest.fixture
    def invalid_appointment_id(self):
        """Invalid appointment UUID format"""
        return "invalid-uuid-format"

    @pytest.fixture
    def patient_cancellation_data(self):
        """Valid patient cancellation data"""
        return {
            "status": "cancelled",
            "cancellation_reason": "Patient unable to attend",
        }

    @pytest.fixture
    def doctor_cancellation_data(self):
        """Valid doctor cancellation data"""
        return {
            "status": "cancelled",
            "cancellation_reason": "Doctor emergency scheduling conflict",
        }

    def test_cancel_appointment_success_patient(
        self, valid_patient_token, valid_appointment_id, patient_cancellation_data
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Success case: Patient cancels own appointment
        Expected: 200 OK with updated Appointment schema
        """
        headers = {"Authorization": valid_patient_token}
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=patient_cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

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
        assert "cancellation_reason" in data
        assert "preparation_notes" in data
        assert "cost" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Validate specific values
        assert data["id"] == valid_appointment_id
        assert data["status"] == "cancelled"
        assert (
            data["cancellation_reason"]
            == patient_cancellation_data["cancellation_reason"]
        )

    def test_cancel_appointment_success_doctor(
        self, valid_doctor_token, valid_appointment_id, doctor_cancellation_data
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Success case: Doctor cancels appointment
        Expected: 200 OK with updated Appointment schema
        """
        headers = {"Authorization": valid_doctor_token}
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=doctor_cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "cancelled"
        assert (
            data["cancellation_reason"]
            == doctor_cancellation_data["cancellation_reason"]
        )

    def test_cancel_appointment_success_without_reason(
        self, valid_patient_token, valid_appointment_id
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Success case: Cancel appointment without reason (optional field)
        Expected: 200 OK
        """
        headers = {"Authorization": valid_patient_token}
        cancellation_data = {"status": "cancelled"}
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "cancelled"
        # cancellation_reason should be null/None if not provided
        assert data["cancellation_reason"] is None

    def test_cancel_appointment_unauthenticated(
        self, valid_appointment_id, patient_cancellation_data
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Error case: No authentication
        Expected: 401 Unauthorized
        """
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            json=patient_cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 401

        # Validate error response schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_cancel_appointment_invalid_token(
        self, invalid_token, valid_appointment_id, patient_cancellation_data
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Error case: Invalid JWT token
        Expected: 401 Unauthorized
        """
        headers = {"Authorization": invalid_token}
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=patient_cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 401

    def test_cancel_appointment_access_denied_other_patient(
        self, other_patient_token, valid_appointment_id, patient_cancellation_data
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Error case: Patient trying to cancel another patient's appointment
        Expected: 403 Forbidden
        """
        headers = {"Authorization": other_patient_token}
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=patient_cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 403

        # Validate error response schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_cancel_appointment_not_found(
        self, valid_patient_token, nonexistent_appointment_id, patient_cancellation_data
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Error case: Appointment does not exist
        Expected: 404 Not Found
        """
        headers = {"Authorization": valid_patient_token}
        response = client.put(
            f"/api/v1/appointments/{nonexistent_appointment_id}",
            headers=headers,
            json=patient_cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 404

        # Validate error response schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_cancel_appointment_invalid_appointment_id_format(
        self, valid_patient_token, invalid_appointment_id, patient_cancellation_data
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Error case: Invalid UUID format for appointment_id
        Expected: 422 Unprocessable Entity
        """
        headers = {"Authorization": valid_patient_token}
        response = client.put(
            f"/api/v1/appointments/{invalid_appointment_id}",
            headers=headers,
            json=patient_cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422

        # Validate error response schema
        data = response.json()
        assert "detail" in data  # FastAPI validation error format

    def test_cancel_appointment_invalid_status_value(
        self, valid_patient_token, valid_appointment_id
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Error case: Invalid status value
        Expected: 422 Unprocessable Entity
        """
        headers = {"Authorization": valid_patient_token}
        invalid_data = {
            "status": "invalid_status",
            "cancellation_reason": "Test reason",
        }
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=invalid_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422

    def test_cancel_appointment_missing_status(
        self, valid_patient_token, valid_appointment_id
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Error case: Missing required status field
        Expected: 422 Unprocessable Entity
        """
        headers = {"Authorization": valid_patient_token}
        invalid_data = {"cancellation_reason": "Test reason"}
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=invalid_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422

    def test_cancel_appointment_reason_too_long(
        self, valid_patient_token, valid_appointment_id
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Error case: Cancellation reason exceeds maximum length (500 chars)
        Expected: 422 Unprocessable Entity
        """
        headers = {"Authorization": valid_patient_token}
        long_reason = "x" * 501  # Exceeds 500 character limit
        invalid_data = {"status": "cancelled", "cancellation_reason": long_reason}
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=invalid_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422

    def test_cancel_appointment_already_cancelled(
        self, valid_patient_token, valid_appointment_id
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Edge case: Trying to cancel already cancelled appointment
        Expected: 400 Bad Request (invalid status transition)
        """
        headers = {"Authorization": valid_patient_token}
        cancellation_data = {
            "status": "cancelled",
            "cancellation_reason": "Second cancellation attempt",
        }
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

        # Validate error response schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_cancel_appointment_already_completed(
        self, valid_patient_token, valid_appointment_id
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Edge case: Trying to cancel completed appointment
        Expected: 400 Bad Request (invalid status transition)
        """
        headers = {"Authorization": valid_patient_token}
        cancellation_data = {
            "status": "cancelled",
            "cancellation_reason": "Trying to cancel completed appointment",
        }
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

    def test_cancel_appointment_in_progress(
        self, valid_doctor_token, valid_appointment_id
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Edge case: Doctor cancelling appointment that's in progress
        Expected: 400 Bad Request (invalid status transition)
        """
        headers = {"Authorization": valid_doctor_token}
        cancellation_data = {
            "status": "cancelled",
            "cancellation_reason": "Emergency cancellation during appointment",
        }
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

    def test_cancel_appointment_late_cancellation_warning(
        self, valid_patient_token, valid_appointment_id
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Business case: Last-minute cancellation (within 24 hours)
        Expected: 200 OK but may include warning in response
        """
        headers = {"Authorization": valid_patient_token}
        cancellation_data = {
            "status": "cancelled",
            "cancellation_reason": "Emergency - cannot attend",
        }
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=cancellation_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "cancelled"
        # System may add warnings or notes for late cancellations

    def test_cancel_appointment_empty_request_body(
        self, valid_patient_token, valid_appointment_id
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Error case: Empty request body
        Expected: 422 Unprocessable Entity
        """
        headers = {"Authorization": valid_patient_token}
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}", headers=headers, json={}
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422

    def test_cancel_appointment_null_values(
        self, valid_patient_token, valid_appointment_id
    ):
        """
        Contract Test: PUT /api/v1/appointments/{id}
        Edge case: Null values in request
        Expected: 422 Unprocessable Entity for null status
        """
        headers = {"Authorization": valid_patient_token}
        invalid_data = {"status": None, "cancellation_reason": None}
        response = client.put(
            f"/api/v1/appointments/{valid_appointment_id}",
            headers=headers,
            json=invalid_data,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422
