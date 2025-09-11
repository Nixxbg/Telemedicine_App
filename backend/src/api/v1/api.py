"""
Main API router for version 1 endpoints
"""

from fastapi import APIRouter

from src.api.v1.endpoints import appointments, auth, medical_records, messages

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(
    medical_records.router, prefix="/medical-records", tags=["medical-records"]
)
api_router.include_router(
    appointments.router, prefix="/appointments", tags=["appointments"]
)
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
