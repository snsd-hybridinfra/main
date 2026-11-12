from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


class RequestCreate(BaseModel):
    product_code: str = Field(min_length=1, max_length=64)
    cpu: int = Field(default=0, ge=0, le=64)
    memory_gib: int = Field(default=0, ge=0, le=512)
    storage_gib: int = Field(default=0, ge=0, le=4096)
    duration_hours: int = Field(ge=1, le=24 * 90)
    purpose: str = Field(min_length=5, max_length=2000)
    parameters: dict[str, Any] = Field(default_factory=dict)


class RequestView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    request_id: str
    idempotency_key: str
    owner_id: str
    product_code: str | None
    blueprint_id: str | None = None
    blueprint_environment: str | None = None
    blueprint_size: str | None = None
    manifest_digest: str | None = None
    cpu: int
    memory_gib: int
    storage_gib: int
    duration_hours: int
    purpose: str
    parameters: dict[str, str | int]
    status: str
    rejection_reason: str | None
    grant_id: str | None
    grant_expires_at: datetime | None
    resource_id: str | None
    resource_status: str | None
    event_version: int
    retry_count: int
    delivery_status: str
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def project_blueprint_fields(self) -> "RequestView":
        blueprint_id = self.parameters.get("_blueprint_id")
        if isinstance(blueprint_id, str):
            self.blueprint_id = blueprint_id
            self.blueprint_environment = str(self.parameters.get("_blueprint_environment", "")) or None
            self.blueprint_size = str(self.parameters.get("_blueprint_size", "")) or None
            self.manifest_digest = str(self.parameters.get("_manifest_digest", "")) or None
        return self

    @field_serializer("product_code")
    def hide_blueprint_execution_profile(self, value: str | None) -> str | None:
        return None if self.blueprint_id else value

    @field_serializer("parameters")
    def hide_server_owned_parameters(
        self, value: dict[str, str | int]
    ) -> dict[str, str | int]:
        return {key: item for key, item in value.items() if not key.startswith("_")}


class StatusUpdate(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=128)
    event_version: int = Field(ge=2)
    retry_count: int = Field(default=0, ge=0)
    status: Literal[
        "APPROVED",
        "REJECTED",
        "GRANTED",
        "REVOKED",
        "EXPIRED",
        "PROVISIONING",
        "RUNNING",
        "TERMINATING",
        "TERMINATED",
        "PROVISION_FAILED",
        "TERMINATION_FAILED",
    ]
    reason: str | None = Field(default=None, max_length=2000)
    grant_id: str | None = None
    grant_expires_at: datetime | None = None
    resource_id: str | None = None
    resource_status: str | None = Field(default=None, max_length=32)
    resource_endpoint: str | None = Field(default=None, max_length=512)


class ResourceView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_id: str
    request_id: str
    owner_id: str
    status: str
    endpoint: str | None
    resource_type: str
    display_name: str
    details: dict[str, str | int | bool]
    event_version: int
    updated_at: datetime


class ResourceStatusUpdate(BaseModel):
    resource_id: str = Field(min_length=1, max_length=36)
    status: Literal[
        "PROVISIONING",
        "RUNNING",
        "PROVISION_FAILED",
        "TERMINATING",
        "TERMINATED",
        "TERMINATION_FAILED",
    ]
    endpoint: str | None = Field(default=None, max_length=512)
    resource_type: str | None = Field(default=None, min_length=1, max_length=64)
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    details: dict[str, str | int | bool] | None = None
    event_version: int = Field(ge=1)


class CatalogParameterOption(BaseModel):
    value: str
    label: str


class CatalogParameter(BaseModel):
    key: str
    label: str
    type: Literal["text", "number", "select"]
    default: str | int | None = None
    min: int | None = None
    max: int | None = None
    required: bool = False
    help: str | None = None
    options: list[CatalogParameterOption] = Field(default_factory=list)


