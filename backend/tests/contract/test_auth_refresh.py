"""
Contract tests for POST /api/v1/auth/refresh endpoint

These tests validate the authentication token refresh API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.

Tests the refresh token flow to get new access tokens.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestTokenRefresh:
    """Contract tests for token refresh endpoint"""

    @pytest.fixture
    def valid_refresh_token(self):
        """Valid refresh token for testing"""
        return (
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
            "eyJzdWIiOiIxMjM0NTY3OC05MGFiLWNkZWYtMTIzNC01Njc4OTBhYmNkZWYiLFxuXCJ1c2VyX3R5cGVcIjpcInBhdGllbnRcIixcImV4cFwiOjE2Nzg5ODc2NTQsXCJpYXRcIjoxNjc4OTg0MDU0LFwidG9rZW5fdHlwZVwiOlwicmVmcmVzaFwifQ."
            "example_refresh_token_signature"
        )

    @pytest.fixture
    def invalid_refresh_token(self):
        """Invalid refresh token for testing"""
        return "invalid.refresh.token"

    @pytest.fixture
    def expired_refresh_token(self):
        """Expired refresh token for testing"""
        return (
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
            "eyJzdWIiOiIxMjM0NTY3OC05MGFiLWNkZWYtMTIzNC01Njc4OTBhYmNkZWYiLFxuXCJ1c2VyX3R5cGVcIjpcInBhdGllbnRcIixcImV4cFwiOjE1Nzg5ODc2NTQsXCJpYXRcIjoxNTc4OTg0MDU0LFwidG9rZW5fdHlwZVwiOlwicmVmcmVzaFwifQ."
            "expired_refresh_token_signature"
        )

    def test_refresh_token_success(self, valid_refresh_token):
        """
        Contract Test: POST /api/v1/auth/refresh
        Success case for token refresh
        Expected: 200 OK with TokenResponse schema
        """
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": valid_refresh_token}
        )

        # Should return 200 OK
        assert response.status_code == 200

        # Validate response schema according to TokenResponse
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data

        # Validate field types and values
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

        # JWT access token should be properly formatted (3 parts separated by dots)
        token_parts = data["access_token"].split(".")
        assert len(token_parts) == 3

    def test_refresh_token_invalid_format(self, invalid_refresh_token):
        """
        Contract Test: POST /api/v1/auth/refresh
        Error case for malformed refresh token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": invalid_refresh_token}
        )

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Validate error response schema
        data = response.json()
        assert "error" in data
        assert "message" in data

        # Validate error content
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)
        assert len(data["message"]) > 0

    def test_refresh_token_expired(self, expired_refresh_token):
        """
        Contract Test: POST /api/v1/auth/refresh
        Error case for expired refresh token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": expired_refresh_token}
        )

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Validate error response schema
        data = response.json()
        assert "error" in data
        assert "message" in data

        # Validate error content
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)
        assert (
            "expired" in data["message"].lower() or "invalid" in data["message"].lower()
        )

    def test_refresh_token_missing_field(self):
        """
        Contract Test: POST /api/v1/auth/refresh
        Error case for missing refresh_token field
        Expected: 422 Unprocessable Entity with validation error
        """
        response = client.post("/api/v1/auth/refresh", json={})

        # Should return 422 for validation error
        assert response.status_code == 422

        # FastAPI validation error response structure
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0

        # Check that the error mentions the missing field
        error_detail = data["detail"][0]
        assert "refresh_token" in str(error_detail)

    def test_refresh_token_empty_string(self):
        """
        Contract Test: POST /api/v1/auth/refresh
        Error case for empty refresh token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": ""})

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Validate error response schema
        data = response.json()
        assert "error" in data
        assert "message" in data

        # Validate error content
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)

    def test_refresh_token_null_value(self):
        """
        Contract Test: POST /api/v1/auth/refresh
        Error case for null refresh token
        Expected: 422 Unprocessable Entity with validation error
        """
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": None})

        # Should return 422 for validation error
        assert response.status_code == 422

        # FastAPI validation error response structure
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_refresh_token_wrong_content_type(self, valid_refresh_token):
        """
        Contract Test: POST /api/v1/auth/refresh
        Error case for wrong content type
        Expected: 422 Unprocessable Entity or 415 Unsupported Media Type
        """
        response = client.post(
            "/api/v1/auth/refresh",
            data={"refresh_token": valid_refresh_token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Should return 422 or 415 for content type issues
        assert response.status_code in [415, 422]

    def test_refresh_endpoint_requires_no_authentication(self, valid_refresh_token):
        """
        Contract Test: POST /api/v1/auth/refresh
        Verify endpoint doesn't require Authorization header
        Expected: Process request based on refresh token only
        """
        # Test without Authorization header - should still process the request
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": valid_refresh_token}
        )

        # Should not return 401 due to missing auth header
        # (it may still return 401 if refresh token is invalid, but not for auth header)
        # Forbidden would indicate auth header required
        assert response.status_code != 403

    def test_refresh_token_extra_fields_ignored(self, valid_refresh_token):
        """
        Contract Test: POST /api/v1/auth/refresh
        Verify extra fields in request are ignored
        Expected: 200 OK with TokenResponse schema (extra fields ignored)
        """
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": valid_refresh_token,
                "extra_field": "should_be_ignored",
                "another_field": 123,
            },
        )

        # Should process successfully (or fail due to token, not extra fields)
        # The status depends on token validity, not extra fields
        assert response.status_code in [200, 401]  # Not 422 for schema validation

        if response.status_code == 200:
            # If successful, should still follow TokenResponse schema
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert "expires_in" in data

    def test_refresh_response_headers(self, valid_refresh_token):
        """
        Contract Test: POST /api/v1/auth/refresh
        Verify response headers for successful token refresh
        Expected: Appropriate content type and security headers
        """
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": valid_refresh_token}
        )

        # Validate content type regardless of status
        assert "application/json" in response.headers.get("content-type", "")

        if response.status_code == 200:
            # For successful responses, verify no sensitive data in headers
            headers = response.headers
            # Should not leak token information in headers
            assert "refresh_token" not in str(headers).lower()
            assert "access_token" not in str(headers).lower()
