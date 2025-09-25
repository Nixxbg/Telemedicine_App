"""
Global exception handlers for the FastAPI application.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.error_handlers import (
    MedicalDataValidationError,
    handle_http_exception,
    handle_medical_validation_error,
    handle_validation_error,
    log_error,
)


def setup_global_exception_handlers(app: FastAPI) -> None:
    """Set up global exception handlers for the FastAPI application."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors from request parsing."""
        log_error(request, exc)
        return handle_validation_error(exc)

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors from schema validation."""
        log_error(request, exc)
        return handle_validation_error(exc)

    @app.exception_handler(MedicalDataValidationError)
    async def medical_validation_exception_handler(
        request: Request, exc: MedicalDataValidationError
    ) -> JSONResponse:
        """Handle medical data validation errors."""
        log_error(request, exc)
        return handle_medical_validation_error(exc)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions with consistent format."""
        log_error(request, exc)
        return handle_http_exception(exc)

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle any unhandled exceptions."""
        log_error(request, exc)

        # In production, don't expose internal error details
        return JSONResponse(
            status_code=500,
            content={
                "error": "server_error",
                "message": "An internal server error occurred",
            },
        )
