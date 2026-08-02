"""provider agnostic discovery source fields

Revision ID: 0003_provider_fields
Revises: 0002_phase2_discovery
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_provider_fields"
down_revision = "0002_phase2_discovery"
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
    if not _has_column("companies", "source_provider"):
        op.add_column("companies", sa.Column("source_provider", sa.String(length=64), nullable=True))
    if not _has_column("companies", "source_record_id"):
        op.add_column("companies", sa.Column("source_record_id", sa.String(length=128), nullable=True))
    if not _has_column("contacts", "source_provider"):
        op.add_column("contacts", sa.Column("source_provider", sa.String(length=64), nullable=True))
    if not _has_column("contacts", "source_record_id"):
        op.add_column("contacts", sa.Column("source_record_id", sa.String(length=128), nullable=True))


def downgrade():
    op.drop_column("contacts", "source_record_id")
    op.drop_column("contacts", "source_provider")
    op.drop_column("companies", "source_record_id")
    op.drop_column("companies", "source_provider")
