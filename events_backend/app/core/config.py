from __future__ import annotations

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and optional .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_title: str = Field(default="Events Backend API", description="OpenAPI title for the service.")
    app_version: str = Field(default="0.1.0", description="Service version.")
    app_env: str = Field(default="development", description="Deployment environment name.")
    log_level: str = Field(default="INFO", description="Logging level.")

    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated list of allowed CORS origins.",
    )

    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string for events_database.",
    )
    mongodb_db: str = Field(default="events", description="MongoDB database name.")

    frontend_url: str = Field(
        default="http://localhost:5173",
        description="Frontend base URL for docs/examples/links.",
    )
    ws_path: str = Field(default="/ws", description="WebSocket path.")

    def cors_origins_list(self) -> List[str]:
        """Return parsed CORS origins list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
