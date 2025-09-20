"""
Contract tests for GET /api/v1/medical-records endpoint

These tests validate the medical records list API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.

Tests patient access to their own medical records with filtering and pagination.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestMedicalRecordsList:
    """Contract tests for medical records list endpoint"""

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

    def test_get_medical_records_success_no_filters(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records
        Success case: Patient retrieves all their medical records without filters
        Expected: 200 OK with MedicalRecordsResponse schema
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get("/api/v1/medical-records", headers=headers)

        # Should return 200 OK
        assert response.status_code == 200

        # Response should match MedicalRecordsResponse schema
        data = response.json()

        # Required response fields
        assert "records" in data
        assert "total_count" in data
        assert "offset" in data
        assert "limit" in data

        # Type validation
        assert isinstance(data["records"], list)
        assert isinstance(data["total_count"], int)
        assert isinstance(data["offset"], int)
        assert isinstance(data["limit"], int)

        # Default pagination values
        assert data["offset"] == 0
        assert data["limit"] == 20

        # Validate each medical record in response
        for record in data["records"]:
            self._validate_medical_record_schema(record)

    def test_get_medical_records_with_record_type_filter(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records?record_type=medication
        Success case: Patient retrieves filtered medical records by type
        Expected: 200 OK with filtered MedicalRecordsResponse
        """
        headers = {"Authorization": valid_patient_token}
        params = {"record_type": "medication"}
        response = client.get("/api/v1/medical-records", headers=headers, params=params)

        # Should return 200 OK
        assert response.status_code == 200

        # Response should match MedicalRecordsResponse schema
        data = response.json()
        assert "records" in data
        assert "total_count" in data

        # All returned records should match the filter
        for record in data["records"]:
            assert record["record_type"] == "medication"
            self._validate_medical_record_schema(record)

    def test_get_medical_records_with_pagination(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records?limit=5&offset=10
        Success case: Patient retrieves paginated medical records
        Expected: 200 OK with paginated MedicalRecordsResponse
        """
        headers = {"Authorization": valid_patient_token}
        params = {"limit": 5, "offset": 10}
        response = client.get("/api/v1/medical-records", headers=headers, params=params)

        # Should return 200 OK
        assert response.status_code == 200

        # Response should match pagination parameters
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 10
        assert len(data["records"]) <= 5

    def test_get_medical_records_all_record_types(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records with each valid record_type
        Success case: Test all valid enum values for record_type
        Expected: 200 OK for each valid record type
        """
        headers = {"Authorization": valid_patient_token}
        valid_record_types = ["medical_history", "medication", "allergy", "procedure"]

        for record_type in valid_record_types:
            params = {"record_type": record_type}
            response = client.get(
                "/api/v1/medical-records", headers=headers, params=params
            )

            assert response.status_code == 200
            data = response.json()

            # All returned records should match the filter
            for record in data["records"]:
                assert record["record_type"] == record_type

    def test_get_medical_records_maximum_limit(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records?limit=100
        Success case: Test maximum allowed limit value
        Expected: 200 OK with limit respected
        """
        headers = {"Authorization": valid_patient_token}
        params = {"limit": 100}
        response = client.get("/api/v1/medical-records", headers=headers, params=params)

        # Should return 200 OK
        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 100
        assert len(data["records"]) <= 100

    def test_get_medical_records_no_authentication(self):
        """
        Contract Test: GET /api/v1/medical-records
        Error case: Request without authentication
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        response = client.get("/api/v1/medical-records")

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should match ErrorResponse schema
        error_data = response.json()
        assert "error" in error_data
        assert "message" in error_data
        assert error_data["error"] == "authentication_error"

    def test_get_medical_records_invalid_token(self, invalid_token):
        """
        Contract Test: GET /api/v1/medical-records
        Error case: Request with invalid JWT token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": invalid_token}
        response = client.get("/api/v1/medical-records", headers=headers)

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should match ErrorResponse schema
        error_data = response.json()
        assert "error" in error_data
        assert "message" in error_data
        assert error_data["error"] == "authentication_error"

    def test_get_medical_records_expired_token(self, expired_token):
        """
        Contract Test: GET /api/v1/medical-records
        Error case: Request with expired JWT token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": expired_token}
        response = client.get("/api/v1/medical-records", headers=headers)

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should match ErrorResponse schema
        error_data = response.json()
        assert "error" in error_data
        assert "message" in error_data

    def test_get_medical_records_invalid_record_type(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records?record_type=invalid_type
        Validation error: Invalid record_type enum value
        Expected: 422 Unprocessable Entity with ValidationErrorResponse
        """
        headers = {"Authorization": valid_patient_token}
        params = {"record_type": "invalid_type"}
        response = client.get("/api/v1/medical-records", headers=headers, params=params)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_get_medical_records_invalid_limit_too_low(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records?limit=0
        Validation error: Limit below minimum value (1)
        Expected: 422 Unprocessable Entity with ValidationErrorResponse
        """
        headers = {"Authorization": valid_patient_token}
        params = {"limit": 0}
        response = client.get("/api/v1/medical-records", headers=headers, params=params)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_get_medical_records_invalid_limit_too_high(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records?limit=101
        Validation error: Limit above maximum value (100)
        Expected: 422 Unprocessable Entity with ValidationErrorResponse
        """
        headers = {"Authorization": valid_patient_token}
        params = {"limit": 101}
        response = client.get("/api/v1/medical-records", headers=headers, params=params)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_get_medical_records_invalid_limit_not_integer(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records?limit=abc
        Validation error: Limit not an integer
        Expected: 422 Unprocessable Entity with ValidationErrorResponse
        """
        headers = {"Authorization": valid_patient_token}
        params = {"limit": "abc"}
        response = client.get("/api/v1/medical-records", headers=headers, params=params)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_get_medical_records_invalid_offset_negative(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records?offset=-1
        Validation error: Negative offset value
        Expected: 422 Unprocessable Entity with ValidationErrorResponse
        """
        headers = {"Authorization": valid_patient_token}
        params = {"offset": -1}
        response = client.get("/api/v1/medical-records", headers=headers, params=params)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_get_medical_records_invalid_offset_not_integer(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records?offset=xyz
        Validation error: Offset not an integer
        Expected: 422 Unprocessable Entity with ValidationErrorResponse
        """
        headers = {"Authorization": valid_patient_token}
        params = {"offset": "xyz"}
        response = client.get("/api/v1/medical-records", headers=headers, params=params)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_get_medical_records_multiple_invalid_params(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records with multiple invalid parameters
        Validation error: Multiple validation errors
        Expected: 422 Unprocessable Entity with ValidationErrorResponse
        """
        headers = {"Authorization": valid_patient_token}
        params = {"record_type": "invalid_type", "limit": 101, "offset": -5}
        response = client.get("/api/v1/medical-records", headers=headers, params=params)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def _validate_medical_record_schema(self, record):
        """
        Helper method to validate MedicalRecord schema
        Validates that a record matches the expected OpenAPI schema
        """
        # Required fields from MedicalRecord schema
        required_fields = [
            "id",
            "patient_id",
            "record_type",
            "title",
            "current_version",
            "is_active",
            "created_at",
            "updated_at",
            "current_data",
        ]

        for field in required_fields:
            assert field in record, f"Missing required field: {field}"

        # Type validations
        assert isinstance(record["id"], str), "id should be string (UUID)"
        assert isinstance(record["patient_id"], str), (
            "patient_id should be string (UUID)"
        )
        assert isinstance(record["title"], str), "title should be string"
        assert isinstance(record["current_version"], int), (
            "current_version should be integer"
        )
        assert isinstance(record["is_active"], bool), "is_active should be boolean"
        assert isinstance(record["created_at"], str), (
            "created_at should be ISO datetime string"
        )
        assert isinstance(record["updated_at"], str), (
            "updated_at should be ISO datetime string"
        )
        assert isinstance(record["current_data"], dict), "current_data should be object"

        # Enum validation for record_type
        valid_record_types = ["medical_history", "medication", "allergy", "procedure"]
        assert record["record_type"] in valid_record_types, (
            f"Invalid record_type: {record['record_type']}"
        )

        # Version should be positive
        assert record["current_version"] > 0, (
            "current_version should be positive integer"
        )
