"""WebSocket routes for API v1."""

from .messages import router as messaging_websocket_router

__all__ = ["messaging_websocket_router"]
