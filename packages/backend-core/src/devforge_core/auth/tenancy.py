from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .contracts import Actor
from .errors import AuthorizationDenied
from .models import Tenant, TenantMembership
from .permissions import RolePermissionPolicy


@dataclass(frozen=True, slots=True)
class TenantContext:
    tenant_id: UUID
    membership_role: str


class SqlAlchemyTenantAccessRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def tenant_is_active(self, tenant_id: UUID) -> bool:
        tenant = self._db.get(Tenant, tenant_id)
        return tenant is not None and tenant.is_active

    def resolve_membership(self, user_id: UUID, tenant_id: UUID) -> TenantContext | None:
        if not self.tenant_is_active(tenant_id):
            return None
        membership = self._db.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user_id,
                TenantMembership.is_active.is_(True),
            )
        )
        if membership is None:
            return None
        return TenantContext(tenant_id=tenant_id, membership_role=membership.role)


@dataclass(slots=True)
class TenantAuthorizationService:
    tenants: SqlAlchemyTenantAccessRepository
    authorization: RolePermissionPolicy

    def require_access(self, actor: Actor, tenant_id: UUID, permission: str) -> TenantContext:
        if not self.tenants.tenant_is_active(tenant_id):
            raise AuthorizationDenied()

        if self.authorization.allows(actor, "*"):
            return TenantContext(tenant_id=tenant_id, membership_role="admin")

        context = self.tenants.resolve_membership(actor.id, tenant_id)
        if context is None:
            raise AuthorizationDenied()

        scoped_actor = Actor(
            id=actor.id,
            email=actor.email,
            display_name=actor.display_name,
            roles=(context.membership_role,),
        )
        if not self.authorization.allows(scoped_actor, permission):
            raise AuthorizationDenied()
        return context
