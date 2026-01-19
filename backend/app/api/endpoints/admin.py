"""Admin management endpoints."""

from __future__ import annotations

import logging
import os
import signal
import time
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Request

from app.api.endpoints.game import verify_admin
from app.schemas.admin import RestartResponse

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


def _schedule_shutdown():
    """Schedule graceful shutdown after response is sent."""
    try:
        time.sleep(1)  # Allow response to be sent
        os.kill(os.getpid(), signal.SIGTERM)
    except Exception as e:
        logger.error(f"Failed to send SIGTERM: {e}, pid={os.getpid()}")


@router.post("/restart", response_model=RestartResponse, status_code=202)
async def restart_service(
    request: Request,
    background_tasks: BackgroundTasks,
    actor: Dict = Depends(verify_admin),
):
    """
    Trigger graceful service restart.
    POST /api/admin/restart

    Security: Admin only (JWT admin or X-Admin-Key)
    The actual restart is handled by external process manager (docker/systemd).
    """
    client_ip: Optional[str] = None
    try:
        if request.client:
            client_ip = request.client.host
    except Exception:
        client_ip = "unknown"

    actor_id = actor.get("player_id", "unknown")

    logger.warning(f"RESTART_REQUESTED by actor={actor_id} from ip={client_ip}")

    background_tasks.add_task(_schedule_shutdown)

    return RestartResponse(
        status="accepted",
        message="Restart scheduled. Service will restart in ~1 second.",
        delay_seconds=1,
    )
