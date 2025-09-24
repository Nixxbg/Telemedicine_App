"""
Contract tests for GET /api/v1/messages endpoint

These tests validate the messaging list API according to the
OpenAPI specification. Tests are written in TDD fashion and should fail
before implementation.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from main import app

client = TestClient(app)


class TestMessagesListEndpoint:
    """Contract tests for GET /api/v1/messages endpoint"""

    @pytest.fixture
    def patient_auth_headers(self):
        """Authentication headers for patient user"""
        # This will need to be implemented with actual JWT token generation
        return {"Authorization": "Bearer patient_jwt_token_here"}

    @pytest.fixture
    def doctor_auth_headers(self):
        """Authentication headers for doctor user"""
        # This will need to be implemented with actual JWT token generation
        return {"Authorization": "Bearer doctor_jwt_token_here"}

    @pytest.fixture
    def sample_appointment_id(self):
        """Sample appointment UUID for filtering"""
        return str(uuid4())

    @pytest.fixture
    def sample_user_id(self):
        """Sample user UUID for conversation filtering"""
        return str(uuid4())

    def test_get_messages_success_default_params(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages
        Success case with default parameters
        Expected: 200 OK with MessagesResponse schema
        """
        response = client.get("/api/v1/messages", headers=patient_auth_headers)

        # Should return 200 when implemented
        assert response.status_code == 200

        data = response.json()

        # Validate MessagesResponse schema
        assert "messages" in data
        assert "total_count" in data
        assert "unread_count" in data
        assert "offset" in data
        assert "limit" in data

        assert isinstance(data["messages"], list)
        assert isinstance(data["total_count"], int)
        assert isinstance(data["unread_count"], int)
        assert isinstance(data["offset"], int)
        assert isinstance(data["limit"], int)

        # Default values from contract
        assert data["offset"] == 0
        assert data["limit"] == 50

    def test_get_messages_with_appointment_filter(
        self, patient_auth_headers, sample_appointment_id
    ):
        """
        Contract Test: GET /api/v1/messages?appointment_id={uuid}
        Success case filtering by appointment
        Expected: 200 OK with filtered messages
        """
        response = client.get(
            f"/api/v1/messages?appointment_id={sample_appointment_id}",
            headers=patient_auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert "messages" in data

        # All returned messages should be related to the appointment
        for message in data["messages"]:
            if "appointment_id" in message and message["appointment_id"]:
                assert message["appointment_id"] == sample_appointment_id

    def test_get_messages_with_conversation_filter(
        self, patient_auth_headers, sample_user_id
    ):
        """
        Contract Test: GET /api/v1/messages?conversation_with={uuid}
        Success case filtering by conversation participant
        Expected: 200 OK with filtered messages
        """
        response = client.get(
            f"/api/v1/messages?conversation_with={sample_user_id}",
            headers=patient_auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert "messages" in data

    def test_get_messages_with_message_type_filter(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages?message_type=text
        Success case filtering by message type
        Expected: 200 OK with filtered messages
        """
        response = client.get(
            "/api/v1/messages?message_type=text", headers=patient_auth_headers
        )

        assert response.status_code == 200

        data = response.json()
        assert "messages" in data

        # All returned messages should be of type 'text'
        for message in data["messages"]:
            assert message["message_type"] == "text"

    def test_get_messages_with_unread_only_filter(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages?unread_only=true
        Success case showing only unread messages
        Expected: 200 OK with only unread messages
        """
        response = client.get(
            "/api/v1/messages?unread_only=true", headers=patient_auth_headers
        )

        assert response.status_code == 200

        data = response.json()
        assert "messages" in data

        # All returned messages should be unread
        for message in data["messages"]:
            assert message["is_read"] is False

    def test_get_messages_with_pagination(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages?limit=10&offset=5
        Success case with pagination parameters
        Expected: 200 OK with paginated results
        """
        response = client.get(
            "/api/v1/messages?limit=10&offset=5", headers=patient_auth_headers
        )

        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 5
        assert len(data["messages"]) <= 10

    def test_get_messages_with_sort_order_asc(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages?sort_order=asc
        Success case with ascending sort order
        Expected: 200 OK with messages in ascending order
        """
        response = client.get(
            "/api/v1/messages?sort_order=asc", headers=patient_auth_headers
        )

        assert response.status_code == 200

        data = response.json()
        assert "messages" in data

        # Verify chronological order (oldest first)
        if len(data["messages"]) > 1:
            timestamps = [msg["sent_at"] for msg in data["messages"]]
            assert timestamps == sorted(timestamps)

    def test_get_messages_with_sort_order_desc(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages?sort_order=desc
        Success case with descending sort order (default)
        Expected: 200 OK with messages in descending order
        """
        response = client.get(
            "/api/v1/messages?sort_order=desc", headers=patient_auth_headers
        )

        assert response.status_code == 200

        data = response.json()
        assert "messages" in data

        # Verify reverse chronological order (newest first)
        if len(data["messages"]) > 1:
            timestamps = [msg["sent_at"] for msg in data["messages"]]
            assert timestamps == sorted(timestamps, reverse=True)

    def test_get_messages_validate_message_schema(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages
        Validate MessageDetail schema structure
        Expected: 200 OK with proper message schema
        """
        response = client.get("/api/v1/messages", headers=patient_auth_headers)

        assert response.status_code == 200

        data = response.json()

        if data["messages"]:
            message = data["messages"][0]

            # Validate Message base schema
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
                assert field in message

            # Validate MessageDetail additional fields
            assert "sender" in message
            assert "recipient" in message

            # Validate UserSummary schema in sender/recipient
            for user in [message["sender"], message["recipient"]]:
                assert "id" in user
                assert "user_type" in user
                assert user["user_type"] in ["patient", "doctor"]
                assert "first_name" in user
                assert "last_name" in user

                if user["user_type"] == "patient":
                    assert "username" in user
                elif user["user_type"] == "doctor":
                    assert "doctor_id" in user

    def test_get_messages_invalid_limit_too_high(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages?limit=150
        Error case with limit above maximum (100)
        Expected: 400 Bad Request
        """
        response = client.get(
            "/api/v1/messages?limit=150", headers=patient_auth_headers
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_messages_invalid_limit_too_low(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages?limit=0
        Error case with limit below minimum (1)
        Expected: 400 Bad Request
        """
        response = client.get("/api/v1/messages?limit=0", headers=patient_auth_headers)

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_messages_invalid_offset_negative(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages?offset=-1
        Error case with negative offset
        Expected: 400 Bad Request
        """
        response = client.get(
            "/api/v1/messages?offset=-1", headers=patient_auth_headers
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_messages_invalid_message_type(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages?message_type=invalid
        Error case with invalid message type
        Expected: 400 Bad Request
        """
        response = client.get(
            "/api/v1/messages?message_type=invalid", headers=patient_auth_headers
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_messages_invalid_sort_order(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages?sort_order=invalid
        Error case with invalid sort order
        Expected: 400 Bad Request
        """
        response = client.get(
            "/api/v1/messages?sort_order=invalid", headers=patient_auth_headers
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_messages_invalid_uuid_formats(self, patient_auth_headers):
        """
        Contract Test: GET /api/v1/messages?appointment_id=invalid-uuid
        Error case with invalid UUID format
        Expected: 400 Bad Request
        """
        response = client.get(
            "/api/v1/messages?appointment_id=invalid-uuid", headers=patient_auth_headers
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_messages_unauthenticated(self):
        """
        Contract Test: GET /api/v1/messages (no auth header)
        Error case without authentication
        Expected: 401 Unauthorized
        """
        response = client.get("/api/v1/messages")

        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_messages_invalid_token(self):
        """
        Contract Test: GET /api/v1/messages (invalid token)
        Error case with invalid JWT token
        Expected: 401 Unauthorized
        """
        response = client.get(
            "/api/v1/messages", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_get_messages_expired_token(self):
        """
        Contract Test: GET /api/v1/messages (expired token)
        Error case with expired JWT token
        Expected: 401 Unauthorized
        """
        # This would use an expired token fixture when auth is implemented
        expired_token = "Bearer expired_jwt_token_here"

        response = client.get(
            "/api/v1/messages", headers={"Authorization": expired_token}
        )

        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert "message" in data
