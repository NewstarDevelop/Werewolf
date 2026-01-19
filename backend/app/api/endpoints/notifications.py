"""Notification REST API endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationCategory,
    NotificationListResponse,
    NotificationPublic,
    UnreadCountResponse,
    MarkReadResponse,
    ReadAllResponse,
    ReadBatchRequest,
    ReadBatchResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    category: Optional[NotificationCategory] = Query(None),
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List durable notifications for current user with pagination.

    Sorting:
    - created_at DESC
    """
    user_id = current_user["user_id"]

    query = db.query(Notification).filter(Notification.user_id == user_id)

    if category:
        query = query.filter(Notification.category == category.value)

    if unread_only:
        query = query.filter(Notification.read_at.is_(None))

    total = int(query.count())
    items = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    notifications = [
        NotificationPublic(
            id=n.id,
            user_id=n.user_id,
            category=NotificationCategory(n.category),
            title=n.title,
            body=n.body,
            data=dict(n.data or {}),
            created_at=n.created_at,
            read_at=n.read_at,
        )
        for n in items
    ]

    return NotificationListResponse(
        notifications=notifications,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return unread durable notification count."""
    user_id = current_user["user_id"]
    count = int(
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
        .scalar()
        or 0
    )
    return UnreadCountResponse(unread_count=count)


@router.post("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark one notification as read.

    Security:
    - Only allows updating notifications owned by current user.
    """
    user_id = current_user["user_id"]
    n: Optional[Notification] = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")

    if n.read_at is None:
        n.read_at = datetime.utcnow()
        db.commit()

    return MarkReadResponse(notification_id=n.id, read_at=n.read_at or datetime.utcnow())


@router.post("/read-all", response_model=ReadAllResponse)
async def mark_all_read(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark all unread notifications as read for current user.

    This is implemented as a single SQL UPDATE for performance.
    """
    user_id = current_user["user_id"]
    now = datetime.utcnow()

    updated = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
        .update({Notification.read_at: now}, synchronize_session=False)
    )
    db.commit()

    return ReadAllResponse(updated=int(updated or 0), read_at=now)


@router.post("/read-batch", response_model=ReadBatchResponse)
async def mark_batch_read(
    body: ReadBatchRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark multiple notifications as read by ID list.

    Security:
    - Only updates notifications owned by current user.
    - Non-existent or other users' notifications are silently ignored.

    Idempotent:
    - Already-read notifications are not modified.
    """
    user_id = current_user["user_id"]
    now = datetime.utcnow()

    updated = (
        db.query(Notification)
        .filter(
            Notification.id.in_(body.notification_ids),
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
        .update({Notification.read_at: now}, synchronize_session=False)
    )
    db.commit()

    return ReadBatchResponse(updated=int(updated or 0), read_at=now)
