"""add Terraform provisioning job lifecycle

Revision ID: 0003_provisioning_jobs
Revises: 0002_control_products
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_provisioning_jobs"
down_revision: str | None = "0002_control_products"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provisioning_jobs",
        sa.Column("job_id", sa.String(36), primary_key=True),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("operation", sa.String(16), nullable=False),
        sa.Column("product_code", sa.String(64), nullable=False),
        sa.Column("product_version", sa.Integer(), nullable=False),
        sa.Column("module_name", sa.String(64), nullable=False),
        sa.Column("module_version", sa.String(32), nullable=False),
        sa.Column("artifact_digest", sa.String(80), nullable=False),
        sa.Column("approved_by", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("state_key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="QUEUED"),
        sa.Column(
            "input_values",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "output_values",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("resource_id", sa.String(36)),
        sa.Column("resource_event_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("runner_id", sa.String(128)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["control_service.approval_requests.request_id"],
            ondelete="RESTRICT",
            name="fk_provisioning_job_request",
        ),
        sa.CheckConstraint("operation IN ('APPLY','DESTROY')", name="ck_provisioning_jobs_operation"),
        sa.CheckConstraint("resource_event_version >= 0", name="ck_provisioning_jobs_resource_version"),
        sa.CheckConstraint("attempts >= 0", name="ck_provisioning_jobs_attempts"),
        schema="control_service",
    )
    op.create_index(
        "ix_provisioning_jobs_request_id",
        "provisioning_jobs",
        ["request_id"],
        schema="control_service",
    )
    op.create_index(
        "ix_provisioning_jobs_operation",
        "provisioning_jobs",
        ["operation"],
        schema="control_service",
    )
    op.create_index(
        "ix_provisioning_jobs_status",
        "provisioning_jobs",
        ["status"],
        schema="control_service",
    )
    op.create_index(
        "ix_provisioning_jobs_state_key",
        "provisioning_jobs",
        ["state_key"],
        schema="control_service",
    )
    op.drop_constraint(
        "ck_audit_events_aggregate_type",
        "audit_events",
        schema="control_service",
        type_="check",
    )
    op.create_check_constraint(
        "ck_audit_events_aggregate_type",
        "audit_events",
        "aggregate_type IN ('request','grant','provisioning-job')",
        schema="control_service",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_audit_events_aggregate_type",
        "audit_events",
        schema="control_service",
        type_="check",
    )
    op.create_check_constraint(
        "ck_audit_events_aggregate_type",
        "audit_events",
        "aggregate_type IN ('request','grant')",
        schema="control_service",
    )
    op.drop_table("provisioning_jobs", schema="control_service")
