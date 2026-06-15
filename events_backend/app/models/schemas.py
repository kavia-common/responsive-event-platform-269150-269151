from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    """Base event fields used for creation and update."""

    title: str = Field(..., description="Event title.")
    description: str = Field(default="", description="Event description.")
    category: str = Field(default="community", description="Event category.")
    locationName: str = Field(default="Unknown", description="Human-friendly location name.")
    lat: Optional[float] = Field(default=None, description="Latitude.")
    lng: Optional[float] = Field(default=None, description="Longitude.")
    startAt: str = Field(..., description="Event start time ISO string.")
    imageUrl: str = Field(default="", description="Event image URL (uploaded or remote).")


class EventCreate(EventBase):
    """Payload for event creation."""


class EventUpdate(BaseModel):
    """Payload for event update."""

    title: Optional[str] = Field(default=None, description="Event title.")
    description: Optional[str] = Field(default=None, description="Event description.")
    category: Optional[str] = Field(default=None, description="Event category.")
    locationName: Optional[str] = Field(default=None, description="Human-friendly location name.")
    lat: Optional[float] = Field(default=None, description="Latitude.")
    lng: Optional[float] = Field(default=None, description="Longitude.")
    startAt: Optional[str] = Field(default=None, description="Event start time ISO string.")
    imageUrl: Optional[str] = Field(default=None, description="Event image URL (uploaded or remote).")


class EventOut(EventBase):
    """Event returned to clients."""

    id: str = Field(..., description="Event id.")
    distanceKm: Optional[float] = Field(default=None, description="Optional computed distance in kilometers.")


class CommentCreate(BaseModel):
    """Payload to create a comment for an event."""

    body: str = Field(..., description="Comment body text.")


class CommentOut(BaseModel):
    """Comment returned to clients."""

    id: str = Field(..., description="Comment id.")
    eventId: str = Field(..., description="Event id this comment belongs to.")
    body: str = Field(..., description="Comment text.")
    authorName: str = Field(..., description="Display name of comment author.")
    createdAt: str = Field(..., description="ISO timestamp.")


class NotificationOut(BaseModel):
    """Notification returned to clients."""

    id: str = Field(..., description="Notification id.")
    title: str = Field(..., description="Short title/type.")
    body: str = Field(..., description="Notification message.")
    read: bool = Field(default=False, description="Read status.")
    createdAt: str = Field(..., description="ISO timestamp.")


class FeedItemOut(BaseModel):
    """Feed item returned to clients."""

    id: str = Field(..., description="Feed item id.")
    title: str = Field(..., description="Title.")
    subtitle: str = Field(default="", description="Secondary line/body.")
    actorUserId: str = Field(default="", description="Actor user id.")
    eventId: str = Field(default="", description="Related event id.")


class RsvpCreate(BaseModel):
    """RSVP payload (frontend may send either eventId in body or in route)."""

    eventId: Optional[str] = Field(default=None, description="Event id (optional if in route).")
    status: Literal["going", "interested", "none"] = Field(..., description="RSVP status.")


class ReportCreate(BaseModel):
    """Moderation report payload."""

    targetType: Literal["event", "comment", "user"] = Field(..., description="Type of target being reported.")
    targetId: str = Field(..., description="Target id being reported.")
    reason: str = Field(..., description="Reason for report.")


class ResolveReport(BaseModel):
    """Resolve moderation report."""

    outcome: str = Field(..., description="Outcome text (e.g., resolved/ignored/action_taken).")


class AdminStatsOut(BaseModel):
    """Admin stats summary."""

    users: int = Field(..., description="Approx user count.")
    events: int = Field(..., description="Event count.")
    reports: int = Field(..., description="Open report count.")


class AnalyticsOut(BaseModel):
    """Analytics metrics displayed in dashboard."""

    rsvps7d: int = Field(..., description="RSVPs created in last 7 days.")
    newEvents7d: int = Field(..., description="New events created in last 7 days.")
    activeRooms: int = Field(..., description="Active chat rooms (approx).")


class WsInboundChatMessage(BaseModel):
    """Inbound WS message from client."""

    type: Literal["chat_message"] = Field(..., description="Message type.")
    roomId: str = Field(..., description="Room id (e.g., event:<eventId>).")
    body: str = Field(..., description="Chat body.")


class WsOutbound(BaseModel):
    """Outbound WS message wrapper."""

    type: str = Field(..., description="Event type for routing (notification/chat_message).")
    roomId: Optional[str] = Field(default=None, description="Room id for chat messages.")
    payload: Dict[str, Any] = Field(..., description="Payload object.")
