"""Add atomic webhook delivery claims.

Revision ID: 0007_webhook_delivery_integrity
Revises: 0006_admin_console
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_webhook_delivery_integrity"
down_revision: str | None = "0006_admin_console"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "webhook_events",
        sa.Column("deduplication_key", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "webhook_events",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "uq_webhook_events_deduplication_key",
        "webhook_events",
        ["deduplication_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_webhook_events_deduplication_key",
        table_name="webhook_events",
    )
    op.drop_column("webhook_events", "locked_until")
    op.drop_column("webhook_events", "deduplication_key")
