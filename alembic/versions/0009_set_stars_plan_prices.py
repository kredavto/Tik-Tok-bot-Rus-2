"""Set approved Telegram Stars plan prices.

Revision ID: 0009_set_stars_plan_prices
Revises: 0008_telegram_stars_payments
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_set_stars_plan_prices"
down_revision: str | None = "0008_telegram_stars_payments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    plans = sa.table(
        "plans",
        sa.column("id", sa.String()),
        sa.column("price_stars", sa.Integer()),
    )
    op.execute(plans.update().where(plans.c.id == "pro").values(price_stars=199))
    op.execute(plans.update().where(plans.c.id == "business").values(price_stars=499))


def downgrade() -> None:
    plans = sa.table(
        "plans",
        sa.column("id", sa.String()),
        sa.column("price_stars", sa.Integer()),
    )
    op.execute(
        plans.update()
        .where(plans.c.id == "pro", plans.c.price_stars == 199)
        .values(price_stars=None)
    )
    op.execute(
        plans.update()
        .where(plans.c.id == "business", plans.c.price_stars == 499)
        .values(price_stars=None)
    )
