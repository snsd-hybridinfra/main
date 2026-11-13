from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from .auth import Principal, require_roles
from .clients import (
    create_grant,
    reset_demo_services,
    seed_demo_request,
    send_request_status,
    send_resource_status,
)
from .config import Settings
from .db import Base, ensure_local_schema_compatibility, get_db, make_engine, make_session_factory
from .models import ApprovalDecision, ApprovalRequest, AuditEvent, ProvisioningJob
from .policies import scopes_for_product
from .provisioning import (
    approved_inputs,
    logical_resource_id,
    module_for_product,
    validate_product_request,
)
from .schemas import (
    ApprovalIngest,
    ApprovalRequestView,
    AuditEventView,
    DemoResetResult,
    DemoSeedResult,
    DecisionCreate,
    DecisionResult,
    HealthView,
    MonitoringDashboard,
    DestroyRequest,
    JobClaim,
    ProvisioningJobView,
    ProvisioningResult,
    ProvisioningResultView,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings.from_env()
    engine = make_engine(app_settings.database_url)
    session_factory = make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if app_settings.auto_create_schema:
            Base.metadata.create_all(engine)
            ensure_local_schema_compatibility(engine)
        yield
        engine.dispose()

    app = FastAPI(title="approval-api", version="0.1.0", lifespan=lifespan)
    app.state.settings = app_settings
    app.state.session_factory = session_factory

    service_principal = require_roles("service", scopes=("service:callback",))
    approver_principal = require_roles("approver", scopes=("approval:manage",))
    audit_principal = require_roles("approver", "auditor", scopes=("audit:read",))

    def queue_provisioning_job(
        item: ApprovalRequest,
        operation: str,
        db: Session,
        *,
        approved_by: str,
    ) -> ProvisioningJob:
        product_spec = module_for_product(item.product_code)
        if product_spec is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "product is not Terraform managed")
        key = f"terraform:{operation.lower()}:{item.request_id}"
        existing = db.scalar(
            select(ProvisioningJob).where(ProvisioningJob.idempotency_key == key)
        )
        if existing:
            return existing

        apply_job = None
        if operation == "DESTROY":
            apply_job = db.scalar(
                select(ProvisioningJob)
                .where(
                    ProvisioningJob.request_id == item.request_id,
                    ProvisioningJob.operation == "APPLY",
                )
                .order_by(ProvisioningJob.created_at.desc())
            )
            if not apply_job or not apply_job.resource_id:
                raise HTTPException(status.HTTP_409_CONFLICT, "request has no provisioned resource")

        input_values = (
            dict(apply_job.input_values)
            if apply_job
            else approved_inputs(item, approved_by=approved_by)
        )
        expires_at = (
            apply_job.expires_at
            if apply_job
            else datetime.fromisoformat(str(input_values["expires_at"]))
        )

        job = ProvisioningJob(
            job_id=str(uuid4()),
            request_id=item.request_id,
            idempotency_key=key,
            operation=operation,
            product_code=item.product_code,
            product_version=product_spec.product_version,
            module_name=product_spec.module_name,
            module_version=product_spec.module_version,
            artifact_digest=product_spec.artifact_digest,
            approved_by=(apply_job.approved_by if apply_job else approved_by),
            expires_at=expires_at,
            state_key=f"requests/{item.request_id}/terraform.tfstate",
            input_values=input_values,
            resource_id=(apply_job.resource_id if apply_job else logical_resource_id(item.request_id)),
            resource_event_version=(apply_job.resource_event_version if apply_job else 0),
        )
        db.add(job)
        db.add(
            AuditEvent(
                audit_id=str(uuid4()),
                event_type=f"TERRAFORM_{operation}_QUEUED",
                aggregate_type="provisioning-job",
                aggregate_id=job.job_id,
                actor_id="approval-api",
                details={"request_id": item.request_id, "module": product_spec.module_name},
            )
        )
        db.commit()
        db.refresh(job)
        return job

    @app.get("/healthz", response_model=HealthView, tags=["operations"])
    def healthz() -> HealthView:
        return HealthView(status="ok")

    @app.get("/readyz", response_model=HealthView, tags=["operations"])
    def readyz(db: Annotated[Session, Depends(get_db)]) -> HealthView:
        try:
            db.execute(text("SELECT 1"))
            if app_settings.required_db_revision:
                revision = db.scalar(text("SELECT version_num FROM control_service.alembic_version"))
                if revision != app_settings.required_db_revision:
                    raise RuntimeError("database revision mismatch")
        except Exception as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "database is not ready") from exc
        return HealthView(status="ready")

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(
            "# HELP iaas_service_up Service process health.\n"
            "# TYPE iaas_service_up gauge\n"
            'iaas_service_up{service="approval-api"} 1\n',
            media_type="text/plain; version=0.0.4",
        )

    @app.post("/internal/v1/requests", response_model=ApprovalRequestView)
    def ingest_request(
        payload: ApprovalIngest,
        principal: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> ApprovalRequest:
        existing = db.get(ApprovalRequest, payload.request_id)
        if existing:
            if existing.idempotency_key != payload.idempotency_key:
                raise HTTPException(status.HTTP_409_CONFLICT, "request_id already exists")
            if payload.event_version > existing.event_version and payload.status == "CANCELLED":
                existing.status = "CANCELLED"
                existing.event_version = payload.event_version
                existing.retry_count = payload.retry_count
                db.add(
                    AuditEvent(
                        audit_id=str(uuid4()),
                        event_type="REQUEST_CANCELLED",
                        aggregate_type="request",
                        aggregate_id=existing.request_id,
                        actor_id=principal.subject,
                        details={"event_version": existing.event_version},
                    )
                )
                db.commit()
                db.refresh(existing)
            return existing
        try:
            validate_product_request(payload)
        except ValueError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        item_values = payload.model_dump(
            exclude={"updated_at", "blueprint_id", "manifest_digest", "resolved_manifest"}
        )
        if payload.blueprint_id is not None:
            item_values["parameters"] = {
                **item_values["parameters"],
                "_blueprint_id": payload.blueprint_id,
                "_manifest_digest": payload.manifest_digest,
                "_resolved_manifest": payload.resolved_manifest,
            }
        item = ApprovalRequest(**item_values)
        db.add(item)
        db.add(
            AuditEvent(
                audit_id=str(uuid4()),
                event_type="REQUEST_RECEIVED",
                aggregate_type="request",
                aggregate_id=item.request_id,
                actor_id=principal.subject,
                details={"event_version": item.event_version},
            )
        )
        db.commit()
        db.refresh(item)
        return item

    @app.get("/admin-api/v1/requests", response_model=list[ApprovalRequestView])
    def list_requests(
        _: Annotated[Principal, Depends(approver_principal)],
        db: Annotated[Session, Depends(get_db)],
        request_status: Annotated[str, Query(alias="status")] = "PENDING",
    ) -> list[ApprovalRequest]:
        stmt = select(ApprovalRequest)
        if request_status.upper() != "ALL":
            stmt = stmt.where(ApprovalRequest.status == request_status.upper())
        return list(db.scalars(stmt.order_by(ApprovalRequest.created_at.asc())))

    @app.get("/admin-api/v1/requests/{request_id}", response_model=ApprovalRequestView)
    def get_request(
        request_id: str,
        _: Annotated[Principal, Depends(approver_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> ApprovalRequest:
        item = db.get(ApprovalRequest, request_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
        return item

    def decide(
        item: ApprovalRequest,
        decision: str,
        payload: DecisionCreate,
        actor: Principal,
        db: Session,
    ) -> DecisionResult:
        if item.requester_id == actor.subject:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "self approval is forbidden")
        if item.status != "PENDING":
            raise HTTPException(status.HTTP_409_CONFLICT, "request is not PENDING")
        item.status = decision
        item.event_version += 1
        db.add(
            ApprovalDecision(
                decision_id=str(uuid4()),
                request_id=item.request_id,
                decision=decision,
                actor_id=actor.subject,
                reason=payload.reason,
                event_version=item.event_version,
            )
        )
        db.add(
            AuditEvent(
                audit_id=str(uuid4()),
                event_type=f"REQUEST_{decision}",
                aggregate_type="request",
                aggregate_id=item.request_id,
                actor_id=actor.subject,
                details={"event_version": item.event_version, "reason": payload.reason},
            )
        )
        db.commit()
        db.refresh(item)

        callback_status, callback_error = send_request_status(app_settings, item, reason=payload.reason)
        grant_status = "NOT_REQUESTED"
        grant_error: str | None = None
        if decision == "APPROVED":
            if app_settings.enable_provisioning_jobs and module_for_product(item.product_code):
                queue_provisioning_job(item, "APPLY", db, approved_by=actor.subject)
                grant_status = "DEFERRED"
            else:
                duration = payload.grant_duration_hours or item.duration_hours
                try:
                    grant_scopes = scopes_for_product(item.product_code, item.parameters)
                except ValueError as exc:
                    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
                grant_status, grant_error = create_grant(app_settings, item, grant_scopes, duration)
        errors = [message for message in (callback_error, grant_error) if message]
        item.delivery_status = (
            "FAILED" if callback_status == "FAILED" or grant_status == "FAILED" else "DELIVERED"
        )
        if callback_status == "SKIPPED" and grant_status in {"SKIPPED", "NOT_REQUESTED", "DEFERRED"}:
            item.delivery_status = "SKIPPED"
        item.last_error = " | ".join(errors) or None
        if errors:
            item.retry_count += 1
        db.commit()
        db.refresh(item)
        return DecisionResult(
            request=ApprovalRequestView.model_validate(item),
            callback_status=callback_status,
            grant_status=grant_status,
        )

    @app.post("/admin-api/v1/requests/{request_id}/approve", response_model=DecisionResult)
    def approve_request(
        request_id: str,
        payload: DecisionCreate,
        principal: Annotated[Principal, Depends(approver_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> DecisionResult:
        item = db.get(ApprovalRequest, request_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
        return decide(item, "APPROVED", payload, principal, db)

    @app.post("/admin-api/v1/requests/{request_id}/reject", response_model=DecisionResult)
    def reject_request(
        request_id: str,
        payload: DecisionCreate,
        principal: Annotated[Principal, Depends(approver_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> DecisionResult:
        item = db.get(ApprovalRequest, request_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
        return decide(item, "REJECTED", payload, principal, db)

    @app.post("/admin-api/v1/requests/{request_id}/retry-sync", response_model=DecisionResult)
    def retry_sync(
        request_id: str,
        principal: Annotated[Principal, Depends(approver_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> DecisionResult:
        item = db.get(ApprovalRequest, request_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
        if item.status not in {"APPROVED", "REJECTED"}:
            raise HTTPException(status.HTTP_409_CONFLICT, "request has no decision to synchronize")
        callback_status, callback_error = send_request_status(app_settings, item)
        grant_status = "NOT_REQUESTED"
        grant_error = None
        if item.status == "APPROVED":
            if app_settings.enable_provisioning_jobs and module_for_product(item.product_code):
                queue_provisioning_job(item, "APPLY", db, approved_by=principal.subject)
                grant_status = "DEFERRED"
            else:
                try:
                    grant_scopes = scopes_for_product(item.product_code, item.parameters)
                except ValueError as exc:
                    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
                grant_status, grant_error = create_grant(
                    app_settings, item, grant_scopes, item.duration_hours
                )
        errors = [message for message in (callback_error, grant_error) if message]
        item.last_error = " | ".join(errors) or None
        item.delivery_status = "FAILED" if errors else "DELIVERED"
        if callback_status == "SKIPPED" and grant_status in {"SKIPPED", "NOT_REQUESTED", "DEFERRED"}:
            item.delivery_status = "SKIPPED"
        if errors:
            item.retry_count += 1
        db.add(
            AuditEvent(
                audit_id=str(uuid4()),
                event_type="REQUEST_SYNC_RETRIED",
                aggregate_type="request",
                aggregate_id=item.request_id,
                actor_id=principal.subject,
                details={"callback_status": callback_status, "grant_status": grant_status},
            )
        )
        db.commit()
        db.refresh(item)
        return DecisionResult(
            request=ApprovalRequestView.model_validate(item),
            callback_status=callback_status,
            grant_status=grant_status,
        )

    @app.get("/admin-api/v1/provisioning/jobs", response_model=list[ProvisioningJobView])
    def list_provisioning_jobs(
        _: Annotated[Principal, Depends(approver_principal)],
        db: Annotated[Session, Depends(get_db)],
        job_status: Annotated[str, Query(alias="status")] = "ALL",
    ) -> list[ProvisioningJob]:
        stmt = select(ProvisioningJob)
        if job_status.upper() != "ALL":
            stmt = stmt.where(ProvisioningJob.status == job_status.upper())
        return list(db.scalars(stmt.order_by(ProvisioningJob.created_at.desc())))

    @app.post("/internal/v1/provisioning/jobs/claim", response_model=ProvisioningJobView)
    def claim_provisioning_job(
        payload: JobClaim,
        principal: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> ProvisioningJob:
        if not app_settings.enable_provisioning_jobs:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "provisioning jobs are disabled")
        if app_settings.auth_mode == "oidc" and payload.runner_id != principal.subject:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "runner_id must match token subject")
        job = db.scalar(
            select(ProvisioningJob)
            .where(ProvisioningJob.status == "QUEUED")
            .order_by(ProvisioningJob.created_at.asc())
            .with_for_update(skip_locked=True)
        )
        if not job:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "no provisioning job is queued")
        job.status = "PLANNING"
        job.runner_id = payload.runner_id
        job.attempts += 1
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        return job

    @app.post(
        "/internal/v1/provisioning/jobs/{job_id}/result",
        response_model=ProvisioningResultView,
    )
    def record_provisioning_result(
        job_id: str,
        payload: ProvisioningResult,
        principal: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> ProvisioningResultView:
        job = db.get(ProvisioningJob, job_id)
        if not job:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "provisioning job not found")
        if job.runner_id and principal.subject != job.runner_id and app_settings.auth_mode == "oidc":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "job belongs to another runner")

        allowed = {
            "APPLY": {"PROVISIONING", "RUNNING", "PROVISION_FAILED"},
            "DESTROY": {"TERMINATING", "TERMINATED", "TERMINATION_FAILED"},
        }
        if payload.status not in allowed[job.operation]:
            raise HTTPException(status.HTTP_409_CONFLICT, "result does not match job operation")
        if payload.status == "RUNNING" and not payload.validation_passed:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "RUNNING requires successful post-apply validation",
            )

        idempotent_status = {
            "APPLYING": "PROVISIONING",
            "SUCCEEDED": "RUNNING",
            "DESTROYING": "TERMINATING",
            "TERMINATED": "TERMINATED",
        }
        if idempotent_status.get(job.status) == payload.status:
            return ProvisioningResultView(
                job=ProvisioningJobView.model_validate(job),
                callback_status="DELIVERED",
                grant_status="DELIVERED" if payload.status == "RUNNING" else "NOT_REQUESTED",
            )

        request_item = db.get(ApprovalRequest, job.request_id)
        if not request_item:
            raise HTTPException(status.HTTP_409_CONFLICT, "approval request is missing")
        resource_id = payload.resource_id or job.resource_id or logical_resource_id(job.request_id)
        if job.resource_id and resource_id != job.resource_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "logical resource_id cannot change")
        job.resource_id = resource_id
        job.output_values = dict(payload.outputs)

        callback_status = "NOT_REQUESTED"
        callback_error: str | None = None
        grant_status = "NOT_REQUESTED"
        grant_error: str | None = None
        next_resource_version = job.resource_event_version + 1
        if job.status == "GRANT_FAILED" and payload.status == "RUNNING":
            callback_status = "DELIVERED"
        else:
            callback_status, callback_error = send_resource_status(
                app_settings,
                request_item,
                resource_id=resource_id,
                resource_status=payload.status,
                event_version=next_resource_version,
                endpoint=payload.endpoint,
                display_name=payload.display_name,
                details=payload.details,
            )
            if callback_status != "FAILED":
                job.resource_event_version = next_resource_version

        terminal_statuses = {"RUNNING", "PROVISION_FAILED", "TERMINATED", "TERMINATION_FAILED"}
        status_map = {
            "PROVISIONING": "APPLYING",
            "RUNNING": "SUCCEEDED",
            "PROVISION_FAILED": payload.failure_code or "APPLY_FAILED",
            "TERMINATING": "DESTROYING",
            "TERMINATED": "TERMINATED",
            "TERMINATION_FAILED": payload.failure_code or "DESTROY_FAILED",
        }
        job.status = status_map[payload.status]
        if callback_status == "FAILED":
            job.status = "CALLBACK_FAILED"
        elif payload.status == "RUNNING":
            try:
                grant_scopes = scopes_for_product(request_item.product_code, request_item.parameters)
            except ValueError as exc:
                grant_status, grant_error = "FAILED", str(exc)
            else:
                grant_status, grant_error = create_grant(
                    app_settings,
                    request_item,
                    grant_scopes,
                    request_item.duration_hours,
                )
            if grant_status == "FAILED":
                job.status = "GRANT_FAILED"
        if payload.status in terminal_statuses:
            job.finished_at = datetime.now(timezone.utc)
        errors = [value for value in (payload.error, callback_error, grant_error) if value]
        job.last_error = " | ".join(errors)[:4000] or None
        db.add(
            AuditEvent(
                audit_id=str(uuid4()),
                event_type=f"TERRAFORM_{job.operation}_{payload.status}",
                aggregate_type="provisioning-job",
                aggregate_id=job.job_id,
                actor_id=principal.subject,
                details={
                    "request_id": job.request_id,
                    "callback_status": callback_status,
                    "grant_status": grant_status,
                    "validation_passed": payload.validation_passed,
                    "failure_code": payload.failure_code,
                    "recovery_status": payload.details.get("recovery_status"),
                    "recovery_verification": payload.details.get("recovery_verification"),
                    "original_failure_code": payload.details.get("original_failure_code"),
                },
            )
        )
        db.commit()
        db.refresh(job)
        return ProvisioningResultView(
            job=ProvisioningJobView.model_validate(job),
            callback_status=callback_status,
            grant_status=grant_status,
        )

    @app.post(
        "/admin-api/v1/provisioning/jobs/{job_id}/retry",
        response_model=ProvisioningJobView,
    )
    def retry_provisioning_job(
        job_id: str,
        principal: Annotated[Principal, Depends(approver_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> ProvisioningJob:
        job = db.get(ProvisioningJob, job_id)
        if not job:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "provisioning job not found")
        if job.status not in {
            "PLANNING",
            "APPLYING",
            "DESTROYING",
            "PLAN_FAILED",
            "POLICY_DENIED",
            "APPLY_FAILED",
            "BOOTSTRAP_FAILED",
            "BOOTSTRAP_VALIDATION_REQUIRED",
            "CONFIGURATION_FAILED",
            "ROLLBACK_FAILED",
            "DESTROY_FAILED",
            "CALLBACK_FAILED",
            "GRANT_FAILED",
        }:
            raise HTTPException(status.HTTP_409_CONFLICT, "job is not retryable")
        previous_status = job.status
        job.status = "QUEUED"
        job.runner_id = None
        job.started_at = None
        job.finished_at = None
        db.add(
            AuditEvent(
                audit_id=str(uuid4()),
                event_type="TERRAFORM_JOB_REQUEUED",
                aggregate_type="provisioning-job",
                aggregate_id=job.job_id,
                actor_id=principal.subject,
                details={"request_id": job.request_id, "previous_status": previous_status},
            )
        )
        db.commit()
        db.refresh(job)
        return job

    @app.post(
        "/internal/v1/provisioning/requests/{request_id}/destroy",
        response_model=ProvisioningJobView,
    )
    def request_destroy(
        request_id: str,
        payload: DestroyRequest,
        principal: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> ProvisioningJob:
        if not app_settings.enable_provisioning_jobs:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "provisioning jobs are disabled")
        item = db.get(ApprovalRequest, request_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
        if module_for_product(item.product_code) is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "request has no Terraform lifecycle")
        job = queue_provisioning_job(item, "DESTROY", db, approved_by=principal.subject)
        db.add(
            AuditEvent(
                audit_id=str(uuid4()),
                event_type="DESTROY_REQUEST_ACCEPTED",
                aggregate_type="provisioning-job",
                aggregate_id=job.job_id,
                actor_id=principal.subject,
                details={"trigger_status": payload.trigger_status, "reason": payload.reason},
            )
        )
        db.commit()
        db.refresh(job)
        return job

    @app.get("/admin-api/v1/audit-events", response_model=list[AuditEventView])
    def list_audit_events(
        _: Annotated[Principal, Depends(audit_principal)],
        db: Annotated[Session, Depends(get_db)],
        aggregate_type: Literal["request", "provisioning-job"] = "request",
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
    ) -> list[AuditEvent]:
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.aggregate_type == aggregate_type)
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt))

    @app.get("/admin-api/v1/monitoring-dashboard", response_model=MonitoringDashboard)
    def monitoring_dashboard(
        _: Annotated[Principal, Depends(audit_principal)],
    ) -> MonitoringDashboard:
        dashboard_url = app_settings.grafana_dashboard_url
        if not dashboard_url:
            return MonitoringDashboard(status="PENDING")
        parsed = urlsplit(dashboard_url)
        is_relative = dashboard_url.startswith("/") and not dashboard_url.startswith("//")
        is_http = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
        if not (is_relative or is_http):
            return MonitoringDashboard(status="INVALID")
        return MonitoringDashboard(status="READY", dashboard_url=dashboard_url)

    @app.post("/admin-api/v1/demo/reset", response_model=DemoResetResult)
    def reset_demo_data(
        _: Annotated[Principal, Depends(approver_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> DemoResetResult:
        if app_settings.auth_mode != "dev" or not app_settings.enable_demo_reset:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "demo reset is not available")
        try:
            deleted = reset_demo_services(app_settings)
        except RuntimeError as exc:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY, "demo reset downstream failed"
            ) from exc

        decision_count = int(db.scalar(select(func.count()).select_from(ApprovalDecision)) or 0)
        job_count = int(db.scalar(select(func.count()).select_from(ProvisioningJob)) or 0)
        audit_count = int(
            db.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(AuditEvent.aggregate_type == "request")
            )
            or 0
        )
        approval_count = int(db.scalar(select(func.count()).select_from(ApprovalRequest)) or 0)
        db.execute(delete(ApprovalDecision))
        db.execute(delete(ProvisioningJob))
        db.execute(delete(AuditEvent).where(AuditEvent.aggregate_type == "request"))
        db.execute(delete(ApprovalRequest))
        db.commit()
        deleted.update(
            {
                "approval_decisions": decision_count,
                "provisioning_jobs": job_count,
                "request_audit_events": audit_count,
                "approval_requests": approval_count,
            }
        )
        return DemoResetResult(deleted=deleted)

    @app.post("/admin-api/v1/demo/seed", response_model=DemoSeedResult)
    def seed_demo_data(
        _: Annotated[Principal, Depends(approver_principal)],
    ) -> DemoSeedResult:
        if app_settings.auth_mode != "dev" or not app_settings.enable_demo_reset:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "demo seed is not available")
        try:
            return DemoSeedResult(**seed_demo_request(app_settings))
        except RuntimeError as exc:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY, "demo seed downstream failed"
            ) from exc

    return app


app = create_app()
