"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column("agreement_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"])
    op.create_index(op.f("ix_users_role"), "users", ["role"])
    op.create_index(op.f("ix_users_is_blocked"), "users", ["is_blocked"])

    op.create_table(
        "plans",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=64), nullable=False),
        sa.Column("price_rub", sa.Integer(), nullable=False),
        sa.Column("daily_limit", sa.Integer(), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title"),
    )

    op.create_table(
        "system_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index(op.f("ix_system_settings_key"), "system_settings", ["key"])

    op.create_table(
        "tiktok_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("open_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tiktok_accounts_open_id"), "tiktok_accounts", ["open_id"])
    op.create_index(op.f("ix_tiktok_accounts_user_id"), "tiktok_accounts", ["user_id"])

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subscriptions_ends_at"), "subscriptions", ["ends_at"])
    op.create_index(op.f("ix_subscriptions_plan_id"), "subscriptions", ["plan_id"])
    op.create_index(op.f("ix_subscriptions_status"), "subscriptions", ["status"])
    op.create_index(op.f("ix_subscriptions_user_id"), "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_user_status_ends", "subscriptions", ["user_id", "status", "ends_at"])

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("plan_id", sa.String(length=32), nullable=False),
        sa.Column("amount_rub", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_invoice_id", sa.Integer(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_invoice_id"),
    )
    op.create_index(op.f("ix_payments_plan_id"), "payments", ["plan_id"])
    op.create_index(op.f("ix_payments_provider_invoice_id"), "payments", ["provider_invoice_id"])
    op.create_index(op.f("ix_payments_status"), "payments", ["status"])
    op.create_index(op.f("ix_payments_user_id"), "payments", ["user_id"])
    op.create_index("ix_payments_status_created", "payments", ["status", "created_at"])
    op.create_index("ix_payments_user_created", "payments", ["user_id", "created_at"])

    op.create_table(
        "upload_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tiktok_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("telegram_file_id", sa.String(length=255), nullable=False),
        sa.Column("local_path", sa.Text(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("tiktok_publish_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tiktok_account_id"], ["tiktok_accounts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_upload_jobs_created_at"), "upload_jobs", ["created_at"])
    op.create_index(op.f("ix_upload_jobs_status"), "upload_jobs", ["status"])
    op.create_index(op.f("ix_upload_jobs_tiktok_publish_id"), "upload_jobs", ["tiktok_publish_id"])
    op.create_index(op.f("ix_upload_jobs_user_id"), "upload_jobs", ["user_id"])
    op.create_index("ix_upload_jobs_status_created", "upload_jobs", ["status", "created_at"])
    op.create_index("ix_upload_jobs_user_created", "upload_jobs", ["user_id", "created_at"])

    op.create_table(
        "upload_job_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("upload_job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["upload_job_id"], ["upload_jobs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_upload_job_events_created_at"), "upload_job_events", ["created_at"])
    op.create_index(op.f("ix_upload_job_events_status"), "upload_job_events", ["status"])
    op.create_index(op.f("ix_upload_job_events_upload_job_id"), "upload_job_events", ["upload_job_id"])
    op.create_index(op.f("ix_upload_job_events_user_id"), "upload_job_events", ["user_id"])
    op.create_index("ix_upload_job_events_job_created", "upload_job_events", ["upload_job_id", "created_at"])
    op.create_index("ix_upload_job_events_user_created", "upload_job_events", ["user_id", "created_at"])

    op.create_table(
        "daily_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("upload_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_daily_usage_user_date", "daily_usage", ["user_id", "usage_date"], unique=True)
    op.create_index(op.f("ix_daily_usage_usage_date"), "daily_usage", ["usage_date"])
    op.create_index(op.f("ix_daily_usage_user_id"), "daily_usage", ["user_id"])

    op.create_table(
        "webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_webhook_events_event_type"), "webhook_events", ["event_type"])
    op.create_index(op.f("ix_webhook_events_external_id"), "webhook_events", ["external_id"])
    op.create_index(op.f("ix_webhook_events_provider"), "webhook_events", ["provider"])
    op.create_index(op.f("ix_webhook_events_status"), "webhook_events", ["status"])

    op.create_table(
        "admin_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admin_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target_type", sa.String(length=128), nullable=True),
        sa.Column("target_id", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["admin_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_actions_action"), "admin_actions", ["action"])
    op.create_index(op.f("ix_admin_actions_admin_user_id"), "admin_actions", ["admin_user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_actions_admin_user_id"), table_name="admin_actions")
    op.drop_index(op.f("ix_admin_actions_action"), table_name="admin_actions")
    op.drop_table("admin_actions")
    op.drop_index(op.f("ix_webhook_events_status"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_provider"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_external_id"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_event_type"), table_name="webhook_events")
    op.drop_table("webhook_events")
    op.drop_index(op.f("ix_daily_usage_user_id"), table_name="daily_usage")
    op.drop_index(op.f("ix_daily_usage_usage_date"), table_name="daily_usage")
    op.drop_index("ix_daily_usage_user_date", table_name="daily_usage")
    op.drop_table("daily_usage")
    op.drop_index("ix_upload_job_events_user_created", table_name="upload_job_events")
    op.drop_index("ix_upload_job_events_job_created", table_name="upload_job_events")
    op.drop_index(op.f("ix_upload_job_events_user_id"), table_name="upload_job_events")
    op.drop_index(op.f("ix_upload_job_events_upload_job_id"), table_name="upload_job_events")
    op.drop_index(op.f("ix_upload_job_events_status"), table_name="upload_job_events")
    op.drop_index(op.f("ix_upload_job_events_created_at"), table_name="upload_job_events")
    op.drop_table("upload_job_events")
    op.drop_index(op.f("ix_upload_jobs_user_id"), table_name="upload_jobs")
    op.drop_index("ix_upload_jobs_user_created", table_name="upload_jobs")
    op.drop_index("ix_upload_jobs_status_created", table_name="upload_jobs")
    op.drop_index(op.f("ix_upload_jobs_tiktok_publish_id"), table_name="upload_jobs")
    op.drop_index(op.f("ix_upload_jobs_status"), table_name="upload_jobs")
    op.drop_index(op.f("ix_upload_jobs_created_at"), table_name="upload_jobs")
    op.drop_table("upload_jobs")
    op.drop_index(op.f("ix_payments_user_id"), table_name="payments")
    op.drop_index("ix_payments_user_created", table_name="payments")
    op.drop_index("ix_payments_status_created", table_name="payments")
    op.drop_index(op.f("ix_payments_status"), table_name="payments")
    op.drop_index(op.f("ix_payments_provider_invoice_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_plan_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_index(op.f("ix_subscriptions_user_id"), table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_status_ends", table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_status"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_plan_id"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_ends_at"), table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index(op.f("ix_tiktok_accounts_user_id"), table_name="tiktok_accounts")
    op.drop_index(op.f("ix_tiktok_accounts_open_id"), table_name="tiktok_accounts")
    op.drop_table("tiktok_accounts")
    op.drop_index(op.f("ix_system_settings_key"), table_name="system_settings")
    op.drop_table("system_settings")
    op.drop_table("plans")
    op.drop_index(op.f("ix_users_is_blocked"), table_name="users")
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
