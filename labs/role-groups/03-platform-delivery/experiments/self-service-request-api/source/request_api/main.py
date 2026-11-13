from contextlib import asynccontextmanager
from datetime import timezone
import hashlib
from time import sleep
from typing import Annotated
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from sqlalchemy import delete, func, or_, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import Principal, require_roles
from .agent_integrations import (
    CREDENTIAL_CLASSES,
    build_egress_policy,
    build_queue_envelope,
    new_lease_metadata,
    utcnow as integration_utcnow,
)
from .agent_jobs import AgentJobError, build_sandbox_bundle, compute_is_allocated, transition_target
from .blueprints import (
    BlueprintResolutionError,
    load_authorities,
    public_blueprints,
    public_resolution,
    resolve_blueprint,
)
from .catalog import CATALOG, CATALOG_BY_CODE, PRODUCT_RUNTIME_SPECS
from .clients import send_to_approval
from .config import Settings
from .db import Base, ensure_local_schema_compatibility, get_db, make_engine, make_session_factory
from .models import (
    AccessRequest,
    AgentBudgetLedger,
    AgentCredentialLease,
    AgentJob,
    AgentQueueItem,
    AgentTraceEvent,
    AgentUsageRecord,
    ResourceProjection,
)
from .policies import normalize_parameters
from .provisioning import build_mock_resource, product_label
from .saas_paas import FinancialSaaSBundleError, build_financial_saas_tenant_bundle
from .schemas import (
    CatalogItem,
    AgentJobCreate,
    AgentJobTransition,
    AgentJobView,
    AgentIntegrationView,
    AgentBudgetLedgerView,
    AgentTraceEventCreate,
    AgentTraceEventView,
    AgentUsageCreate,
    AgentUsageResult,
    BlueprintCatalogItem,
    BlueprintResolveRequest,
    BlueprintResolutionView,
    BlueprintRequestView,
    DemoResetResult,
    DemoSeedResult,
    HealthView,
    InternalBlueprintResolutionView,
    FinancialSaaSTenantBundleView,
    RequestCreate,
    RequestView,
    ResourceStatusUpdate,
    ResourceView,
    StatusUpdate,
)


BASE_TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"APPROVED", "REJECTED", "CANCELLED"},
    "APPROVED": {"GRANTED"},
    "GRANTED": {"REVOKED", "EXPIRED"},
}
PROVISIONING_TRANSITIONS: dict[str, set[str]] = {
    "APPROVED": {"PROVISIONING"},
    "PROVISIONING": {"RUNNING", "PROVISION_FAILED"},
    "RUNNING": {"TERMINATING"},
    "TERMINATING": {"TERMINATED", "TERMINATION_FAILED"},
}
RESOURCE_TRANSITIONS: dict[str, set[str]] = {
    "PROVISIONING": {"RUNNING", "PROVISION_FAILED", "TERMINATING"},
    "RUNNING": {"TERMINATING"},
    "PROVISION_FAILED": {"PROVISIONING", "TERMINATING"},
    "TERMINATING": {"TERMINATED", "TERMINATION_FAILED"},
    "TERMINATION_FAILED": {"TERMINATING"},
}


