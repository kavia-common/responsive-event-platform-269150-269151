from __future__ import annotations

import asyncio
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    """Tracks active WebSocket connections and room subscriptions."""

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._rooms: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a websocket."""
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a websocket and any room memberships."""
        async with self._lock:
            self._connections.discard(websocket)
            for members in self._rooms.values():
                members.discard(websocket)

    async def join_room(self, room_id: str, websocket: WebSocket) -> None:
        """Subscribe websocket to a room."""
        async with self._lock:
            self._rooms.setdefault(room_id, set()).add(websocket)

    async def broadcast(self, message_text: str) -> None:
        """Send message to all active connections."""
        async with self._lock:
            conns = list(self._connections)
        for ws in conns:
            try:
                await ws.send_text(message_text)
            except Exception:
                # best-effort; connection cleanup happens on disconnect
                pass

    async def broadcast_room(self, room_id: str, message_text: str) -> None:
        """Send message to all connections in a specific room."""
        async with self._lock:
            conns = list(self._rooms.get(room_id, set()))
        for ws in conns:
            try:
                await ws.send_text(message_text)
            except Exception:
                pass
