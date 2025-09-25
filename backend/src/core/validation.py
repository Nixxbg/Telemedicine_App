"""
Enhanced validation utilities for medical data and input sanitization.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any, Dict

from pydantic import BaseModel, model_validator


class MedicalDataValidationError(Exception):
    """Custom exception for medical data validation errors."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def sanitize_medical_text(text: str) -> str:
    """Sanitize medical record text input to prevent XSS and ensure formatting."""
    if not text:
        return text

    # First, remove HTML/XML tags to prevent XSS
    tag_pattern = r"<[^>]*>"
    sanitized = re.sub(tag_pattern, "", text)

    # Remove script content between script tags (in case tags were malformed)
    script_pattern = r"(?i)script.*?/script"
    sanitized = re.sub(script_pattern, "", sanitized)

    # Remove potentially dangerous characters but preserve medical notation
    # Allow: letters, numbers, spaces, basic punctuation, medical symbols
    # Note: < and > are allowed for medical comparisons like "<100mg" or ">normal"
    allowed_pattern = r"[^a-zA-Z0-9\s\.,;:\-\(\)\[\]\/\%\+\*\=\<\>\&\#\@\!\?\'\"°µμ]"
    sanitized = re.sub(allowed_pattern, "", sanitized)

    # Normalize whitespace
    sanitized = " ".join(sanitized.split())

    return sanitized.strip()


def validate_age_appropriate_data(age_years: int, data: Dict[str, Any]) -> None:
    """Validate that medical record data is appropriate for patient's age."""

    # Pediatric validations (under 18)
    if age_years < 18:
        # Check for adult-only medications or procedures
        adult_only_keywords = [
            "birth control",
            "contraceptive",
            "viagra",
            "cialis",
            "hormone replacement",
            "colonoscopy",
            "mammogram",
        ]
        data_str = str(data).lower()
        for keyword in adult_only_keywords:
            if keyword in data_str:
                raise MedicalDataValidationError(
                    "data", f"Medical record contains adult-only content: {keyword}"
                )

    # Geriatric considerations (over 65)
    elif age_years > 65:
        # Could add geriatric-specific validations here
        pass


def validate_medical_measurement(value: str, measurement_type: str) -> bool:
    """Validate medical measurements like blood pressure, weight, height, etc."""

    if not value or not isinstance(value, str):
        return False

    value = value.strip().lower()

    patterns = {
        "blood_pressure": r"^\d{2,3}\/\d{2,3}(\s*mmhg)?$",
        "weight": r"^\d{1,3}(\.\d{1,2})?\s*(kg|lbs?|pounds?)$",
        "height": r"^(\d{1,2}\'?\s*\d{1,2}\"?|\d{2,3}\s*cm|\d{1,2}\.\d{1,2}\s*m)$",
        "temperature": r"^\d{2,3}(\.\d{1,2})?\s*[°]?[fcF]?$",
        "heart_rate": r"^\d{2,3}\s*(bpm|beats?\s*per\s*minute?)?$",
        "dosage": (
            r"^\d{1,4}(\.\d{1,2})?\s*(mg|g|ml|mcg|units?|iu)"
            r"(\s*\/\s*(day|daily|bid|tid|qid|qhs|prn))?$"
        ),
    }

    pattern = patterns.get(measurement_type)
    if not pattern:
        return True  # Unknown type, assume valid

    return bool(re.match(pattern, value, re.IGNORECASE))


def validate_appointment_time_slot(start: datetime, end: datetime) -> None:
    """Validate appointment scheduling constraints."""

    now = datetime.now(timezone.utc)

    # Must be in the future
    if start <= now:
        raise MedicalDataValidationError(
            "scheduled_start", "Appointment must be scheduled in the future"
        )

    # End must be after start
    if end <= start:
        raise MedicalDataValidationError(
            "scheduled_end", "Appointment end time must be after start time"
        )

    # Duration limits (15 minutes to 4 hours)
    duration_minutes = (end - start).total_seconds() / 60
    if duration_minutes < 15:
        raise MedicalDataValidationError(
            "duration", "Appointment must be at least 15 minutes long"
        )
    if duration_minutes > 240:  # 4 hours
        raise MedicalDataValidationError(
            "duration", "Appointment cannot exceed 4 hours"
        )

    # Business hours check (8 AM to 8 PM)
    start_hour = start.hour
    end_hour = end.hour
    if start_hour < 8 or start_hour > 20 or end_hour < 8 or end_hour > 20:
        raise MedicalDataValidationError(
            "business_hours",
            "Appointments must be scheduled between 8:00 AM and 8:00 PM",
        )

    # No weekend appointments for now (can be configured later)
    if start.weekday() >= 5:  # Saturday = 5, Sunday = 6
        raise MedicalDataValidationError(
            "weekday", "Weekend appointments are not currently available"
        )


