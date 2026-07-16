"""Remove Robokassa signatures from stored audit payloads.

Revision ID: 0010_scrub_robokassa_signatures
Revises: 0009_set_stars_plan_prices
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010_scrub_robokassa_signatures"
down_revision: str | None = "0009_set_stars_plan_prices"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE payments SET raw_payload = raw_payload - 'SignatureValue' "
        "WHERE raw_payload ? 'SignatureValue'"
    )
    op.execute(
        "UPDATE webhook_events SET payload = payload - 'SignatureValue' "
        "WHERE provider = 'robokassa' AND payload ? 'SignatureValue'"
    )


def downgrade() -> None:
    # Removed callback signatures must not be restored.
    pass
