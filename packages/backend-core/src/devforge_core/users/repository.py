from uuid import UUID

from sqlalchemy.orm import Session

from devforge_core.auth.models import User

from .contracts import UpdateProfileCommand, UserProfile


class SqlAlchemyUserProfileRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, user_id: UUID) -> UserProfile | None:
        user = self._db.get(User, user_id)
        if user is None:
            return None
        return self._to_profile(user)

    def update(self, user_id: UUID, command: UpdateProfileCommand) -> UserProfile | None:
        user = self._db.get(User, user_id)
        if user is None:
            return None

        display_name = command.display_name
        if display_name is not None:
            display_name = display_name.strip() or None
            if display_name is not None and len(display_name) > 200:
                raise ValueError("display_name_too_long")

        user.display_name = display_name
        self._db.commit()
        self._db.refresh(user)
        return self._to_profile(user)

    @staticmethod
    def _to_profile(user: User) -> UserProfile:
        return UserProfile(
            user_id=user.id,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
        )
