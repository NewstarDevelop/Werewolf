"""
WebSocket endpoint: /ws/notifications

Auth:
- Uses Sec-WebSocket-Protocol: auth, <jwt_token> (same as /ws/game/{game_id})
- Requires JWT payload contains user_id (logged-in user)

Delivery:
- Per-instance user connection manager delivers messages to connected clients.
- Cross-instance routing relies on Redis Pub/Sub subscriber (best-effort bootstrap here).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional, List, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.auth import verify_player_token
from app.core.database import SessionLocal
from app.models.user import User
from app.services.notification_connection_manager import UserConnectionManager
from app.services.redis_pubsub import create_redis_client, RedisSubscriber
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter()

user_connection_manager = UserConnectionManager()

_redis_task: Optional[asyncio.Task] = None


def _extract_token_from_subprotocols(subprotocols: List[str]) -> Optional[str]:
    """
    Extract JWT token from Sec-WebSocket-Protocol header.

    Client sends: Sec-WebSocket-Protocol: auth, <jwt_token>
    """
    if not subprotocols or len(subprotocols) < 2:
        return None
    return subprotocols[1] if subprotocols[0] == "auth" else None


async def _ensure_redis_subscription_started() -> None:
    """
    Start a per-process Redis subscription task (lazy).

    This keeps changes self-contained without requiring edits in app startup hooks.
    In production, you may prefer explicit startup wiring in app.main.py.
    """
    global _redis_task
    if _redis_task and not _redis_task.done():
        return

    client = await create_redis_client()
    if not client:
        return

    subscriber = RedisSubscriber(client)

    async def handler(message: dict[str, Any]) -> None:
        """
        Route by user_id and forward to WebSocket.

        Expected message format (see schemas.notification.PubSubMessage):
        {
          "version": 1,
          "user_id": "...",
          "message_type": "notification",
          "data": { ... }
        }
        """
        try:
            user_id = str(message.get("user_id") or "")
            message_type = str(message.get("message_type") or "")
            data = message.get("data")
            if not user_id or not message_type or not isinstance(data, dict):
                return
            await user_connection_manager.send_to_user(user_id, message_type, data)
        except Exception as e:
            logger.warning(f"[notifications] redis handler failed: {e}")

    _redis_task = asyncio.create_task(subscriber.run("notifications", handler))
    logger.info("[notifications] redis subscription task started")


@router.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket):
    """
    User-level notification WebSocket.

    Message envelope:
    {
      "type": "connected" | "notification" | "error" | "pong",
      "data": { ... }
    }
    """
    async def _reject(reason: str) -> None:
        try:
            await websocket.accept()
        except Exception:
            pass
        await websocket.close(code=1008, reason=reason)

    subprotocols = websocket.scope.get("subprotocols", [])
    auth_token = _extract_token_from_subprotocols(subprotocols)

    if not auth_token:
        await _reject("Authentication required: provide token via Sec-WebSocket-Protocol")
        return

    try:
        payload = verify_player_token(auth_token)
    except Exception as e:
        logger.error(f"[notifications] websocket auth failed: {e}")
        await _reject("Authentication failed")
        return

    user_id = payload.get("user_id")
    if not user_id:
        await _reject("User authentication required")
        return

    # Real-time validation: ensure user exists and is active (same security intent as get_current_user)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await _reject("User not found")
            return
        if not user.is_active:
            await _reject("User disabled")
            return

        accepted_subprotocol = "auth" if subprotocols and subprotocols[0] == "auth" else None
        await user_connection_manager.connect(user_id, websocket, subprotocol=accepted_subprotocol)

        # Start Redis subscription (best-effort)
        await _ensure_redis_subscription_started()

        # Send initial state (unread count)
        service = NotificationService(publisher=None)
        unread = service.get_unread_count(db, user_id=user_id)

        await websocket.send_json(
            {
                "type": "connected",
                "data": {"user_id": user_id, "unread_count": unread},
            }
        )

        # Keep alive loop (same ping/pong convention as existing endpoints)
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong", "data": {}})

    except WebSocketDisconnect:
        logger.info(f"[notifications] websocket disconnected user={user_id}")
    except Exception as e:
        logger.error(f"[notifications] websocket error user={user_id}: {e}", exc_info=True)
    finally:
        try:
            await user_connection_manager.disconnect(user_id, websocket)
        except Exception:
            pass
        db.close()
