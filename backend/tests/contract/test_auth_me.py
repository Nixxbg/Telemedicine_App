"""
Contract tests for GET /api/v1/auth/me endpoint

These tests validate the user profile retrieval API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.

Tests both patient and doctor profile responses with proper authentication.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestAuthMe:
    """Contract tests for current user profile endpoint"""

    @pytest.fixture
    def patient_auth_token(self):
        """Mock patient authentication token for testing"""
        # This should be a valid JWT token for a patient user
        # Will fail until JWT authentication is implemented
        return "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.patient_token"

    @pytest.fixture
    def doctor_auth_token(self):
        """Mock doctor authentication token for testing"""
        # This should be a valid JWT token for a doctor user
        # Will fail until JWT authentication is implemented
        return "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.doctor_token"

    @pytest.fixture
    def invalid_auth_token(self):
        """Invalid authentication token for testing"""
        return "Bearer invalid_token_123"

    @pytest.fixture
    def expired_auth_token(self):
        """Expired authentication token for testing"""
        return "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.expired_token"

    def test_get_patient_profile_success(self, patient_auth_token):
        """
        Contract Test: GET /api/v1/auth/me
        Success case for authenticated patient
        Expected: 200 OK with PatientProfile schema
        """
        headers = {"Authorization": patient_auth_token}
        response = client.get("/api/v1/auth/me", headers=headers)

        # Should return 200 OK
        assert response.status_code == 200

        # Response should match PatientProfile schema
        data = response.json()

        # Required PatientProfile fields
        assert "id" in data
        assert "email" in data
        assert "user_type" in data
        assert "username" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "profile_completed" in data
        assert "created_at" in data

        # Validate field types and values
        assert data["user_type"] == "patient"
        assert isinstance(data["id"], str)
        assert "@" in data["email"]  # Basic email validation
        assert isinstance(data["username"], str)
        assert len(data["username"]) >= 3
        assert isinstance(data["first_name"], str)
        assert isinstance(data["last_name"], str)
        assert isinstance(data["profile_completed"], bool)
        assert isinstance(data["created_at"], str)

        # Optional fields (should be present but can be None)
        if "date_of_birth" in data:
            assert isinstance(data["date_of_birth"], (str, type(None)))
        if "phone_number" in data:
            assert isinstance(data["phone_number"], (str, type(None)))

    def test_get_doctor_profile_success(self, doctor_auth_token):
        """
        Contract Test: GET /api/v1/auth/me
        Success case for authenticated doctor
        Expected: 200 OK with DoctorProfile schema
        """
        headers = {"Authorization": doctor_auth_token}
        response = client.get("/api/v1/auth/me", headers=headers)

        # Should return 200 OK
        assert response.status_code == 200

        # Response should match DoctorProfile schema
        data = response.json()

        # Required DoctorProfile fields
        assert "id" in data
        assert "email" in data
        assert "user_type" in data
        assert "doctor_id" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "specializations" in data
        assert "created_at" in data

        # Validate field types and values
        assert data["user_type"] == "doctor"
        assert isinstance(data["id"], str)
        assert "@" in data["email"]  # Basic email validation
        assert isinstance(data["doctor_id"], str)
        assert len(data["doctor_id"]) >= 3
        assert isinstance(data["first_name"], str)
        assert isinstance(data["last_name"], str)
        assert isinstance(data["specializations"], list)
        assert len(data["specializations"]) >= 1
        assert isinstance(data["created_at"], str)

        # Validate specializations are strings
        for specialization in data["specializations"]:
            assert isinstance(specialization, str)

        # Optional fields (should be present but can be None)
        if "license_number" in data:
            assert isinstance(data["license_number"], (str, type(None)))
        if "bio" in data:
            assert isinstance(data["bio"], (str, type(None)))
        if "years_experience" in data:
            assert isinstance(data["years_experience"], (int, type(None)))
        if "is_accepting_patients" in data:
            assert isinstance(data["is_accepting_patients"], bool)

    def test_get_profile_unauthorized_no_token(self):
        """
        Contract Test: GET /api/v1/auth/me
        Error case - No authentication token provided
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        response = client.get("/api/v1/auth/me")

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)

    def test_get_profile_unauthorized_invalid_token(self, invalid_auth_token):
        """
        Contract Test: GET /api/v1/auth/me
        Error case - Invalid authentication token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": invalid_auth_token}
        response = client.get("/api/v1/auth/me", headers=headers)

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)

    def test_get_profile_unauthorized_expired_token(self, expired_auth_token):
        """
        Contract Test: GET /api/v1/auth/me
        Error case - Expired authentication token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": expired_auth_token}
        response = client.get("/api/v1/auth/me", headers=headers)

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)

    def test_get_profile_unauthorized_malformed_token(self):
        """
        Contract Test: GET /api/v1/auth/me
        Error case - Malformed authorization header
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        # Test various malformed authorization headers
        malformed_headers = [
            {"Authorization": "invalid_format"},
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": "Basic dGVzdA=="},  # Wrong auth type
            {"Authorization": ""},  # Empty value
        ]

        for headers in malformed_headers:
            response = client.get("/api/v1/auth/me", headers=headers)

            # Should return 401 Unauthorized
            assert response.status_code == 401

            # Response should match ErrorResponse schema
            data = response.json()
            assert "error" in data
            assert "message" in data
            assert isinstance(data["error"], str)
            assert isinstance(data["message"], str)

    def test_response_content_type(self, patient_auth_token):
        """
        Contract Test: GET /api/v1/auth/me
        Verify response content type is application/json
        """
        headers = {"Authorization": patient_auth_token}
        response = client.get("/api/v1/auth/me", headers=headers)

        # Content-Type should be application/json
        assert response.headers.get("content-type") == "application/json"

    def test_profile_data_consistency(self, patient_auth_token):
        """
        Contract Test: GET /api/v1/auth/me
        Verify profile data consistency across multiple requests
        """
        headers = {"Authorization": patient_auth_token}

        # Make multiple requests
        response1 = client.get("/api/v1/auth/me", headers=headers)
        response2 = client.get("/api/v1/auth/me", headers=headers)

        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Data should be identical
        data1 = response1.json()
        data2 = response2.json()

        # Core identity fields should remain the same
        assert data1["id"] == data2["id"]
        assert data1["email"] == data2["email"]
        assert data1["user_type"] == data2["user_type"]
        assert data1["created_at"] == data2["created_at"]

    def test_profile_security_no_sensitive_data(self, patient_auth_token):
        """
        Contract Test: GET /api/v1/auth/me
        Verify no sensitive data (passwords, tokens) in response
        """
        headers = {"Authorization": patient_auth_token}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Ensure no sensitive fields are exposed
        sensitive_fields = [
            "password",
            "password_hash",
            "hashed_password",
            "access_token",
            "refresh_token",
            "token",
            "secret",
            "private_key",
            "salt",
        ]

        for field in sensitive_fields:
            assert field not in data, (
                f"Sensitive field '{field}' should not be in response"
            )

        # Recursively check nested objects
        def check_nested_data(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_path = f"{path}.{key}" if path else key
                    assert key not in sensitive_fields, (
                        f"Sensitive field '{full_path}' found in response"
                    )
                    check_nested_data(value, full_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_nested_data(item, f"{path}[{i}]")

        check_nested_data(data)
