"""create control service schema

Revision ID: 0001_control
Revises:
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_control"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("request_id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("requester_id", sa.String(255), nullable=False),
        sa.Column("product_code", sa.String(64), nullable=False),
        sa.Column("cpu", sa.Integer(), nullable=False),
        sa.Column("memory_gib", sa.Integer(), nullable=False),
        sa.Column("storage_gib", sa.Integer(), nullable=False),
        sa.Column("duration_hours", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("event_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delivery_status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("cpu BETWEEN 0 AND 64", name="ck_approval_requests_cpu"),
        sa.CheckConstraint("memory_gib BETWEEN 0 AND 512", name="ck_approval_requests_memory"),
        sa.CheckConstraint("storage_gib BETWEEN 0 AND 4096", name="ck_approval_requests_storage"),
        sa.CheckConstraint("duration_hours BETWEEN 1 AND 2160", name="ck_approval_requests_duration"),
        sa.CheckConstraint("char_length(purpose) BETWEEN 5 AND 2000", name="ck_approval_requests_purpose"),
        sa.CheckConstraint("status IN ('PENDING','APPROVED','REJECTED','CANCELLED')", name="ck_approval_requests_status"),
        sa.CheckConstraint("event_version >= 1", name="ck_approval_requests_event_version"),
        sa.CheckConstraint("retry_count >= 0", name="ck_approval_requests_retry_count"),
        sa.CheckConstraint("delivery_status IN ('PENDING','DELIVERED','FAILED','SKIPPED')", name="ck_approval_requests_delivery"),
        schema="control_service",
    )
    op.create_index("ix_approval_requests_requester_id", "approval_requests", ["requester_id"], schema="control_service")
    op.create_index("ix_approval_requests_status", "approval_requests", ["status"], schema="control_service")

    op.create_table(
        "approval_decisions",
        sa.Column("decision_id", sa.String(36), primary_key=True),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("event_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["request_id"], ["control_service.approval_requests.request_id"],
            ondelete="RESTRICT", name="fk_approval_decision_request",
        ),
        sa.UniqueConstraint("request_id", "event_version", name="uq_approval_decision_version"),
        sa.CheckConstraint("decision IN ('APPROVED','REJECTED')", name="ck_approval_decisions_decision"),
        sa.CheckConstraint("event_version >= 2", name="ck_approval_decisions_event_version"),
        schema="control_service",
    )
    op.create_index("ix_approval_decisions_request_id", "approval_decisions", ["request_id"], schema="control_service")

    op.create_table(
        "grants",
        sa.Column("grant_id", sa.String(36), primary_key=True),
        sa.Column("request_id", sa.String(36), nullable=False, unique=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("subject_id", sa.String(255), nullable=False),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("event_version", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("callback_status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("last_error", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("jsonb_typeof(scopes) = 'array'", name="ck_grants_scopes_array"),
        sa.CheckConstraint("status IN ('ACTIVE','REVOKED','EXPIRED')", name="ck_grants_status"),
        sa.CheckConstraint("expires_at > issued_at", name="ck_grants_expiry"),
        sa.CheckConstraint("event_version >= 1", name="ck_grants_event_version"),
        sa.CheckConstraint("retry_count >= 0", name="ck_grants_retry_count"),
        sa.CheckConstraint("callback_status IN ('PENDING','DELIVERED','FAILED','SKIPPED')", name="ck_grants_callback"),
        sa.CheckConstraint("(status = 'REVOKED' AND revoked_at IS NOT NULL) OR status <> 'REVOKED'", name="ck_grants_revoked_at"),
        schema="control_service",
    )
    op.create_index("ix_grants_subject_id", "grants", ["subject_id"], schema="control_service")
    op.create_index("ix_grants_status", "grants", ["status"], schema="control_service")
    op.create_index("ix_grants_expires_at", "grants", ["expires_at"], schema="control_service")

    op.create_table(
        "audit_events",
        sa.Column("audit_id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("aggregate_type", sa.String(32), nullable=False),
        sa.Column("aggregate_id", sa.String(36), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("aggregate_type IN ('request','grant')", name="ck_audit_events_aggregate_type"),
        schema="control_service",
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"], schema="control_service")
    op.create_index("ix_audit_events_aggregate_id", "audit_events", ["aggregate_id"], schema="control_service")
    op.create_index("ix_audit_events_created_at", "audit_events", [sa.text("created_at DESC")], schema="control_service")


def downgrade() -> None:
    op.drop_table("audit_events", schema="control_service")
    op.drop_table("grants", schema="control_service")
    op.drop_table("approval_decisions", schema="control_service")
    op.drop_table("approval_requests", schema="control_service")
