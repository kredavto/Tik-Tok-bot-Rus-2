"""Add Telegram Stars payment fields.

Revision ID: 0008_telegram_stars_payments
Revises: 0007_webhook_delivery_integrity
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_telegram_stars_payments"
down_revision: str | None = "0007_webhook_delivery_integrity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("price_stars", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("amount_stars", sa.Integer(), nullable=True))
    op.add_column(
        "payments",
        sa.Column("currency", sa.String(length=8), server_default="RUB", nullable=False),
    )
    op.add_column(
        "payments",
        sa.Column("provider_charge_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "uq_payments_provider_charge",
        "payments",
        ["provider", "provider_charge_id"],
        unique=True,
        postgresql_where=sa.text("provider_charge_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_payments_provider_charge", table_name="payments")
    op.drop_column("payments", "provider_charge_id")
    op.drop_column("payments", "currency")
    op.drop_column("payments", "amount_stars")
    op.drop_column("plans", "price_stars")