class CatalogItem(BaseModel):
    product_code: str
    name: str
    description: str
    mvp_primary: bool
    requires_compute_spec: bool
    product_version: int
    category: Literal["COMPUTE", "PAAS", "CONTAINER", "DATABASE", "STORAGE"]
    provisioner: Literal["terraform"]
    module_name: str
    module_version: str
    artifact_digest: str
    configuration_digest: str | None = None
    allowed_duration_hours: list[int]
    max_resources_per_user: int
    fixed_spec: dict[str, str]
    parameters: list[CatalogParameter] = Field(default_factory=list)


class BlueprintCatalogItem(BaseModel):
    blueprint_id: str
    display_name: str
    summary: str
    business_domain_profiles: list[str]
    network_profile: str
    allowed_environments: list[str]
    allowed_sizes: list[str]
    allowed_duration_hours: list[int]


class BlueprintResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    blueprint_id: str = Field(min_length=1, max_length=64)
    environment: str = Field(min_length=1, max_length=16)
    size: str = Field(min_length=1, max_length=16)
    duration_hours: int = Field(ge=1, le=24 * 90)
    purpose: str = Field(min_length=5, max_length=200)


class BlueprintResolutionView(BaseModel):
    blueprint_id: str
    environment: str
    size: str
    duration_hours: int
    purpose: str
    business_domain_profiles: list[str]
    network_profile: str
    resolution_status: Literal["RESOLVED_LOCAL", "BLOCKED_UNIMPLEMENTED_COMPONENTS"]
    manifest_digest: str
    runtime_authorized: Literal[False] = False


class BlueprintRequestView(BaseModel):
    request_id: str
    idempotency_key: str
    owner_id: str
    blueprint_id: str
    environment: str
    size: str
    duration_hours: int
    purpose: str
    manifest_digest: str
    status: str
    delivery_status: str
    retry_count: int
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class InternalBlueprintResolutionView(BaseModel):
    schema_version: Literal["1.0.0"]
    blueprint_id: str
    environment: str
    size: str
    duration_hours: int
    purpose: str
    business_domain_profiles: list[str]
    network_profile: str
    component_plan: list[dict[str, str]]
    selected_execution_profile: str | None
    deployment_transaction: Literal["ALL_OR_NOTHING"]
    rollback_component_order: list[str]
    resolution_status: Literal["RESOLVED_LOCAL", "BLOCKED_UNIMPLEMENTED_COMPONENTS"]
    blocking_components: list[str]
    blocking_gates: list[str]
    runtime_authorized: Literal[False] = False
    manifest_digest: str


class FinancialSaaSTenantBundleView(BaseModel):
    bundle: dict[str, Any]
    bundle_digest: str


class AgentJobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_alias: str = Field(pattern=r"^[a-z][a-z0-9_-]{2,63}$")
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    task_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    environment: Literal["DEV", "TEST"]
    size: Literal["STANDARD", "LARGE"]


class AgentJobTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(ge=2)
    action: Literal[
        "ENQUEUE",
        "START",
        "POD_READY",
        "CHECKPOINT",
        "WAIT_FOR_APPROVAL",
        "APPROVE",
        "REJECT",
        "RESUME",
        "COMPLETE",
        "FAIL",
        "CANCEL",
        "TIMEOUT",
    ]
    checkpoint_digest: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    approval_action: Literal[
        "MAIN_BRANCH_MUTATION",
        "BRANCH_PROTECTION_BYPASS",
        "PRODUCTION_ACCESS",
        "DATABASE_SCHEMA_CHANGE",
        "SECRET_ACCESS",
        "NEW_EGRESS_DESTINATION",
        "INFRASTRUCTURE_MUTATION",
        "DEPENDENCY_SOURCE_CHANGE",
    ] | None = None


class AgentJobView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    idempotency_key: str
    owner_id: str
    repository_alias: str
    source_commit: str
    task_digest: str
    environment: str
    size: str
    sandbox_spec: dict[str, Any]
    sandbox_spec_digest: str
    status: str
    checkpoint_digest: str | None
    checkpoint_sequence: int
    awaiting_action: str | None
    event_version: int
    compute_allocated: bool
    runtime_authorized: Literal[False] = False
    created_at: datetime
    updated_at: datetime


