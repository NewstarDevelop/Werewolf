"""API router aggregation."""
from fastapi import APIRouter

from app.api.endpoints import game

api_router = APIRouter(prefix="/api")
api_router.include_router(game.router)
