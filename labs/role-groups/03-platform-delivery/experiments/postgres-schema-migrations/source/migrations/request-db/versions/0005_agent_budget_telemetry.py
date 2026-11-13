"""add bounded budget ledger and sanitized trace events

Revision ID: 0005_agent_budget_trace
Revises: 0004_agent_integrations
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0005_agent_budget_trace"
down_revision: str | None = "0004_agent_integrations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_budget_ledgers",
        sa.Column("job_id", sa.String(36), primary_key=True),
        sa.Column("wall_clock_limit_seconds", sa.Integer(), nullable=False),
        sa.Column("iteration_limit", sa.Integer(), nullable=False),
        sa.Column("model_token_limit", sa.Integer(), nullable=False),
        sa.Column("monetary_cost_limit_microunits", sa.Integer(), nullable=False),
        sa.Column("external_call_limit", sa.Integer(), nullable=False),
        sa.Column("egress_byte_limit", sa.Integer(), nullable=False),
        sa.Column("concurrency_limit", sa.Integer(), nullable=False),
        sa.Column("wall_clock_consumed_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("iterations_consumed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("model_tokens_consumed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monetary_cost_consumed_microunits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("external_calls_consumed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("egress_bytes_consumed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("concurrency_peak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["request_service.agent_jobs.job_id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('ACTIVE','EXHAUSTED','CLOSED')", name="ck_agent_budget_status"),
        schema="request_service",
    )

    op.create_table(
        "agent_usage_records",
        sa.Column("usage_id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("trace_id", sa.String(32), nullable=False),
        sa.Column("span_id", sa.String(16), nullable=False),
        sa.Column("meter_name", sa.String(32), nullable=False),
        sa.Column("wall_clock_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("iterations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("model_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monetary_cost_microunits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("external_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("egress_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("concurrency_observed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("exceeded_dimensions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["request_service.agent_jobs.job_id"], ondelete="CASCADE"),
        sa.CheckConstraint("outcome IN ('APPLIED','DENIED')", name="ck_agent_usage_outcome"),
        schema="request_service",
    )
    op.create_index("ix_agent_usage_records_job_id", "agent_usage_records", ["job_id"], schema="request_service")

    op.create_table(
        "agent_trace_events",
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("trace_id", sa.String(32), nullable=False),
        sa.Column("span_id", sa.String(16), nullable=False),
        sa.Column("parent_span_id", sa.String(16)),
        sa.Column("span_name", sa.String(32), nullable=False),
        sa.Column("phase", sa.String(8), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("measurements", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("policy_reason_code", sa.String(64)),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["request_service.agent_jobs.job_id"], ondelete="CASCADE"),
        schema="request_service",
    )
    op.create_index("ix_agent_trace_events_job_id", "agent_trace_events", ["job_id"], schema="request_service")
    op.create_index("ix_agent_trace_events_trace_id", "agent_trace_events", ["trace_id"], schema="request_service")


def downgrade() -> None:
    op.drop_table("agent_trace_events", schema="request_service")
    op.drop_table("agent_usage_records", schema="request_service")
    op.drop_table("agent_budget_ledgers", schema="request_service")
