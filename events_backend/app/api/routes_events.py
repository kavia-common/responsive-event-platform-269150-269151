from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.utils import clean_mongo_doc, now_iso, to_object_id
from app.models.schemas import EventCreate, EventOut, EventUpdate, RsvpCreate

router = APIRouter()


def _events_col(db: AsyncIOMotorDatabase):
    return db["events"]


def _rsvps_col(db: AsyncIOMotorDatabase):
    return db["rsvps"]


# PUBLIC_INTERFACE
@router.get(
    "/events",
    response_model=List[EventOut],
    summary="List events (discovery/search/filter)",
    description="List events with optional query/category/date/distance filters. Distance filtering is best-effort unless geo indexes are configured.",
    operation_id="listEvents",
)
async def list_events(
    q: Optional[str] = Query(default=None, description="Search query for title/description."),
    category: Optional[str] = Query(default=None, description="Category filter."),
    from_: Optional[str] = Query(default=None, alias="from", description="ISO start range (inclusive)."),
    to: Optional[str] = Query(default=None, description="ISO end range (inclusive)."),
    max_distance_km: Optional[float] = Query(default=None, description="Max distance in km (best-effort)."),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[EventOut]:
    """List events for discovery page."""
    query = {}
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    if category and category != "all":
        query["category"] = category
    if from_ or to:
        start_query = {}
        if from_:
            start_query["$gte"] = from_
        if to:
            start_query["$lte"] = to
        query["startAt"] = start_query

    cursor = _events_col(db).find(query).sort("startAt", 1).limit(200)
    items = [clean_mongo_doc(d) async for d in cursor]

    # distanceKm is optional; frontend tolerates null. For now we do not compute without user location.
    # If max_distance_km is provided, we return events but keep distanceKm null (no user location passed in API).
    for it in items:
        it.setdefault("distanceKm", None)

    return [EventOut(**it) for it in items]


# PUBLIC_INTERFACE
@router.post(
    "/events",
    response_model=EventOut,
    summary="Create an event",
    description="Create a new event. For image uploads use /events/{id}/image or provide imageUrl directly.",
    operation_id="createEvent",
)
async def create_event(payload: EventCreate, db: AsyncIOMotorDatabase = Depends(get_db)) -> EventOut:
    """Create event."""
    doc = payload.model_dump()
    doc.setdefault("createdAt", now_iso())
    res = await _events_col(db).insert_one(doc)
    created = await _events_col(db).find_one({"_id": res.inserted_id})
    assert created is not None
    out = clean_mongo_doc(created)
    out.setdefault("distanceKm", None)
    return EventOut(**out)


# PUBLIC_INTERFACE
@router.put(
    "/events/{event_id}",
    response_model=EventOut,
    summary="Update an event",
    description="Update event fields by id.",
    operation_id="updateEvent",
)
async def update_event(
    event_id: str,
    payload: EventUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> EventOut:
    """Update event."""
    oid = to_object_id(event_id)
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not patch:
        found = await _events_col(db).find_one({"_id": oid})
        if not found:
            raise HTTPException(status_code=404, detail="Event not found")
        out = clean_mongo_doc(found)
        out.setdefault("distanceKm", None)
        return EventOut(**out)

    await _events_col(db).update_one({"_id": oid}, {"$set": patch})
    updated = await _events_col(db).find_one({"_id": oid})
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    out = clean_mongo_doc(updated)
    out.setdefault("distanceKm", None)
    return EventOut(**out)


# PUBLIC_INTERFACE
@router.delete(
    "/events/{event_id}",
    summary="Delete an event",
    description="Delete an event by id.",
    operation_id="deleteEvent",
)
async def delete_event(event_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    """Delete event."""
    oid = to_object_id(event_id)
    res = await _events_col(db).delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    await _rsvps_col(db).delete_many({"eventId": event_id})
    await db["comments"].delete_many({"eventId": event_id})
    return {"ok": True}


# PUBLIC_INTERFACE
@router.post(
    "/events/{event_id}/image",
    response_model=EventOut,
    summary="Upload event image",
    description="Accept an uploaded image and store a placeholder URL. In a real deployment this should upload to object storage.",
    operation_id="uploadEventImage",
)
async def upload_event_image(
    event_id: str,
    file: UploadFile = File(..., description="Image file to upload."),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> EventOut:
    """Upload image (template implementation stores metadata only)."""
    oid = to_object_id(event_id)

    # Template: we do not persist binary in Mongo. We store a pseudo-URL that references filename.
    # Frontend accepts imageUrl string; real implementation would return a CDN URL.
    image_url = f"/uploads/{event_id}/{file.filename}"
    await _events_col(db).update_one({"_id": oid}, {"$set": {"imageUrl": image_url}})
    updated = await _events_col(db).find_one({"_id": oid})
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    out = clean_mongo_doc(updated)
    out.setdefault("distanceKm", None)
    return EventOut(**out)


# PUBLIC_INTERFACE
@router.post(
    "/events/{event_id}/rsvp",
    summary="Set RSVP status for an event",
    description="Sets RSVP status (going/interested/none) for the current user (stubbed 'me').",
    operation_id="setRsvp",
)
async def set_rsvp(
    event_id: str,
    payload: RsvpCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Set RSVP status."""
    # Stubbed user identity
    user_id = "me"
    status = payload.status
    await _rsvps_col(db).update_one(
        {"eventId": event_id, "userId": user_id},
        {"$set": {"eventId": event_id, "userId": user_id, "status": status, "updatedAt": now_iso()}},
        upsert=True,
    )
    return {"ok": True}
