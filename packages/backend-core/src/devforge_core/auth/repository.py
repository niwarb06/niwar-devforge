from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .contracts import Actor, RegisterCommand
from .errors import EmailAlreadyExists
from .models import User, UserRole


class SqlAlchemyUserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    async def get_by_identifier(self, identifier: str) -> tuple[Actor, str] | None:
        email = identifier.strip().lower()
        user = self._db.scalar(select(User).where(User.email == email))
        if user is None or not user.is_active:
            return None
        return self._to_actor(user), user.password_hash

    async def create(self, command: RegisterCommand, password_hash: str) -> Actor:
        user = User(
            email=command.email.strip().lower(),
            display_name=command.display_name,
            password_hash=password_hash,
        )
        self._db.add(user)
        try:
            self._db.flush()
            self._db.add(UserRole(user_id=user.id, role="user"))
            self._db.commit()
        except IntegrityError as exc:
            self._db.rollback()
            raise EmailAlreadyExists() from exc
        self._db.refresh(user)
        return self._to_actor(user)

    def roles_for_user(self, user_id: UUID) -> tuple[str, ...]:
        roles = self._db.scalars(
            select(UserRole.role).where(UserRole.user_id == user_id).order_by(UserRole.role)
        ).all()
        return tuple(roles)

    def _to_actor(self, user: User) -> Actor:
        return Actor(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            roles=self.roles_for_user(user.id),
        )
