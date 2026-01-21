"""
WebSocket endpoint: /ws/notifications

Auth (priority order):
1. Cookie: user_access_token (HttpOnly cookie set by /auth/login)
2. Sec-WebSocket-Protocol: auth, <jwt_token> (fallback for non-browser clients)

Requires JWT payload contains user_id (logged-in user).

Delivery:
- Per-instance user connection manager delivers messages to connected clients.
- Cross-instance routing relies on Redis Pub/Sub subscriber (best-effort bootstrap here).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional, List, Any
from urllib.parse import urlparse

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.auth import verify_player_token
from app.core.config import settings
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


def _validate_origin(websocket: WebSocket) -> bool:
    """
    Validate Origin header to prevent Cross-Site WebSocket Hijacking (CSWSH).

    Returns True if origin is allowed, False otherwise.
    """
    origin = websocket.headers.get("origin")
    if not origin:
        # No origin header - likely non-browser client, allow
        return True

    # Parse origin to get host
    try:
        parsed = urlparse(origin)
        origin_host = parsed.netloc.lower()
    except Exception:
        return False

    # Build allowed origins list
    allowed_origins = set()

    # Always allow same-host connections
    request_host = websocket.headers.get("host", "").lower()
    if request_host:
        allowed_origins.add(request_host)

    # Add configured frontend URL if present
    frontend_url = getattr(settings, "FRONTEND_URL", None)
    if frontend_url:
        try:
            parsed_frontend = urlparse(frontend_url)
            if parsed_frontend.netloc:
                allowed_origins.add(parsed_frontend.netloc.lower())
        except Exception:
            pass

    # Add localhost variants for development
    allowed_origins.update([
        "localhost:5173",
        "localhost:3000",
        "127.0.0.1:5173",
        "127.0.0.1:3000",
    ])

    return origin_host in allowed_origins


def _extract_token_from_cookies(websocket: WebSocket) -> Optional[str]:
    """
    Extract JWT token from HttpOnly cookie.

    Cookie name: user_access_token (set by /auth/login)
    """
    return websocket.cookies.get("user_access_token")


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

    # Security: Validate origin to prevent CSWSH attacks
    if not _validate_origin(websocket):
        logger.warning(f"[notifications] rejected connection from invalid origin: {websocket.headers.get('origin')}")
        await _reject("Invalid origin")
        return

    # Auth priority: Cookie first, then Sec-WebSocket-Protocol
    auth_token = _extract_token_from_cookies(websocket)
    auth_source = "cookie"

    if not auth_token:
        subprotocols = websocket.scope.get("subprotocols", [])
        auth_token = _extract_token_from_subprotocols(subprotocols)
        auth_source = "subprotocol"

    if not auth_token:
        await _reject("Authentication required: login or provide token via Sec-WebSocket-Protocol")
        return

    try:
        payload = verify_player_token(auth_token)
    except Exception as e:
        logger.error(f"[notifications] websocket auth failed ({auth_source}): {e}")
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

        # Accept with subprotocol only if client used Sec-WebSocket-Protocol
        subprotocols = websocket.scope.get("subprotocols", [])
        accepted_subprotocol = "auth" if subprotocols and subprotocols[0] == "auth" else None
        await user_connection_manager.connect(user_id, websocket, subprotocol=accepted_subprotocol)

        logger.info(f"[notifications] websocket connected user={user_id} auth_source={auth_source}")

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
