"""add automation tables

Revision ID: 0004_add_automation_tables
Revises: 0003_provider_fields
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_add_automation_tables"
down_revision = "0003_provider_fields"
branch_labels = None
depends_on = None


def create_table_if_missing(name, *args, **kwargs):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if name in inspector.get_table_names():
        return
    op.create_table(name, *args, **kwargs)


def upgrade():
    create_table_if_missing(
        "workspace_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("key", name="uq_workspace_settings_key"),
    )
    create_table_if_missing(
        "daily_lead_targets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_segment", sa.String(length=255), nullable=False),
        sa.Column("target_leads_per_day", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("companies_per_run", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("contacts_per_company", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("max_emails_per_batch", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("default_campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("default_mailbox_id", sa.Integer(), sa.ForeignKey("mailboxes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("product_segment", name="uq_daily_lead_targets_product_segment"),
    )
    create_table_if_missing(
        "discovery_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_segment", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=128), nullable=True),
        sa.Column("keywords", sa.Text(), nullable=False, server_default=""),
        sa.Column("company_limit", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("contacts_per_company", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("max_leads", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("current_step", sa.String(length=255), nullable=False, server_default="queued"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("contacts_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("qualified_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("api_calls_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quota_remaining", sa.Integer(), nullable=True),
        sa.Column("request_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("result_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    create_table_if_missing(
        "discovery_job_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("discovery_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.String(length=32), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("discovery_job_logs")
    op.drop_table("discovery_jobs")
    op.drop_table("daily_lead_targets")
    op.drop_table("workspace_settings")
