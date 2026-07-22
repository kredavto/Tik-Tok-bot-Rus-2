"""Enforce one active subscription per user.

Revision ID: 0003_subscription_integrity
Revises: 0002_payment_invoice_sequence
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_subscription_integrity"
down_revision: str | None = "0002_payment_invoice_sequence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE plans SET title = UPPER(id) WHERE id IN ('free', 'pro', 'business')")
    op.execute(
        "UPDATE subscriptions SET status = 'expired' "
        "WHERE status = 'active' AND ends_at IS NOT NULL AND ends_at < NOW()"
    )
    op.execute(
        "WITH ranked AS ("
        "  SELECT id, ROW_NUMBER() OVER ("
        "    PARTITION BY user_id "
        "    ORDER BY CASE WHEN plan_id = 'free' THEN 1 ELSE 0 END, created_at DESC"
        "  ) AS position "
        "  FROM subscriptions WHERE status = 'active'"
        ") "
        "UPDATE subscriptions SET status = 'expired', ends_at = COALESCE(ends_at, NOW()) "
        "WHERE id IN (SELECT id FROM ranked WHERE position > 1)"
    )
    op.create_index(
        "uq_subscriptions_one_active_per_user",
        "subscriptions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_subscriptions_one_active_per_user", table_name="subscriptions")
