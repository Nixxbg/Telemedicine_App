"""
Contract tests for GET /api/v1/medical-records/{record_id}/versions endpoint

These tests validate the medical record versions API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.

Tests patient and doctor access to medical record version history with proper
authorization and data validation.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestMedicalRecordVersions:
    """Contract tests for medical record versions endpoint"""

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
    def valid_record_id(self):
        """Valid medical record UUID"""
        return "123e4567-e89b-12d3-a456-426614174000"

    @pytest.fixture
    def nonexistent_record_id(self):
        """UUID that doesn't exist in database"""
        return "999e4567-e89b-12d3-a456-426614174999"

    @pytest.fixture
    def invalid_record_id(self):
        """Invalid UUID format"""
        return "invalid-uuid-format"

    def test_get_medical_record_versions_success_patient_own_record(
        self, valid_patient_token, valid_record_id
    ):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Success case: Patient retrieves versions of their own medical record
        Expected: 200 OK with MedicalRecordVersionsResponse schema
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get(
            f"/api/v1/medical-records/{valid_record_id}/versions", headers=headers
        )

        # Should return 200 OK
        assert response.status_code == 200

        # Response should match MedicalRecordVersionsResponse schema
        data = response.json()

        # Required response fields according to OpenAPI spec
        assert "record_id" in data
        assert "versions" in data
        assert "total_versions" in data

        # Type validation
        assert isinstance(data["record_id"], str)
        assert isinstance(data["versions"], list)
        assert isinstance(data["total_versions"], int)

        # record_id should match requested ID
        assert data["record_id"] == valid_record_id

        # total_versions should match array length
        assert data["total_versions"] == len(data["versions"])

        # Validate each version in response
        for version in data["versions"]:
            self._validate_medical_record_version_schema(version)

        # Versions should be ordered by version_number (newest first typically)
        if len(data["versions"]) > 1:
            version_numbers = [v["version_number"] for v in data["versions"]]
            assert version_numbers == sorted(version_numbers, reverse=True), (
                "Versions should be ordered by version_number descending"
            )

    def test_get_medical_record_versions_success_doctor_authorized_record(
        self, valid_doctor_token, valid_record_id
    ):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Success case: Doctor retrieves versions of authorized patient's record
        Expected: 200 OK with MedicalRecordVersionsResponse schema
        """
        headers = {"Authorization": valid_doctor_token}
        response = client.get(
            f"/api/v1/medical-records/{valid_record_id}/versions", headers=headers
        )

        # Should return 200 OK
        assert response.status_code == 200

        # Response should match schema
        data = response.json()
        assert "record_id" in data
        assert "versions" in data
        assert "total_versions" in data

        # Validate version data
        for version in data["versions"]:
            self._validate_medical_record_version_schema(version)

    def test_get_medical_record_versions_not_authenticated(self, valid_record_id):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Auth error: No authentication token provided
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        # No Authorization header
        response = client.get(f"/api/v1/medical-records/{valid_record_id}/versions")

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should include error details
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data

    def test_get_medical_record_versions_invalid_token(
        self, invalid_token, valid_record_id
    ):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Auth error: Invalid JWT token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": invalid_token}
        response = client.get(
            f"/api/v1/medical-records/{valid_record_id}/versions", headers=headers
        )

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should include error details
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data

    def test_get_medical_record_versions_expired_token(
        self, expired_token, valid_record_id
    ):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Auth error: Expired JWT token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": expired_token}
        response = client.get(
            f"/api/v1/medical-records/{valid_record_id}/versions", headers=headers
        )

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should include error details
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data

    def test_get_medical_record_versions_access_denied_patient_other_record(
        self, valid_patient_token, valid_record_id
    ):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Access denied: Patient trying to access another patient's record
        Expected: 403 Forbidden with ErrorResponse schema
        """
        headers = {"Authorization": valid_patient_token}
        # Assuming valid_record_id belongs to a different patient
        response = client.get(
            f"/api/v1/medical-records/{valid_record_id}/versions", headers=headers
        )

        # Should return 403 Forbidden
        assert response.status_code == 403

        # Response should include error details
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data

    def test_get_medical_record_versions_access_denied_doctor_unauthorized_record(
        self, valid_doctor_token, valid_record_id
    ):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Access denied: Doctor trying to access unauthorized patient's record
        Expected: 403 Forbidden with ErrorResponse schema
        """
        headers = {"Authorization": valid_doctor_token}
        # Assuming valid_record_id belongs to patient not assigned to this doctor
        response = client.get(
            f"/api/v1/medical-records/{valid_record_id}/versions", headers=headers
        )

        # Should return 403 Forbidden
        assert response.status_code == 403

        # Response should include error details
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data

    def test_get_medical_record_versions_record_not_found(
        self, valid_patient_token, nonexistent_record_id
    ):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Not found error: Medical record doesn't exist
        Expected: 404 Not Found with ErrorResponse schema
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get(
            f"/api/v1/medical-records/{nonexistent_record_id}/versions", headers=headers
        )

        # Should return 404 Not Found
        assert response.status_code == 404

        # Response should include error details
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data

    def test_get_medical_record_versions_invalid_uuid_format(
        self, valid_patient_token, invalid_record_id
    ):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Validation error: Invalid UUID format for record_id
        Expected: 422 Unprocessable Entity with ValidationErrorResponse
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get(
            f"/api/v1/medical-records/{invalid_record_id}/versions", headers=headers
        )

        # Should return 422 Unprocessable Entity for invalid UUID
        assert response.status_code == 422

        # Response should include validation error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_get_medical_record_versions_empty_record_id(self, valid_patient_token):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Validation error: Empty record_id parameter
        Expected: 422 Unprocessable Entity or 404 Not Found
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get("/api/v1/medical-records//versions", headers=headers)

        # Should return 422 or 404 depending on FastAPI routing behavior
        assert response.status_code in [404, 422]

        # Response should include error details
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

    def test_get_medical_record_versions_single_version_record(
        self, valid_patient_token, valid_record_id
    ):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Edge case: Medical record with only one version
        Expected: 200 OK with single version in array
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get(
            f"/api/v1/medical-records/{valid_record_id}/versions", headers=headers
        )

        # Should return 200 OK
        assert response.status_code == 200

        data = response.json()

        # Should have exactly one version for new records
        if data["total_versions"] == 1:
            assert len(data["versions"]) == 1
            version = data["versions"][0]
            assert version["version_number"] == 1
            self._validate_medical_record_version_schema(version)

    def test_get_medical_record_versions_multiple_versions_record(
        self, valid_patient_token, valid_record_id
    ):
        """
        Contract Test: GET /api/v1/medical-records/{record_id}/versions
        Success case: Medical record with multiple versions
        Expected: 200 OK with all versions ordered properly
        """
        headers = {"Authorization": valid_patient_token}
        response = client.get(
            f"/api/v1/medical-records/{valid_record_id}/versions", headers=headers
        )

        # Should return 200 OK
        assert response.status_code == 200

        data = response.json()

        # If multiple versions exist, validate ordering and completeness
        if data["total_versions"] > 1:
            versions = data["versions"]

            # Should include all versions
            assert len(versions) == data["total_versions"]

            # Version numbers should be sequential
            version_numbers = [v["version_number"] for v in versions]
            expected_versions = list(range(1, data["total_versions"] + 1))
            assert sorted(version_numbers) == expected_versions

            # Each version should have different timestamps
            timestamps = [v["created_at"] for v in versions]
            assert len(set(timestamps)) == len(timestamps), (
                "Each version should have unique timestamp"
            )

    def _validate_medical_record_version_schema(self, version):
        """
        Helper method to validate MedicalRecordVersion schema
        Validates that a version matches the expected OpenAPI schema
        """
        # Required fields from MedicalRecordVersion schema
        required_fields = [
            "id",
            "medical_record_id",
            "version_number",
            "data",
            "change_reason",
            "changed_by_user_id",
            "changed_by_user_type",
            "created_at",
        ]

        for field in required_fields:
            assert field in version, f"Missing required field: {field}"

        # Type validations
        assert isinstance(version["id"], str), "id should be string (UUID)"
        assert isinstance(version["medical_record_id"], str), (
            "medical_record_id should be string (UUID)"
        )
        assert isinstance(version["version_number"], int), (
            "version_number should be integer"
        )
        assert isinstance(version["data"], dict), "data should be object"
        assert isinstance(version["change_reason"], str), (
            "change_reason should be string"
        )
        assert isinstance(version["changed_by_user_id"], str), (
            "changed_by_user_id should be string (UUID)"
        )
        assert isinstance(version["changed_by_user_type"], str), (
            "changed_by_user_type should be string"
        )
        assert isinstance(version["created_at"], str), (
            "created_at should be ISO datetime string"
        )

        # Enum validation for changed_by_user_type
        valid_user_types = ["patient", "doctor"]
        assert version["changed_by_user_type"] in valid_user_types, (
            f"Invalid changed_by_user_type: {version['changed_by_user_type']}"
        )

        # Version number should be positive
        assert version["version_number"] > 0, (
            "version_number should be positive integer"
        )

        # Data should not be empty
        assert len(version["data"]) > 0, "data should not be empty object"

        # Change reason should not be empty
        assert len(version["change_reason"].strip()) > 0, (
            "change_reason should not be empty string"
        )

    def _validate_error_response_schema(self, error_data):
        """
        Helper method to validate ErrorResponse schema
        Validates that an error response matches the expected OpenAPI schema
        """
        # Should have either 'error' or 'detail' field
        assert "error" in error_data or "detail" in error_data, (
            "Error response should contain 'error' or 'detail' field"
        )

        if "error" in error_data:
            assert isinstance(error_data["error"], str), "error should be string"
            assert len(error_data["error"]) > 0, "error should not be empty"

        if "detail" in error_data:
            # detail can be string or list of validation errors
            assert isinstance(error_data["detail"], (str, list)), (
                "detail should be string or list"
            )
