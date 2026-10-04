"""identity and session tables

Revision ID: 0002_identity_sessions
Revises: 0001_backend_core_baseline
Create Date: 2026-08-22
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_identity_sessions"
down_revision: str | None = "0001_backend_core_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "devforge_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_devforge_users_email", "devforge_users", ["email"], unique=False)

    op.create_table(
        "devforge_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["devforge_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_devforge_sessions_expires_at", "devforge_sessions", ["expires_at"], unique=False
    )
    op.create_index(
        "ix_devforge_sessions_token_hash", "devforge_sessions", ["token_hash"], unique=False
    )
    op.create_index("ix_devforge_sessions_user_id", "devforge_sessions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_devforge_sessions_user_id", table_name="devforge_sessions")
    op.drop_index("ix_devforge_sessions_token_hash", table_name="devforge_sessions")
    op.drop_index("ix_devforge_sessions_expires_at", table_name="devforge_sessions")
    op.drop_table("devforge_sessions")
    op.drop_index("ix_devforge_users_email", table_name="devforge_users")
    op.drop_table("devforge_users")
