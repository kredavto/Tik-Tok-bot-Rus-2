"""Store user-selected TikTok Direct Post options.

Revision ID: 0004_tiktok_post_options
Revises: 0003_subscription_integrity
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_tiktok_post_options"
down_revision: str | None = "0003_subscription_integrity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "upload_jobs",
        sa.Column(
            "privacy_level", sa.String(length=64), nullable=False, server_default="SELF_ONLY"
        ),
    )
    op.add_column(
        "upload_jobs",
        sa.Column("disable_comment", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "upload_jobs",
        sa.Column("disable_duet", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "upload_jobs",
        sa.Column("disable_stitch", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "upload_jobs",
        sa.Column("brand_content_toggle", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "upload_jobs",
        sa.Column("brand_organic_toggle", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("upload_jobs", "brand_organic_toggle")
    op.drop_column("upload_jobs", "brand_content_toggle")
    op.drop_column("upload_jobs", "disable_stitch")
    op.drop_column("upload_jobs", "disable_duet")
    op.drop_column("upload_jobs", "disable_comment")
    op.drop_column("upload_jobs", "privacy_level")
