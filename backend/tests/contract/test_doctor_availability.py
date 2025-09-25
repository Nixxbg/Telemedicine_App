"""
Contract tests for GET /api/v1/doctors/{id}/availability endpoint

These tests validate the doctor availability API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.

Tests doctor availability retrieval with various scenarios.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestDoctorAvailability:
    """Contract tests for doctor availability endpoint"""

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
    def valid_doctor_id(self):
        """Valid doctor UUID"""
        return "123e4567-e89b-12d3-a456-426614174001"

    @pytest.fixture
    def nonexistent_doctor_id(self):
        """Nonexistent doctor UUID"""
        return "99999999-9999-9999-9999-999999999999"

    @pytest.fixture
    def invalid_doctor_id(self):
        """Invalid doctor UUID format"""
        return "invalid-uuid-format"

    def test_get_doctor_availability_success(
        self, valid_patient_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Success case: Patient gets doctor availability
        Expected: 200 OK with DoctorAvailabilityResponse schema
        """
        headers = {"Authorization": valid_patient_token}
        params = {
            "from_date": "2025-09-15",
            "to_date": "2025-09-22",
            "appointment_duration": 30,
        }
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        # Validate response schema according to OpenAPI spec
        data = response.json()
        assert "doctor_id" in data
        assert "doctor_name" in data
        assert "from_date" in data
        assert "to_date" in data
        assert "available_slots" in data
        assert "appointment_duration_minutes" in data

        # Validate specific values
        assert data["doctor_id"] == valid_doctor_id
        assert data["from_date"] == "2025-09-15"
        assert data["to_date"] == "2025-09-22"
        assert data["appointment_duration_minutes"] == 30
        assert isinstance(data["available_slots"], list)

        # Validate availability slot schema if slots exist
        if data["available_slots"]:
            slot = data["available_slots"][0]
            assert "start_time" in slot
            assert "end_time" in slot
            assert "is_available" in slot
            assert isinstance(slot["is_available"], bool)

    def test_get_doctor_availability_success_default_duration(
        self, valid_patient_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Success case: Default appointment duration (30 minutes)
        Expected: 200 OK with default duration
        """
        headers = {"Authorization": valid_patient_token}
        params = {"from_date": "2025-09-15", "to_date": "2025-09-22"}
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert data["appointment_duration_minutes"] == 30  # Default value

    def test_get_doctor_availability_success_custom_duration(
        self, valid_patient_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Success case: Custom appointment duration
        Expected: 200 OK with custom duration
        """
        headers = {"Authorization": valid_patient_token}
        params = {
            "from_date": "2025-09-15",
            "to_date": "2025-09-22",
            "appointment_duration": 60,
        }
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert data["appointment_duration_minutes"] == 60

    def test_get_doctor_availability_doctor_can_access_own(
        self, valid_doctor_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Success case: Doctor accessing own availability
        Expected: 200 OK
        """
        headers = {"Authorization": valid_doctor_token}
        params = {"from_date": "2025-09-15", "to_date": "2025-09-22"}
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

    def test_get_doctor_availability_unauthenticated(self, valid_doctor_id):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Error case: No authentication
        Expected: 401 Unauthorized
        """
        params = {"from_date": "2025-09-15", "to_date": "2025-09-22"}
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability", params=params
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 401

        # Validate error response schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_doctor_availability_invalid_token(
        self, invalid_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Error case: Invalid JWT token
        Expected: 401 Unauthorized
        """
        headers = {"Authorization": invalid_token}
        params = {"from_date": "2025-09-15", "to_date": "2025-09-22"}
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 401

    def test_get_doctor_availability_doctor_not_found(
        self, valid_patient_token, nonexistent_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Error case: Doctor does not exist
        Expected: 404 Not Found
        """
        headers = {"Authorization": valid_patient_token}
        params = {"from_date": "2025-09-15", "to_date": "2025-09-22"}
        response = client.get(
            f"/api/v1/doctors/{nonexistent_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 404

        # Validate error response schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_doctor_availability_invalid_doctor_id_format(
        self, valid_patient_token, invalid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Error case: Invalid UUID format for doctor_id
        Expected: 422 Unprocessable Entity
        """
        headers = {"Authorization": valid_patient_token}
        params = {"from_date": "2025-09-15", "to_date": "2025-09-22"}
        response = client.get(
            f"/api/v1/doctors/{invalid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422

        # Validate error response schema
        data = response.json()
        assert "detail" in data  # FastAPI validation error format

    def test_get_doctor_availability_missing_required_from_date(
        self, valid_patient_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Error case: Missing required from_date parameter
        Expected: 422 Unprocessable Entity
        """
        headers = {"Authorization": valid_patient_token}
        params = {"to_date": "2025-09-22"}
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422

    def test_get_doctor_availability_missing_required_to_date(
        self, valid_patient_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Error case: Missing required to_date parameter
        Expected: 422 Unprocessable Entity
        """
        headers = {"Authorization": valid_patient_token}
        params = {"from_date": "2025-09-15"}
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422

    def test_get_doctor_availability_invalid_date_format(
        self, valid_patient_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Error case: Invalid date format
        Expected: 422 Unprocessable Entity
        """
        headers = {"Authorization": valid_patient_token}
        params = {"from_date": "invalid-date", "to_date": "2025-09-22"}
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422

    def test_get_doctor_availability_invalid_duration_too_small(
        self, valid_patient_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Error case: Appointment duration below minimum (15 minutes)
        Expected: 422 Unprocessable Entity
        """
        headers = {"Authorization": valid_patient_token}
        params = {
            "from_date": "2025-09-15",
            "to_date": "2025-09-22",
            "appointment_duration": 10,  # Below minimum of 15
        }
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422

    def test_get_doctor_availability_invalid_duration_too_large(
        self, valid_patient_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Error case: Appointment duration above maximum (120 minutes)
        Expected: 422 Unprocessable Entity
        """
        headers = {"Authorization": valid_patient_token}
        params = {
            "from_date": "2025-09-15",
            "to_date": "2025-09-22",
            "appointment_duration": 150,  # Above maximum of 120
        }
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 422

    def test_get_doctor_availability_from_date_after_to_date(
        self, valid_patient_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Error case: from_date is after to_date
        Expected: 400 Bad Request
        """
        headers = {"Authorization": valid_patient_token}
        params = {
            "from_date": "2025-09-22",
            "to_date": "2025-09-15",  # Before from_date
        }
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 400

        # Validate error response schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_doctor_availability_date_range_too_large(
        self, valid_patient_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Edge case: Very large date range
        Expected: 200 OK (system should handle reasonable limits)
        """
        headers = {"Authorization": valid_patient_token}
        params = {
            "from_date": "2025-09-15",
            "to_date": "2025-12-31",  # Large range
        }
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

    def test_get_doctor_availability_past_dates(
        self, valid_patient_token, valid_doctor_id
    ):
        """
        Contract Test: GET /api/v1/doctors/{id}/availability
        Edge case: Request availability for past dates
        Expected: 200 OK with empty slots or appropriate response
        """
        headers = {"Authorization": valid_patient_token}
        params = {
            "from_date": "2020-01-01",
            "to_date": "2020-01-07",  # Past dates
        }
        response = client.get(
            f"/api/v1/doctors/{valid_doctor_id}/availability",
            headers=headers,
            params=params,
        )

        # This test MUST fail until the endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        # Past dates should typically return empty availability
        assert data["available_slots"] == []
