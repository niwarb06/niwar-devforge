from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.orm import Session

from devforge_core.config import get_settings

from .contracts import Actor
from .models import Session as SessionModel
from .models import User, UserRole


class DatabaseSessionIssuer:
    """Issues opaque session tokens while storing only a SHA-256 digest server-side."""

    def __init__(self, db: Session, ttl: timedelta | None = None) -> None:
        self._db = db
        settings = get_settings()
        self._ttl = ttl or timedelta(minutes=settings.session_ttl_minutes)

    async def issue(self, actor: Actor) -> str:
        raw_token = token_urlsafe(48)
        record = SessionModel(
            user_id=actor.id,
            token_hash=self._digest(raw_token),
            expires_at=datetime.now(UTC) + self._ttl,
        )
        self._db.add(record)
        self._db.commit()
        return raw_token

    async def resolve(self, raw_token: str) -> Actor | None:
        now = datetime.now(UTC)
        record = self._db.scalar(
            select(SessionModel).where(
                SessionModel.token_hash == self._digest(raw_token),
                SessionModel.revoked_at.is_(None),
                SessionModel.expires_at > now,
            )
        )
        if record is None:
            return None

        user = self._db.get(User, record.user_id)
        if user is None or not user.is_active:
            return None

        roles = self._db.scalars(
            select(UserRole.role)
            .where(UserRole.user_id == user.id)
            .order_by(UserRole.role)
        ).all()
        return Actor(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            roles=tuple(roles),
        )

    async def revoke(self, raw_token: str) -> None:
        record = self._db.scalar(
            select(SessionModel).where(SessionModel.token_hash == self._digest(raw_token))
        )
        if record is None or record.revoked_at is not None:
            return
        record.revoked_at = datetime.now(UTC)
        self._db.commit()

    @staticmethod
    def _digest(raw_token: str) -> str:
        return sha256(raw_token.encode("utf-8")).hexdigest()
