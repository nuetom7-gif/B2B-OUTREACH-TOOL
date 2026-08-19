"""store all discovery profiles that produced a contact"""

from alembic import op
import sqlalchemy as sa


revision = "0011_contact_discovery_profiles"
down_revision = "0010_discovery_job_city"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("contacts", sa.Column("discovery_profiles_json", sa.Text(), nullable=False, server_default="[]"))
    op.alter_column("contacts", "discovery_profiles_json", server_default=None)


def downgrade():
    op.drop_column("contacts", "discovery_profiles_json")
