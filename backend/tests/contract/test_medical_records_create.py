"""
Contract tests for POST /api/v1/medical-records endpoint

These tests validate the medical records creation API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.

Tests patient ability to create new medical records of different types
(medical_history, medication, allergy, procedure) with proper validation.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestMedicalRecordsCreate:
    """Contract tests for medical records creation endpoint"""

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
    def medication_record_data(self):
        """Valid medication record creation payload"""
        return {
            "record_type": "medication",
            "title": "Daily Blood Pressure Medication",
            "data": {
                "medication_name": "Lisinopril",
                "dosage": "10mg",
                "frequency": "Once daily",
                "start_date": "2025-01-01",
                "prescribing_doctor": "Dr. Smith",
                "notes": "Take with food",
            },
        }

    @pytest.fixture
    def allergy_record_data(self):
        """Valid allergy record creation payload"""
        return {
            "record_type": "allergy",
            "title": "Penicillin Allergy",
            "data": {
                "allergen": "Penicillin",
                "reaction_type": "Severe rash",
                "severity": "High",
                "date_discovered": "2020-03-15",
            },
        }

    @pytest.fixture
    def medical_history_record_data(self):
        """Valid medical history record creation payload"""
        return {
            "record_type": "medical_history",
            "title": "Previous Surgery",
            "data": {
                "procedure": "Appendectomy",
                "date": "2018-06-15",
                "hospital": "General Hospital",
                "surgeon": "Dr. Johnson",
                "complications": "None",
                "notes": "Routine procedure, full recovery",
            },
        }

    @pytest.fixture
    def procedure_record_data(self):
        """Valid procedure record creation payload"""
        return {
            "record_type": "procedure",
            "title": "Annual Physical Exam",
            "data": {
                "procedure_name": "Comprehensive Physical Examination",
                "date": "2025-01-15",
                "provider": "Dr. Wilson",
                "findings": "Normal examination",
                "follow_up": "Annual check-up recommended",
            },
        }

    @pytest.fixture
    def minimal_record_data(self):
        """Minimal valid record creation payload (only required fields)"""
        return {
            "record_type": "medication",
            "title": "Basic Medication",
            "data": {"medication_name": "Aspirin"},
        }

    def test_create_medication_record_success(
        self, valid_patient_token, medication_record_data
    ):
        """
        Contract Test: POST /api/v1/medical-records
        Success case: Create medication record with all fields
        Expected: 201 Created with MedicalRecord schema
        """
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=medication_record_data, headers=headers
        )

        # Should return 201 Created
        assert response.status_code == 201

        # Response should match MedicalRecord schema
        data = response.json()

        # Required MedicalRecord fields
        assert "id" in data
        assert isinstance(data["id"], str)  # UUID format
        assert "patient_id" in data
        assert isinstance(data["patient_id"], str)  # UUID format
        assert "record_type" in data
        assert data["record_type"] == "medication"
        assert "title" in data
        assert data["title"] == "Daily Blood Pressure Medication"
        assert "current_version" in data
        assert data["current_version"] == 1  # First version
        assert "is_active" in data
        assert data["is_active"] is True
        assert "created_at" in data
        assert isinstance(data["created_at"], str)  # ISO datetime
        assert "updated_at" in data
        assert isinstance(data["updated_at"], str)  # ISO datetime
        assert "current_data" in data
        assert isinstance(data["current_data"], dict)

        # Verify current_data contains the submitted data
        assert data["current_data"]["medication_name"] == "Lisinopril"
        assert data["current_data"]["dosage"] == "10mg"
        assert data["current_data"]["frequency"] == "Once daily"

    def test_create_allergy_record_success(
        self, valid_patient_token, allergy_record_data
    ):
        """
        Contract Test: POST /api/v1/medical-records
        Success case: Create allergy record
        Expected: 201 Created with MedicalRecord schema
        """
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=allergy_record_data, headers=headers
        )

        # Should return 201 Created
        assert response.status_code == 201

        # Response should match MedicalRecord schema
        data = response.json()
        assert data["record_type"] == "allergy"
        assert data["title"] == "Penicillin Allergy"
        assert data["current_version"] == 1
        assert data["current_data"]["allergen"] == "Penicillin"
        assert data["current_data"]["severity"] == "High"

    def test_create_medical_history_record_success(
        self, valid_patient_token, medical_history_record_data
    ):
        """
        Contract Test: POST /api/v1/medical-records
        Success case: Create medical history record
        Expected: 201 Created with MedicalRecord schema
        """
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=medical_history_record_data, headers=headers
        )

        # Should return 201 Created
        assert response.status_code == 201

        # Response should match MedicalRecord schema
        data = response.json()
        assert data["record_type"] == "medical_history"
        assert data["title"] == "Previous Surgery"
        assert data["current_data"]["procedure"] == "Appendectomy"

    def test_create_procedure_record_success(
        self, valid_patient_token, procedure_record_data
    ):
        """
        Contract Test: POST /api/v1/medical-records
        Success case: Create procedure record
        Expected: 201 Created with MedicalRecord schema
        """
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=procedure_record_data, headers=headers
        )

        # Should return 201 Created
        assert response.status_code == 201

        # Response should match MedicalRecord schema
        data = response.json()
        assert data["record_type"] == "procedure"
        assert data["title"] == "Annual Physical Exam"
        procedure_name = data["current_data"]["procedure_name"]
        assert procedure_name == "Comprehensive Physical Examination"

    def test_create_minimal_record_success(
        self, valid_patient_token, minimal_record_data
    ):
        """
        Contract Test: POST /api/v1/medical-records
        Success case: Create record with minimal required fields only
        Expected: 201 Created with MedicalRecord schema
        """
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=minimal_record_data, headers=headers
        )

        # Should return 201 Created
        assert response.status_code == 201

        # Response should match MedicalRecord schema
        data = response.json()
        assert data["record_type"] == "medication"
        assert data["title"] == "Basic Medication"
        assert data["current_data"]["medication_name"] == "Aspirin"

    def test_create_record_missing_record_type(self, valid_patient_token):
        """
        Contract Test: POST /api/v1/medical-records
        Error case: Missing required record_type field
        Expected: 400 Bad Request with ErrorResponse schema
        """
        invalid_data = {"title": "Missing Record Type", "data": {"some": "data"}}
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=invalid_data, headers=headers
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "record_type" in data["message"].lower()

    def test_create_record_invalid_record_type(self, valid_patient_token):
        """
        Contract Test: POST /api/v1/medical-records
        Error case: Invalid record_type value
        Expected: 400 Bad Request with ErrorResponse schema
        """
        invalid_data = {
            "record_type": "invalid_type",
            "title": "Invalid Type Record",
            "data": {"some": "data"},
        }
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=invalid_data, headers=headers
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_record_missing_title(self, valid_patient_token):
        """
        Contract Test: POST /api/v1/medical-records
        Error case: Missing required title field
        Expected: 400 Bad Request with ErrorResponse schema
        """
        invalid_data = {
            "record_type": "medication",
            "data": {"medication_name": "Test"},
        }
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=invalid_data, headers=headers
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "title" in data["message"].lower()

    def test_create_record_empty_title(self, valid_patient_token):
        """
        Contract Test: POST /api/v1/medical-records
        Error case: Empty title (violates minLength: 1)
        Expected: 400 Bad Request with ErrorResponse schema
        """
        invalid_data = {
            "record_type": "medication",
            "title": "",
            "data": {"medication_name": "Test"},
        }
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=invalid_data, headers=headers
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_record_title_too_long(self, valid_patient_token):
        """
        Contract Test: POST /api/v1/medical-records
        Error case: Title exceeds maxLength: 200
        Expected: 400 Bad Request with ErrorResponse schema
        """
        long_title = "x" * 201  # Exceeds 200 character limit
        invalid_data = {
            "record_type": "medication",
            "title": long_title,
            "data": {"medication_name": "Test"},
        }
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=invalid_data, headers=headers
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_record_missing_data(self, valid_patient_token):
        """
        Contract Test: POST /api/v1/medical-records
        Error case: Missing required data field
        Expected: 400 Bad Request with ErrorResponse schema
        """
        invalid_data = {"record_type": "medication", "title": "Missing Data"}
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=invalid_data, headers=headers
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "data" in data["message"].lower()

    def test_create_record_unauthenticated(self, medication_record_data):
        """
        Contract Test: POST /api/v1/medical-records
        Error case: Request without authentication token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        response = client.post("/api/v1/medical-records", json=medication_record_data)

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_record_invalid_token(self, invalid_token, medication_record_data):
        """
        Contract Test: POST /api/v1/medical-records
        Error case: Request with invalid authentication token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": invalid_token, "Content-Type": "application/json"}
        response = client.post(
            "/api/v1/medical-records", json=medication_record_data, headers=headers
        )

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_record_expired_token(self, expired_token, medication_record_data):
        """
        Contract Test: POST /api/v1/medical-records
        Error case: Request with expired authentication token
        Expected: 401 Unauthorized with ErrorResponse schema
        """
        headers = {"Authorization": expired_token, "Content-Type": "application/json"}
        response = client.post(
            "/api/v1/medical-records", json=medication_record_data, headers=headers
        )

        # Should return 401 Unauthorized
        assert response.status_code == 401

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_record_invalid_json(self, valid_patient_token):
        """
        Contract Test: POST /api/v1/medical-records
        Error case: Invalid JSON in request body
        Expected: 400 Bad Request with ErrorResponse schema
        """
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        # Send malformed JSON as content instead of using data parameter
        response = client.request(
            "POST",
            "/api/v1/medical-records",
            content='{"record_type": "medication", "title": "Test", invalid json}',
            headers=headers,
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_record_empty_body(self, valid_patient_token):
        """
        Contract Test: POST /api/v1/medical-records
        Error case: Empty request body
        Expected: 400 Bad Request with ErrorResponse schema
        """
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post("/api/v1/medical-records", json={}, headers=headers)

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Response should match ErrorResponse schema
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_record_content_type_validation(
        self, valid_patient_token, medication_record_data
    ):
        """
        Contract Test: POST /api/v1/medical-records
        Validation: Correct content-type header handling
        Expected: 201 Created when content-type is application/json
        """
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=medication_record_data, headers=headers
        )

        # Should return 201 Created
        assert response.status_code == 201

        # Response should have correct content-type
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    def test_create_record_response_structure_validation(
        self, valid_patient_token, medication_record_data
    ):
        """
        Contract Test: POST /api/v1/medical-records
        Validation: Complete response structure validation
        Expected: Response matches exact MedicalRecord schema structure
        """
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }
        response = client.post(
            "/api/v1/medical-records", json=medication_record_data, headers=headers
        )

        # Should return 201 Created
        assert response.status_code == 201

        # Validate complete response structure
        data = response.json()

        # All required fields must be present
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
            assert field in data, f"Required field '{field}' missing"

        # Type validations
        assert isinstance(data["id"], str)
        assert isinstance(data["patient_id"], str)
        assert isinstance(data["record_type"], str)
        assert isinstance(data["title"], str)
        assert isinstance(data["current_version"], int)
        assert isinstance(data["is_active"], bool)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
        assert isinstance(data["current_data"], dict)

        # Value validations
        valid_types = ["medical_history", "medication", "allergy", "procedure"]
        assert data["record_type"] in valid_types
        assert data["current_version"] >= 1
        assert len(data["title"]) > 0
        assert len(data["title"]) <= 200

    def test_create_record_idempotency_check(
        self, valid_patient_token, medication_record_data
    ):
        """
        Contract Test: POST /api/v1/medical-records
        Validation: Multiple identical requests create separate records
        Expected: Each request creates a new record with unique ID
        """
        headers = {
            "Authorization": valid_patient_token,
            "Content-Type": "application/json",
        }

        # First request
        response1 = client.post(
            "/api/v1/medical-records", json=medication_record_data, headers=headers
        )
        assert response1.status_code == 201
        data1 = response1.json()

        # Second identical request
        response2 = client.post(
            "/api/v1/medical-records", json=medication_record_data, headers=headers
        )
        assert response2.status_code == 201
        data2 = response2.json()

        # Should create separate records
        assert data1["id"] != data2["id"]
        assert data1["title"] == data2["title"]  # Same content
        assert data1["record_type"] == data2["record_type"]  # Same content
