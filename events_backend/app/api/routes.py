from __future__ import annotations

from fastapi import APIRouter

from app.api.routes_admin import router as admin_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_comments import router as comments_router
from app.api.routes_events import router as events_router
from app.api.routes_feed import router as feed_router
from app.api.routes_moderation import router as moderation_router
from app.api.routes_notifications import router as notifications_router
from app.api.routes_profile import router as profile_router

api_router = APIRouter()
api_router.include_router(profile_router, tags=["profile"])
api_router.include_router(events_router, tags=["events"])
api_router.include_router(comments_router, tags=["comments"])
api_router.include_router(notifications_router, tags=["notifications"])
api_router.include_router(feed_router, tags=["feed"])
api_router.include_router(moderation_router, tags=["moderation"])
api_router.include_router(admin_router, tags=["admin"])
api_router.include_router(analytics_router, tags=["analytics"])
