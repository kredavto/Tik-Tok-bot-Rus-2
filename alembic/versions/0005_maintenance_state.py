"""Track subscription expiration notices and blocked token refreshes.

Revision ID: 0005_maintenance_state
Revises: 0004_tiktok_post_options
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_maintenance_state"
down_revision: str | None = "0004_tiktok_post_options"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("expiration_notified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE subscriptions SET expiration_notified_at = NOW() "
        "WHERE status = 'expired' AND plan_id <> 'free'"
    )
    op.add_column(
        "tiktok_accounts",
        sa.Column("refresh_blocked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tiktok_accounts",
        sa.Column("refresh_error_code", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_tiktok_accounts_refresh_due",
        "tiktok_accounts",
        ["token_expires_at", "refresh_blocked_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_tiktok_accounts_refresh_due", table_name="tiktok_accounts")
    op.drop_column("tiktok_accounts", "refresh_error_code")
    op.drop_column("tiktok_accounts", "refresh_blocked_at")
    op.drop_column("subscriptions", "expiration_notified_at")
