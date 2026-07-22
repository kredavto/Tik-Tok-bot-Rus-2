"""Add UNLIMIT plan and idempotent failed-publication refunds.

Revision ID: 0011_unlimit_and_usage_refunds
Revises: 0010_scrub_robokassa_signatures
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_unlimit_and_usage_refunds"
down_revision: str | None = "0010_scrub_robokassa_signatures"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("upload_jobs", sa.Column("usage_date", sa.Date(), nullable=True))
    op.add_column(
        "upload_jobs",
        sa.Column("usage_refunded_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute(
        "UPDATE upload_jobs "
        "SET usage_date = (created_at AT TIME ZONE 'Europe/Moscow')::date "
        "WHERE tiktok_publish_id IS NOT NULL"
    )
    op.execute(
        "WITH refunds AS ("
        "  SELECT user_id, usage_date, count(*) AS refund_count "
        "  FROM upload_jobs "
        "  WHERE tiktok_publish_id IS NOT NULL AND status = 'FAILED' "
        "  GROUP BY user_id, usage_date"
        ") "
        "UPDATE daily_usage AS usage "
        "SET upload_count = GREATEST(0, usage.upload_count - refunds.refund_count) "
        "FROM refunds "
        "WHERE usage.user_id = refunds.user_id "
        "AND usage.usage_date = refunds.usage_date"
    )
    op.execute(
        "UPDATE upload_jobs SET usage_refunded_at = updated_at "
        "WHERE tiktok_publish_id IS NOT NULL AND status = 'FAILED'"
    )
    op.execute(
        "INSERT INTO plans "
        "(id, title, price_rub, price_stars, daily_limit, duration_days, is_active) "
        "VALUES ('unlimit', 'UNLIMIT', 1999, 999, 0, 30, true) "
        "ON CONFLICT (id) DO UPDATE SET "
        "title = EXCLUDED.title, price_rub = EXCLUDED.price_rub, "
        "price_stars = EXCLUDED.price_stars, daily_limit = EXCLUDED.daily_limit, "
        "duration_days = EXCLUDED.duration_days, is_active = EXCLUDED.is_active"
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM plans WHERE id = 'unlimit' "
        "AND NOT EXISTS (SELECT 1 FROM subscriptions WHERE plan_id = 'unlimit') "
        "AND NOT EXISTS (SELECT 1 FROM payments WHERE plan_id = 'unlimit')"
    )
    op.drop_column("upload_jobs", "usage_refunded_at")
    op.drop_column("upload_jobs", "usage_date")
