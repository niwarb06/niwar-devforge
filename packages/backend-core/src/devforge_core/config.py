from functools import lru_cache
from ipaddress import ip_network
from typing import Literal

from pydantic import Field, field_validator
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
    credential_rate_limit_window_seconds: int = Field(default=60, ge=10, le=3_600)
    login_ip_limit: int = Field(default=10, ge=1, le=10_000)
    login_identifier_limit: int = Field(default=5, ge=1, le=10_000)
    register_ip_limit: int = Field(default=5, ge=1, le=10_000)
    register_identifier_limit: int = Field(default=3, ge=1, le=10_000)
    trusted_proxy_cidrs: list[str] = Field(default_factory=list)

    @field_validator("trusted_proxy_cidrs")
    @classmethod
    def validate_trusted_proxy_cidrs(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            try:
                network = ip_network(value.strip(), strict=False)
            except ValueError as exc:
                raise ValueError(f"invalid trusted proxy CIDR: {value}") from exc
            if network.prefixlen == 0:
                raise ValueError("trusted proxy CIDRs cannot trust the entire address space")
            canonical = str(network)
            if canonical not in normalized:
                normalized.append(canonical)
        return normalized

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
