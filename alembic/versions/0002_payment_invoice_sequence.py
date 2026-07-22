"""Use a PostgreSQL sequence for Robokassa invoice identifiers.

Revision ID: 0002_payment_invoice_sequence
Revises: 0001_initial
Create Date: 2026-07-13
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_payment_invoice_sequence"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE payment_inv_id_seq START WITH 1001")
    op.execute(
        "SELECT setval('payment_inv_id_seq', "
        "GREATEST(COALESCE((SELECT MAX(provider_invoice_id) FROM payments), 1000), 1000))"
    )
    op.execute(
        "ALTER TABLE payments ALTER COLUMN provider_invoice_id "
        "SET DEFAULT nextval('payment_inv_id_seq')"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE payments ALTER COLUMN provider_invoice_id DROP DEFAULT")
    op.execute("DROP SEQUENCE payment_inv_id_seq")
