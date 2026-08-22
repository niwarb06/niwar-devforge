from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DEVFORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Niwar DevForge API"
    environment: Literal["development", "test", "staging", "production"] = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+pysqlite:///./devforge.db"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = Field(default_factory=list)
    log_level: str = "INFO"
    session_ttl_minutes: int = Field(default=10_080, ge=5, le=43_200)
    auth_login_identifier_limit: int = Field(default=5, ge=1, le=100)
    auth_login_source_limit: int = Field(default=60, ge=1, le=10_000)
    auth_login_window_seconds: int = Field(default=300, ge=30, le=3_600)
    auth_register_identifier_limit: int = Field(default=3, ge=1, le=100)
    auth_register_source_limit: int = Field(default=20, ge=1, le=10_000)
    auth_register_window_seconds: int = Field(default=3_600, ge=60, le=86_400)
    auth_trust_proxy_headers: bool = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
