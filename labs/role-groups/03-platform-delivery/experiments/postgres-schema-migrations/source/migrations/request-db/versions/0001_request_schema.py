"""create request service schema

Revision ID: 0001_request
Revises:
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_request"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "access_requests",
        sa.Column("request_id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("owner_id", sa.String(255), nullable=False),
        sa.Column("product_code", sa.String(64), nullable=False),
        sa.Column("cpu", sa.Integer(), nullable=False),
        sa.Column("memory_gib", sa.Integer(), nullable=False),
        sa.Column("storage_gib", sa.Integer(), nullable=False),
        sa.Column("duration_hours", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("grant_id", sa.String(36)),
        sa.Column("grant_expires_at", sa.DateTime(timezone=True)),
        sa.Column("resource_id", sa.String(36)),
        sa.Column("resource_status", sa.String(32)),
        sa.Column("event_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delivery_status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("cpu BETWEEN 0 AND 64", name="ck_access_requests_cpu"),
        sa.CheckConstraint("memory_gib BETWEEN 0 AND 512", name="ck_access_requests_memory"),
        sa.CheckConstraint("storage_gib BETWEEN 0 AND 4096", name="ck_access_requests_storage"),
        sa.CheckConstraint("duration_hours BETWEEN 1 AND 2160", name="ck_access_requests_duration"),
        sa.CheckConstraint("char_length(purpose) BETWEEN 5 AND 2000", name="ck_access_requests_purpose"),
        sa.CheckConstraint("event_version >= 1", name="ck_access_requests_event_version"),
        sa.CheckConstraint("retry_count >= 0", name="ck_access_requests_retry_count"),
        sa.CheckConstraint(
            "status IN ('PENDING','APPROVED','REJECTED','CANCELLED','GRANTED','REVOKED','EXPIRED','PROVISIONING','RUNNING','TERMINATING','TERMINATED','PROVISION_FAILED','TERMINATION_FAILED')",
            name="ck_access_requests_status",
        ),
        sa.CheckConstraint(
            "delivery_status IN ('PENDING','DELIVERED','FAILED','SKIPPED')",
            name="ck_access_requests_delivery",
        ),
        schema="request_service",
    )
    op.create_index("ix_access_requests_owner_id", "access_requests", ["owner_id"], schema="request_service")
    op.create_index("ix_access_requests_status", "access_requests", ["status"], schema="request_service")
    op.create_index("ix_access_requests_grant_id", "access_requests", ["grant_id"], schema="request_service")
    op.create_index("ix_access_requests_resource_id", "access_requests", ["resource_id"], schema="request_service")

    op.create_table(
        "resource_projections",
        sa.Column("resource_id", sa.String(36), primary_key=True),
        sa.Column("request_id", sa.String(36), nullable=False, unique=True),
        sa.Column("owner_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("endpoint", sa.String(512)),
        sa.Column("event_version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["request_service.access_requests.request_id"],
            ondelete="CASCADE",
            name="fk_resource_projection_request",
        ),
        sa.CheckConstraint("event_version >= 1", name="ck_resource_projection_event_version"),
        schema="request_service",
    )
    op.create_index("ix_resource_projections_owner_id", "resource_projections", ["owner_id"], schema="request_service")


def downgrade() -> None:
    op.drop_table("resource_projections", schema="request_service")
    op.drop_table("access_requests", schema="request_service")
