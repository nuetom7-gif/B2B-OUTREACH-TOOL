"""add discovery reason tracking

Revision ID: 0006_discovery_reasons
Revises: 0005_qual_explain
Create Date: 2026-08-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_discovery_reasons"
down_revision = "0005_qual_explain"
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
    if not _has_column("discovery_runs", "reason_breakdown_json"):
        op.add_column(
            "discovery_runs",
            sa.Column("reason_breakdown_json", sa.Text(), nullable=False, server_default="{}"),
        )

    if not _has_column("discovery_staging_records", "decision_stage"):
        op.add_column(
            "discovery_staging_records",
            sa.Column("decision_stage", sa.String(length=64), nullable=False, server_default="staged"),
        )
    if not _has_column("discovery_staging_records", "reason_category"):
        op.add_column(
            "discovery_staging_records",
            sa.Column("reason_category", sa.String(length=64), nullable=False, server_default="staged"),
        )
    if not _has_column("discovery_staging_records", "reason_details_json"):
        op.add_column(
            "discovery_staging_records",
            sa.Column("reason_details_json", sa.Text(), nullable=False, server_default="{}"),
        )


def downgrade():
    op.drop_column("discovery_staging_records", "reason_details_json")
    op.drop_column("discovery_staging_records", "reason_category")
    op.drop_column("discovery_staging_records", "decision_stage")
    op.drop_column("discovery_runs", "reason_breakdown_json")
