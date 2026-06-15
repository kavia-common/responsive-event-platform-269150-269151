from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.utils import clean_mongo_doc, now_iso
from app.models.schemas import CommentCreate, CommentOut

router = APIRouter()


def _comments_col(db: AsyncIOMotorDatabase):
    return db["comments"]


# PUBLIC_INTERFACE
@router.get(
    "/events/{event_id}/comments",
    response_model=List[CommentOut],
    summary="List comments for an event",
    description="Returns comments for a given event id.",
    operation_id="listComments",
)
async def list_comments(event_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> List[CommentOut]:
    """List event comments."""
    cursor = _comments_col(db).find({"eventId": event_id}).sort("createdAt", 1).limit(500)
    items = [clean_mongo_doc(d) async for d in cursor]
    return [CommentOut(**it) for it in items]


# PUBLIC_INTERFACE
@router.post(
    "/events/{event_id}/comments",
    response_model=CommentOut,
    summary="Post a comment for an event",
    description="Creates a new comment for an event. Author identity is stubbed as 'Me'.",
    operation_id="postComment",
)
async def post_comment(
    event_id: str,
    payload: CommentCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> CommentOut:
    """Create event comment."""
    doc = {
        "eventId": event_id,
        "body": payload.body,
        "authorName": "Me",
        "createdAt": now_iso(),
    }
    res = await _comments_col(db).insert_one(doc)
    created = await _comments_col(db).find_one({"_id": res.inserted_id})
    assert created is not None
    out = clean_mongo_doc(created)
    return CommentOut(**out)
