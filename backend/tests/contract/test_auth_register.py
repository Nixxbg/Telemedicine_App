"""
Contract tests for POST /api/v1/auth/register/patient endpoint

These tests validate the authentication registration API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestPatientRegistration:
    """Contract tests for patient registration endpoint"""

    @pytest.fixture
    def valid_patient_data(self):
        """Valid patient registration payload"""
        return {
            "email": "john.doe@example.com",
            "username": "johndoe123",
            "password": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-05-15",
            "phone_number": "+1234567890",
        }

    @pytest.fixture
    def minimal_patient_data(self):
        """Minimal valid patient registration payload (only required fields)"""
        return {
            "email": "jane.smith@example.com",
            "username": "janesmith456",
            "password": "SecurePass456!",
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1992-08-22",
        }

    def test_register_patient_success_with_all_fields(self, valid_patient_data):
        """
        Contract Test: POST /api/v1/auth/register/patient
        Success case with all optional fields included
        Expected: 201 Created with AuthenticationResponse schema
        """
        response = client.post("/api/v1/auth/register/patient", json=valid_patient_data)

        # Should return 201 Created
        assert response.status_code == 201

        # Response should match AuthenticationResponse schema
        data = response.json()

        # Required authentication response fields
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data

        # Token validation
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert isinstance(data["refresh_token"], str)
        assert len(data["refresh_token"]) > 0

        # User profile validation (PatientProfile schema)
        user = data["user"]
        assert user["email"] == valid_patient_data["email"]
        assert user["username"] == valid_patient_data["username"]
        assert user["first_name"] == valid_patient_data["first_name"]
        assert user["last_name"] == valid_patient_data["last_name"]
        assert user["date_of_birth"] == valid_patient_data["date_of_birth"]
        assert user["phone_number"] == valid_patient_data["phone_number"]
        assert user["user_type"] == "patient"
        assert "id" in user
        assert "profile_completed" in user
        assert "created_at" in user

    def test_register_patient_success_minimal_fields(self, minimal_patient_data):
        """
        Contract Test: POST /api/v1/auth/register/patient
        Success case with only required fields
        Expected: 201 Created with AuthenticationResponse schema
        """
        response = client.post(
            "/api/v1/auth/register/patient", json=minimal_patient_data
        )

        assert response.status_code == 201
        data = response.json()

        # Verify required response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data

        # Verify user data
        user = data["user"]
        assert user["email"] == minimal_patient_data["email"]
        assert user["username"] == minimal_patient_data["username"]
        assert user["user_type"] == "patient"
        # Optional fields should be null or have default values
        assert user.get("phone_number") is None

    def test_register_patient_duplicate_email(self, valid_patient_data):
        """
        Contract Test: POST /api/v1/auth/register/patient
        Error case: Email already exists
        Expected: 400 Bad Request with ErrorResponse schema
        """
        # First registration should succeed
        response1 = client.post(
            "/api/v1/auth/register/patient", json=valid_patient_data
        )
        assert response1.status_code == 201

        # Second registration with same email should fail
        duplicate_data = valid_patient_data.copy()
        # Different username, same email
        duplicate_data["username"] = "different_username"

        response2 = client.post("/api/v1/auth/register/patient", json=duplicate_data)

        assert response2.status_code == 400
        error_data = response2.json()

        # Should match ErrorResponse schema
        assert "error" in error_data
        assert "message" in error_data
        assert error_data["error"] == "validation_error"
        message_lower = error_data["message"].lower()
        assert (
            "already registered" in message_lower or "already exists" in message_lower
        )

        if "details" in error_data:
            assert error_data["details"]["field"] == "email"
            assert error_data["details"]["code"] == "already_exists"

    def test_register_patient_duplicate_username(self, valid_patient_data):
        """
        Contract Test: POST /api/v1/auth/register/patient
        Error case: Username already exists
        Expected: 400 Bad Request with ErrorResponse schema
        """
        # First registration should succeed
        response1 = client.post(
            "/api/v1/auth/register/patient", json=valid_patient_data
        )
        assert response1.status_code == 201

        # Second registration with same username should fail
        duplicate_data = valid_patient_data.copy()
        # Different email, same username
        duplicate_data["email"] = "different@example.com"

        response2 = client.post("/api/v1/auth/register/patient", json=duplicate_data)

        assert response2.status_code == 400
        error_data = response2.json()

        # Should match ErrorResponse schema
        assert "error" in error_data
        assert "message" in error_data
        assert error_data["error"] == "validation_error"
        assert "username" in error_data["message"].lower()

    @pytest.mark.parametrize(
        "field,invalid_value,expected_message",
        [
            ("email", "not-an-email", "email"),
            ("email", "", "email"),
            ("username", "ab", "username"),  # Too short (min 3)
            ("username", "a" * 51, "username"),  # Too long (max 50)
            ("username", "user@name", "username"),  # Invalid characters
            ("password", "short", "password"),  # Too short (min 8)
            ("password", "", "password"),
            ("first_name", "", "first_name"),
            ("last_name", "", "last_name"),
            ("date_of_birth", "invalid-date", "date_of_birth"),
            ("date_of_birth", "2030-01-01", "date_of_birth"),  # Future date
            ("phone_number", "invalid-phone", "phone_number"),
        ],
    )
    def test_register_patient_validation_errors(
        self, valid_patient_data, field, invalid_value, expected_message
    ):
        """
        Contract Test: POST /api/v1/auth/register/patient
        Validation error cases for various field constraints
        Expected: 422 Unprocessable Entity with ValidationErrorResponse schema
        """
        invalid_data = valid_patient_data.copy()
        invalid_data[field] = invalid_value

        response = client.post("/api/v1/auth/register/patient", json=invalid_data)

        assert response.status_code == 422
        error_data = response.json()

        # Should match ValidationErrorResponse schema
        assert error_data["error"] == "validation_error"
        assert "message" in error_data
        assert "details" in error_data
        assert isinstance(error_data["details"], list)

        # Find the field error in details
        field_errors = [
            detail for detail in error_data["details"] if detail["field"] == field
        ]
        assert len(field_errors) > 0, f"Expected validation error for field '{field}'"

    @pytest.mark.parametrize(
        "missing_field",
        ["email", "username", "password", "first_name", "last_name", "date_of_birth"],
    )
    def test_register_patient_missing_required_fields(
        self, valid_patient_data, missing_field
    ):
        """
        Contract Test: POST /api/v1/auth/register/patient
        Missing required field validation
        Expected: 422 Unprocessable Entity with ValidationErrorResponse schema
        """
        incomplete_data = valid_patient_data.copy()
        del incomplete_data[missing_field]

        response = client.post("/api/v1/auth/register/patient", json=incomplete_data)

        assert response.status_code == 422
        error_data = response.json()

        # Should match ValidationErrorResponse schema
        assert error_data["error"] == "validation_error"
        assert "details" in error_data

        # Should have error for missing field
        field_errors = [
            detail
            for detail in error_data["details"]
            if detail["field"] == missing_field
        ]
        assert len(field_errors) > 0, (
            f"Expected validation error for missing field '{missing_field}'"
        )

    def test_register_patient_empty_request_body(self):
        """
        Contract Test: POST /api/v1/auth/register/patient
        Empty request body validation
        Expected: 422 Unprocessable Entity
        """
        response = client.post("/api/v1/auth/register/patient", json={})

        assert response.status_code == 422
        error_data = response.json()

        assert error_data["error"] == "validation_error"
        assert "details" in error_data

        # Should have errors for all required fields
        required_fields = [
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "date_of_birth",
        ]
        error_fields = [detail["field"] for detail in error_data["details"]]

        for field in required_fields:
            assert field in error_fields, (
                f"Missing validation error for required field '{field}'"
            )

    def test_register_patient_invalid_content_type(self):
        """
        Contract Test: POST /api/v1/auth/register/patient
        Invalid Content-Type header
        Expected: 422 Unprocessable Entity
        """
        response = client.post(
            "/api/v1/auth/register/patient",
            content="invalid-json-data",
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 422

    def test_register_patient_malformed_json(self):
        """
        Contract Test: POST /api/v1/auth/register/patient
        Malformed JSON in request body
        Expected: 422 Unprocessable Entity
        """
        response = client.post(
            "/api/v1/auth/register/patient",
            content="{ invalid json }",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
