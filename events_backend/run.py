"""Uvicorn entrypoint for the events_backend service."""

import uvicorn


# PUBLIC_INTERFACE
def main() -> None:
    """Run the FastAPI service with Uvicorn."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=3001, reload=True)


if __name__ == "__main__":
    main()