def calculate_age_in_years(birth_date: date, reference_date: date | None = None) -> int:
    """Calculate age in years from birth date."""
    if reference_date is None:
        reference_date = date.today()

    age = reference_date.year - birth_date.year
    if reference_date.month < birth_date.month or (
        reference_date.month == birth_date.month and reference_date.day < birth_date.day
    ):
        age -= 1

    return age


def validate_emergency_contact(
    contact_name: str | None, contact_phone: str | None
) -> None:
    """Validate emergency contact information consistency."""

    # If one is provided, both should be provided
    if bool(contact_name) != bool(contact_phone):
        raise MedicalDataValidationError(
            "emergency_contact",
            "Both emergency contact name and phone number must be provided together",
        )


def validate_message_content_safety(content: str) -> str:
    """Validate and sanitize message content for safety and appropriateness."""

    if not content or not content.strip():
        raise MedicalDataValidationError("content", "Message content cannot be empty")

    content = content.strip()

    # Check length
    if len(content) > 2000:
        raise MedicalDataValidationError(
            "content", f"Message content too long: {len(content)} characters (max 2000)"
        )

    # Check for potential security issues
    suspicious_patterns = [
        r"<script[^>]*>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"<iframe[^>]*>",
    ]

    content_lower = content.lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, content_lower):
            raise MedicalDataValidationError(
                "content", "Message content contains potentially unsafe elements"
            )

    return content


def validate_medical_record_data_structure(
    record_type: str, data: Dict[str, Any]
) -> None:
    """Validate that medical record data has the correct structure for its type."""

    required_fields = {
        "medication": ["name", "dosage", "frequency"],
        "allergy": ["allergen", "reaction", "severity"],
        "procedure": ["name", "date", "provider"],
        "lab_result": ["test_name", "value", "reference_range", "date"],
        "vital_signs": ["measurement_type", "value", "date"],
        "diagnosis": ["condition", "date_diagnosed", "icd_code"],
        "immunization": ["vaccine", "date_administered", "provider"],
        "family_history": ["relation", "condition", "age_at_diagnosis"],
    }

    if record_type in required_fields:
        missing_fields = []
        for field in required_fields[record_type]:
            if field not in data or not data[field]:
                missing_fields.append(field)

        if missing_fields:
            missing_str = ", ".join(missing_fields)
            raise MedicalDataValidationError(
                "data", f"Missing required fields for {record_type}: {missing_str}"
            )

    # Validate specific field formats
    if record_type == "medication" and "dosage" in data:
        if not validate_medical_measurement(str(data["dosage"]), "dosage"):
            raise MedicalDataValidationError(
                "data.dosage", "Invalid medication dosage format"
            )

    if record_type == "vital_signs":
        measurement_type = data.get("measurement_type", "").lower()
        value = str(data.get("value", ""))
        if not validate_medical_measurement(value, measurement_type):
            raise MedicalDataValidationError(
                "data.value", f"Invalid format for {measurement_type} measurement"
            )


class EnhancedValidationMixin(BaseModel):
    """Mixin class to add enhanced validation capabilities to Pydantic models."""

    @model_validator(mode="after")
    def validate_model_integrity(self) -> "EnhancedValidationMixin":
        """Perform cross-field validation and business rule checks."""
        return self

    def sanitize_text_fields(self) -> None:
        """Sanitize all string fields in the model."""
        for field_name, field_info in self.model_fields.items():
            value = getattr(self, field_name)
            if isinstance(value, str):
                sanitized = sanitize_medical_text(value)
                setattr(self, field_name, sanitized)