def _blueprint_request_view(item: AccessRequest) -> dict:
    return {
        "request_id": item.request_id,
        "idempotency_key": item.idempotency_key,
        "owner_id": item.owner_id,
        "blueprint_id": item.parameters["_blueprint_id"],
        "environment": item.parameters["_blueprint_environment"],
        "size": item.parameters["_blueprint_size"],
        "duration_hours": item.duration_hours,
        "purpose": item.purpose,
        "manifest_digest": item.parameters["_manifest_digest"],
        "status": item.status,
        "delivery_status": item.delivery_status,
        "retry_count": item.retry_count,
        "last_error": item.last_error,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _can_transition(current: str, target: str, provisioning_enabled: bool) -> bool:
    allowed = set(BASE_TRANSITIONS.get(current, set()))
    if provisioning_enabled:
        allowed.update(PROVISIONING_TRANSITIONS.get(current, set()))
    return target in allowed


def _apply_resource_update(
    db: Session,
    request_item: AccessRequest,
    payload: ResourceStatusUpdate,
) -> ResourceProjection:
    projection = db.get(ResourceProjection, payload.resource_id)
    if request_item.resource_id and request_item.resource_id != payload.resource_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "request already has a different resource")

    if projection is None:
        if request_item.status not in {"APPROVED", "GRANTED"}:
            raise HTTPException(status.HTTP_409_CONFLICT, "resource requires an approved request")
        if payload.event_version != 1:
            raise HTTPException(status.HTTP_409_CONFLICT, "resource event_version must start at 1")
        if payload.status not in {"PROVISIONING", "RUNNING", "PROVISION_FAILED"}:
            raise HTTPException(status.HTTP_409_CONFLICT, "invalid initial resource status")
        projection = ResourceProjection(
            resource_id=payload.resource_id,
            request_id=request_item.request_id,
            owner_id=request_item.owner_id,
            status=payload.status,
            endpoint=payload.endpoint,
            resource_type=payload.resource_type or request_item.product_code,
            display_name=payload.display_name or product_label(request_item.product_code),
            details=payload.details or {},
            event_version=payload.event_version,
        )
        db.add(projection)
    else:
        if projection.request_id != request_item.request_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "resource belongs to another request")
        if payload.event_version <= projection.event_version:
            return projection
        if payload.event_version != projection.event_version + 1:
            raise HTTPException(status.HTTP_409_CONFLICT, "resource event_version gap")
        if payload.status not in RESOURCE_TRANSITIONS.get(projection.status, set()):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"invalid resource transition: {projection.status} -> {payload.status}",
            )
        projection.status = payload.status
        projection.event_version = payload.event_version
        if "endpoint" in payload.model_fields_set:
            projection.endpoint = payload.endpoint
        if payload.resource_type is not None:
            projection.resource_type = payload.resource_type
        if payload.display_name is not None:
            projection.display_name = payload.display_name
        if payload.details is not None:
            projection.details = payload.details

    request_item.resource_id = payload.resource_id
    request_item.resource_status = payload.status
    return projection


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings.from_env()
    engine = make_engine(app_settings.database_url)
    session_factory = make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if app_settings.auto_create_schema:
            Base.metadata.create_all(engine)
            ensure_local_schema_compatibility(engine)
        if app_settings.auth_mode == "dev" and app_settings.enable_mock_provisioner:
            with session_factory() as startup_db:
                missing_resources = startup_db.scalars(
                    select(AccessRequest).where(
                        AccessRequest.status == "GRANTED",
                        AccessRequest.resource_id.is_(None),
                    )
                )
                for request_item in missing_resources:
                    spec = build_mock_resource(request_item)
                    _apply_resource_update(
                        startup_db,
                        request_item,
                        ResourceStatusUpdate(
                            resource_id=spec.resource_id,
                            status="RUNNING",
                            endpoint=spec.endpoint,
                            resource_type=spec.resource_type,
                            display_name=spec.display_name,
                            details=spec.details,
                            event_version=1,
                        ),
                    )
                startup_db.commit()
        yield
        engine.dispose()

    app = FastAPI(title="request-api", version="0.1.0", lifespan=lifespan)
    app.state.settings = app_settings
    app.state.session_factory = session_factory

    user_principal = require_roles("user", scopes=("request:access",))
    service_principal = require_roles("service", scopes=("service:callback",))

    def complete_mock_provision(request_id: str, resource_id: str) -> None:
        sleep(max(0.0, app_settings.mock_provision_delay_seconds))
        with session_factory() as worker_db:
            request_item = worker_db.get(AccessRequest, request_id)
            projection = worker_db.get(ResourceProjection, resource_id)
            if not request_item or not projection:
                return
            if request_item.status != "GRANTED" or projection.status != "PROVISIONING":
                return
            _apply_resource_update(
                worker_db,
                request_item,
                ResourceStatusUpdate(
                    resource_id=resource_id,
                    status="RUNNING",
                    endpoint=build_mock_resource(request_item).endpoint,
                    event_version=projection.event_version + 1,
                ),
            )
            worker_db.commit()

    def complete_mock_termination(request_id: str, resource_id: str) -> None:
        sleep(max(0.0, app_settings.mock_provision_delay_seconds))
        with session_factory() as worker_db:
            request_item = worker_db.get(AccessRequest, request_id)
            projection = worker_db.get(ResourceProjection, resource_id)
            if not request_item or not projection or projection.status != "TERMINATING":
                return
            _apply_resource_update(
                worker_db,
                request_item,
                ResourceStatusUpdate(
                    resource_id=resource_id,
                    status="TERMINATED",
                    endpoint=None,
                    event_version=projection.event_version + 1,
                ),
            )
            worker_db.commit()

    @app.get("/healthz", response_model=HealthView, tags=["operations"])
    def healthz() -> HealthView:
        return HealthView(status="ok")

    @app.get("/readyz", response_model=HealthView, tags=["operations"])
    def readyz(db: Annotated[Session, Depends(get_db)]) -> HealthView:
        try:
            db.execute(text("SELECT 1"))
            if app_settings.required_db_revision:
                revision = db.scalar(text("SELECT version_num FROM request_service.alembic_version"))
                if revision != app_settings.required_db_revision:
                    raise RuntimeError("database revision mismatch")
        except Exception as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "database is not ready") from exc
        try:
            load_authorities()
        except BlueprintResolutionError as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "catalog authority is not ready") from exc
        return HealthView(status="ready")

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(
            "# HELP iaas_service_up Service process health.\n"
            "# TYPE iaas_service_up gauge\n"
            'iaas_service_up{service="request-api"} 1\n',
            media_type="text/plain; version=0.0.4",
        )

    @app.get("/api/v1/catalog", response_model=list[BlueprintCatalogItem])
    def list_catalog(_: Annotated[Principal, Depends(user_principal)]) -> list[dict]:
        try:
            return public_blueprints()
        except BlueprintResolutionError as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    @app.get(
        "/internal/v1/execution-profiles",
        response_model=list[CatalogItem],
    )
    def list_execution_profiles(
        _: Annotated[Principal, Depends(service_principal)],
    ) -> list[dict]:
        return list(CATALOG)

    @app.get("/api/v1/blueprints", response_model=list[BlueprintCatalogItem])
    def list_blueprints(_: Annotated[Principal, Depends(user_principal)]) -> list[dict]:
        try:
            return public_blueprints()
        except BlueprintResolutionError as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    @app.post("/api/v1/blueprints/resolve", response_model=BlueprintResolutionView)
    def resolve_public_blueprint(
        payload: BlueprintResolveRequest,
        _: Annotated[Principal, Depends(user_principal)],
    ) -> dict:
        try:
            return public_resolution(resolve_blueprint(**payload.model_dump()))
        except BlueprintResolutionError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    @app.post(
        "/internal/v1/blueprints/resolve",
        response_model=InternalBlueprintResolutionView,
    )
    def resolve_internal_blueprint(
        payload: BlueprintResolveRequest,
        _: Annotated[Principal, Depends(service_principal)],
    ) -> dict:
        try:
            return resolve_blueprint(**payload.model_dump())
        except BlueprintResolutionError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    @app.post(
        "/internal/v1/financial-saas/tenant-bundle",
        response_model=FinancialSaaSTenantBundleView,
    )
    def resolve_financial_saas_tenant_bundle(
        payload: BlueprintResolveRequest,
        _: Annotated[Principal, Depends(service_principal)],
    ) -> dict:
        try:
            resolution = resolve_blueprint(**payload.model_dump())
            bundle, bundle_digest = build_financial_saas_tenant_bundle(resolution)
            return {"bundle": bundle, "bundle_digest": bundle_digest}
        except (BlueprintResolutionError, FinancialSaaSBundleError) as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    @app.post(
        "/internal/v1/agent-job-simulations",
        response_model=AgentJobView,
        status_code=status.HTTP_201_CREATED,
    )
    def create_agent_job_simulation(
        payload: AgentJobCreate,
        principal: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
        idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    ) -> AgentJob:
        existing = db.scalar(select(AgentJob).where(AgentJob.idempotency_key == idempotency_key))
        if existing:
            expected = payload.model_dump()
            actual = {
                "repository_alias": existing.repository_alias,
                "source_commit": existing.source_commit,
                "task_digest": existing.task_digest,
                "environment": existing.environment,
                "size": existing.size,
            }
            if existing.owner_id != principal.subject or actual != expected:
                raise HTTPException(status.HTTP_409_CONFLICT, "idempotency key payload differs")
            return existing

        job_id = str(uuid4())
        try:
            bundle, bundle_digest = build_sandbox_bundle(job_id=job_id, **payload.model_dump())
        except AgentJobError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        item = AgentJob(
            job_id=job_id,
            idempotency_key=idempotency_key,
            owner_id=principal.subject,
            repository_alias=payload.repository_alias,
            source_commit=payload.source_commit,
            task_digest=payload.task_digest,
            environment=payload.environment,
            size=payload.size,
            sandbox_spec=bundle,
            sandbox_spec_digest=bundle_digest,
            status="RECEIVED",
            event_version=1,
            compute_allocated=False,
            runtime_authorized=False,
        )
        db.add(item)
        budgets = bundle["budgets"]
        db.add(
            AgentBudgetLedger(
                job_id=job_id,
                wall_clock_limit_seconds=budgets["active_deadline_seconds"],
                iteration_limit=budgets["max_iterations"],
                model_token_limit=budgets["model_token_budget"],
                monetary_cost_limit_microunits=budgets["monetary_budget_microunits"],
                external_call_limit=budgets["external_call_budget"],
                egress_byte_limit=budgets["egress_byte_budget"],
                concurrency_limit=budgets["concurrency_limit"],
            )
        )
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "duplicate agent job") from exc
        db.refresh(item)
        return item

    @app.get(
        "/internal/v1/agent-job-simulations/{job_id}",
        response_model=AgentJobView,
    )
    def get_agent_job_simulation(
        job_id: str,
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> AgentJob:
        item = db.get(AgentJob, job_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "agent job not found")
        return item

    @app.get(
        "/internal/v1/agent-job-simulations/{job_id}/integrations",
        response_model=AgentIntegrationView,
    )
    def get_agent_job_integrations(
        job_id: str,
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> dict:
        item = db.get(AgentJob, job_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "agent job not found")
        queue_item = db.scalar(select(AgentQueueItem).where(AgentQueueItem.job_id == job_id))
        leases = list(
            db.scalars(
                select(AgentCredentialLease)
                .where(AgentCredentialLease.job_id == job_id)
                .order_by(AgentCredentialLease.issued_at, AgentCredentialLease.credential_class)
            )
        )
        now = integration_utcnow()
        expired = False
        for lease in leases:
            expires_at = lease.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if lease.status == "ACTIVE" and expires_at <= now:
                lease.status = "EXPIRED"
                lease.revoked_at = now
                expired = True
        if expired:
            db.commit()
        egress_policy, egress_policy_digest = build_egress_policy(job_id)
        return {
            "queue": queue_item,
            "credential_leases": leases,
            "egress_policy": egress_policy,
            "egress_policy_digest": egress_policy_digest,
            "raw_token_material_present": False,
            "runtime_authorized": False,
        }

    @app.get(
        "/internal/v1/agent-job-simulations/{job_id}/budget",
        response_model=AgentBudgetLedgerView,
    )
    def get_agent_job_budget(
        job_id: str,
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> AgentBudgetLedger:
        ledger = db.get(AgentBudgetLedger, job_id)
        if ledger is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "agent budget not found")
        return ledger

    @app.post(
        "/internal/v1/agent-job-simulations/{job_id}/usage-reservations",
        response_model=AgentUsageResult,
    )
    def reserve_agent_job_usage(
        job_id: str,
        payload: AgentUsageCreate,
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
        idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    ) -> dict:
        existing = db.scalar(
            select(AgentUsageRecord).where(AgentUsageRecord.idempotency_key == idempotency_key)
        )
        if existing is not None:
            expected = payload.model_dump()
            actual = {
                "trace_id": existing.trace_id,
                "span_id": existing.span_id,
                "meter_name": existing.meter_name,
                "wall_clock_seconds": existing.wall_clock_seconds,
                "iterations": existing.iterations,
                "model_tokens": existing.model_tokens,
                "monetary_cost_microunits": existing.monetary_cost_microunits,
                "external_calls": existing.external_calls,
                "egress_bytes": existing.egress_bytes,
                "concurrency_observed": existing.concurrency_observed,
            }
            if existing.job_id != job_id or actual != expected:
                raise HTTPException(status.HTTP_409_CONFLICT, "usage idempotency key payload differs")
            ledger = db.get(AgentBudgetLedger, job_id)
            job = db.get(AgentJob, job_id)
            assert ledger is not None and job is not None
            return {"usage": existing, "budget": ledger, "job_status": job.status, "compute_allocated": job.compute_allocated, "runtime_authorized": False}

        job = db.get(AgentJob, job_id)
        ledger = db.get(AgentBudgetLedger, job_id)
        if job is None or ledger is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "agent job or budget not found")
        if job.status != "RUNNING" or ledger.status != "ACTIVE":
            raise HTTPException(status.HTTP_409_CONFLICT, "usage can be reserved only for an active running job")

        proposed = {
            "WALL_CLOCK": ledger.wall_clock_consumed_seconds + payload.wall_clock_seconds,
            "ITERATIONS": ledger.iterations_consumed + payload.iterations,
            "MODEL_TOKENS": ledger.model_tokens_consumed + payload.model_tokens,
            "MONETARY_COST": ledger.monetary_cost_consumed_microunits + payload.monetary_cost_microunits,
            "EXTERNAL_CALLS": ledger.external_calls_consumed + payload.external_calls,
            "EGRESS_BYTES": ledger.egress_bytes_consumed + payload.egress_bytes,
            "CONCURRENCY": max(ledger.concurrency_peak, payload.concurrency_observed),
        }
        limits = {
            "WALL_CLOCK": ledger.wall_clock_limit_seconds,
            "ITERATIONS": ledger.iteration_limit,
            "MODEL_TOKENS": ledger.model_token_limit,
            "MONETARY_COST": ledger.monetary_cost_limit_microunits,
            "EXTERNAL_CALLS": ledger.external_call_limit,
            "EGRESS_BYTES": ledger.egress_byte_limit,
            "CONCURRENCY": ledger.concurrency_limit,
        }
        exceeded = sorted(name for name, value in proposed.items() if value > limits[name])
        usage = AgentUsageRecord(
            usage_id=str(uuid4()),
            idempotency_key=idempotency_key,
            job_id=job_id,
            **payload.model_dump(),
            outcome="DENIED" if exceeded else "APPLIED",
            exceeded_dimensions=exceeded,
        )
        db.add(usage)
        ledger_values: dict = {"version": ledger.version + 1}
        if exceeded:
            ledger_values["status"] = "EXHAUSTED"
        else:
            ledger_values.update(
                wall_clock_consumed_seconds=proposed["WALL_CLOCK"],
                iterations_consumed=proposed["ITERATIONS"],
                model_tokens_consumed=proposed["MODEL_TOKENS"],
                monetary_cost_consumed_microunits=proposed["MONETARY_COST"],
                external_calls_consumed=proposed["EXTERNAL_CALLS"],
                egress_bytes_consumed=proposed["EGRESS_BYTES"],
                concurrency_peak=proposed["CONCURRENCY"],
            )
        budget_update = db.execute(
            update(AgentBudgetLedger)
            .where(AgentBudgetLedger.job_id == job_id, AgentBudgetLedger.version == ledger.version)
            .values(**ledger_values)
            .execution_options(synchronize_session=False)
        )
        if budget_update.rowcount != 1:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "concurrent budget reservation")

        measurements = {
            key: value
            for key, value in {
                "wall_clock_seconds": payload.wall_clock_seconds,
                "iterations": payload.iterations,
                "model_tokens": payload.model_tokens,
                "cost_microunits": payload.monetary_cost_microunits,
                "external_calls": payload.external_calls,
                "egress_bytes": payload.egress_bytes,
                "concurrency_observed": payload.concurrency_observed,
            }.items()
            if value
        }
        db.add(
            AgentTraceEvent(
                event_id=str(uuid4()),
                idempotency_key=f"budget:{idempotency_key}",
                job_id=job_id,
                trace_id=payload.trace_id,
                span_id=payload.span_id,
                parent_span_id=None,
                span_name=payload.meter_name,
                phase="POINT",
                outcome="BUDGET_DENIED" if exceeded else "OK",
                measurements=measurements,
                policy_reason_code="BUDGET_EXCEEDED" if exceeded else None,
            )
        )
        if exceeded:
            job_update = db.execute(
                update(AgentJob)
                .where(AgentJob.job_id == job_id, AgentJob.event_version == job.event_version)
                .values(status="BUDGET_EXHAUSTED", event_version=job.event_version + 1, compute_allocated=False, runtime_authorized=False)
                .execution_options(synchronize_session=False)
            )
            if job_update.rowcount != 1:
                db.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, "concurrent budget stop")
            queue_item = db.scalar(select(AgentQueueItem).where(AgentQueueItem.job_id == job_id))
            if queue_item is not None:
                queue_item.status = "CANCELLED"
                queue_item.event_version += 1
            active_leases = list(db.scalars(select(AgentCredentialLease).where(AgentCredentialLease.job_id == job_id, AgentCredentialLease.status == "ACTIVE")))
            stopped_at = integration_utcnow()
            for lease in active_leases:
                lease.status = "REVOKED"
                lease.revoked_at = stopped_at
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "duplicate usage reservation") from exc
        db.refresh(usage)
        db.expire(ledger)
        db.refresh(ledger)
        db.expire(job)
        db.refresh(job)
        return {"usage": usage, "budget": ledger, "job_status": job.status, "compute_allocated": job.compute_allocated, "runtime_authorized": False}

    @app.post(
        "/internal/v1/agent-job-simulations/{job_id}/trace-events",
        response_model=AgentTraceEventView,
        status_code=status.HTTP_201_CREATED,
    )
    def create_agent_trace_event(
        job_id: str,
        payload: AgentTraceEventCreate,
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
        idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    ) -> AgentTraceEvent:
        job = db.get(AgentJob, job_id)
        if job is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "agent job not found")
        existing = db.scalar(select(AgentTraceEvent).where(AgentTraceEvent.idempotency_key == idempotency_key))
        measurements = {
            key: value
            for key, value in payload.model_dump().items()
            if key in {"duration_ms", "attempt", "queue_latency_ms", "cold_start_ms", "model_tokens", "cost_microunits", "exit_code"}
            and value is not None
        }
        if existing is not None:
            if existing.job_id != job_id or existing.trace_id != payload.trace_id or existing.span_id != payload.span_id or existing.span_name != payload.span_name or existing.phase != payload.phase or existing.outcome != payload.outcome or existing.measurements != measurements or existing.policy_reason_code != payload.policy_reason_code:
                raise HTTPException(status.HTTP_409_CONFLICT, "trace idempotency key payload differs")
            return existing
        item = AgentTraceEvent(
            event_id=str(uuid4()),
            idempotency_key=idempotency_key,
            job_id=job_id,
            trace_id=payload.trace_id,
            span_id=payload.span_id,
            parent_span_id=payload.parent_span_id,
            span_name=payload.span_name,
            phase=payload.phase,
            outcome=payload.outcome,
            measurements=measurements,
            policy_reason_code=payload.policy_reason_code,
        )
        db.add(item)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "duplicate trace event") from exc
        db.refresh(item)
        return item

    @app.post(
        "/internal/v1/agent-job-simulations/{job_id}/transitions",
        response_model=AgentJobView,
    )
    def transition_agent_job_simulation(
        job_id: str,
        payload: AgentJobTransition,
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> AgentJob:
        item = db.get(AgentJob, job_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "agent job not found")
        if payload.event_version != item.event_version + 1:
            raise HTTPException(status.HTTP_409_CONFLICT, "agent job event_version gap or replay")
        if payload.action == "WAIT_FOR_APPROVAL" and item.checkpoint_digest is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "approval wait requires a persisted checkpoint")
        try:
            target = transition_target(
                item.status,
                payload.action,
                checkpoint_digest=payload.checkpoint_digest,
                approval_action=payload.approval_action,
            )
        except AgentJobError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        queue_item = db.scalar(select(AgentQueueItem).where(AgentQueueItem.job_id == job_id))
        if payload.action == "ENQUEUE" and queue_item is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "agent job already has a queue item")
        if payload.action == "START" and (queue_item is None or queue_item.status != "READY"):
            raise HTTPException(status.HTTP_409_CONFLICT, "agent job is not ready in the local queue")
        if payload.action in {"APPROVE", "RESUME"} and (
            queue_item is None or queue_item.status != "PAUSED"
        ):
            raise HTTPException(status.HTTP_409_CONFLICT, "agent job has no paused queue item to resume")
        values: dict = {
            "status": target,
            "event_version": payload.event_version,
            "compute_allocated": compute_is_allocated(target),
            "runtime_authorized": False,
        }
        if payload.action == "CHECKPOINT":
            values["checkpoint_digest"] = payload.checkpoint_digest
            values["checkpoint_sequence"] = item.checkpoint_sequence + 1
        if payload.action == "WAIT_FOR_APPROVAL":
            values["awaiting_action"] = payload.approval_action
        elif payload.action in {"APPROVE", "REJECT"}:
            values["awaiting_action"] = None
        updated = db.execute(
            update(AgentJob)
            .where(
                AgentJob.job_id == job_id,
                AgentJob.event_version == item.event_version,
            )
            .values(**values)
            .execution_options(synchronize_session=False)
        )
        if updated.rowcount != 1:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "concurrent agent job transition")

        if payload.action == "ENQUEUE":
            envelope, envelope_digest = build_queue_envelope(item)
            queue_item = AgentQueueItem(
                queue_id=str(uuid4()),
                job_id=job_id,
                envelope=envelope,
                envelope_digest=envelope_digest,
                status="READY",
                delivery_attempt=0,
                event_version=1,
            )
            db.add(queue_item)
        elif payload.action in {"START", "APPROVE", "RESUME"}:
            assert queue_item is not None
            queue_item.status = "CLAIMED"
            queue_item.delivery_attempt += 1
            queue_item.event_version += 1
            for credential_class in CREDENTIAL_CLASSES:
                db.add(
                    AgentCredentialLease(
                        **new_lease_metadata(job_id, credential_class, payload.event_version)
                    )
                )
        elif payload.action in {"CHECKPOINT", "WAIT_FOR_APPROVAL"}:
            if queue_item is not None:
                queue_item.status = "PAUSED"
                queue_item.event_version += 1
        elif target in {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"}:
            if queue_item is not None:
                queue_item.status = "DONE" if target == "COMPLETED" else "CANCELLED"
                queue_item.event_version += 1

        if payload.action == "CHECKPOINT" or target in {
            "COMPLETED",
            "FAILED",
            "CANCELLED",
            "TIMED_OUT",
        }:
            active_leases = list(
                db.scalars(
                    select(AgentCredentialLease).where(
                        AgentCredentialLease.job_id == job_id,
                        AgentCredentialLease.status == "ACTIVE",
                    )
                )
            )
            revoked_at = integration_utcnow()
            for lease in active_leases:
                lease.status = "REVOKED"
                lease.revoked_at = revoked_at
        if target in {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"}:
            ledger = db.get(AgentBudgetLedger, job_id)
            if ledger is not None and ledger.status == "ACTIVE":
                ledger.status = "CLOSED"
                ledger.version += 1
        db.commit()
        db.expire(item)
        db.refresh(item)
        return item

    @app.post("/api/v1/requests", response_model=RequestView, status_code=status.HTTP_201_CREATED)
    def create_request(
        payload: RequestCreate,
        principal: Annotated[Principal, Depends(user_principal)],
        db: Annotated[Session, Depends(get_db)],
        idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    ) -> AccessRequest:
        if not app_settings.enable_legacy_execution_profile_requests:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "direct execution-profile requests are disabled; use a blueprint request",
            )
        product = CATALOG_BY_CODE.get(payload.product_code)
        if product is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown product_code")
        if any((payload.cpu, payload.memory_gib, payload.storage_gib)):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "OpenStack compute and network settings are determined by the approved product SKU",
            )
        if payload.duration_hours not in product["allowed_duration_hours"]:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "duration must be one of the approved product durations",
            )
        try:
            parameters = normalize_parameters(payload.product_code, payload.parameters)
        except ValueError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        existing = db.scalar(select(AccessRequest).where(AccessRequest.idempotency_key == idempotency_key))
        if existing:
            if existing.owner_id != principal.subject:
                raise HTTPException(status.HTTP_409_CONFLICT, "idempotency key belongs to another owner")
            if existing.delivery_status == "FAILED":
                delivery_status, error = send_to_approval(app_settings, existing)
                existing.delivery_status = delivery_status
                existing.last_error = error
                if error:
                    existing.retry_count += 1
                db.commit()
                db.refresh(existing)
            return existing
        active_count = int(
            db.scalar(
                select(func.count())
                .select_from(AccessRequest)
                .where(
                    AccessRequest.owner_id == principal.subject,
                    AccessRequest.product_code == payload.product_code,
                    AccessRequest.status.notin_({"REJECTED", "CANCELLED", "REVOKED", "EXPIRED", "TERMINATED"}),
                )
            )
            or 0
        )
        if active_count >= int(product["max_resources_per_user"]):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "the active resource limit for this product has been reached",
            )
        runtime_spec = PRODUCT_RUNTIME_SPECS[payload.product_code]
        item = AccessRequest(
            request_id=str(uuid4()),
            idempotency_key=idempotency_key,
            owner_id=principal.subject,
            product_code=payload.product_code,
            cpu=runtime_spec["cpu"],
            memory_gib=runtime_spec["memory_gib"],
            storage_gib=runtime_spec["storage_gib"],
            duration_hours=payload.duration_hours,
            purpose=payload.purpose,
            parameters=parameters,
        )
        db.add(item)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "duplicate request") from exc
        db.refresh(item)
        delivery_status, error = send_to_approval(app_settings, item)
        item.delivery_status = delivery_status
        item.last_error = error
        if delivery_status == "FAILED":
            item.retry_count += 1
        db.commit()
        db.refresh(item)
        return item

    def submit_blueprint_request(
        payload: BlueprintResolveRequest, principal: Principal, db: Session,
        idempotency_key: str, portal_context: dict[str, str] | None = None,
    ) -> dict:
        try:
            resolution = resolve_blueprint(**payload.model_dump())
        except BlueprintResolutionError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        if resolution["resolution_status"] != "RESOLVED_LOCAL":
            blockers = ", ".join(
                [*resolution["blocking_components"], *resolution["blocking_gates"]]
            )
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"blueprint has unimplemented dependencies: {blockers}",
            )
        product_code = str(resolution["selected_execution_profile"])
        product = CATALOG_BY_CODE[product_code]
        existing = db.scalar(
            select(AccessRequest).where(AccessRequest.idempotency_key == idempotency_key)
        )
        if existing:
            expected_context = portal_context or {}
            actual_context = {k: v for k, v in existing.parameters.items() if k.startswith("_portal_")}
            if actual_context != expected_context:
                raise HTTPException(status.HTTP_409_CONFLICT, "idempotency key context differs")
            if existing.owner_id != principal.subject:
                raise HTTPException(status.HTTP_409_CONFLICT, "idempotency key belongs to another owner")
            if existing.parameters.get("_manifest_digest") != resolution["manifest_digest"]:
                raise HTTPException(status.HTTP_409_CONFLICT, "idempotency key payload differs")
            if existing.delivery_status == "FAILED":
                delivery_status, error = send_to_approval(app_settings, existing)
                existing.delivery_status = delivery_status
                existing.last_error = error
                if error:
                    existing.retry_count += 1
                db.commit()
                db.refresh(existing)
            return _blueprint_request_view(existing)

        active_count = int(
            db.scalar(
                select(func.count())
                .select_from(AccessRequest)
                .where(
                    AccessRequest.owner_id == principal.subject,
                    AccessRequest.parameters["_blueprint_id"].as_string()
                    == payload.blueprint_id,
                    AccessRequest.status.notin_({"REJECTED", "CANCELLED", "REVOKED", "EXPIRED", "TERMINATED"}),
                )
            )
            or 0
        )
        if active_count >= int(product["max_resources_per_user"]):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "the active resource limit for this blueprint has been reached",
            )

        project_suffix = hashlib.sha256(
            f"{principal.subject}|{idempotency_key}".encode("utf-8")
        ).hexdigest()[:12]
        parameters: dict[str, str | int] = {
            "project_name": f"lab-{project_suffix}",
            "workload_purpose": "saas-application-development",
            "_blueprint_id": payload.blueprint_id,
            "_blueprint_environment": payload.environment,
            "_blueprint_size": payload.size,
            "_manifest_digest": resolution["manifest_digest"],
        }
        parameters.update(portal_context or {})
        runtime_spec = PRODUCT_RUNTIME_SPECS[product_code]
        item = AccessRequest(
            request_id=str(uuid4()),
            idempotency_key=idempotency_key,
            owner_id=principal.subject,
            product_code=product_code,
            cpu=runtime_spec["cpu"],
            memory_gib=runtime_spec["memory_gib"],
            storage_gib=runtime_spec["storage_gib"],
            duration_hours=payload.duration_hours,
            purpose=payload.purpose,
            parameters=parameters,
        )
        db.add(item)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "duplicate request") from exc
        db.refresh(item)
        delivery_status, error = send_to_approval(app_settings, item)
        item.delivery_status = delivery_status
        item.last_error = error
        if delivery_status == "FAILED":
            item.retry_count += 1
        db.commit()
        db.refresh(item)
        return _blueprint_request_view(item)

    @app.post(
        "/api/v1/blueprint-requests",
        response_model=BlueprintRequestView,
        status_code=status.HTTP_201_CREATED,
    )
    def create_blueprint_request(
        payload: BlueprintResolveRequest,
        principal: Annotated[Principal, Depends(user_principal)],
        db: Annotated[Session, Depends(get_db)],
        idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    ) -> dict:
        return submit_blueprint_request(payload, principal, db, idempotency_key)

    @app.get("/api/v1/requests", response_model=list[RequestView])
    def list_requests(
        principal: Annotated[Principal, Depends(user_principal)],
        db: Annotated[Session, Depends(get_db)],
        request_status: Annotated[str | None, Query(alias="status")] = None,
    ) -> list[AccessRequest]:
        stmt = select(AccessRequest).where(AccessRequest.owner_id == principal.subject,
            or_(AccessRequest.parameters["_portal_tenant"].as_string().is_(None),
                AccessRequest.parameters["_portal_tenant"].as_string() == (principal.tenant_id or "")))
        if request_status:
            stmt = stmt.where(AccessRequest.status == request_status.upper())
        return list(db.scalars(stmt.order_by(AccessRequest.created_at.desc())))

    @app.get("/api/v1/requests/{request_id}", response_model=RequestView)
    def get_request(
        request_id: str,
        principal: Annotated[Principal, Depends(user_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> AccessRequest:
        item = db.get(AccessRequest, request_id)
        if (not item or item.owner_id != principal.subject
                or (item.parameters.get("_portal_tenant") and item.parameters["_portal_tenant"] != principal.tenant_id)):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
        return item

    @app.post("/api/v1/requests/{request_id}/cancel", response_model=RequestView)
    def cancel_request(
        request_id: str,
        principal: Annotated[Principal, Depends(user_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> AccessRequest:
        item = db.get(AccessRequest, request_id)
        if (not item or item.owner_id != principal.subject
                or (item.parameters.get("_portal_tenant") and item.parameters["_portal_tenant"] != principal.tenant_id)):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
        if item.status != "PENDING":
            raise HTTPException(status.HTTP_409_CONFLICT, "only a PENDING request can be cancelled")
        item.status = "CANCELLED"
        item.event_version += 1
        db.commit()
        db.refresh(item)
        delivery_status, error = send_to_approval(app_settings, item)
        item.delivery_status = delivery_status
        item.last_error = error
        if error:
            item.retry_count += 1
        db.commit()
        db.refresh(item)
        return item

    @app.post("/internal/v1/requests/{request_id}/redeliver", response_model=RequestView)
    def redeliver_request(
        request_id: str,
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> AccessRequest:
        item = db.get(AccessRequest, request_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
        delivery_status, error = send_to_approval(app_settings, item)
        item.delivery_status = delivery_status
        item.last_error = error
        if error:
            item.retry_count += 1
        db.commit()
        db.refresh(item)
        return item

    @app.post("/internal/v1/requests/{request_id}/status", response_model=RequestView)
    def update_status(
        request_id: str,
        payload: StatusUpdate,
        background_tasks: BackgroundTasks,
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> AccessRequest:
        item = db.get(AccessRequest, request_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
        if payload.event_version <= item.event_version:
            return item
        if payload.event_version != item.event_version + 1:
            raise HTTPException(status.HTTP_409_CONFLICT, "event_version gap")
        if not _can_transition(item.status, payload.status, app_settings.enable_provisioning_states):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"invalid state transition: {item.status} -> {payload.status}",
            )
        item.status = payload.status
        item.event_version = payload.event_version
        item.retry_count = payload.retry_count
        item.rejection_reason = payload.reason if payload.status == "REJECTED" else item.rejection_reason
        item.grant_id = payload.grant_id or item.grant_id
        item.grant_expires_at = payload.grant_expires_at or item.grant_expires_at
        item.resource_id = payload.resource_id or item.resource_id
        item.resource_status = payload.resource_status or item.resource_status
        if payload.resource_id:
            projection = db.get(ResourceProjection, payload.resource_id)
            if projection is None:
                projection = ResourceProjection(
                    resource_id=payload.resource_id,
                    request_id=item.request_id,
                    owner_id=item.owner_id,
                    status=payload.resource_status or payload.status,
                    endpoint=payload.resource_endpoint,
                    resource_type=item.product_code,
                    display_name=product_label(item.product_code),
                    details={},
                    event_version=payload.event_version,
                )
                db.add(projection)
            else:
                projection.status = payload.resource_status or payload.status
                projection.endpoint = payload.resource_endpoint or projection.endpoint
                projection.event_version = payload.event_version
        mock_task: tuple[str, str] | None = None
        mock_enabled = app_settings.auth_mode == "dev" and app_settings.enable_mock_provisioner
        if (
            mock_enabled
            and payload.status == "GRANTED"
            and not item.resource_id
        ):
            spec = build_mock_resource(item)
            resource_id = spec.resource_id
            _apply_resource_update(
                db,
                item,
                ResourceStatusUpdate(
                    resource_id=resource_id,
                    status="PROVISIONING",
                    resource_type=spec.resource_type,
                    display_name=spec.display_name,
                    details=spec.details,
                    event_version=1,
                ),
            )
            mock_task = ("provision", resource_id)
        elif (
            mock_enabled
            and payload.status in {"REVOKED", "EXPIRED"}
            and item.resource_id
            and item.resource_id.startswith("DEMO-")
        ):
            projection = db.get(ResourceProjection, item.resource_id)
            if projection and projection.status in {"PROVISIONING", "RUNNING", "PROVISION_FAILED"}:
                _apply_resource_update(
                    db,
                    item,
                    ResourceStatusUpdate(
                        resource_id=projection.resource_id,
                        status="TERMINATING",
                        event_version=projection.event_version + 1,
                    ),
                )
                mock_task = ("terminate", projection.resource_id)
        db.commit()
        db.refresh(item)
        if mock_task:
            operation, resource_id = mock_task
            task = complete_mock_provision if operation == "provision" else complete_mock_termination
            background_tasks.add_task(task, item.request_id, resource_id)
        return item

    @app.post(
        "/internal/v1/requests/{request_id}/resource",
        response_model=ResourceView,
        tags=["internal"],
    )
    def update_resource(
        request_id: str,
        payload: ResourceStatusUpdate,
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> ResourceProjection:
        item = db.get(AccessRequest, request_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
        projection = _apply_resource_update(db, item, payload)
        db.commit()
        db.refresh(projection)
        return projection

    @app.get("/api/v1/resources", response_model=list[ResourceView])
    def list_resources(
        principal: Annotated[Principal, Depends(user_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> list[ResourceProjection]:
        stmt = select(ResourceProjection).join(AccessRequest, ResourceProjection.request_id == AccessRequest.request_id).where(
            ResourceProjection.owner_id == principal.subject,
            or_(AccessRequest.parameters["_portal_tenant"].as_string().is_(None),
                AccessRequest.parameters["_portal_tenant"].as_string() == (principal.tenant_id or "")))
        return list(db.scalars(stmt.order_by(ResourceProjection.updated_at.desc())))

    @app.get("/api/v1/resources/{resource_id}", response_model=ResourceView)
    def get_resource(
        resource_id: str,
        principal: Annotated[Principal, Depends(user_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> ResourceProjection:
        item = db.get(ResourceProjection, resource_id)
        if not item or item.owner_id != principal.subject:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "resource not found")
        owner = db.get(AccessRequest, item.request_id)
        if owner and owner.parameters.get("_portal_tenant") and owner.parameters["_portal_tenant"] != principal.tenant_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "resource not found")
        return item

    @app.post("/internal/v1/demo/reset", response_model=DemoResetResult, include_in_schema=False)
    def reset_demo_data(
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> DemoResetResult:
        if app_settings.auth_mode != "dev" or not app_settings.enable_demo_reset:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "demo reset is not available")
        resource_count = int(db.scalar(select(func.count()).select_from(ResourceProjection)) or 0)
        request_count = int(db.scalar(select(func.count()).select_from(AccessRequest)) or 0)
        db.execute(delete(ResourceProjection))
        db.execute(delete(AccessRequest))
        db.commit()
        return DemoResetResult(deleted={"resources": resource_count, "requests": request_count})

    @app.post("/internal/v1/demo/seed", response_model=DemoSeedResult, include_in_schema=False)
    def seed_demo_data(
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> DemoSeedResult:
        if app_settings.auth_mode != "dev" or not app_settings.enable_demo_reset:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "demo seed is not available")

        idempotency_key = "demo-seed-dev-os-vm-s-v1"
        existing = db.scalar(
            select(AccessRequest).where(AccessRequest.idempotency_key == idempotency_key)
        )
        if existing:
            if existing.delivery_status == "FAILED":
                delivery_status, error = send_to_approval(app_settings, existing)
                existing.delivery_status = delivery_status
                existing.last_error = error
                if error:
                    existing.retry_count += 1
                db.commit()
            return DemoSeedResult(
                status="existing",
                created=False,
                delivery_status=existing.delivery_status,
            )

        item = AccessRequest(
            request_id=str(uuid4()),
            idempotency_key=idempotency_key,
            owner_id="demo-user",
            product_code="DEV-OS-VM-S",
            cpu=2,
            memory_gib=2,
            storage_gib=30,
            duration_hours=24,
            purpose="MVP 핵심 시연용 사내 SaaS 개발 VM",
            parameters={
                "project_name": "mvp-demo",
                "workload_purpose": "backend-integration-test",
            },
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        delivery_status, error = send_to_approval(app_settings, item)
        item.delivery_status = delivery_status
        item.last_error = error
        if error:
            item.retry_count += 1
        db.commit()
        return DemoSeedResult(
            status="seeded",
            created=True,
            delivery_status=delivery_status,
        )

    from .portal import install_portal_routes

    install_portal_routes(app, submit_blueprint_request, cancel_request)
    return app


app = create_app()
