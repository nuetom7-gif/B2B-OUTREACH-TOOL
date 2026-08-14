"""store the optional city used for a discovery job"""

from alembic import op
import sqlalchemy as sa


revision = "0010_discovery_job_city"
down_revision = "0009_discovery_staging_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("discovery_jobs", sa.Column("city", sa.String(length=128), nullable=True))


def downgrade():
    op.drop_column("discovery_jobs", "city")
