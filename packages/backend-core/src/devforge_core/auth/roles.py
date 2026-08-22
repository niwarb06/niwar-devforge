from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .contracts import Actor
from .errors import AuthorizationDenied
from .models import User, UserRole
from .permissions import RolePermissionPolicy

ALLOWED_GLOBAL_ROLES = frozenset({"user", "admin"})


class InvalidRole(ValueError):
    code = "invalid_role"


class UserNotFound(ValueError):
    code = "user_not_found"


class SqlAlchemyRoleRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def assign(self, user_id: UUID, role: str) -> None:
        if self._db.get(User, user_id) is None:
            raise UserNotFound("user_not_found")
        self._db.add(UserRole(user_id=user_id, role=role))
        try:
            self._db.commit()
        except IntegrityError:
            self._db.rollback()

    def revoke(self, user_id: UUID, role: str) -> None:
        self._db.execute(
            delete(UserRole).where(UserRole.user_id == user_id, UserRole.role == role)
        )
        self._db.commit()

    def list_for_user(self, user_id: UUID) -> tuple[str, ...]:
        roles = self._db.scalars(
            select(UserRole.role).where(UserRole.user_id == user_id).order_by(UserRole.role)
        ).all()
        return tuple(roles)


@dataclass(slots=True)
class RoleAssignmentService:
    roles: SqlAlchemyRoleRepository
    authorization: RolePermissionPolicy

    def assign(self, actor: Actor, user_id: UUID, role: str) -> None:
        normalized = role.strip().lower()
        if normalized not in ALLOWED_GLOBAL_ROLES:
            raise InvalidRole("invalid_role")
        if not self.authorization.allows(actor, "roles.manage"):
            raise AuthorizationDenied()
        self.roles.assign(user_id, normalized)

    def revoke(self, actor: Actor, user_id: UUID, role: str) -> None:
        normalized = role.strip().lower()
        if normalized not in ALLOWED_GLOBAL_ROLES:
            raise InvalidRole("invalid_role")
        if normalized == "user":
            raise InvalidRole("base_user_role_required")
        if not self.authorization.allows(actor, "roles.manage"):
            raise AuthorizationDenied()
        self.roles.revoke(user_id, normalized)
