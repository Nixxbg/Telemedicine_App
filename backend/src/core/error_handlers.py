"""
Centralized error handling utilities for consistent API error responses.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.validation import MedicalDataValidationError

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for API-specific errors."""

    def __init__(
        self,
        status_code: int,
        error: str,
        message: str,
        details: Dict[str, Any] | None = None,
    ):
        self.status_code = status_code
        self.error = error
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationAPIError(APIError):
    """Error for validation failures."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: Dict[str, Any] | None = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="validation_error",
            message=message,
            details=error_details,
        )


class AuthenticationAPIError(APIError):
    """Error for authentication failures."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error="authentication_error",
            message=message,
        )


class AuthorizationAPIError(APIError):
    """Error for authorization failures."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error="authorization_error",
            message=message,
        )


class NotFoundAPIError(APIError):
    """Error for resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error="not_found",
            message=message,
        )


class ConflictAPIError(APIError):
    """Error for resource conflicts."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error="conflict",
            message=message,
        )


class BusinessRuleAPIError(APIError):
    """Error for business rule violations."""

    def __init__(self, message: str, rule: str | None = None):
        details = {"rule": rule} if rule else {}
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="business_rule_violation",
            message=message,
            details=details,
        )


def create_error_response(error: APIError) -> JSONResponse:
    """Create a standardized JSON error response."""
    content = {
        "error": error.error,
        "message": error.message,
    }

    if error.details:
        content["details"] = error.details

    return JSONResponse(
        status_code=error.status_code,
        content=content,
    )


def handle_validation_error(
    exc: ValidationError | RequestValidationError,
) -> JSONResponse:
    """Convert Pydantic validation errors to API error format."""
    errors = []

    if isinstance(exc, RequestValidationError):
        validation_errors = exc.errors()
    else:
        validation_errors = exc.errors()

    for error in validation_errors:
        field_path = ".".join(str(loc) for loc in error["loc"])
        field_name = field_path.split(".")[-1] if field_path else "unknown"

        error_detail = {
            "field": field_name,
            "message": error["msg"],
            "type": error["type"],
        }

        if "input" in error:
            error_detail["input"] = str(error["input"])[:100]  # Limit input length

        errors.append(error_detail)

    # If there's only one error, use simplified format
    if len(errors) == 1:
        error_detail = errors[0]
        return create_error_response(
            ValidationAPIError(
                message=error_detail["message"],
                field=error_detail["field"],
                details={"type": error_detail["type"]},
            )
        )

    # Multiple errors
    return create_error_response(
        ValidationAPIError(
            message="Multiple validation errors occurred",
            details={"errors": errors},
        )
    )


def handle_medical_validation_error(exc: MedicalDataValidationError) -> JSONResponse:
    """Convert medical validation errors to API error format."""
    return create_error_response(
        ValidationAPIError(
            message=exc.message,
            field=exc.field,
            details={"type": "medical_validation_error"},
        )
    )


def handle_http_exception(exc: HTTPException | StarletteHTTPException) -> JSONResponse:
    """Convert HTTP exceptions to consistent API error format."""

    # If the exception already has structured detail, use it
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )

    # Map status codes to error types
    error_type_map = {
        status.HTTP_400_BAD_REQUEST: "validation_error",
        status.HTTP_401_UNAUTHORIZED: "authentication_error",
        status.HTTP_403_FORBIDDEN: "authorization_error",
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_409_CONFLICT: "conflict",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "validation_error",
        status.HTTP_429_TOO_MANY_REQUESTS: "rate_limit_exceeded",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "server_error",
    }

    error_type = error_type_map.get(exc.status_code, "request_error")
    message = str(exc.detail) if exc.detail else "An error occurred"

    return create_error_response(
        APIError(
            status_code=exc.status_code,
            error=error_type,
            message=message,
        )
    )


def log_error(request: Request, error: Exception, user_id: str | None = None) -> None:
    """Log errors with context information."""

    context = {
        "method": request.method,
        "url": str(request.url),
        "user_agent": request.headers.get("user-agent"),
    }

    if user_id:
        context["user_id"] = user_id

    if hasattr(request, "state") and hasattr(request.state, "request_id"):
        context["request_id"] = request.state.request_id

    logger.error(
        f"API Error: {type(error).__name__}: {str(error)}",
        extra=context,
        exc_info=True,
    )


def sanitize_error_message_for_user(message: str, is_production: bool = True) -> str:
    """Sanitize error messages to prevent information leakage in production."""

    if not is_production:
        return message

    # In production, hide potentially sensitive error details
    sensitive_keywords = [
        "database",
        "sql",
        "connection",
        "password",
        "token",
        "key",
        "secret",
        "internal",
        "system",
    ]

    message_lower = message.lower()
    for keyword in sensitive_keywords:
        if keyword in message_lower:
            return "An internal error occurred. Please try again later."

    return message


class RateLimitAPIError(APIError):
    """Error for rate limiting violations."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error="rate_limit_exceeded",
            message=message,
            details=details,
        )


def create_validation_error_from_dict(
    errors: Dict[str, List[str]],
) -> ValidationAPIError:
    """Create a validation error from a dictionary of field errors."""

    if len(errors) == 1:
        field, messages = next(iter(errors.items()))
        return ValidationAPIError(
            message=messages[0],
            field=field,
            details={"messages": messages} if len(messages) > 1 else {},
        )

    # Multiple field errors
    error_details = []
    for field, messages in errors.items():
        for message in messages:
            error_details.append(
                {
                    "field": field,
                    "message": message,
                }
            )

    return ValidationAPIError(
        message="Multiple validation errors occurred",
        details={"errors": error_details},
    )


def get_error_context_from_request(request: Request) -> Dict[str, Any]:
    """Extract relevant context from the request for error logging."""

    context = {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
    }

    # Add user context if available
    if hasattr(request.state, "user"):
        context["user_id"] = str(request.state.user.id)
        context["user_type"] = request.state.user.user_type.value

    # Add request ID if available
    if hasattr(request.state, "request_id"):
        context["request_id"] = request.state.request_id

    return context
