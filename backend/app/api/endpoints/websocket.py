"""WebSocket endpoints for real-time game updates."""
import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional, List

from app.services.websocket_manager import websocket_manager
from app.services.websocket_auth import (
    authenticate_websocket,
    validate_origin,
    WebSocketAuthError,
    close_with_error,
)
from app.models.game import game_store
from app.core.auth import verify_player_token
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration: whether to allow deprecated query token authentication
# Set to False in production after migration period
ALLOW_QUERY_TOKEN = settings.DEBUG


def _extract_token_from_subprotocols(subprotocols: List[str]) -> Optional[str]:
    """
    Extract JWT token from Sec-WebSocket-Protocol header.

    The client sends: Sec-WebSocket-Protocol: auth, <jwt_token>
    We extract the token (second item) for authentication.
    """
    if not subprotocols or len(subprotocols) < 2:
        return None
    # First protocol is 'auth', second is the actual token
    return subprotocols[1] if subprotocols[0] == "auth" else None


@router.websocket("/ws/game/{game_id}")
async def game_websocket(
    websocket: WebSocket,
    game_id: str,
    token: Optional[str] = Query(None)  # Keep for backward compatibility
):
    """
    WebSocket endpoint for real-time game updates with JWT authentication.

    Authentication methods (in order of preference):
    1. Sec-WebSocket-Protocol header: ["auth", "<jwt_token>"] (recommended, secure)
    2. Query string: ?token=<jwt_token> (deprecated, for backward compatibility)

    Message format:
    {
        "type": "game_update" | "connected" | "error" | "pong",
        "data": { ... game state or error details ... }
    }
    """
    async def _reject(reason: str) -> None:
        try:
            await websocket.accept()
        except Exception:
            pass
        await websocket.close(code=1008, reason=reason)

    # Step 1: Extract token from Sec-WebSocket-Protocol (preferred) or query string (fallback)
    subprotocols = websocket.scope.get("subprotocols", [])
    auth_token = _extract_token_from_subprotocols(subprotocols)

    # Fallback to query string for backward compatibility (deprecated)
    if not auth_token:
        auth_token = token
        if auth_token:
            logger.warning(f"WebSocket using deprecated query string auth for game {game_id}")

    if not auth_token:
        await _reject("Authentication required: provide token via Sec-WebSocket-Protocol")
        return

    # Step 2: Authenticate and extract player_id from JWT
    try:
        payload = verify_player_token(auth_token)
        player_id = payload.get("player_id") or payload.get("sub")
        room_id = payload.get("room_id")
        if room_id and room_id != game_id:
            await _reject("Token room_id does not match game_id")
            return
        if not player_id:
            await _reject("Invalid token: missing player_id")
            return
    except Exception as e:
        logger.error(f"WebSocket auth failed for game {game_id}: {e}")
        await _reject("Authentication failed")
        return

    # Step 2: Verify game exists
    game = game_store.get_game(game_id)
    if not game:
        await _reject(f"Game {game_id} not found")
        return

    # Step 3: Verify player is in this game
    player = game.get_player_by_id(player_id)
    if not player:
        await _reject("Player not in game")
        return

    # Step 4: Establish connection with player identity
    # If using subprotocol auth, respond with "auth" to confirm
    accepted_subprotocol = "auth" if subprotocols and subprotocols[0] == "auth" else None
    await websocket_manager.connect(game_id, player_id, websocket, subprotocol=accepted_subprotocol)

    try:
        # Send initial state filtered for this player
        initial_state = game.get_state_for_player(player_id)
        await websocket.send_json({
            "type": "connected",
            "data": initial_state
        })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()

            # Handle ping/pong for connection keepalive
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "data": {}
                })

    except WebSocketDisconnect:
        logger.info(f"Player {player_id} disconnected from game {game_id}")
    except Exception as e:
        logger.error(f"WebSocket error for player {player_id} in game {game_id}: {e}", exc_info=True)
    finally:
        websocket_manager.disconnect(game_id, player_id, websocket)


@router.websocket("/ws/room/{room_id}")
async def room_websocket(
    websocket: WebSocket,
    room_id: str,
):
    """
    WebSocket endpoint for real-time room updates (lobby).

    Clients connect to this endpoint while in the room lobby to receive
    instant updates when players join/leave/ready up.

    Security:
    - Origin validation to prevent CSWSH (Cross-Site WebSocket Hijacking)
    - Optional authentication (if token provided, validates it)
    """
    # Validate origin to prevent CSWSH attacks
    is_valid_origin, origin = validate_origin(websocket)
    if not is_valid_origin:
        logger.warning(f"Room WS rejected invalid origin: {origin} for room {room_id}")
        await websocket.close(code=4003, reason="Invalid origin")
        return

    # Optional authentication - if token provided, validate it
    # This allows anonymous viewing but tracks authenticated users
    user_id = None
    try:
        payload = await authenticate_websocket(
            websocket,
            require_auth=False,  # Authentication optional for room lobby
            allow_query_token=ALLOW_QUERY_TOKEN,
            validate_origin_header=False,  # Already validated above
        )
        if payload:
            user_id = payload.get("sub") or payload.get("user_id")
    except WebSocketAuthError as e:
        logger.warning(f"Room WS auth failed: {e.message}")
        # Continue without authentication for public room viewing

    room_key = f"room_{room_id}"
    connection_id = user_id or str(uuid.uuid4())
    await websocket_manager.connect(room_key, connection_id, websocket)

    try:
        # Send initial confirmation
        await websocket.send_json({
            "type": "connected",
            "data": {"room_id": room_id, "authenticated": user_id is not None}
        })

        # Keep connection alive
        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "data": {}
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally for room {room_id}")
    except Exception as e:
        logger.error(f"WebSocket error for room {room_id}: {e}", exc_info=True)
    finally:
        websocket_manager.disconnect(room_key, connection_id, websocket)
