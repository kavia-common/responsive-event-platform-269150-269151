from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.core.utils import clean_mongo_doc, now_iso
from app.models.schemas import ReportCreate, ResolveReport

router = APIRouter()


def _reports_col(db: AsyncIOMotorDatabase):
    return db["reports"]


class ModerationReportOut(BaseModel):
    """Moderation report for admin/moderator queue."""

    id: str = Field(..., description="Report id.")
    targetType: str = Field(..., description="Target type.")
    targetId: str = Field(..., description="Target id.")
    reason: str = Field(..., description="Reason.")


# PUBLIC_INTERFACE
@router.post(
    "/reports",
    summary="Submit a moderation report",
    description="Submit a report against an event/comment/user.",
    operation_id="submitReport",
)
async def submit_report(payload: ReportCreate, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    """Submit report."""
    await _reports_col(db).insert_one(
        {
            "targetType": payload.targetType,
            "targetId": payload.targetId,
            "reason": payload.reason,
            "status": "open",
            "createdAt": now_iso(),
        }
    )
    return {"ok": True}


# PUBLIC_INTERFACE
@router.get(
    "/moderation/reports",
    response_model=List[ModerationReportOut],
    summary="List moderation queue reports",
    description="Returns open reports for moderation queue.",
    operation_id="listModerationQueue",
)
async def list_reports(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[ModerationReportOut]:
    """List reports."""
    cursor = _reports_col(db).find({"status": "open"}).sort("createdAt", -1).limit(200)
    items = [clean_mongo_doc(d) async for d in cursor]
    return [
        ModerationReportOut(
            id=it["id"],
            targetType=it.get("targetType", "event"),
            targetId=it.get("targetId", ""),
            reason=it.get("reason", ""),
        )
        for it in items
    ]


# PUBLIC_INTERFACE
@router.post(
    "/moderation/reports/{report_id}/resolve",
    summary="Resolve a report",
    description="Resolve an open report with an outcome string.",
    operation_id="resolveReport",
)
async def resolve_report(report_id: str, payload: ResolveReport, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    """Resolve report."""
    from app.core.utils import to_object_id

    oid = to_object_id(report_id)
    await _reports_col(db).update_one({"_id": oid}, {"$set": {"status": "resolved", "outcome": payload.outcome}})
    return {"ok": True}
