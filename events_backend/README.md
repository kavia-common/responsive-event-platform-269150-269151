# events_backend (FastAPI)

This service provides REST endpoints + a WebSocket for the responsive event platform frontend.

## Setup

1. Create a virtualenv
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment (copy `.env.example` to `.env` and fill values).

Required env vars:
- `MONGODB_URI`
- `MONGODB_DB`
- `CORS_ORIGINS` (include frontend origin)

## Run

```bash
python run.py
```

Server defaults to `http://localhost:3001`.

## OpenAPI

- Swagger UI: `http://localhost:3001/docs`
- OpenAPI JSON: `http://localhost:3001/openapi.json`

## WebSocket

- URL: `ws://localhost:3001/ws`

Send:

```json
{ "type": "chat_message", "roomId": "event:<eventId>", "body": "Hello!" }
```

Receive:

- Notification:

```json
{ "type": "notification", "payload": { "title": "...", "body": "...", "read": false, "createdAt": "..." } }
```

- Chat:

```json
{ "type": "chat_message", "roomId": "event:<eventId>", "payload": { "authorName": "Me", "body": "...", "createdAt": "..." } }
```
