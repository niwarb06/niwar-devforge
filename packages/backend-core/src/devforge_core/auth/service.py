from dataclasses import dataclass
from typing import Protocol

from .contracts import Actor, LoginCommand, RegisterCommand


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


class UserRepository(Protocol):
    async def get_by_identifier(self, identifier: str) -> tuple[Actor, str] | None: ...

    async def create(self, command: RegisterCommand, password_hash: str) -> Actor: ...


class SessionIssuer(Protocol):
    async def issue(self, actor: Actor) -> str: ...


@dataclass(slots=True)
class AuthService:
    users: UserRepository
    passwords: PasswordHasher
    sessions: SessionIssuer

    async def register(self, command: RegisterCommand) -> Actor:
        password_hash = self.passwords.hash(command.password)
        return await self.users.create(command, password_hash)

    async def login(self, command: LoginCommand) -> tuple[Actor, str]:
        record = await self.users.get_by_identifier(command.identifier)
        if record is None:
            raise ValueError("invalid_credentials")

        actor, password_hash = record
        if not self.passwords.verify(command.password, password_hash):
            raise ValueError("invalid_credentials")

        session_id = await self.sessions.issue(actor)
        return actor, session_id
