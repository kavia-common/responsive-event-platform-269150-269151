from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.utils import clean_mongo_doc, now_iso
from app.models.schemas import NotificationOut

router = APIRouter()


def _notif_col(db: AsyncIOMotorDatabase):
    return db["notifications"]


# PUBLIC_INTERFACE
@router.get(
    "/notifications",
    response_model=List[NotificationOut],
    summary="List notifications",
    description="Lists notifications for the current user (stubbed).",
    operation_id="listNotifications",
)
async def list_notifications(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[NotificationOut]:
    """List notifications."""
    cursor = _notif_col(db).find({"userId": "me"}).sort("createdAt", -1).limit(200)
    items = [clean_mongo_doc(d) async for d in cursor]
    return [NotificationOut(**it) for it in items]


# PUBLIC_INTERFACE
@router.post(
    "/notifications/read-all",
    summary="Mark all notifications as read",
    description="Marks all notifications read for current user (stubbed).",
    operation_id="markAllNotificationsRead",
)
async def mark_all_read(db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    """Mark all notifications read."""
    await _notif_col(db).update_many({"userId": "me", "read": {"$ne": True}}, {"$set": {"read": True}})
    return {"ok": True}


async def seed_notification(db: AsyncIOMotorDatabase, title: str, body: str) -> None:
    """Internal helper to create a notification for the stubbed user."""
    await _notif_col(db).insert_one(
        {"userId": "me", "title": title, "body": body, "read": False, "createdAt": now_iso()}
    )
