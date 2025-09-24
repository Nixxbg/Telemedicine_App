"""Telemedicine Application Backend FastAPI entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Sequence

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import src.models  # noqa: F401
from src.api.v1.api import api_router
from src.core.config import settings
from src.core.database import create_tables, drop_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database tables exist before serving requests."""

    await drop_tables()
    await create_tables()
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return consistent 422 responses across the application."""

    details = _format_validation_errors(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "details": details,
        },
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "telemedicine-backend"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
