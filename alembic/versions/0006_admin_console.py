"""Add typed settings and administrative request metadata.

Revision ID: 0006_admin_console
Revises: 0005_maintenance_state
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_admin_console"
down_revision: str | None = "0005_maintenance_state"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "admin_actions",
        sa.Column("ip_address", sa.String(length=45), nullable=True),
    )
    op.add_column(
        "system_settings",
        sa.Column(
            "value_type",
            sa.String(length=16),
            nullable=False,
            server_default="string",
        ),
    )
    op.add_column(
        "system_settings",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "system_settings",
        sa.Column(
            "is_editable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "system_settings",
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_system_settings_updated_by_users",
        "system_settings",
        "users",
        ["updated_by"],
        ["id"],
    )
    op.create_index(
        "ix_system_settings_updated_by",
        "system_settings",
        ["updated_by"],
    )


def downgrade() -> None:
    op.drop_index("ix_system_settings_updated_by", table_name="system_settings")
    op.drop_constraint(
        "fk_system_settings_updated_by_users",
        "system_settings",
        type_="foreignkey",
    )
    op.drop_column("system_settings", "updated_by")
    op.drop_column("system_settings", "is_editable")
    op.drop_column("system_settings", "description")
    op.drop_column("system_settings", "value_type")
    op.drop_column("admin_actions", "ip_address")
