from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .contracts import Actor, RegisterCommand
from .models import User


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
            self._db.commit()
        except IntegrityError as exc:
            self._db.rollback()
            raise ValueError("email_already_exists") from exc
        self._db.refresh(user)
        return self._to_actor(user)

    @staticmethod
    def _to_actor(user: User) -> Actor:
        return Actor(id=user.id, email=user.email, display_name=user.display_name, roles=("user",))
