"""Telemedicine Application Backend FastAPI entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import src.models  # noqa: F401
from src.api.v1.api import api_router
from src.api.v1.websocket import messaging_websocket_router
from src.core.config import settings
from src.core.database import create_tables, drop_tables
from src.core.exception_handlers import setup_global_exception_handlers
from src.core.seed_data import seed_reference_data


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

# Set up global exception handlers
setup_global_exception_handlers(app)

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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "telemedicine-backend"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
