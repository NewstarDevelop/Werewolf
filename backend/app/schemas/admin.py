"""Admin-related schemas."""

from pydantic import BaseModel


class RestartResponse(BaseModel):
    """Response for restart endpoint."""

    status: str
    message: str
    delay_seconds: int
