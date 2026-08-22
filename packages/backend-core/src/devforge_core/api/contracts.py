from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


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
