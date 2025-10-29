"""
API v1 router aggregation.

Anonymous session management - no authentication required.
"""
from fastapi import APIRouter

from gustobot.interfaces.http.v1 import sessions

api_router = APIRouter()

# Include routers (no authentication required)
api_router.include_router(sessions.router, prefix="/sessions", tags=["Chat Sessions"])
