"""
Integration tests for appointment booking flow

These tests validate the complete appointment booking workflow,
including appointment creation, availability checking, booking
confirmation, and status management. Integration tests verify
the full end-to-end functionality rather than individual API contracts.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


class TestAppointmentBookingFlow:
    """Integration tests for complete appointment booking workflow"""

    @pytest.fixture
    def patient_auth_token(self):
        """Mock patient authentication token"""
        # TODO: Once auth is implemented, replace with actual login
        return "mock_patient_token_123"

    @pytest.fixture
    def doctor_auth_token(self):
        """Mock doctor authentication token"""
        # TODO: Once auth is implemented, replace with actual login
        return "mock_doctor_token_456"

    @pytest.fixture
    def doctor_id(self):
        """Mock doctor ID for appointment booking"""
        return "123e4567-e89b-12d3-a456-426614174001"

    @pytest.fixture
    def future_appointment_data(self, doctor_id):
        """Valid appointment booking data for future date"""
        future_date = datetime.now() + timedelta(days=7)
        start_time = future_date.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=30)

        return {
            "doctor_id": doctor_id,
            "scheduled_start": start_time.isoformat() + "Z",
            "scheduled_end": end_time.isoformat() + "Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Regular check-up and blood pressure monitoring",
        }

    @pytest.fixture
    def follow_up_appointment_data(self, doctor_id):
        """Follow-up appointment booking data"""
        future_date = datetime.now() + timedelta(days=14)
        start_time = future_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=30)

        return {
            "doctor_id": doctor_id,
            "scheduled_start": start_time.isoformat() + "Z",
            "scheduled_end": end_time.isoformat() + "Z",
            "appointment_type": "follow_up",
            "reason_for_visit": "Follow-up on blood pressure medication",
        }

    async def test_complete_appointment_booking_workflow(
        self, patient_auth_token, doctor_auth_token, future_appointment_data, doctor_id
    ):
        """
        Integration Test: Complete appointment booking workflow

        This test validates the entire appointment booking process:
        1. Check doctor availability
        2. Book appointment as patient
        3. Verify booking confirmation
        4. Doctor can see the appointment
        5. Patient can see the appointment in their list

        Expected: Full booking workflow completes successfully
        """
        patient_headers = {"Authorization": f"Bearer {patient_auth_token}"}
        doctor_headers = {"Authorization": f"Bearer {doctor_auth_token}"}

        # Step 1: Check doctor availability
        availability_response = client.get(
            f"/api/v1/doctors/{doctor_id}/availability", headers=patient_headers
        )

        # Should fail initially (TDD - no implementation yet)
        assert availability_response.status_code == 404

        # TODO: Once implemented, verify:
        # assert availability_response.status_code == 200
        # availability_data = availability_response.json()
        # assert "available_slots" in availability_data
        #
        # # Step 2: Book appointment
        # booking_response = client.post(
        #     "/api/v1/appointments",
        #     json=future_appointment_data,
        #     headers=patient_headers
        # )
        # assert booking_response.status_code == 201
        # booking_data = booking_response.json()
        # appointment_id = booking_data["id"]
        # assert booking_data["status"] == "scheduled"
        # assert booking_data["doctor_id"] == doctor_id
        #
        # # Step 3: Verify patient can see appointment
        # patient_appointments_response = client.get(
        #     "/api/v1/appointments",
        #     headers=patient_headers
        # )
        # assert patient_appointments_response.status_code == 200
        # patient_appointments = patient_appointments_response.json()
        # assert len(patient_appointments["appointments"]) >= 1
        #
        # booked_appointment = next(
        #     apt for apt in patient_appointments["appointments"]
        #     if apt["id"] == appointment_id
        # )
        # assert booked_appointment["status"] == "scheduled"
        #
        # # Step 4: Verify doctor can see appointment
        # doctor_appointments_response = client.get(
        #     "/api/v1/appointments",
        #     headers=doctor_headers
        # )
        # assert doctor_appointments_response.status_code == 200
        # doctor_appointments = doctor_appointments_response.json()
        #
        # doctor_appointment = next(
        #     apt for apt in doctor_appointments["appointments"]
        #     if apt["id"] == appointment_id
        # )
        # assert doctor_appointment["patient_id"] is not None

    async def test_appointment_booking_double_booking_prevention(
        self, patient_auth_token, future_appointment_data
    ):
        """
        Integration Test: Double booking prevention

        Tests that the system prevents double booking of the same
        time slot for a doctor.
        """
        headers = {"Authorization": f"Bearer {patient_auth_token}"}

        # First booking attempt
        first_booking_response = client.post(
            "/api/v1/appointments", json=future_appointment_data, headers=headers
        )

        # Should fail initially (TDD)
        assert first_booking_response.status_code == 404

        # TODO: Once implemented:
        # assert first_booking_response.status_code == 201
        #
        # # Second booking attempt for same time slot
        # second_booking_response = client.post(
        #     "/api/v1/appointments",
        #     json=future_appointment_data,
        #     headers=headers
        # )
        # assert second_booking_response.status_code == 409  # Conflict
        # error_data = second_booking_response.json()
        # assert "time slot" in error_data["message"].lower()

    async def test_appointment_booking_past_date_validation(
        self, patient_auth_token, doctor_id
    ):
        """
        Integration Test: Past date booking validation

        Tests that appointments cannot be booked for past dates.
        """
        headers = {"Authorization": f"Bearer {patient_auth_token}"}

        # Create appointment data for past date
        past_date = datetime.now() - timedelta(days=1)
        start_time = past_date.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=30)

        past_appointment_data = {
            "doctor_id": doctor_id,
            "scheduled_start": start_time.isoformat() + "Z",
            "scheduled_end": end_time.isoformat() + "Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Past date test",
        }

        response = client.post(
            "/api/v1/appointments", json=past_appointment_data, headers=headers
        )

        # Should fail initially (TDD)
        assert response.status_code == 404

        # TODO: Once implemented:
        # assert response.status_code == 422  # Validation error
        # error_data = response.json()
        # assert "past" in error_data["message"].lower()

    async def test_appointment_booking_outside_business_hours(
        self, patient_auth_token, doctor_id
    ):
        """
        Integration Test: Business hours validation

        Tests that appointments can only be booked during
        doctor's available business hours.
        """
        headers = {"Authorization": f"Bearer {patient_auth_token}"}

        # Create appointment data for late night (outside business hours)
        future_date = datetime.now() + timedelta(days=7)
        start_time = future_date.replace(hour=23, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=30)

        late_night_appointment = {
            "doctor_id": doctor_id,
            "scheduled_start": start_time.isoformat() + "Z",
            "scheduled_end": end_time.isoformat() + "Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Late night test",
        }

        response = client.post(
            "/api/v1/appointments", json=late_night_appointment, headers=headers
        )

        # Should fail initially (TDD)
        assert response.status_code == 404

        # TODO: Once implemented:
        # assert response.status_code == 422  # Validation error
        # error_data = response.json()
        # assert "business hours" in error_data["message"].lower()

    async def test_appointment_cancellation_workflow(
        self, patient_auth_token, doctor_auth_token, future_appointment_data
    ):
        """
        Integration Test: Appointment cancellation workflow

        Tests the complete appointment cancellation process
        including notifications and status updates.
        """
        patient_headers = {"Authorization": f"Bearer {patient_auth_token}"}
        # doctor_headers = {"Authorization": f"Bearer {doctor_auth_token}"}

        # Book appointment first
        booking_response = client.post(
            "/api/v1/appointments",
            json=future_appointment_data,
            headers=patient_headers,
        )

        # Should fail initially (TDD)
        assert booking_response.status_code == 404

        # TODO: Once implemented:
        # assert booking_response.status_code == 201
        # booking_data = booking_response.json()
        # appointment_id = booking_data["id"]
        #
        # # Cancel appointment
        # cancel_response = client.put(
        #     f"/api/v1/appointments/{appointment_id}/cancel",
        #     json={"cancellation_reason": "Personal emergency"},
        #     headers=patient_headers
        # )
        # assert cancel_response.status_code == 200
        # cancel_data = cancel_response.json()
        # assert cancel_data["status"] == "cancelled"
        #
        # # Verify doctor can see cancellation
        # doctor_appointments_response = client.get(
        #     "/api/v1/appointments",
        #     headers=doctor_headers
        # )
        # doctor_appointments = doctor_appointments_response.json()
        # cancelled_appointment = next(
        #     apt for apt in doctor_appointments["appointments"]
        #     if apt["id"] == appointment_id
        # )
        # assert cancelled_appointment["status"] == "cancelled"

    async def test_appointment_reschedule_workflow(
        self, patient_auth_token, future_appointment_data, doctor_id
    ):
        """
        Integration Test: Appointment reschedule workflow

        Tests the complete appointment rescheduling process
        including availability checking and confirmation.
        """
        headers = {"Authorization": f"Bearer {patient_auth_token}"}

        # Book initial appointment
        booking_response = client.post(
            "/api/v1/appointments", json=future_appointment_data, headers=headers
        )

        # Should fail initially (TDD)
        assert booking_response.status_code == 404

        # TODO: Once implemented:
        # assert booking_response.status_code == 201
        # booking_data = booking_response.json()
        # appointment_id = booking_data["id"]
        #
        # # Reschedule to new time
        # new_date = datetime.now() + timedelta(days=10)
        # new_start_time = new_date.replace(hour=15, minute=0, second=0,
        #                                  microsecond=0)
        # new_end_time = new_start_time + timedelta(minutes=30)
        #
        # reschedule_data = {
        #     "scheduled_start": new_start_time.isoformat() + "Z",
        #     "scheduled_end": new_end_time.isoformat() + "Z",
        #     "reason": "Scheduling conflict resolved"
        # }
        #
        # reschedule_response = client.put(
        #     f"/api/v1/appointments/{appointment_id}",
        #     json=reschedule_data,
        #     headers=headers
        # )
        # assert reschedule_response.status_code == 200
        # reschedule_data = reschedule_response.json()
        # assert reschedule_data["scheduled_start"] == new_start_time.isoformat() + "Z"

    async def test_appointment_status_progression_workflow(
        self, patient_auth_token, doctor_auth_token, future_appointment_data
    ):
        """
        Integration Test: Appointment status progression

        Tests the complete appointment lifecycle from booking
        to completion with proper status transitions.
        """
        patient_headers = {"Authorization": f"Bearer {patient_auth_token}"}
        # doctor_headers = {"Authorization": f"Bearer {doctor_auth_token}"}

        # Book appointment
        booking_response = client.post(
            "/api/v1/appointments",
            json=future_appointment_data,
            headers=patient_headers,
        )

        # Should fail initially (TDD)
        assert booking_response.status_code == 404

        # TODO: Once implemented:
        # assert booking_response.status_code == 201
        # booking_data = booking_response.json()
        # appointment_id = booking_data["id"]
        # assert booking_data["status"] == "scheduled"
        #
        # # Doctor starts appointment
        # start_response = client.put(
        #     f"/api/v1/appointments/{appointment_id}",
        #     json={"status": "in_progress"},
        #     headers=doctor_headers
        # )
        # assert start_response.status_code == 200
        # start_data = start_response.json()
        # assert start_data["status"] == "in_progress"
        #
        # # Doctor completes appointment
        # complete_response = client.put(
        #     f"/api/v1/appointments/{appointment_id}",
        #     json={
        #         "status": "completed",
        #         "consultation_notes": "Patient doing well, continue medication"
        #     },
        #     headers=doctor_headers
        # )
        # assert complete_response.status_code == 200
        # complete_data = complete_response.json()
        # assert complete_data["status"] == "completed"

    async def test_multiple_appointments_booking_workflow(
        self, patient_auth_token, future_appointment_data, follow_up_appointment_data
    ):
        """
        Integration Test: Multiple appointments booking

        Tests booking multiple appointments for the same patient
        with different doctors and time slots.
        """
        headers = {"Authorization": f"Bearer {patient_auth_token}"}

        # Book first appointment
        first_booking_response = client.post(
            "/api/v1/appointments", json=future_appointment_data, headers=headers
        )

        # Book second appointment
        second_booking_response = client.post(
            "/api/v1/appointments", json=follow_up_appointment_data, headers=headers
        )

        # Should fail initially (TDD)
        assert first_booking_response.status_code == 404
        assert second_booking_response.status_code == 404

        # TODO: Once implemented:
        # assert first_booking_response.status_code == 201
        # assert second_booking_response.status_code == 201
        #
        # first_data = first_booking_response.json()
        # second_data = second_booking_response.json()
        #
        # # Verify both appointments exist
        # appointments_response = client.get(
        #     "/api/v1/appointments",
        #     headers=headers
        # )
        # appointments_data = appointments_response.json()
        # assert len(appointments_data["appointments"]) >= 2
        #
        # appointment_ids = [apt["id"] for apt in appointments_data["appointments"]]
        # assert first_data["id"] in appointment_ids
        # assert second_data["id"] in appointment_ids

    async def test_appointment_booking_with_preferences(
        self, patient_auth_token, doctor_id
    ):
        """
        Integration Test: Appointment booking with patient preferences

        Tests booking appointments with specific patient preferences
        like appointment type, duration, and special requirements.
        """
        headers = {"Authorization": f"Bearer {patient_auth_token}"}

        # Book appointment with preferences
        future_date = datetime.now() + timedelta(days=7)
        start_time = future_date.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=45)  # Longer appointment

        preference_appointment_data = {
            "doctor_id": doctor_id,
            "scheduled_start": start_time.isoformat() + "Z",
            "scheduled_end": end_time.isoformat() + "Z",
            "appointment_type": "consultation",
            "reason_for_visit": "Comprehensive health review",
            "special_requirements": [
                "Wheelchair accessible room",
                "Language interpreter needed",
            ],
            "preferred_communication": "video_call",
        }

        response = client.post(
            "/api/v1/appointments", json=preference_appointment_data, headers=headers
        )

        # Should fail initially (TDD)
        assert response.status_code == 404

        # TODO: Once implemented:
        # assert response.status_code == 201
        # booking_data = response.json()
        # assert booking_data["special_requirements"] is not None
        # assert "Wheelchair accessible" in booking_data["special_requirements"]

    async def test_appointment_booking_notification_workflow(
        self, patient_auth_token, doctor_auth_token, future_appointment_data
    ):
        """
        Integration Test: Appointment booking notifications

        Tests that proper notifications are sent to both patient
        and doctor when appointments are booked, modified, or cancelled.
        """
        patient_headers = {"Authorization": f"Bearer {patient_auth_token}"}
        # doctor_headers = {"Authorization": f"Bearer {doctor_auth_token}"}

        # Mock notification service
        # TODO: Once notification service is implemented

        # Book appointment
        booking_response = client.post(
            "/api/v1/appointments",
            json=future_appointment_data,
            headers=patient_headers,
        )

        # Should fail initially (TDD)
        assert booking_response.status_code == 404

        # TODO: Once implemented:
        # assert booking_response.status_code == 201
        #
        # # Verify notifications were sent
        # # This would typically involve checking a notification service
        # # or database for notification records
        # notifications_response = client.get(
        #     "/api/v1/notifications",
        #     headers=patient_headers
        # )
        # notifications_data = notifications_response.json()
        #
        # # Should have booking confirmation notification
        # booking_notifications = [
        #     n for n in notifications_data["notifications"]
        #     if (
        #         "appointment" in n["message"].lower()
        #         and "booked" in n["message"].lower()
        #     )
        # ]
        # assert len(booking_notifications) >= 1

    async def test_appointment_booking_calendar_integration(
        self, patient_auth_token, future_appointment_data
    ):
        """
        Integration Test: Calendar integration workflow

        Tests that booked appointments can be exported to
        calendar formats and integrated with external calendars.
        """
        headers = {"Authorization": f"Bearer {patient_auth_token}"}

        # Book appointment
        booking_response = client.post(
            "/api/v1/appointments", json=future_appointment_data, headers=headers
        )

        # Should fail initially (TDD)
        assert booking_response.status_code == 404

        # TODO: Once implemented:
        # assert booking_response.status_code == 201
        # booking_data = booking_response.json()
        # appointment_id = booking_data["id"]
        #
        # # Request calendar export
        # calendar_response = client.get(
        #     f"/api/v1/appointments/{appointment_id}/calendar",
        #     headers=headers
        # )
        # assert calendar_response.status_code == 200
        #
        # # Verify calendar format (iCal)
        # calendar_content = calendar_response.text
        # assert "BEGIN:VCALENDAR" in calendar_content
        # assert "BEGIN:VEVENT" in calendar_content
        # assert future_appointment_data["reason_for_visit"] in calendar_content
