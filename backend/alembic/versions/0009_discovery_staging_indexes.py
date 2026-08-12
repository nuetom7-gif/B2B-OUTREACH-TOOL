"""index paginated discovery staging queries"""

from alembic import op


revision = "0009_discovery_staging_indexes"
down_revision = "0008_discovery_diagnostics"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_discovery_staging_created_at", "discovery_staging_records", ["created_at"])
    op.create_index("ix_discovery_staging_run_id", "discovery_staging_records", ["run_id"])
    op.create_index("ix_discovery_staging_manual_review", "discovery_staging_records", ["needs_manual_review"])


def downgrade():
    op.drop_index("ix_discovery_staging_manual_review", table_name="discovery_staging_records")
    op.drop_index("ix_discovery_staging_run_id", table_name="discovery_staging_records")
    op.drop_index("ix_discovery_staging_created_at", table_name="discovery_staging_records")
