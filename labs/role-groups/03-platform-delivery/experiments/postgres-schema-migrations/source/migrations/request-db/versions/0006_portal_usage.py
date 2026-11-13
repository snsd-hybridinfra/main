"""Numeric local-simulator usage only; no prompts or provider billing."""
from alembic import op
import sqlalchemy as sa

revision = "0006_portal_usage"
down_revision = "0005_agent_budget_trace"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("portal_usage",
        sa.Column("usage_id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(64), nullable=False, unique=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("owner_id", sa.String(255), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("input_units", sa.Integer(), nullable=False),
        sa.Column("output_units", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="request_service")
    op.create_index("ix_portal_usage_tenant_id", "portal_usage", ["tenant_id"], schema="request_service")
    op.create_index("ix_portal_usage_owner_id", "portal_usage", ["owner_id"], schema="request_service")


def downgrade():
    op.drop_table("portal_usage", schema="request_service")
