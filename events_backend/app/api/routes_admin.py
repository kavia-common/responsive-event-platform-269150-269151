from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.utils import to_object_id
from app.models.schemas import AdminStatsOut

router = APIRouter(prefix="/admin")


# PUBLIC_INTERFACE
@router.get(
    "/stats",
    response_model=AdminStatsOut,
    summary="Admin stats",
    description="Returns simple platform stats (counts). Auth is not implemented in this template.",
    operation_id="getAdminStats",
)
async def get_admin_stats(db: AsyncIOMotorDatabase = Depends(get_db)) -> AdminStatsOut:
    """Get admin stats."""
    users = await db["users"].estimated_document_count()
    events = await db["events"].estimated_document_count()
    reports = await db["reports"].count_documents({"status": "open"})
    return AdminStatsOut(users=int(users), events=int(events), reports=int(reports))


# PUBLIC_INTERFACE
@router.post(
    "/users/{user_id}/ban",
    summary="Ban a user",
    description="Template endpoint to ban a user (marks user as banned).",
    operation_id="adminBanUser",
)
async def ban_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    """Ban user."""
    await db["users"].update_one({"userId": user_id}, {"$set": {"userId": user_id, "banned": True}}, upsert=True)
    return {"ok": True}


# PUBLIC_INTERFACE
@router.delete(
    "/events/{event_id}",
    summary="Admin delete event",
    description="Delete an event by id (admin action).",
    operation_id="adminDeleteEvent",
)
async def admin_delete_event(event_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    """Admin delete event."""
    oid = to_object_id(event_id)
    res = await db["events"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    await db["rsvps"].delete_many({"eventId": event_id})
    await db["comments"].delete_many({"eventId": event_id})
    return {"ok": True}
