from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class ProfileUpdate(BaseModel):
    """Update current user's profile (stubbed auth: single 'me' user)."""

    displayName: Optional[str] = Field(default=None, description="Display name.")
    bio: Optional[str] = Field(default=None, description="Bio text.")


# PUBLIC_INTERFACE
@router.put(
    "/me",
    summary="Update current user profile",
    description="Updates the current user's profile fields. Authentication is stubbed for now (single user).",
    operation_id="updateMe",
)
@router.put(
    "/profile",
    include_in_schema=False,
)
async def update_me(payload: ProfileUpdate) -> dict:
    """Update current user profile.

    Args:
        payload: Fields to update.

    Returns:
        A small acknowledgement object.
    """
    # For this template backend, we don't persist user profiles yet.
    return {"ok": True, "profile": payload.model_dump(exclude_none=True)}
