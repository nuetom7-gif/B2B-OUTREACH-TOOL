"""store Apollo diagnostic payloads and qualification inputs"""

from alembic import op
import sqlalchemy as sa


revision = "0008_discovery_diagnostics"
down_revision = "0007_discovery_contact_priority"
branch_labels = None
depends_on = None


def upgrade():
    columns = (
        "raw_organization_json",
        "organization_mapping_json",
        "people_request_json",
        "raw_people_response_json",
        "normalized_company_json",
        "normalized_contacts_json",
        "qualification_input_json",
    )
    inspector = sa.inspect(op.get_bind())
    existing = {item["name"] for item in inspector.get_columns("discovery_staging_records")}
    for name in columns:
        if name not in existing:
            op.add_column(
                "discovery_staging_records",
                sa.Column(name, sa.Text(), nullable=False, server_default=sa.text("'{}'")),
            )


def downgrade():
    for name in (
        "qualification_input_json",
        "normalized_contacts_json",
        "normalized_company_json",
        "raw_people_response_json",
        "people_request_json",
        "organization_mapping_json",
        "raw_organization_json",
    ):
        op.drop_column("discovery_staging_records", name)
