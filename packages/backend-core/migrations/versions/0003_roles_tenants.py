"""roles and tenant memberships

Revision ID: 0003_roles_tenants
Revises: 0002_identity_sessions
Create Date: 2026-08-22
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_roles_tenants"
down_revision: str | None = "0002_identity_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "devforge_user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["devforge_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role"),
    )

    op.create_table(
        "devforge_tenants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_devforge_tenants_slug", "devforge_tenants", ["slug"], unique=False)

    op.create_table(
        "devforge_tenant_memberships",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["devforge_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["devforge_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("tenant_id", "user_id"),
    )

    op.execute(
        "INSERT INTO devforge_user_roles (user_id, role, created_at) "
        "SELECT id, 'user', created_at FROM devforge_users"
    )


def downgrade() -> None:
    op.drop_table("devforge_tenant_memberships")
    op.drop_index("ix_devforge_tenants_slug", table_name="devforge_tenants")
    op.drop_table("devforge_tenants")
    op.drop_table("devforge_user_roles")
