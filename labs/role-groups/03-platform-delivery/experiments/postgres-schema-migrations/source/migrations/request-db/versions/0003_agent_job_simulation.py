"""add bounded local AI agent job simulation state

Revision ID: 0003_agent_jobs
Revises: 0002_request_products
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0003_agent_jobs"
down_revision: str | None = "0002_request_products"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_jobs",
        sa.Column("job_id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("owner_id", sa.String(255), nullable=False),
        sa.Column("repository_alias", sa.String(64), nullable=False),
        sa.Column("source_commit", sa.String(40), nullable=False),
        sa.Column("task_digest", sa.String(71), nullable=False),
        sa.Column("environment", sa.String(16), nullable=False),
        sa.Column("size", sa.String(16), nullable=False),
        sa.Column("sandbox_spec", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sandbox_spec_digest", sa.String(71), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="RECEIVED"),
        sa.Column("checkpoint_digest", sa.String(71)),
        sa.Column("checkpoint_sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("awaiting_action", sa.String(64)),
        sa.Column("event_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("compute_allocated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("runtime_authorized", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("environment IN ('DEV','TEST')", name="ck_agent_jobs_environment"),
        sa.CheckConstraint("size IN ('STANDARD','LARGE')", name="ck_agent_jobs_size"),
        sa.CheckConstraint("event_version >= 1", name="ck_agent_jobs_event_version"),
        sa.CheckConstraint("checkpoint_sequence >= 0", name="ck_agent_jobs_checkpoint_sequence"),
        sa.CheckConstraint("runtime_authorized = false", name="ck_agent_jobs_runtime_unauthorized"),
        schema="request_service",
    )
    op.create_index("ix_agent_jobs_owner_id", "agent_jobs", ["owner_id"], schema="request_service")
    op.create_index("ix_agent_jobs_status", "agent_jobs", ["status"], schema="request_service")


def downgrade() -> None:
    op.drop_table("agent_jobs", schema="request_service")
