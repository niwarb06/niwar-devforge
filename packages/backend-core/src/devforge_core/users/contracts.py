from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserProfile:
    user_id: UUID
    email: str
    display_name: str | None
    is_active: bool


@dataclass(frozen=True, slots=True)
class UpdateProfileCommand:
    display_name: str | None
