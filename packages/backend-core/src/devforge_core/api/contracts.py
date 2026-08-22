from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginRequest(ApiModel):
    identifier: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class RegisterRequest(ApiModel):
    email: str = Field(
        min_length=3,
        max_length=320,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
    )
    password: str = Field(min_length=1, max_length=1024)
    display_name: str | None = Field(default=None, max_length=200)


class RegistrationAcceptedResponse(ApiModel):
    accepted: Literal[True] = True


class SessionTokenResponse(ApiModel):
    session_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in_seconds: int = Field(gt=0)


class UserProfileResponse(ApiModel):
    user_id: UUID
    email: str
    display_name: str | None
    is_active: bool


class UpdateProfileRequest(ApiModel):
    display_name: str | None = Field(default=None, max_length=200)


class PermissionCheckResponse(ApiModel):
    permission: str
    allowed: bool


class ErrorResponse(ApiModel):
    code: str
    message: str | None = None
