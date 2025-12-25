"""Action schemas."""
from typing import Optional
from pydantic import BaseModel

from .enums import ActionType


class ActionRequest(BaseModel):
    """Request schema for player action."""
    seat_id: int
    action_type: ActionType
    target_id: Optional[int] = None
    content: Optional[str] = None  # For speech


class ActionRecord(BaseModel):
    """Record of an action taken."""
    id: int
    game_id: str
    day: int
    phase: str
    player_id: int
    target_id: Optional[int] = None
    action_type: ActionType


class ActionResponse(BaseModel):
    """Response schema for action."""
    success: bool
    message: Optional[str] = None
