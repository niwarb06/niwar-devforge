from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Actor:
    id: UUID
    email: str | None
    display_name: str | None
    roles: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LoginCommand:
    identifier: str
    password: str


@dataclass(frozen=True, slots=True)
class RegisterCommand:
    email: str
    password: str
    display_name: str | None = None


class IdentityProvider(Protocol):
    async def register(self, command: RegisterCommand) -> Actor: ...

    async def authenticate(self, command: LoginCommand) -> Actor: ...

    async def revoke_session(self, session_id: str) -> None: ...


class AuthorizationPolicy(Protocol):
    def allows(self, actor: Actor, permission: str) -> bool: ...
