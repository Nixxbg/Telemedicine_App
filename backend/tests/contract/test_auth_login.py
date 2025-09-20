"""
Contract tests for POST /api/v1/auth/login endpoint

These tests validate the authentication login API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.

Tests both patient and doctor login flows using email/password authentication.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestUserLogin:
    """Contract tests for user login endpoint"""

    @pytest.fixture
    def valid_patient_credentials(self):
        """Valid patient login credentials"""
        return {
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
        }

    @pytest.fixture
    def valid_doctor_credentials(self):
        """Valid doctor login credentials"""
        return {
            "email": "dr.smith@example.com",
            "password": "SecurePass123!",
        }

    @pytest.fixture
    def invalid_credentials(self):
        """Invalid login credentials"""
        return {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!",
        }

    def test_login_patient_success(self, valid_patient_credentials):
        """
        Contract Test: POST /api/v1/auth/login
        Success case for patient authentication
        Expected: 200 OK with AuthenticationResponse schema
        """
        response = client.post("/api/v1/auth/login", json=valid_patient_credentials)

        # Should return 200 OK
        assert response.status_code == 200

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
        assert user["email"] == valid_patient_credentials["email"]
        assert user["user_type"] == "patient"
        assert "id" in user
        assert "username" in user
        assert "first_name" in user
        assert "last_name" in user
        assert "profile_completed" in user
        assert "created_at" in user

    def test_login_doctor_success(self, valid_doctor_credentials):
        """
        Contract Test: POST /api/v1/auth/login
        Success case for doctor authentication
        Expected: 200 OK with AuthenticationResponse schema
        """
        response = client.post("/api/v1/auth/login", json=valid_doctor_credentials)

        # Should return 200 OK
        assert response.status_code == 200

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

        # User profile validation (DoctorProfile schema)
        user = data["user"]
        assert user["email"] == valid_doctor_credentials["email"]
        assert user["user_type"] == "doctor"
        assert "id" in user
        assert "doctor_id" in user
        assert "first_name" in user
        assert "last_name" in user
        assert "specializations" in user
        assert isinstance(user["specializations"], list)

    def test_login_invalid_credentials(self, invalid_credentials):
        """
        Contract Test: POST /api/v1/auth/login
        Error case: Invalid email or password
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        response = client.post("/api/v1/auth/login", json=invalid_credentials)

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should match ErrorResponse schema
        error_data = response.json()
        assert "error" in error_data
        assert "message" in error_data
        assert error_data["error"] == "authentication_error"

        message_lower = error_data["message"].lower()
        assert "invalid" in message_lower and (
            "email" in message_lower or "password" in message_lower
        )

    def test_login_wrong_password(self, valid_patient_credentials):
        """
        Contract Test: POST /api/v1/auth/login
        Error case: Correct email but wrong password
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        wrong_password_data = {
            "email": valid_patient_credentials["email"],
            "password": "DefinitelyWrongPassword123!",
        }

        response = client.post("/api/v1/auth/login", json=wrong_password_data)

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should match ErrorResponse schema
        error_data = response.json()
        assert "error" in error_data
        assert "message" in error_data
        assert error_data["error"] == "authentication_error"

    def test_login_missing_email(self):
        """
        Contract Test: POST /api/v1/auth/login
        Validation error: Missing email field
        Expected: 422 Unprocessable Entity with ValidationErrorResponse schema
        """
        incomplete_data = {
            "password": "SecurePass123!",
        }

        response = client.post("/api/v1/auth/login", json=incomplete_data)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_login_missing_password(self):
        """
        Contract Test: POST /api/v1/auth/login
        Validation error: Missing password field
        Expected: 422 Unprocessable Entity with ValidationErrorResponse schema
        """
        incomplete_data = {
            "email": "john.doe@example.com",
        }

        response = client.post("/api/v1/auth/login", json=incomplete_data)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_login_invalid_email_format(self):
        """
        Contract Test: POST /api/v1/auth/login
        Validation error: Invalid email format
        Expected: 422 Unprocessable Entity with ValidationErrorResponse schema
        """
        invalid_email_data = {
            "email": "not-a-valid-email",
            "password": "SecurePass123!",
        }

        response = client.post("/api/v1/auth/login", json=invalid_email_data)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_login_empty_password(self):
        """
        Contract Test: POST /api/v1/auth/login
        Validation error: Empty password
        Expected: 422 Unprocessable Entity with ValidationErrorResponse schema
        """
        empty_password_data = {
            "email": "john.doe@example.com",
            "password": "",
        }

        response = client.post("/api/v1/auth/login", json=empty_password_data)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_login_null_values(self):
        """
        Contract Test: POST /api/v1/auth/login
        Validation error: Null values for required fields
        Expected: 422 Unprocessable Entity with ValidationErrorResponse schema
        """
        null_data = {
            "email": None,
            "password": None,
        }

        response = client.post("/api/v1/auth/login", json=null_data)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data
