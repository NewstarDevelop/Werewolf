"""User profile and statistics API endpoints.

A3-FIX: All endpoints are sync (def) to avoid event loop blocking.
These are pure DB operations with no async I/O.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.game_history import GameParticipant
from app.schemas.auth import UserResponse
from app.schemas.user import UpdateProfileRequest, UserStatsResponse
from app.schemas.preferences import UserPreferences, UserPreferencesResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile.
    """
    user = db.query(User).get(current_user["user_id"])

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.from_orm(user)


@router.put("/me", response_model=UserResponse)
def update_user_profile(
    body: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    """
    from sqlalchemy.exc import IntegrityError

    user = db.query(User).get(current_user["user_id"])

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check nickname uniqueness before update
    if body.nickname is not None and body.nickname != user.nickname:
        existing = db.query(User).filter(
            User.nickname == body.nickname,
            User.id != user.id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Nickname already taken")

    # Update fields if provided
    if body.nickname is not None:
        user.nickname = body.nickname

    if body.bio is not None:
        user.bio = body.bio

    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url

    user.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Nickname already taken")

    return UserResponse.from_orm(user)


@router.get("/me/stats", response_model=UserStatsResponse)
def get_user_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's game statistics.
    """
    user_id = current_user["user_id"]

    # Query game statistics
    stats = db.query(
        func.count(GameParticipant.id).label("games_played"),
        func.sum(GameParticipant.is_winner).label("games_won")
    ).filter(
        GameParticipant.user_id == user_id
    ).first()

    games_played = stats.games_played or 0
    games_won = int(stats.games_won or 0)
    win_rate = (games_won / games_played) if games_played > 0 else 0.0

    # Get recent games
    recent_participations = db.query(GameParticipant).filter(
        GameParticipant.user_id == user_id
    ).order_by(
        GameParticipant.created_at.desc()
    ).limit(10).all()

    recent_games = [
        {
            "game_id": p.game_id,
            "seat_id": p.seat_id,
            "role": p.role,
            "is_winner": p.is_winner,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in recent_participations
    ]

    return UserStatsResponse(
        games_played=games_played,
        games_won=games_won,
        win_rate=round(win_rate, 3),
        recent_games=recent_games
    )


@router.get("/me/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's preferences.
    Returns merged defaults for missing fields.
    """
    user = db.query(User).get(current_user["user_id"])

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get preferences from DB, default to empty dict
    prefs_data = user.preferences or {}

    # Merge with defaults
    try:
        user_prefs = UserPreferences(**prefs_data)
    except Exception:
        # If parsing fails, return defaults
        user_prefs = UserPreferences()

    return UserPreferencesResponse(preferences=user_prefs)


@router.put("/me/preferences", response_model=UserPreferencesResponse)
def update_user_preferences(
    body: UserPreferences,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's preferences (idempotent PUT).
    Returns the updated preferences with merged defaults.
    """
    user = db.query(User).get(current_user["user_id"])

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Normalize volume to 2 decimal places to reduce write churn
    prefs_dict = body.dict()
    if 'sound_effects' in prefs_dict and 'volume' in prefs_dict['sound_effects']:
        prefs_dict['sound_effects']['volume'] = round(prefs_dict['sound_effects']['volume'], 2)

    # Update preferences (MutableDict will track changes)
    user.preferences = prefs_dict
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Return updated preferences
    return UserPreferencesResponse(preferences=UserPreferences(**user.preferences))
