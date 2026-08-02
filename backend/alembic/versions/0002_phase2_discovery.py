"""phase 2 discovery staging and metadata

Revision ID: 0002_phase2_discovery
Revises: 0001_initial
Create Date: 2026-07-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_phase2_discovery"
down_revision = "0001_initial"
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


def _has_unique_constraint(table: str, name: str) -> bool:
    if not _has_table(table):
        return False
    return any(item["name"] == name for item in _inspector().get_unique_constraints(table))


def upgrade():
    if not _has_column("companies", "apollo_organization_id"):
        op.add_column("companies", sa.Column("apollo_organization_id", sa.String(length=64), nullable=True))
    if not _has_column("companies", "apollo_last_updated"):
        op.add_column("companies", sa.Column("apollo_last_updated", sa.DateTime(timezone=True), nullable=True))
    if not _has_column("companies", "last_sync"):
        op.add_column("companies", sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True))
    if not _has_column("companies", "sync_status"):
        op.add_column(
            "companies",
            sa.Column("sync_status", sa.String(length=32), nullable=False, server_default="pending"),
        )
    if not _has_column("companies", "needs_manual_review"):
        op.add_column(
            "companies",
            sa.Column("needs_manual_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
    if not _has_column("companies", "owner_id"):
        op.add_column("companies", sa.Column("owner_id", sa.Integer(), nullable=True))
    if not _has_column("companies", "assignment_status"):
        op.add_column(
            "companies",
            sa.Column("assignment_status", sa.String(length=32), nullable=False, server_default="unassigned"),
        )
    if not _has_column("companies", "assigned_at"):
        op.add_column("companies", sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True))
    if not _has_column("companies", "assignment_source"):
        op.add_column("companies", sa.Column("assignment_source", sa.String(length=64), nullable=True))
    if not _has_column("companies", "lead_score"):
        op.add_column("companies", sa.Column("lead_score", sa.Integer(), nullable=False, server_default="0"))
    if not _has_unique_constraint("companies", "uq_companies_apollo_organization_id"):
        op.create_unique_constraint("uq_companies_apollo_organization_id", "companies", ["apollo_organization_id"])

    if not _has_column("contacts", "apollo_person_id"):
        op.add_column("contacts", sa.Column("apollo_person_id", sa.String(length=64), nullable=True))
    if not _has_column("contacts", "verification_status"):
        op.add_column(
            "contacts",
            sa.Column("verification_status", sa.String(length=32), nullable=False, server_default="unknown"),
        )
    if not _has_column("contacts", "last_sync"):
        op.add_column("contacts", sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True))
    if not _has_column("contacts", "lead_score"):
        op.add_column("contacts", sa.Column("lead_score", sa.Integer(), nullable=False, server_default="0"))
    if not _has_unique_constraint("contacts", "uq_contacts_apollo_person_id"):
        op.create_unique_constraint("uq_contacts_apollo_person_id", "contacts", ["apollo_person_id"])

    if not _has_table("discovery_runs"):
        op.create_table(
            "discovery_runs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("product_name", sa.String(length=255), nullable=False),
            sa.Column("search_frequency", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("duration_seconds", sa.Integer(), nullable=True),
            sa.Column("companies_found", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("companies_imported", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("companies_updated", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("companies_skipped", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("contacts_found", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("contacts_imported", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("contacts_updated", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("contacts_skipped", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("api_calls_used", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("quota_remaining", sa.Integer(), nullable=True),
            sa.Column("errors_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("warnings_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    if not _has_table("discovery_staging_records"):
        op.create_table(
            "discovery_staging_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("run_id", sa.Integer(), sa.ForeignKey("discovery_runs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("product_name", sa.String(length=255), nullable=False),
            sa.Column("provider_name", sa.String(length=64), nullable=False),
            sa.Column("record_type", sa.String(length=32), nullable=False),
            sa.Column("apollo_organization_id", sa.String(length=64), nullable=True),
            sa.Column("apollo_person_id", sa.String(length=64), nullable=True),
            sa.Column("company_name", sa.String(length=255), nullable=True),
            sa.Column("company_domain", sa.String(length=255), nullable=True),
            sa.Column("industry", sa.String(length=255), nullable=True),
            sa.Column("country", sa.String(length=128), nullable=True),
            sa.Column("region", sa.String(length=128), nullable=True),
            sa.Column("employee_count", sa.Integer(), nullable=True),
            sa.Column("company_size", sa.String(length=64), nullable=True),
            sa.Column("person_name", sa.String(length=255), nullable=True),
            sa.Column("person_title", sa.String(length=255), nullable=True),
            sa.Column("person_email", sa.String(length=255), nullable=True),
            sa.Column("person_phone", sa.String(length=64), nullable=True),
            sa.Column("person_linkedin_url", sa.String(length=512), nullable=True),
            sa.Column("person_seniority", sa.String(length=64), nullable=True),
            sa.Column("raw_payload_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("qualification_status", sa.String(length=32), nullable=False, server_default="staged"),
            sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("confidence", sa.String(length=32), nullable=False, server_default="unknown"),
            sa.Column("needs_manual_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("sync_status", sa.String(length=32), nullable=False, server_default="staged"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("warning_message", sa.Text(), nullable=True),
            sa.Column("crm_company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
            sa.Column("crm_contact_id", sa.Integer(), sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True),
            sa.Column("apollo_last_updated", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade():
    op.drop_table("discovery_staging_records")
    op.drop_table("discovery_runs")
    op.drop_constraint("uq_contacts_apollo_person_id", "contacts", type_="unique")
    op.drop_column("contacts", "lead_score")
    op.drop_column("contacts", "last_sync")
    op.drop_column("contacts", "verification_status")
    op.drop_column("contacts", "apollo_person_id")
    op.drop_constraint("uq_companies_apollo_organization_id", "companies", type_="unique")
    op.drop_column("companies", "lead_score")
    op.drop_column("companies", "assignment_source")
    op.drop_column("companies", "assigned_at")
    op.drop_column("companies", "assignment_status")
    op.drop_column("companies", "owner_id")
    op.drop_column("companies", "needs_manual_review")
    op.drop_column("companies", "sync_status")
    op.drop_column("companies", "last_sync")
    op.drop_column("companies", "apollo_last_updated")
    op.drop_column("companies", "apollo_organization_id")
