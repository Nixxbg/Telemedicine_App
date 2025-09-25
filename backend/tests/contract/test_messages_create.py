"""
Contract tests for POST /api/v1/messages endpoint

These tests validate the messaging creation API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.core.reference_data import (
    APPOINTMENT_ID,
    DOCTOR_USER_ID,
    OTHER_PATIENT_USER_ID,
    PATIENT_USER_ID,
    URGENT_APPOINTMENT_ID,
    VALID_DOCTOR_TOKEN,
    VALID_PATIENT_TOKEN,
)

from main import app

client = TestClient(app)


class TestMessagesCreateEndpoint:
    """Contract tests for POST /api/v1/messages endpoint"""

    @pytest.fixture
    def patient_auth_headers(self):
        """Authentication headers for patient user"""
        return {"Authorization": f"Bearer {VALID_PATIENT_TOKEN}"}

    @pytest.fixture
    def doctor_auth_headers(self):
        """Authentication headers for doctor user"""
        return {"Authorization": f"Bearer {VALID_DOCTOR_TOKEN}"}

    @pytest.fixture
    def sample_doctor_id(self):
        """Sample doctor UUID for messaging"""
        return str(DOCTOR_USER_ID)

    @pytest.fixture
    def sample_patient_id(self):
        """Sample patient UUID for messaging"""
        return str(OTHER_PATIENT_USER_ID)

    @pytest.fixture
    def sample_appointment_id(self):
        """Sample appointment UUID for message context"""
        return str(APPOINTMENT_ID)

    @pytest.fixture
    def valid_message_data(self, sample_doctor_id, sample_appointment_id):
        """Valid message creation payload"""
        return {
            "recipient_id": sample_doctor_id,
            "appointment_id": sample_appointment_id,
            "content": (
                "I have been experiencing some side effects from the medication. "
                "Can we discuss alternative options?"
            ),
        }

    @pytest.fixture
    def minimal_message_data(self, sample_doctor_id):
        """Minimal valid message creation payload (only required fields)"""
        return {
            "recipient_id": sample_doctor_id,
            "content": "Hello, I have a question about my treatment.",
        }

    @pytest.fixture
    def doctor_message_data(self, sample_appointment_id):
        """Doctor sending message to patient"""
        return {
            "recipient_id": str(PATIENT_USER_ID),
            "appointment_id": sample_appointment_id,
            "content": (
                "Thank you for letting me know. Please describe the specific side "
                "effects you're experiencing. We can definitely explore other "
                "medication options during our next appointment."
            ),
        }

    def test_send_message_success_with_appointment(
        self, patient_auth_headers, valid_message_data
    ):
        """
        Contract Test: POST /api/v1/messages
        Success case with appointment context
        Expected: 201 Created with Message schema
        """
        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=valid_message_data
        )

        # Should return 201 when implemented
        assert response.status_code == 201

        data = response.json()

        # Validate Message schema
        required_fields = [
            "id",
            "sender_id",
            "recipient_id",
            "content",
            "message_type",
            "is_read",
            "sent_at",
        ]
        for field in required_fields:
            assert field in data

        # Validate specific values
        assert data["recipient_id"] == valid_message_data["recipient_id"]
        assert data["content"] == valid_message_data["content"]
        assert data["message_type"] == "text"
        assert data["is_read"] is False
        assert data["appointment_id"] == valid_message_data["appointment_id"]

        # Validate UUID format
        import uuid

        assert uuid.UUID(data["id"])
        assert uuid.UUID(data["sender_id"])
        assert uuid.UUID(data["recipient_id"])

    def test_send_message_success_minimal_data(
        self, patient_auth_headers, minimal_message_data
    ):
        """
        Contract Test: POST /api/v1/messages
        Success case with only required fields
        Expected: 201 Created with Message schema
        """
        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=minimal_message_data
        )

        assert response.status_code == 201

        data = response.json()

        # Validate required fields are present
        assert data["recipient_id"] == minimal_message_data["recipient_id"]
        assert data["content"] == minimal_message_data["content"]
        assert data["message_type"] == "text"
        assert data["is_read"] is False

        # appointment_id should be null when not provided
        assert data.get("appointment_id") is None

    def test_send_message_doctor_to_patient(
        self, doctor_auth_headers, doctor_message_data
    ):
        """
        Contract Test: POST /api/v1/messages (doctor sender)
        Success case with doctor sending to patient
        Expected: 201 Created with Message schema
        """
        response = client.post(
            "/api/v1/messages", headers=doctor_auth_headers, json=doctor_message_data
        )

        assert response.status_code == 201

        data = response.json()
        assert data["recipient_id"] == doctor_message_data["recipient_id"]
        assert data["content"] == doctor_message_data["content"]

    def test_send_message_content_max_length(
        self, patient_auth_headers, sample_doctor_id
    ):
        """
        Contract Test: POST /api/v1/messages
        Success case with maximum allowed content length (2000 chars)
        Expected: 201 Created
        """
        max_content = "A" * 2000  # 2000 characters

        message_data = {"recipient_id": sample_doctor_id, "content": max_content}

        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=message_data
        )

        assert response.status_code == 201

        data = response.json()
        assert data["content"] == max_content

    def test_send_message_empty_content(self, patient_auth_headers, sample_doctor_id):
        """
        Contract Test: POST /api/v1/messages
        Error case with empty content
        Expected: 400 Bad Request
        """
        message_data = {"recipient_id": sample_doctor_id, "content": ""}

        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=message_data
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data
        assert data["error"] == "validation_error"

    def test_send_message_content_too_long(
        self, patient_auth_headers, sample_doctor_id
    ):
        """
        Contract Test: POST /api/v1/messages
        Error case with content exceeding max length (2000 chars)
        Expected: 400 Bad Request
        """
        too_long_content = "A" * 2001  # 2001 characters

        message_data = {"recipient_id": sample_doctor_id, "content": too_long_content}

        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=message_data
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_send_message_missing_recipient_id(self, patient_auth_headers):
        """
        Contract Test: POST /api/v1/messages
        Error case with missing recipient_id (required field)
        Expected: 400 Bad Request
        """
        message_data = {"content": "Hello, I have a question."}

        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=message_data
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_send_message_missing_content(self, patient_auth_headers, sample_doctor_id):
        """
        Contract Test: POST /api/v1/messages
        Error case with missing content (required field)
        Expected: 400 Bad Request
        """
        message_data = {"recipient_id": sample_doctor_id}

        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=message_data
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_send_message_invalid_recipient_uuid(self, patient_auth_headers):
        """
        Contract Test: POST /api/v1/messages
        Error case with invalid recipient_id UUID format
        Expected: 400 Bad Request
        """
        message_data = {
            "recipient_id": "invalid-uuid",
            "content": "Hello, I have a question.",
        }

        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=message_data
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_send_message_invalid_appointment_uuid(
        self, patient_auth_headers, sample_doctor_id
    ):
        """
        Contract Test: POST /api/v1/messages
        Error case with invalid appointment_id UUID format
        Expected: 400 Bad Request
        """
        message_data = {
            "recipient_id": sample_doctor_id,
            "appointment_id": "invalid-uuid",
            "content": "Hello, I have a question.",
        }

        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=message_data
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_send_message_patient_to_invalid_recipient(
        self, patient_auth_headers, sample_patient_id
    ):
        """
        Contract Test: POST /api/v1/messages
        Error case with patient trying to message another patient
        Expected: 403 Forbidden
        """
        message_data = {
            "recipient_id": sample_patient_id,
            "content": "Hello fellow patient.",
        }

        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=message_data
        )

        assert response.status_code == 403

        data = response.json()
        assert "error" in data
        assert "message" in data
        assert data["error"] == "access_denied"

    def test_send_message_nonexistent_recipient(self, patient_auth_headers):
        """
        Contract Test: POST /api/v1/messages
        Error case with nonexistent recipient_id
        Expected: 403 Forbidden
        """
        nonexistent_id = str(uuid4())

        message_data = {
            "recipient_id": nonexistent_id,
            "content": "Hello, I have a question.",
        }

        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=message_data
        )

        assert response.status_code == 403

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_send_message_invalid_appointment_context(
        self, patient_auth_headers, sample_doctor_id
    ):
        """
        Contract Test: POST /api/v1/messages
        Error case with appointment_id that doesn't involve the patient
        Expected: 403 Forbidden
        """
        invalid_appointment_id = str(URGENT_APPOINTMENT_ID)

        message_data = {
            "recipient_id": sample_doctor_id,
            "appointment_id": invalid_appointment_id,
            "content": "Hello, I have a question about our appointment.",
        }

        response = client.post(
            "/api/v1/messages", headers=patient_auth_headers, json=message_data
        )

        assert response.status_code == 403

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_send_message_unauthenticated(self, sample_doctor_id):
        """
        Contract Test: POST /api/v1/messages (no auth header)
        Error case without authentication
        Expected: 401 Unauthorized
        """
        message_data = {
            "recipient_id": sample_doctor_id,
            "content": "Hello, I have a question.",
        }

        response = client.post("/api/v1/messages", json=message_data)

        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_send_message_invalid_token(self, sample_doctor_id):
        """
        Contract Test: POST /api/v1/messages (invalid token)
        Error case with invalid JWT token
        Expected: 401 Unauthorized
        """
        message_data = {
            "recipient_id": sample_doctor_id,
            "content": "Hello, I have a question.",
        }

        response = client.post(
            "/api/v1/messages",
            headers={"Authorization": "Bearer invalid_token"},
            json=message_data,
        )

        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_send_message_expired_token(self, sample_doctor_id):
        """
        Contract Test: POST /api/v1/messages (expired token)
        Error case with expired JWT token
        Expected: 401 Unauthorized
        """
        message_data = {
            "recipient_id": sample_doctor_id,
            "content": "Hello, I have a question.",
        }

        # This would use an expired token fixture when auth is implemented
        expired_token = "Bearer expired_jwt_token_here"

        response = client.post(
            "/api/v1/messages",
            headers={"Authorization": expired_token},
            json=message_data,
        )

        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_send_message_malformed_json(self, patient_auth_headers):
        """
        Contract Test: POST /api/v1/messages
        Error case with malformed JSON body
        Expected: 400 Bad Request
        """
        response = client.post(
            "/api/v1/messages",
            headers=patient_auth_headers,
            content=b"invalid json content",
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_send_message_missing_content_type(
        self, patient_auth_headers, sample_doctor_id
    ):
        """
        Contract Test: POST /api/v1/messages
        Error case with missing Content-Type header
        Expected: 400 Bad Request
        """
        import json

        message_data = {
            "recipient_id": sample_doctor_id,
            "content": "Hello, I have a question.",
        }

        headers = patient_auth_headers.copy()
        # Remove Content-Type to test default behavior
        response = client.post(
            "/api/v1/messages",
            headers=headers,
            content=json.dumps(message_data).encode(),
        )

        # FastAPI should handle this gracefully,
        # but test behavior without explicit Content-Type
        assert response.status_code in [400, 422]

    def test_send_message_validate_response_schema(
        self, doctor_auth_headers, doctor_message_data
    ):
        """
        Contract Test: POST /api/v1/messages
        Validate complete Message response schema
        Expected: 201 Created with proper Message schema
        """
        response = client.post(
            "/api/v1/messages", headers=doctor_auth_headers, json=doctor_message_data
        )

        assert response.status_code == 201

        data = response.json()

        # Validate all Message schema fields
        assert isinstance(data["id"], str)
        assert isinstance(data["sender_id"], str)
        assert isinstance(data["recipient_id"], str)
        assert isinstance(data["content"], str)
        assert data["message_type"] in ["text", "system_notification"]
        assert isinstance(data["is_read"], bool)
        assert isinstance(data["sent_at"], str)

        # Optional fields
        if "appointment_id" in data:
            assert (
                isinstance(data["appointment_id"], str)
                or data["appointment_id"] is None
            )

        if "read_at" in data:
            assert isinstance(data["read_at"], str) or data["read_at"] is None

        # Validate ISO datetime format
        from datetime import datetime

        datetime.fromisoformat(data["sent_at"].replace("Z", "+00:00"))
