from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .contracts import Actor
from .errors import AuthorizationDenied
from .models import TenantMembership, UserRole
from .permissions import RolePermissionPolicy, default_authorization_policy


@dataclass(frozen=True, slots=True)
class TenantAccessContext:
    tenant_id: UUID
    actor_id: UUID
    roles: tuple[str, ...]


class SqlAlchemyAccessService:
    def __init__(self, db: Session, policy: RolePermissionPolicy | None = None) -> None:
        self._db = db
        self._policy = policy or default_authorization_policy()

    def assign_global_role(self, user_id: UUID, role: str) -> None:
        normalized = role.strip().lower()
        if normalized not in self._policy.role_permissions:
            raise ValueError("unknown_role")
        if self._db.get(UserRole, {"user_id": user_id, "role": normalized}) is None:
            self._db.add(UserRole(user_id=user_id, role=normalized))
            self._db.commit()

    def tenant_context(self, actor: Actor, tenant_id: UUID) -> TenantAccessContext:
        membership = self._db.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == actor.id,
                TenantMembership.is_active.is_(True),
            )
        )
        if membership is None:
            raise AuthorizationDenied()
        return TenantAccessContext(tenant_id=tenant_id, actor_id=actor.id, roles=(membership.role,))

    def require_tenant_permission(self, actor: Actor, tenant_id: UUID, permission: str) -> None:
        context = self.tenant_context(actor, tenant_id)
        tenant_actor = Actor(
            id=actor.id,
            email=actor.email,
            display_name=actor.display_name,
            roles=context.roles,
        )
        if not self._policy.allows(tenant_actor, permission):
            raise AuthorizationDenied()
