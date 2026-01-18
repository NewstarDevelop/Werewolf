"""
UserConnectionManager for /ws/notifications.

This is intentionally separate from backend/app/services/websocket_manager.py:
- websocket_manager.py is game/room scoped (game_id, player_id)
- notifications are user scoped (user_id), and may have multiple connections per user
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import DefaultDict, Set, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class UserConnectionManager:
    """Manage WebSocket connections keyed by user_id."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._connections: DefaultDict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: str, websocket: WebSocket, subprotocol: Optional[str] = None) -> None:
        """
        Accept WebSocket and bind to user_id.

        subprotocol:
        - When client uses Sec-WebSocket-Protocol: auth, <token>
          server should accept 'auth' to confirm.
        """
        await websocket.accept(subprotocol=subprotocol)
        async with self._lock:
            self._connections[user_id].add(websocket)
        logger.info(f"[notifications] user {user_id} connected (conns={self.get_connection_count(user_id)})")

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from a user."""
        async with self._lock:
            if user_id in self._connections:
                self._connections[user_id].discard(websocket)
                if not self._connections[user_id]:
                    del self._connections[user_id]
        logger.info(f"[notifications] user {user_id} disconnected (conns={self.get_connection_count(user_id)})")

    async def send_to_user(self, user_id: str, message_type: str, data: dict) -> None:
        """
        Send a message to all active connections of a user.

        Message envelope is consistent with existing WebSocket style:
        { "type": "<message_type>", "data": { ... } }
        """
        async with self._lock:
            sockets = list(self._connections.get(user_id, set()))

        if not sockets:
            return

        for ws in sockets:
            try:
                await ws.send_json({"type": message_type, "data": data})
            except Exception as e:
                logger.warning(f"[notifications] send failed user={user_id}: {e}")
                try:
                    await ws.close(code=1011)
                except Exception:
                    pass
                await self.disconnect(user_id, ws)

    def get_connection_count(self, user_id: str) -> int:
        """Return current active connection count for a user."""
        return len(self._connections.get(user_id, set()))
