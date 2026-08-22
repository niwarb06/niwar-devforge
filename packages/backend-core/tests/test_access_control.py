from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from devforge_core.auth.contracts import Actor
from devforge_core.auth.errors import AuthorizationDenied
from devforge_core.auth.models import Base, Tenant, TenantMembership, User
from devforge_core.auth.permissions import default_authorization_policy
from devforge_core.auth.roles import InvalidRole, RoleAssignmentService, SqlAlchemyRoleRepository
from devforge_core.auth.tenancy import SqlAlchemyTenantAccessRepository, TenantAuthorizationService


def make_db() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return factory()


def test_role_assignment_requires_privileged_actor() -> None:
    with make_db() as db:
        target = User(email="target@example.com", password_hash="hash")
        db.add(target)
        db.commit()
        db.refresh(target)

        service = RoleAssignmentService(
            roles=SqlAlchemyRoleRepository(db),
            authorization=default_authorization_policy(),
        )
        user_actor = Actor(
            id=uuid4(), email="user@example.com", display_name=None, roles=("user",)
        )
        admin_actor = Actor(
            id=uuid4(), email="admin@example.com", display_name=None, roles=("admin",)
        )

        with pytest.raises(AuthorizationDenied):
            service.assign(user_actor, target.id, "admin")

        service.assign(admin_actor, target.id, "admin")
        service.assign(admin_actor, target.id, "admin")
        assert service.roles.list_for_user(target.id) == ("admin",)

        with pytest.raises(InvalidRole):
            service.revoke(admin_actor, target.id, "user")


def test_tenant_authorization_denies_cross_tenant_access() -> None:
    with make_db() as db:
        member = User(email="member@example.com", password_hash="hash")
        tenant_a = Tenant(slug="tenant-a", name="Tenant A")
        tenant_b = Tenant(slug="tenant-b", name="Tenant B")
        db.add_all([member, tenant_a, tenant_b])
        db.flush()
        db.add(
            TenantMembership(
                tenant_id=tenant_a.id,
                user_id=member.id,
                role="member",
            )
        )
        db.commit()

        actor = Actor(id=member.id, email=member.email, display_name=None, roles=("user",))
        service = TenantAuthorizationService(
            tenants=SqlAlchemyTenantAccessRepository(db),
            authorization=default_authorization_policy(),
        )

        context = service.require_access(actor, tenant_a.id, "tenant.read")
        assert context.tenant_id == tenant_a.id
        assert context.membership_role == "member"

        with pytest.raises(AuthorizationDenied):
            service.require_access(actor, tenant_b.id, "tenant.read")

        with pytest.raises(AuthorizationDenied):
            service.require_access(actor, tenant_a.id, "tenant.write")


def test_tenant_roles_are_namespaced_from_global_roles() -> None:
    policy = default_authorization_policy()
    global_owner = Actor(id=uuid4(), email=None, display_name=None, roles=("owner",))
    tenant_owner = Actor(id=uuid4(), email=None, display_name=None, roles=("tenant:owner",))

    assert policy.allows(global_owner, "tenant.write") is False
    assert policy.allows(tenant_owner, "tenant.write") is True
    assert policy.allows(tenant_owner, "roles.manage") is False


def test_global_admin_cannot_bypass_inactive_tenant_boundary() -> None:
    with make_db() as db:
        tenant = Tenant(slug="disabled", name="Disabled", is_active=False)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        admin = Actor(id=uuid4(), email="admin@example.com", display_name=None, roles=("admin",))
        service = TenantAuthorizationService(
            tenants=SqlAlchemyTenantAccessRepository(db),
            authorization=default_authorization_policy(),
        )

        with pytest.raises(AuthorizationDenied):
            service.require_access(admin, tenant.id, "tenant.read")
