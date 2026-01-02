"""WebSocket endpoints for real-time game updates."""
import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from app.services.websocket_manager import websocket_manager
from app.models.game import game_store
from app.core.auth import verify_player_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/game/{game_id}")
async def game_websocket(
    websocket: WebSocket,
    game_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time game updates with JWT authentication.

    Clients connect with token in query string for player identification.

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

    # Step 1: Authenticate and extract player_id from JWT
    try:
        payload = verify_player_token(token)
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
    await websocket_manager.connect(game_id, player_id, websocket)

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
    """
    room_key = f"room_{room_id}"
    connection_id = str(uuid.uuid4())
    await websocket_manager.connect(room_key, connection_id, websocket)

    try:
        # Send initial confirmation
        await websocket.send_json({
            "type": "connected",
            "data": {"room_id": room_id}
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
