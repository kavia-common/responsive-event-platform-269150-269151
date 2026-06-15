from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.models.schemas import AnalyticsOut

router = APIRouter()


# PUBLIC_INTERFACE
@router.get(
    "/analytics",
    response_model=AnalyticsOut,
    summary="Analytics metrics",
    description="Returns basic analytics metrics for dashboard (best-effort).",
    operation_id="getAnalytics",
)
async def get_analytics(db: AsyncIOMotorDatabase = Depends(get_db)) -> AnalyticsOut:
    """Compute basic analytics from stored collections."""
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    new_events_7d = await db["events"].count_documents({"createdAt": {"$gte": seven_days_ago}})
    rsvps_7d = await db["rsvps"].count_documents({"updatedAt": {"$gte": seven_days_ago}})
    # activeRooms: approximate number of event rooms that have at least 1 comment
    active_rooms = len(await db["comments"].distinct("eventId"))
    return AnalyticsOut(rsvps7d=int(rsvps_7d), newEvents7d=int(new_events_7d), activeRooms=int(active_rooms))