class AgentQueueView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    queue_id: str
    job_id: str
    envelope: dict[str, Any]
    envelope_digest: str
    status: str
    delivery_attempt: int
    event_version: int
    created_at: datetime
    updated_at: datetime


class AgentCredentialLeaseView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lease_id: str
    job_id: str
    credential_class: str
    lease_reference: str
    status: str
    issued_for_event_version: int
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


class AgentIntegrationView(BaseModel):
    queue: AgentQueueView | None
    credential_leases: list[AgentCredentialLeaseView]
    egress_policy: dict[str, Any]
    egress_policy_digest: str
    raw_token_material_present: Literal[False] = False
    runtime_authorized: Literal[False] = False


class AgentUsageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    span_id: str = Field(pattern=r"^[0-9a-f]{16}$")
    meter_name: Literal["agent.iteration", "llm.request", "tool.exec", "test.run"]
    wall_clock_seconds: int = Field(default=0, ge=0, le=3600)
    iterations: int = Field(default=0, ge=0, le=1)
    model_tokens: int = Field(default=0, ge=0, le=1_000_000)
    monetary_cost_microunits: int = Field(default=0, ge=0, le=100_000_000)
    external_calls: int = Field(default=0, ge=0, le=100)
    egress_bytes: int = Field(default=0, ge=0, le=1_073_741_824)
    concurrency_observed: int = Field(default=1, ge=0, le=64)


class AgentBudgetLedgerView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    wall_clock_limit_seconds: int
    iteration_limit: int
    model_token_limit: int
    monetary_cost_limit_microunits: int
    external_call_limit: int
    egress_byte_limit: int
    concurrency_limit: int
    wall_clock_consumed_seconds: int
    iterations_consumed: int
    model_tokens_consumed: int
    monetary_cost_consumed_microunits: int
    external_calls_consumed: int
    egress_bytes_consumed: int
    concurrency_peak: int
    status: str
    version: int
    updated_at: datetime


class AgentUsageRecordView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    usage_id: str
    idempotency_key: str
    job_id: str
    trace_id: str
    span_id: str
    meter_name: str
    wall_clock_seconds: int
    iterations: int
    model_tokens: int
    monetary_cost_microunits: int
    external_calls: int
    egress_bytes: int
    concurrency_observed: int
    outcome: str
    exceeded_dimensions: list[str]
    created_at: datetime


class AgentUsageResult(BaseModel):
    usage: AgentUsageRecordView
    budget: AgentBudgetLedgerView
    job_status: str
    compute_allocated: bool
    runtime_authorized: Literal[False] = False


class AgentTraceEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    span_id: str = Field(pattern=r"^[0-9a-f]{16}$")
    parent_span_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{16}$")
    span_name: Literal[
        "request.queue", "pod.schedule", "image.pull", "repo.clone",
        "agent.iteration", "llm.request", "tool.exec", "test.run",
        "checkpoint.write", "git.push", "pr.create", "cleanup",
    ]
    phase: Literal["START", "END", "POINT"]
    outcome: Literal["OK", "ERROR", "POLICY_DENIED", "BUDGET_DENIED"]
    duration_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    attempt: int | None = Field(default=None, ge=0, le=100)
    queue_latency_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    cold_start_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    model_tokens: int | None = Field(default=None, ge=0, le=1_000_000)
    cost_microunits: int | None = Field(default=None, ge=0, le=100_000_000)
    exit_code: int | None = Field(default=None, ge=-1, le=255)
    policy_reason_code: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]{2,63}$")


class AgentTraceEventView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    idempotency_key: str
    job_id: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    span_name: str
    phase: str
    outcome: str
    measurements: dict[str, int]
    policy_reason_code: str | None
    occurred_at: datetime


class HealthView(BaseModel):
    status: str


class DemoResetResult(BaseModel):
    status: Literal["reset"] = "reset"
    deleted: dict[str, int]


class DemoSeedResult(BaseModel):
    status: Literal["seeded", "existing"]
    created: bool
    delivery_status: str
