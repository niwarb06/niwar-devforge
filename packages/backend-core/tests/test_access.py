from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from devforge_core.auth.access import SqlAlchemyAccessService
from devforge_core.auth.contracts import Actor
from devforge_core.auth.errors import AuthorizationDenied
from devforge_core.auth.models import Base, Tenant, TenantMembership, User, UserRole


def _factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def test_role_assignment_is_persisted_and_idempotent() -> None:
    factory = _factory()
    with factory() as db:
        user = User(email=f"role-{uuid4()}@example.com", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)

        access = SqlAlchemyAccessService(db)
        access.assign_global_role(user.id, "admin")
        access.assign_global_role(user.id, "admin")

        roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
        assert [role.role for role in roles] == ["admin"]


def test_tenant_permission_requires_active_membership() -> None:
    factory = _factory()
    with factory() as db:
        user = User(email=f"tenant-{uuid4()}@example.com", password_hash="hash")
        tenant = Tenant(slug=f"tenant-{uuid4()}", name="Tenant")
        db.add_all([user, tenant])
        db.commit()
        db.refresh(user)
        db.refresh(tenant)

        actor = Actor(id=user.id, email=user.email, display_name=None, roles=("admin",))
        access = SqlAlchemyAccessService(db)

        with pytest.raises(AuthorizationDenied):
            access.require_tenant_permission(actor, tenant.id, "profile.read:self")

        db.add(TenantMembership(tenant_id=tenant.id, user_id=user.id, role="user"))
        db.commit()
        access.require_tenant_permission(actor, tenant.id, "profile.read:self")


def test_global_admin_does_not_bypass_tenant_membership() -> None:
    factory = _factory()
    with factory() as db:
        user = User(email=f"admin-{uuid4()}@example.com", password_hash="hash")
        tenant = Tenant(slug=f"tenant-{uuid4()}", name="Tenant")
        db.add_all([user, tenant])
        db.commit()
        db.refresh(user)
        db.refresh(tenant)

        actor = Actor(id=user.id, email=user.email, display_name=None, roles=("admin",))
        with pytest.raises(AuthorizationDenied):
            SqlAlchemyAccessService(db).require_tenant_permission(
                actor,
                tenant.id,
                "users.manage",
            )
