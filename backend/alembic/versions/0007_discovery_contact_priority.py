"""add discovery contact priority explainability fields

Revision ID: 0007_discovery_contact_priority
Revises: 0006_discovery_reasons
Create Date: 2026-08-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_discovery_contact_priority"
down_revision = "0006_discovery_reasons"
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
    if not _has_column("companies", "discovery_contacts_returned"):
        op.add_column(
            "companies",
            sa.Column("discovery_contacts_returned", sa.Integer(), nullable=False, server_default="0"),
        )
    if not _has_column("companies", "contact_status"):
        op.add_column(
            "companies",
            sa.Column("contact_status", sa.String(length=64), nullable=False, server_default="No Contact Found"),
        )
    if not _has_column("companies", "fallback_contact_used"):
        op.add_column(
            "companies",
            sa.Column("fallback_contact_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    if not _has_column("contacts", "contact_priority"):
        op.add_column(
            "contacts",
            sa.Column("contact_priority", sa.String(length=32), nullable=True),
        )
    if not _has_column("contacts", "recommended_primary_contact"):
        op.add_column(
            "contacts",
            sa.Column("recommended_primary_contact", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if not _has_column("contacts", "fallback_contact_used"):
        op.add_column(
            "contacts",
            sa.Column("fallback_contact_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if not _has_column("contacts", "contact_selection_reason"):
        op.add_column(
            "contacts",
            sa.Column("contact_selection_reason", sa.Text(), nullable=True),
        )


def downgrade():
    op.drop_column("contacts", "contact_selection_reason")
    op.drop_column("contacts", "fallback_contact_used")
    op.drop_column("contacts", "recommended_primary_contact")
    op.drop_column("contacts", "contact_priority")
    op.drop_column("companies", "fallback_contact_used")
    op.drop_column("companies", "contact_status")
    op.drop_column("companies", "discovery_contacts_returned")
