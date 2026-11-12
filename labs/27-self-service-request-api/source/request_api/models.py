from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AccessRequest(Base):
    __tablename__ = "access_requests"

    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    owner_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    cpu: Mapped[int] = mapped_column(Integer, nullable=False)
    memory_gib: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_gib: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="PENDING")
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    grant_id: Mapped[str | None] = mapped_column(String(36), index=True)
    grant_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resource_id: Mapped[str | None] = mapped_column(String(36), index=True)
    resource_status: Mapped[str | None] = mapped_column(String(32))
    event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delivery_status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class ResourceProjection(Base):
    __tablename__ = "resource_projections"
    __table_args__ = (UniqueConstraint("request_id", name="uq_resource_projection_request"),)

    resource_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    endpoint: Mapped[str | None] = mapped_column(String(512))
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False, default="DEV-OS-VM-S")
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, default="할당 자원")
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    event_version: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class AgentJob(Base):
    __tablename__ = "agent_jobs"

    job_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    owner_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    repository_alias: Mapped[str] = mapped_column(String(64), nullable=False)
    source_commit: Mapped[str] = mapped_column(String(40), nullable=False)
    task_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    environment: Mapped[str] = mapped_column(String(16), nullable=False)
    size: Mapped[str] = mapped_column(String(16), nullable=False)
    sandbox_spec: Mapped[dict] = mapped_column(JSON, nullable=False)
    sandbox_spec_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="RECEIVED")
    checkpoint_digest: Mapped[str | None] = mapped_column(String(71))
    checkpoint_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    awaiting_action: Mapped[str | None] = mapped_column(String(64))
    event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    compute_allocated: Mapped[bool] = mapped_column(nullable=False, default=False)
    runtime_authorized: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class AgentQueueItem(Base):
    __tablename__ = "agent_queue_items"

    queue_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    envelope: Mapped[dict] = mapped_column(JSON, nullable=False)
    envelope_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    status: Mapped[str] = mapped_column(String(16), index=True, nullable=False, default="READY")
    delivery_attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class AgentCredentialLease(Base):
    __tablename__ = "agent_credential_leases"

    lease_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    credential_class: Mapped[str] = mapped_column(String(32), nullable=False)
    lease_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), index=True, nullable=False, default="ACTIVE")
    issued_for_event_version: Mapped[int] = mapped_column(Integer, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AgentBudgetLedger(Base):
    __tablename__ = "agent_budget_ledgers"

    job_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    wall_clock_limit_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    iteration_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    model_token_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    monetary_cost_limit_microunits: Mapped[int] = mapped_column(Integer, nullable=False)
    external_call_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    egress_byte_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    concurrency_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    wall_clock_consumed_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    iterations_consumed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model_tokens_consumed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monetary_cost_consumed_microunits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    external_calls_consumed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    egress_bytes_consumed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    concurrency_peak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AgentUsageRecord(Base):
    __tablename__ = "agent_usage_records"

    usage_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    job_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    trace_id: Mapped[str] = mapped_column(String(32), nullable=False)
    span_id: Mapped[str] = mapped_column(String(16), nullable=False)
    meter_name: Mapped[str] = mapped_column(String(32), nullable=False)
    wall_clock_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    iterations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monetary_cost_microunits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    external_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    egress_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    concurrency_observed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    exceeded_dimensions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AgentTraceEvent(Base):
    __tablename__ = "agent_trace_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    job_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    trace_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    span_id: Mapped[str] = mapped_column(String(16), nullable=False)
    parent_span_id: Mapped[str | None] = mapped_column(String(16))
    span_name: Mapped[str] = mapped_column(String(32), nullable=False)
    phase: Mapped[str] = mapped_column(String(8), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    measurements: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    policy_reason_code: Mapped[str | None] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
