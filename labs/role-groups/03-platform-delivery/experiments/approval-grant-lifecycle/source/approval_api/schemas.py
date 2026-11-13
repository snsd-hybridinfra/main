from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ApprovalIngest(BaseModel):
    request_id: str
    idempotency_key: str = Field(min_length=1, max_length=128)
    requester_id: str = Field(min_length=1, max_length=255)
    product_code: str = Field(min_length=1, max_length=64)
    cpu: int = Field(default=0, ge=0, le=64)
    memory_gib: int = Field(default=0, ge=0, le=512)
    storage_gib: int = Field(default=0, ge=0, le=4096)
    duration_hours: int = Field(ge=1, le=24 * 90)
    purpose: str = Field(min_length=5, max_length=2000)
    parameters: dict[str, Any] = Field(default_factory=dict)
    blueprint_id: str | None = Field(default=None, min_length=1, max_length=64)
    manifest_digest: str | None = Field(default=None, min_length=71, max_length=71)
    resolved_manifest: dict[str, Any] | None = None
    status: Literal["PENDING", "CANCELLED"] = "PENDING"
    event_version: int = Field(default=1, ge=1)
    retry_count: int = Field(default=0, ge=0)
    updated_at: datetime


class ApprovalRequestView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    request_id: str
    idempotency_key: str
    requester_id: str
    product_code: str
    cpu: int
    memory_gib: int
    storage_gib: int
    duration_hours: int
    purpose: str
    parameters: dict[str, Any]
    status: str
    event_version: int
    retry_count: int
    delivery_status: str
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class DecisionCreate(BaseModel):
    # Ignore the retired client-supplied grant_scopes field for cached MVP clients.
    # Effective scopes are always calculated by approval_api.policies.
    model_config = ConfigDict(extra="ignore")

    reason: str | None = Field(default=None, max_length=2000)
    grant_duration_hours: int | None = Field(default=None, ge=1, le=24 * 90)


class DecisionResult(BaseModel):
    request: ApprovalRequestView
    callback_status: str
    grant_status: str


class JobClaim(BaseModel):
    runner_id: str = Field(min_length=1, max_length=128)


class ProvisioningJobView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    request_id: str
    idempotency_key: str
    operation: str
    product_code: str
    product_version: int
    module_name: str
    module_version: str
    artifact_digest: str
    approved_by: str
    expires_at: datetime
    state_key: str
    status: str
    input_values: dict[str, Any]
    output_values: dict[str, Any]
    resource_id: str | None
    resource_event_version: int
    attempts: int
    runner_id: str | None
    last_error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    updated_at: datetime


class ProvisioningResult(BaseModel):
    status: Literal[
        "PROVISIONING",
        "RUNNING",
        "PROVISION_FAILED",
        "TERMINATING",
        "TERMINATED",
        "TERMINATION_FAILED",
    ]
    resource_id: str | None = Field(default=None, min_length=1, max_length=36)
    endpoint: str | None = Field(default=None, max_length=512)
    display_name: str | None = Field(default=None, max_length=255)
    details: dict[str, str | int | bool] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    validation_passed: bool = False
    failure_code: Literal[
        "PLAN_FAILED",
        "POLICY_DENIED",
        "APPLY_FAILED",
        "BOOTSTRAP_FAILED",
        "BOOTSTRAP_VALIDATION_REQUIRED",
        "CONFIGURATION_FAILED",
        "ROLLBACK_FAILED",
        "DESTROY_FAILED",
    ] | None = None
    error: str | None = Field(default=None, max_length=4000)


class ProvisioningResultView(BaseModel):
    job: ProvisioningJobView
    callback_status: str
    grant_status: str


class DestroyRequest(BaseModel):
    trigger_status: Literal["REVOKED", "EXPIRED"]
    reason: str | None = Field(default=None, max_length=2000)


class AuditEventView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    actor_id: str
    details: dict
    created_at: datetime


class HealthView(BaseModel):
    status: str


class DemoResetResult(BaseModel):
    status: Literal["reset"] = "reset"
    deleted: dict[str, int]


class DemoSeedResult(BaseModel):
    status: Literal["seeded", "existing"]
    created: bool
    delivery_status: str


class MonitoringDashboard(BaseModel):
    provider: Literal["grafana"] = "grafana"
    status: Literal["PENDING", "READY", "INVALID"]
    dashboard_url: str | None = None
