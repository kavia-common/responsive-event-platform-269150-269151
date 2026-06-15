from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.utils import clean_mongo_doc
from app.models.schemas import FeedItemOut

router = APIRouter()


def _feed_col(db: AsyncIOMotorDatabase):
    return db["feed"]


# PUBLIC_INTERFACE
@router.get(
    "/feed",
    response_model=List[FeedItemOut],
    summary="Get user feed",
    description="Returns a simple activity feed for the current user (stubbed).",
    operation_id="getFeed",
)
async def get_feed(db: AsyncIOMotorDatabase = Depends(get_db)) -> List[FeedItemOut]:
    """Return feed."""
    cursor = _feed_col(db).find({"userId": "me"}).sort("createdAt", -1).limit(200)
    items = [clean_mongo_doc(d) async for d in cursor]
    return [FeedItemOut(**it) for it in items]
