"""Telemedicine Application Backend FastAPI entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Sequence

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import src.models  # noqa: F401
from src.api.v1.api import api_router
from src.api.v1.websocket import messaging_websocket_router
from src.core.config import settings
from src.core.database import create_tables, drop_tables
from src.core.seed_data import seed_reference_data

ERROR_DEFAULTS: dict[int, tuple[str, str]] = {
    status.HTTP_400_BAD_REQUEST: ("validation_error", "Invalid request"),
    status.HTTP_401_UNAUTHORIZED: ("authentication_error", "Authentication required"),
    status.HTTP_403_FORBIDDEN: ("authorization_error", "Access denied"),
    status.HTTP_404_NOT_FOUND: ("not_found", "Resource not found"),
    status.HTTP_409_CONFLICT: ("scheduling_conflict", "Scheduling conflict detected"),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database tables exist before serving requests."""

    await drop_tables()
    await create_tables()
    await seed_reference_data()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Telemedicine platform for patient-doctor consultations",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(messaging_websocket_router)


def _format_validation_errors(errors: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    """Convert FastAPI validation errors into contract-compliant details."""

    formatted: list[dict[str, str]] = []
    for error in errors:
        location = [str(loc) for loc in error.get("loc", []) if loc != "body"]
        if not location:
            loc = error.get("loc", [])
            if len(loc) > 1 and loc[0] == "body":
                location = [str(loc[1])]

        field = ".".join(location) if location else "body"
        formatted.append(
            {
                "field": field,
                "message": error.get("msg", "Invalid value"),
                "code": error.get("type", "value_error"),
            }
        )

    return formatted


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Convert :class:`HTTPException` payloads into contract-compliant responses."""

    detail_payload: dict[str, Any]
    text_detail = ""
    if isinstance(exc.detail, dict):
        detail_payload = {**exc.detail}
    else:
        detail_payload = {}
        if exc.detail is not None:
            text_detail = str(exc.detail)

    is_server_error = exc.status_code >= 500
    fallback_error = "server_error" if is_server_error else "request_error"
    fallback_message = (
        "Internal server error" if is_server_error else "Request could not be processed"
    )
    default_error, default_message = ERROR_DEFAULTS.get(
        exc.status_code,
        (fallback_error, fallback_message),
    )

    detail_payload.setdefault("error", default_error)
    message = detail_payload.get("message")
    if not message:
        message = text_detail or default_message
        detail_payload["message"] = message

    headers = exc.headers if exc.headers else None
    return JSONResponse(
        status_code=exc.status_code,
        content=detail_payload,
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return consistent 422 responses across the application."""

    details = _format_validation_errors(exc.errors())
    content = {
        "error": "validation_error",
        "message": "Request validation failed",
        "details": details,
        "detail": details,
    }
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content,
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "telemedicine-backend"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
