"""Connection manager for messaging WebSocket sessions."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, DefaultDict
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manage active WebSocket connections grouped by user."""

    def __init__(self) -> None:
        self._connections: DefaultDict[UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: UUID, websocket: WebSocket) -> None:
        """Register a connected WebSocket for the given user."""

        async with self._lock:
            self._connections[user_id].add(websocket)

    async def disconnect(self, user_id: UUID, websocket: WebSocket) -> None:
        """Remove a WebSocket from the active connection list."""

        async with self._lock:
            sockets = self._connections.get(user_id)
            if not sockets:
                return
            sockets.discard(websocket)
            if not sockets:
                self._connections.pop(user_id, None)

    async def broadcast_to_user(self, user_id: UUID, message: dict[str, Any]) -> None:
        """Send a JSON message to all active sockets for the given user."""

        async with self._lock:
            sockets = list(self._connections.get(user_id, set()))

        if not sockets:
            return

        to_remove: list[WebSocket] = []
        for socket in sockets:
            try:
                await socket.send_json(message)
            except (RuntimeError, WebSocketDisconnect):
                to_remove.append(socket)

        if to_remove:
            async with self._lock:
                remaining = self._connections.get(user_id)
                if not remaining:
                    return
                for socket in to_remove:
                    remaining.discard(socket)
                if not remaining:
                    self._connections.pop(user_id, None)

    async def broadcast_except(
        self,
        user_id: UUID,
        message: dict[str, Any],
        *,
        exclude: WebSocket | None = None,
    ) -> None:
        """Broadcast a message to a user's sockets, optionally excluding one."""

        async with self._lock:
            sockets = list(self._connections.get(user_id, set()))

        if not sockets:
            return

        for socket in sockets:
            if exclude is not None and socket is exclude:
                continue
            try:
                await socket.send_json(message)
            except (RuntimeError, WebSocketDisconnect):
                continue


connection_manager = ConnectionManager()
