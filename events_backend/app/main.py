from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.api.routes_notifications import seed_notification
from app.core.config import settings
from app.core.db import close_mongo_connection, connect_to_mongo, get_db
from app.core.utils import now_iso
from app.models.schemas import WsInboundChatMessage, WsOutbound
from app.realtime.connection_manager import ConnectionManager

openapi_tags = [
    {"name": "profile", "description": "Profile endpoints (stubbed auth)."},
    {"name": "events", "description": "Event discovery and CRUD."},
    {"name": "comments", "description": "Event comments."},
    {"name": "notifications", "description": "User notifications."},
    {"name": "feed", "description": "User activity feed."},
    {"name": "moderation", "description": "Reporting and moderation queue."},
    {"name": "admin", "description": "Admin tools."},
    {"name": "analytics", "description": "Analytics metrics for dashboards."},
    {"name": "realtime", "description": "WebSocket realtime chat/notifications."},
]

app = FastAPI(
    title=settings.app_title,
    description=(
        "Backend API for the responsive event platform.\n\n"
        "WebSocket usage:\n"
        f"- Connect to `{settings.ws_path}` (e.g. `ws://<host>:<port>{settings.ws_path}`)\n"
        "- Send chat messages: `{type:'chat_message', roomId:'event:<eventId>', body:'hi'}`\n"
        "- Receive:\n"
        "  - notifications: `{type:'notification', payload:{...}}`\n"
        "  - chat: `{type:'chat_message', roomId:'event:<eventId>', payload:{...}}`\n"
    ),
    version=settings.app_version,
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()


@app.on_event("startup")
async def _startup() -> None:
    """Startup hook: connect to MongoDB."""
    await connect_to_mongo()


@app.on_event("shutdown")
async def _shutdown() -> None:
    """Shutdown hook: close MongoDB connection."""
    await close_mongo_connection()


@app.get(
    "/health",
    tags=["meta"],
    summary="Health check",
    description="Basic health check endpoint.",
    operation_id="healthCheck",
)
async def health() -> Dict[str, Any]:
    """Health check."""
    return {"ok": True, "env": settings.app_env, "time": now_iso()}


@app.get(
    "/docs/realtime",
    tags=["realtime"],
    summary="WebSocket usage help",
    description="Returns example payloads and connection info for WebSocket clients.",
    operation_id="realtimeDocs",
)
async def realtime_docs() -> Dict[str, Any]:
    """WebSocket usage help.

    Returns:
        JSON object with WebSocket URL pattern and message shapes.
    """
    return {
        "ws_path": settings.ws_path,
        "connect_example": f"ws://localhost:3001{settings.ws_path}",
        "send_chat_example": {"type": "chat_message", "roomId": "event:<eventId>", "body": "Hello!"},
        "receive_notification_example": {"type": "notification", "payload": {"title": "Example", "body": "..."}} ,
        "receive_chat_example": {
            "type": "chat_message",
            "roomId": "event:<eventId>",
            "payload": {"authorName": "User", "body": "Hello!", "createdAt": now_iso()},
        },
    }


app.include_router(api_router)


# PUBLIC_INTERFACE
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for chat and notifications.

    Frontend expectations (see events_frontend/src/utils/wsClient.js):
    - Outbound from server:
      - `{type:'notification', payload:{...}}`
      - `{type:'chat_message', roomId:'event:<eventId>', payload:{...}}`
    - Inbound from client:
      - `{type:'chat_message', roomId:'event:<eventId>', body:'...'}`
    """
    await manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except Exception:
                continue

            msg_type = data.get("type") or data.get("event")
            if msg_type == "chat_message":
                try:
                    inbound = WsInboundChatMessage.model_validate(data)
                except Exception:
                    continue

                # Auto-join sender to room so they receive their own broadcast consistently.
                await manager.join_room(inbound.roomId, websocket)

                payload = {
                    "id": data.get("id") or "",
                    "authorName": "Me",
                    "body": inbound.body,
                    "createdAt": now_iso(),
                }
                out = WsOutbound(type="chat_message", roomId=inbound.roomId, payload=payload)
                await manager.broadcast_room(inbound.roomId, out.model_dump_json())

                # Also create a notification for demo purposes
                db = get_db()
                await seed_notification(db, title="New chat message", body=f"Room {inbound.roomId}: {inbound.body[:80]}")
                notif = WsOutbound(
                    type="notification",
                    payload={"id": "", "title": "New chat message", "body": inbound.body, "read": False, "createdAt": now_iso()},
                )
                await manager.broadcast(notif.model_dump_json())
            elif msg_type == "join_room":
                room_id = data.get("roomId") or data.get("room_id")
                if room_id:
                    await manager.join_room(str(room_id), websocket)
            else:
                # Ignore unknown message types
                continue
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
