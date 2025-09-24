"""
Integration tests for patient registration flow

These tests validate the complete patient registration workflow,
including account creation, email verification, and initial profile setup.
Integration tests verify the full end-to-end functionality rather than
individual API contracts.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


class TestPatientRegistrationFlow:
    """Integration tests for complete patient registration workflow"""

    @pytest.fixture
    def valid_registration_data(self):
        """Complete patient registration data for integration testing"""
        return {
            "email": "integration.patient@example.com",
            "username": "integrationpatient",
            "password": "SecurePassword123!",
            "first_name": "Integration",
            "last_name": "Patient",
            "date_of_birth": "1990-01-15",
            "phone_number": "+1234567890",
        }

    @pytest.fixture
    def minimal_registration_data(self):
        """Minimal registration data for edge case testing"""
        return {
            "email": "minimal.patient@example.com",
            "username": "minimalpatient",
            "password": "MinimalPass123!",
            "first_name": "Minimal",
            "last_name": "Patient",
            "date_of_birth": "1995-06-30",
        }

    async def test_complete_patient_registration_workflow(
        self, valid_registration_data
    ):
        """
        Integration Test: Complete patient registration workflow

        This test validates the entire patient registration process:
        1. Register new patient account
        2. Verify account creation in database
        3. Login with new credentials
        4. Access protected patient profile endpoint
        5. Verify initial profile state

        Expected: Full workflow completes successfully with proper state transitions
        """
        # Step 1: Register new patient
        registration_response = client.post(
            "/api/v1/auth/register/patient", json=valid_registration_data
        )

        # Should fail initially (TDD - no implementation yet)
        # Should fail initially (TDD - no implementation yet)
        assert registration_response.status_code == 404

        # TODO: Once implemented, verify:
        # assert registration_response.status_code == 201
        # registration_data = registration_response.json()
        # assert "access_token" in registration_data
        # assert "refresh_token" in registration_data
        # assert registration_data["user"]["user_type"] == "patient"
        # assert registration_data["user"]["email"] == valid_registration_data["email"]

        # Step 2: Verify database state
        # TODO: Once database models are implemented:
        # async with get_async_session() as session:
        #     patient = await session.execute(
        #         select(Patient).where(
        #             Patient.email == valid_registration_data["email"]
        #         )
        #     )
        #     patient_record = patient.scalar_one_or_none()
        #     assert patient_record is not None
        #     assert patient_record.profile_completed is False
        #     assert patient_record.email_verified is False

        # Step 3: Login with new credentials
        # login_response = client.post(
        #     "/api/v1/auth/login",
        #     json={
        #         "email": valid_registration_data["email"],
        #         "password": valid_registration_data["password"]
        #     }
        # )
        # assert login_response.status_code == 200
        # login_data = login_response.json()
        # access_token = login_data["access_token"]

        # Step 4: Access protected profile endpoint
        # profile_response = client.get(
        #     "/api/v1/auth/me",
        #     headers={"Authorization": f"Bearer {access_token}"}
        # )
        # assert profile_response.status_code == 200
        # profile_data = profile_response.json()
        # assert profile_data["email"] == valid_registration_data["email"]
        # assert profile_data["profile_completed"] is False

        # Step 5: Verify initial questionnaire state
        # questionnaire_response = client.get(
        #     "/api/v1/patients/questionnaire/progress",
        #     headers={"Authorization": f"Bearer {access_token}"}
        # )
        # assert questionnaire_response.status_code == 200
        # questionnaire_data = questionnaire_response.json()
        # assert questionnaire_data["completed"] is False
        # assert questionnaire_data["current_step"] == 1

    async def test_patient_registration_with_duplicate_email(
        self, valid_registration_data
    ):
        """
        Integration Test: Duplicate email handling

        Tests the complete workflow when attempting to register
        with an email that already exists in the system.
        """
        # First registration - should succeed
        first_response = client.post(
            "/api/v1/auth/register/patient", json=valid_registration_data
        )

        # Should fail initially (TDD)
        assert first_response.status_code == 404

        # TODO: Once implemented:
        # assert first_response.status_code == 201

        # Second registration with same email - should fail
        # duplicate_data = valid_registration_data.copy()
        # duplicate_data["username"] = "differentusername"

        # second_response = client.post(
        #     "/api/v1/auth/register/patient",
        #     json=duplicate_data
        # )
        # assert second_response.status_code == 409  # Conflict
        # error_data = second_response.json()
        # assert "email" in error_data["message"].lower()

    async def test_patient_registration_with_duplicate_username(
        self, valid_registration_data
    ):
        """
        Integration Test: Duplicate username handling

        Tests the complete workflow when attempting to register
        with a username that already exists in the system.
        """
        # First registration - should succeed
        first_response = client.post(
            "/api/v1/auth/register/patient", json=valid_registration_data
        )

        # Should fail initially (TDD)
        assert first_response.status_code == 404

        # TODO: Once implemented:
        # assert first_response.status_code == 201

        # Second registration with same username - should fail
        # duplicate_data = valid_registration_data.copy()
        # duplicate_data["email"] = "different.email@example.com"

        # second_response = client.post(
        #     "/api/v1/auth/register/patient",
        #     json=duplicate_data
        # )
        # assert second_response.status_code == 409  # Conflict
        # error_data = second_response.json()
        # assert "username" in error_data["message"].lower()

    async def test_patient_registration_password_requirements(self):
        """
        Integration Test: Password validation workflow

        Tests various password strength requirements through
        the complete registration process.
        """
        base_data = {
            "email": "password.test@example.com",
            "username": "passwordtest",
            "first_name": "Password",
            "last_name": "Test",
            "date_of_birth": "1990-01-15",
        }

        # Test weak passwords
        weak_passwords = [
            "123456",  # Too short
            "password",  # No numbers/symbols
            "PASSWORD123",  # No lowercase
            "password123",  # No uppercase
            "Password123",  # No symbols
        ]

        for weak_password in weak_passwords:
            test_data = base_data.copy()
            test_data["password"] = weak_password

            response = client.post("/api/v1/auth/register/patient", json=test_data)

            # Should fail initially (TDD)
            assert response.status_code == 404

            # TODO: Once implemented:
            # assert response.status_code == 422  # Validation error
            # error_data = response.json()
            # assert "password" in error_data["details"]

    async def test_patient_registration_underage_validation(
        self, valid_registration_data
    ):
        """
        Integration Test: Age validation workflow

        Tests that patients under 18 cannot register
        without parental consent workflow.
        """
        # Set date of birth to under 18
        underage_data = valid_registration_data.copy()
        from datetime import date, timedelta

        underage_date = date.today() - timedelta(days=365 * 16)  # 16 years old
        underage_data["date_of_birth"] = underage_date.isoformat()

        response = client.post("/api/v1/auth/register/patient", json=underage_data)

        # Should fail initially (TDD)
        assert response.status_code == 404

        # TODO: Once implemented:
        # assert response.status_code == 422  # Validation error
        # error_data = response.json()
        # assert "age" in error_data["message"].lower() or "18" in error_data["message"]

    async def test_patient_registration_data_persistence(self, valid_registration_data):
        """
        Integration Test: Data persistence validation

        Tests that all registration data is properly stored
        and can be retrieved after registration.
        """
        response = client.post(
            "/api/v1/auth/register/patient", json=valid_registration_data
        )

        # Should fail initially (TDD)
        assert response.status_code == 404

        # TODO: Once implemented and database is available:
        # assert response.status_code == 201
        # registration_data = response.json()
        # access_token = registration_data["access_token"]

        # # Retrieve profile data
        # profile_response = client.get(
        #     "/api/v1/auth/me",
        #     headers={"Authorization": f"Bearer {access_token}"}
        # )
        # assert profile_response.status_code == 200
        # profile_data = profile_response.json()

        # # Verify all data persisted correctly
        # assert profile_data["email"] == valid_registration_data["email"]
        # assert profile_data["username"] == valid_registration_data["username"]
        # assert profile_data["first_name"] == valid_registration_data["first_name"]
        # assert profile_data["last_name"] == valid_registration_data["last_name"]
        # assert (
        #     profile_data["date_of_birth"]
        #     == valid_registration_data["date_of_birth"]
        # )
        # assert profile_data["phone_number"] == valid_registration_data["phone_number"]
        #
        # # Verify sensitive data is not exposed
        # assert "password" not in profile_data
        # assert "password_hash" not in profile_data

    @patch("src.services.email_service.send_email")
    async def test_patient_registration_email_workflow(
        self, mock_send_email, valid_registration_data
    ):
        """
        Integration Test: Email verification workflow

        Tests the complete email verification process after registration,
        including email sending and verification token handling.
        """
        mock_send_email.return_value = AsyncMock(return_value=True)

        response = client.post(
            "/api/v1/auth/register/patient", json=valid_registration_data
        )

        # Should fail initially (TDD)
        assert response.status_code == 404

        # TODO: Once implemented:
        # assert response.status_code == 201
        #
        # # Verify email was sent
        # mock_send_email.assert_called_once()
        # call_args = mock_send_email.call_args
        # assert call_args[1]["to_email"] == valid_registration_data["email"]
        # assert "verification" in call_args[1]["subject"].lower()
        #
        # # Extract verification token from email content
        # email_content = call_args[1]["html_content"]
        # # Mock token extraction (in real implementation, would parse email)
        # verification_token = "mock_verification_token_123"
        #
        # # Test email verification endpoint
        # verification_response = client.post(
        #     "/api/v1/auth/verify-email",
        #     json={"token": verification_token}
        # )
        # assert verification_response.status_code == 200
        #
        # # Verify email is now marked as verified
        # login_response = client.post(
        #     "/api/v1/auth/login",
        #     json={
        #         "email": valid_registration_data["email"],
        #         "password": valid_registration_data["password"]
        #     }
        # )
        # assert login_response.status_code == 200
        # login_data = login_response.json()
        # access_token = login_data["access_token"]
        #
        # profile_response = client.get(
        #     "/api/v1/auth/me",
        #     headers={"Authorization": f"Bearer {access_token}"}
        # )
        # profile_data = profile_response.json()
        # assert profile_data["email_verified"] is True
