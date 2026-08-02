"""add qualification explainability fields

Revision ID: 0005_qual_explain
Revises: 0004_add_automation_tables
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_qual_explain"
down_revision = "0004_add_automation_tables"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return any(item["name"] == column for item in _inspector().get_columns(table))


def upgrade():
    if not _has_column("discovery_runs", "qualification_summary_json"):
        op.add_column(
            "discovery_runs",
            sa.Column("qualification_summary_json", sa.Text(), nullable=False, server_default="{}"),
        )
    if not _has_column("discovery_runs", "qualification_top_failure_reasons_json"):
        op.add_column(
            "discovery_runs",
            sa.Column("qualification_top_failure_reasons_json", sa.Text(), nullable=False, server_default="[]"),
        )
    if not _has_column("discovery_runs", "qualification_average_score"):
        op.add_column(
            "discovery_runs",
            sa.Column("qualification_average_score", sa.Float(), nullable=False, server_default="0"),
        )
    if not _has_column("discovery_runs", "qualification_evaluated_count"):
        op.add_column(
            "discovery_runs",
            sa.Column("qualification_evaluated_count", sa.Integer(), nullable=False, server_default="0"),
        )
    if not _has_column("discovery_runs", "qualification_imported_count"):
        op.add_column(
            "discovery_runs",
            sa.Column("qualification_imported_count", sa.Integer(), nullable=False, server_default="0"),
        )
    if not _has_column("discovery_runs", "qualification_manual_review_count"):
        op.add_column(
            "discovery_runs",
            sa.Column("qualification_manual_review_count", sa.Integer(), nullable=False, server_default="0"),
        )
    if not _has_column("discovery_runs", "qualification_rejected_count"):
        op.add_column(
            "discovery_runs",
            sa.Column("qualification_rejected_count", sa.Integer(), nullable=False, server_default="0"),
        )

    if not _has_column("discovery_staging_records", "final_status"):
        op.add_column(
            "discovery_staging_records",
            sa.Column("final_status", sa.String(length=32), nullable=False, server_default="staged"),
        )
    if not _has_column("discovery_staging_records", "qualification_threshold"):
        op.add_column(
            "discovery_staging_records",
            sa.Column("qualification_threshold", sa.Integer(), nullable=True),
        )
    if not _has_column("discovery_staging_records", "manual_review_threshold"):
        op.add_column(
            "discovery_staging_records",
            sa.Column("manual_review_threshold", sa.Integer(), nullable=True),
        )
    if not _has_column("discovery_staging_records", "qualification_evaluated_at"):
        op.add_column(
            "discovery_staging_records",
            sa.Column("qualification_evaluated_at", sa.DateTime(timezone=True), nullable=True),
        )
    if not _has_column("discovery_staging_records", "qualification_result_json"):
        op.add_column(
            "discovery_staging_records",
            sa.Column("qualification_result_json", sa.Text(), nullable=False, server_default="{}"),
        )


def downgrade():
    op.drop_column("discovery_staging_records", "qualification_result_json")
    op.drop_column("discovery_staging_records", "qualification_evaluated_at")
    op.drop_column("discovery_staging_records", "manual_review_threshold")
    op.drop_column("discovery_staging_records", "qualification_threshold")
    op.drop_column("discovery_staging_records", "final_status")

    op.drop_column("discovery_runs", "qualification_rejected_count")
    op.drop_column("discovery_runs", "qualification_manual_review_count")
    op.drop_column("discovery_runs", "qualification_imported_count")
    op.drop_column("discovery_runs", "qualification_evaluated_count")
    op.drop_column("discovery_runs", "qualification_average_score")
    op.drop_column("discovery_runs", "qualification_top_failure_reasons_json")
    op.drop_column("discovery_runs", "qualification_summary_json")
