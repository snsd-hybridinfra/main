"""add local queue outbox and non-secret credential lease metadata

Revision ID: 0004_agent_integrations
Revises: 0003_agent_jobs
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0004_agent_integrations"
down_revision: str | None = "0003_agent_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_queue_items",
        sa.Column("queue_id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), nullable=False, unique=True),
        sa.Column("envelope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("envelope_digest", sa.String(71), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="READY"),
        sa.Column("delivery_attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("event_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["request_service.agent_jobs.job_id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('READY','CLAIMED','PAUSED','DONE','CANCELLED')", name="ck_agent_queue_status"),
        sa.CheckConstraint("delivery_attempt >= 0", name="ck_agent_queue_delivery_attempt"),
        sa.CheckConstraint("event_version >= 1", name="ck_agent_queue_event_version"),
        schema="request_service",
    )
    op.create_index("ix_agent_queue_items_job_id", "agent_queue_items", ["job_id"], schema="request_service")
    op.create_index("ix_agent_queue_items_status", "agent_queue_items", ["status"], schema="request_service")

    op.create_table(
        "agent_credential_leases",
        sa.Column("lease_id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("credential_class", sa.String(32), nullable=False),
        sa.Column("lease_reference", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("issued_for_event_version", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["job_id"], ["request_service.agent_jobs.job_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("job_id", "credential_class", "issued_for_event_version", name="uq_agent_lease_issue"),
        sa.CheckConstraint("credential_class IN ('GITHUB_APP','MODEL_BROKER')", name="ck_agent_lease_class"),
        sa.CheckConstraint("status IN ('ACTIVE','REVOKED','EXPIRED')", name="ck_agent_lease_status"),
        sa.CheckConstraint("issued_for_event_version >= 1", name="ck_agent_lease_event_version"),
        schema="request_service",
    )
    op.create_index("ix_agent_credential_leases_job_id", "agent_credential_leases", ["job_id"], schema="request_service")
    op.create_index("ix_agent_credential_leases_status", "agent_credential_leases", ["status"], schema="request_service")


def downgrade() -> None:
    op.drop_table("agent_credential_leases", schema="request_service")
    op.drop_table("agent_queue_items", schema="request_service")
