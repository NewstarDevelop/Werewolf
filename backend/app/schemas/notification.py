"""Notification schemas (Pydantic)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class NotificationCategory(str, Enum):
    """Business category for filtering and UI grouping."""

    GAME = "GAME"
    ROOM = "ROOM"
    SOCIAL = "SOCIAL"
    SYSTEM = "SYSTEM"


class NotificationPersistPolicy(str, Enum):
    """
    Storage policy (tiered storage).

    - VOLATILE: real-time only (toast), not stored
    - DURABLE: stored in DB + outbox + real-time push
    """

    VOLATILE = "VOLATILE"
    DURABLE = "DURABLE"


class NotificationPublic(BaseModel):
    """Public notification payload returned by REST APIs."""

    id: str
    user_id: str
    category: NotificationCategory
    title: str
    body: str
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notification list response."""

    notifications: list[NotificationPublic]
    total: int
    page: int
    page_size: int


class UnreadCountResponse(BaseModel):
    """Unread count response."""

    unread_count: int


class MarkReadResponse(BaseModel):
    """Mark-one-as-read response."""

    notification_id: str
    read_at: datetime


class ReadAllResponse(BaseModel):
    """Mark-all-as-read response."""

    updated: int
    read_at: datetime


class NotificationMessageData(BaseModel):
    """
    Data field inside WebSocket envelope for notification messages.

    This keeps the WebSocket envelope consistent with existing style:
    { "type": "<message_type>", "data": { ... } }
    """

    persisted: bool
    notification: Optional[NotificationPublic] = None
    event_id: Optional[str] = None  # for volatile messages without DB id


class PubSubMessage(BaseModel):
    """
    Redis Pub/Sub message schema.

    The subscriber routes by user_id and forwards to WebSocket via:
    send_to_user(user_id, message_type, data).
    """

    version: int = 1
    user_id: str
    message_type: str
    data: dict[str, Any]
