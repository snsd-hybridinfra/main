"""Frontend facade over the approved request authority; no infrastructure executor."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

import httpx
from fastapi import Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.convertors import Convertor, register_url_convertor
from sqlalchemy import DateTime, Integer, String, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from .auth import Principal, current_principal
from .blueprints import BlueprintResolutionError, public_blueprints, resolve_blueprint
from .db import Base, get_db
from .models import AccessRequest, ResourceProjection
from .monitoring_assistant import (
    MonitoringAssistRequest,
    MonitoringAssistantError,
    local_advisory,
    openai_advisory,
)
from .schemas import BlueprintResolveRequest
from .service_auth import authorization_headers


class DomainConvertor(Convertor):
    regex = "developer|manufacturing|finance|public"

    def convert(self, value):
        return value

    def to_string(self, value):
        return value


register_url_convertor("portal_domain", DomainConvertor())


class DecisionConvertor(DomainConvertor):
    regex = "approve|reject"


register_url_convertor("portal_decision", DecisionConvertor())


class PortalUsage(Base):
    __tablename__ = "portal_usage"
    usage_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    owner_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    input_units: Mapped[int] = mapped_column(Integer, nullable=False)
    output_units: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PortalRequestCreate(BlueprintResolveRequest):
    project: str = Field(pattern=r"^[a-z][a-z0-9-]{2,39}$")


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=5, max_length=500, pattern=r"^[^\x00-\x1f\x7f]+$")


class Chat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: Literal["local-simulator"]
    prompt: str = Field(min_length=1, max_length=2000)


class WorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    size: Literal["Small", "SMALL"] = "SMALL"


CUSTOMERS = {"CUSTOMER_USER", "CUSTOMER_MANAGER"}
OPERATORS = {"MSP_OPERATOR", "MSP_ADMIN"}
MODEL_MESSAGE = "Local simulator: the request was handled locally. No external model was invoked."
RATES = {"SMALL": 70000, "STANDARD": 120000, "LARGE": 220000}


def access(principal: Principal, roles: set[str], scope: str) -> Principal:
    if not principal.tenant_id or len(principal.tenant_id) > 128:
        raise HTTPException(403, "tenant identity is required")
    if not principal.roles.intersection(roles) or scope not in principal.scopes:
        raise HTTPException(403, "required role or scope is missing")
    return principal


def _context(item: AccessRequest) -> dict:
    return {k: v for k, v in item.parameters.items() if k.startswith("_portal_")}


def _request_view(item: AccessRequest) -> dict:
    return {
        "id": item.request_id, "request_id": item.request_id,
        "tenant_id": item.parameters.get("_portal_tenant"), "requested_by": item.owner_id,
        "domain": item.parameters.get("_portal_domain"),
        "project": item.parameters.get("_portal_project"),
        "blueprint_id": item.parameters.get("_blueprint_id"),
        "environment": item.parameters.get("_blueprint_environment"),
        "size": item.parameters.get("_blueprint_size"), "duration_hours": item.duration_hours,
        "purpose": item.purpose, "status": item.status,
        "delivery_status": item.delivery_status, "retry_count": item.retry_count,
        "resource_id": item.resource_id, "resource_status": item.resource_status,
        "grant_id": item.grant_id, "grant_expires_at": item.grant_expires_at,
        "manifest_digest": item.parameters.get("_manifest_digest"),
        "rejection_reason": item.rejection_reason,
        "created_at": item.created_at, "updated_at": item.updated_at,
        "estimated_monthly_krw": RATES.get(item.parameters.get("_blueprint_size"), 0),
        "cost_source": "LOCAL_ESTIMATE", "runtime_evidence": "NOT_VALIDATED",
    }


def install_portal_routes(app, submit_request, cancel_request) -> None:
    @app.get("/api/portal/runtime")
    def runtime():
        return {"demoAuth": app.state.settings.auth_mode == "dev", "mockDomains": [], "apiBase": "/api"}

    @app.get("/api/portal/me")
    @app.get("/auth/session")
    def me(principal: Principal = Depends(current_principal)):
        if not principal.tenant_id:
            raise HTTPException(403, "tenant identity is required")
        return {"userId": principal.subject, "tenantId": principal.tenant_id,
                "tenantName": principal.tenant_id, "roles": sorted(principal.roles), "scopes": sorted(principal.scopes)}

    @app.get("/api/portal/team")
    def team(principal: Principal = Depends(current_principal)):
        access(principal, {"CUSTOMER_MANAGER"}, "team:read")
        return {"items": [], "source": "NOT_CONNECTED",
                "message": "Identity directory is not connected. Membership and roles cannot be inferred from request records."}

    @app.get("/api/admin/users")
    def users(principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        access(principal, {"MSP_ADMIN"}, "admin:write")
        rows = items(db, principal, all_tenants=True)
        return {"items": [{"user_id": owner, "tenant_id": tenant, "source": "OBSERVED_REQUESTER"}
                          for tenant, owner in sorted({(r.parameters["_portal_tenant"], r.owner_id) for r in rows})],
                "directory_connected": False, "role_management": "NOT_CONNECTED"}

    def domain_access(domain: str, principal: Principal, *, write=False):
        if domain not in {"developer", "manufacturing", "finance", "public"}:
            raise HTTPException(404, "domain not found")
        if f"{domain}:read" not in principal.scopes:
            raise HTTPException(403, "industry or developer scope is missing")
        if not write and domain in {"finance", "public"} and principal.roles.intersection(OPERATORS):
            return access(principal, OPERATORS, "admin:read")
        return access(principal, CUSTOMERS, "cloud:request" if write else "cloud:read")

    def items(db: Session, principal: Principal, domain: str | None = None, *, all_tenants=False):
        stmt = select(AccessRequest).where(AccessRequest.parameters["_portal_tenant"].as_string().is_not(None))
        if not all_tenants:
            stmt = stmt.where(AccessRequest.parameters["_portal_tenant"].as_string() == principal.tenant_id)
            if "CUSTOMER_MANAGER" not in principal.roles or "team:read" not in principal.scopes:
                stmt = stmt.where(AccessRequest.owner_id == principal.subject)
        if domain:
            stmt = stmt.where(AccessRequest.parameters["_portal_domain"].as_string() == domain)
        return list(db.scalars(stmt.order_by(AccessRequest.created_at.desc())))

    def owned(db: Session, principal: Principal, domain: str, request_id: str):
        item = db.get(AccessRequest, request_id)
        if (not item or item.owner_id != principal.subject
                or item.parameters.get("_portal_tenant") != principal.tenant_id
                or item.parameters.get("_portal_domain") != domain):
            raise HTTPException(404, "request not found")
        return item

    def approval_call(request: Request, principal: Principal, method: str, path: str, payload=None, *, service=False):
        settings = app.state.settings
        if not settings.approval_api_url:
            raise HTTPException(503, "Approval API is not connected")
        if service:
            headers = authorization_headers(settings, "approval-api")
        elif settings.auth_mode == "dev":
            headers = {"X-Dev-User": principal.subject, "X-Dev-Roles": "approver,auditor",
                       "X-Dev-Scopes": " ".join(principal.scopes)}
        else:
            # The downstream audience must accept this token; do not elevate with a service token.
            headers = {"Authorization": request.headers.get("Authorization", "")}
        try:
            adapter = getattr(app.state, "portal_approval_transport", None)
            with httpx.Client(transport=adapter, timeout=settings.callback_timeout_seconds) as client:
                response = client.request(method, settings.approval_api_url + path, headers=headers, json=payload)
            if response.status_code >= 400:
                if response.status_code in {401, 403, 404, 409, 422}:
                    raise HTTPException(response.status_code, "Approval API denied the operation")
                raise HTTPException(503, "Approval API is unavailable")
            return response.json()
        except (httpx.HTTPError, ValueError, OSError) as exc:
            raise HTTPException(503, "Approval API is unavailable") from exc

    def catalog_items():
        result = []
        for product in public_blueprints():
            resolution = resolve_blueprint(blueprint_id=product["blueprint_id"],
                environment=product["allowed_environments"][0], size=product["allowed_sizes"][0],
                duration_hours=product["allowed_duration_hours"][0], purpose="local catalog readiness")
            result.append({**product, "resolution_status": resolution["resolution_status"],
                "requestable": resolution["resolution_status"] == "RESOLVED_LOCAL",
                "runtime_authorized": False, "runtime_evidence": "NOT_VALIDATED"})
        return result

    def catalog():
        try:
            return catalog_items()
        except BlueprintResolutionError as exc:
            raise HTTPException(503, "catalog authority unavailable") from exc

    @app.get("/api/{domain:portal_domain}/catalog")
    def domain_catalog(domain: str, principal: Principal = Depends(current_principal)):
        domain_access(domain, principal)
        try:
            return {"items": catalog()}
        except BlueprintResolutionError as exc:
            raise HTTPException(503, "catalog authority unavailable") from exc

    @app.get("/api/{domain:portal_domain}/workspace")
    def workspace(domain: str, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        domain_access(domain, principal)
        rows = items(db, principal, domain)
        resources = []
        if rows:
            for resource in db.scalars(select(ResourceProjection).where(ResourceProjection.request_id.in_([r.request_id for r in rows]))):
                owner = next(r for r in rows if r.request_id == resource.request_id)
                resources.append({"id": resource.resource_id, "request_id": resource.request_id,
                    "project": owner.parameters["_portal_project"], "name": resource.display_name,
                    "status": resource.status, "updated_at": resource.updated_at,
                    "access": "GRANT_REQUIRED", "runtime_evidence": "NOT_VALIDATED"})
        return {"tenant_id": principal.tenant_id, "domain": domain, "catalog": catalog(),
                "requests": [_request_view(r) for r in rows], "resources": resources,
                "monitoring": {"source": "NOT_CONNECTED", "cpu_percent": None, "memory_percent": None,
                               "alerts": None, "runtime_evidence": "NOT_VALIDATED"},
                "finops": {"source": "LOCAL_ESTIMATE", "actual_krw": None,
                    "estimated_monthly_krw": sum(RATES.get(r.parameters.get("_blueprint_size"), 0) for r in rows
                        if r.status not in {"REJECTED", "CANCELLED", "TERMINATED", "REVOKED", "EXPIRED"}),
                    "rates_krw": RATES, "currency": "KRW", "billing_connected": False}}

    @app.get("/api/{domain:portal_domain}/requests")
    def requests(domain: str, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        domain_access(domain, principal)
        return {"items": [_request_view(r) for r in items(db, principal, domain)]}

    @app.get("/api/{domain:portal_domain}/requests/{request_id}")
    def request_detail(domain: str, request_id: str, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        domain_access(domain, principal)
        row = next((r for r in items(db, principal, domain) if r.request_id == request_id), None)
        if not row:
            raise HTTPException(404, "request not found")
        return _request_view(row)

    @app.get("/api/{domain:portal_domain}/resources")
    def resources(domain: str, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        return {"items": workspace(domain, principal, db)["resources"]}

    @app.get("/api/{domain:portal_domain}/monitoring")
    def monitoring(domain: str, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        return workspace(domain, principal, db)["monitoring"]

    @app.get("/api/{domain:portal_domain}/finops")
    def finops(domain: str, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        return workspace(domain, principal, db)["finops"]

    @app.post("/api/{domain:portal_domain}/requests", status_code=201)
    def create(domain: str, payload: PortalRequestCreate, principal: Principal = Depends(current_principal),
               db: Session = Depends(get_db), idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128)):
        domain_access(domain, principal, write=True)
        context = {"_portal_tenant": principal.tenant_id, "_portal_domain": domain, "_portal_project": payload.project}
        key = hashlib.sha256(json.dumps([principal.tenant_id, principal.subject, domain, idempotency_key]).encode()).hexdigest()
        blueprint = BlueprintResolveRequest(**payload.model_dump(exclude={"project"}))
        created = submit_request(blueprint, principal, db, key, context)
        return _request_view(db.get(AccessRequest, created["request_id"]))

    @app.post("/api/{domain:portal_domain}/requests/{request_id}/cancel")
    def cancel(domain: str, request_id: str, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        domain_access(domain, principal, write=True)
        owned(db, principal, domain, request_id)
        return _request_view(cancel_request(request_id, principal, db))

    @app.post("/api/{domain:portal_domain}/requests/{request_id}/redeliver")
    def redeliver(domain: str, request_id: str, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        domain_access(domain, principal, write=True)
        item = owned(db, principal, domain, request_id)
        if item.delivery_status != "FAILED":
            raise HTTPException(409, "only failed deliveries can be retried")
        from .clients import send_to_approval
        item.delivery_status, item.last_error = send_to_approval(app.state.settings, item)
        item.retry_count += 1
        db.commit()
        return _request_view(item)

    @app.post("/api/{domain:portal_domain}/requests/{request_id}/destroy", status_code=202)
    def destroy(domain: str, request_id: str, payload: Decision, request: Request,
                principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        domain_access(domain, principal, write=True)
        item = owned(db, principal, domain, request_id)
        if item.resource_status != "RUNNING":
            raise HTTPException(409, "only a RUNNING resource can be destroyed")
        settings = app.state.settings
        if not item.grant_id or not settings.grant_api_url:
            raise HTTPException(503, "grant revocation must be connected before resource recovery")
        try:
            adapter = getattr(app.state, "portal_grant_transport", None)
            with httpx.Client(transport=adapter, timeout=settings.callback_timeout_seconds) as client:
                response = client.post(settings.grant_api_url + f"/internal/v1/grants/{item.grant_id}/revoke",
                    headers=authorization_headers(settings, "grant-api"),
                    json={"request_id": item.request_id, "owner_id": item.owner_id, "reason": payload.reason})
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError, OSError) as exc:
            raise HTTPException(503, "grant revocation or recovery delivery is unavailable") from exc
        if result.get("callback_status") != "DELIVERED" or result.get("deprovision_status") != "QUEUED":
            raise HTTPException(503, "grant revoked; callback or recovery delivery requires retry")
        return {"request_id": request_id, "status": "RECOVERY_REQUESTED", "operation": "DESTROY"}

    @app.get("/api/admin/workspace")
    def admin_workspace(request: Request, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        access(principal, OPERATORS, "admin:read")
        rows = items(db, principal, all_tenants=True)
        request_rows = [_request_view(r) for r in rows]
        ids = {r.request_id for r in rows}
        try:
            queue = approval_call(request, principal, "GET", "/admin-api/v1/requests?status=ALL")
            jobs = approval_call(request, principal, "GET", "/admin-api/v1/provisioning/jobs?status=ALL")
            queue_map = {r["request_id"]: r for r in queue}
            for row in request_rows:
                if row["request_id"] in queue_map:
                    row["approval_status"] = queue_map[row["request_id"]]["status"]
            job_rows = [{k: j.get(k) for k in ("job_id", "request_id", "operation", "status", "attempts", "runner_id", "updated_at")}
                        for j in jobs if j["request_id"] in ids]
            connection = "CONNECTED"
        except HTTPException as exc:
            if exc.status_code != 503:
                raise
            job_rows, connection = [], "NOT_CONNECTED"
        tenants = []
        if "MSP_ADMIN" in principal.roles:
            for tenant in sorted({r.parameters["_portal_tenant"] for r in rows}):
                own = [r for r in rows if r.parameters["_portal_tenant"] == tenant]
                tenants.append({"id": tenant, "requests": len(own),
                    "environments": sum(r.resource_status == "RUNNING" for r in own),
                    "estimated_monthly_krw": sum(RATES.get(r.parameters.get("_blueprint_size"), 0) for r in own
                        if r.status not in {"REJECTED", "CANCELLED", "TERMINATED", "REVOKED", "EXPIRED"})})
        return {"requests": request_rows, "jobs": job_rows, "tenants": tenants,
                "approval_connection": connection, "monitoring": {"source": "NOT_CONNECTED"},
                "cost_source": "LOCAL_ESTIMATE", "runtime_evidence": "NOT_VALIDATED"}

    @app.post("/api/admin/requests/{request_id}/{action}")
    def decide(request_id: str, action: Literal["approve", "reject"], payload: Decision, request: Request,
               principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        access(principal, OPERATORS, "approval:manage")
        item = db.get(AccessRequest, request_id)
        if not item or not _context(item):
            raise HTTPException(404, "portal request not found")
        if item.owner_id == principal.subject:
            raise HTTPException(403, "self approval is forbidden")
        result = approval_call(request, principal, "POST", f"/admin-api/v1/requests/{request_id}/{action}", payload.model_dump())
        return {"request_id": request_id, "decision": action.upper(),
                "callback_status": result.get("callback_status"), "grant_status": result.get("grant_status")}

    @app.post("/api/admin/jobs/{job_id}/retry")
    def retry(job_id: str, request: Request, principal: Principal = Depends(current_principal)):
        access(principal, OPERATORS, "approval:manage")
        result = approval_call(request, principal, "POST", f"/admin-api/v1/provisioning/jobs/{job_id}/retry", {})
        return {k: result.get(k) for k in ("job_id", "request_id", "status", "operation")}

    @app.post("/api/admin/requests/{request_id}/retry-sync")
    def retry_sync(request_id: str, request: Request, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        access(principal, OPERATORS, "approval:manage")
        item = db.get(AccessRequest, request_id)
        if not item or not _context(item):
            raise HTTPException(404, "portal request not found")
        result = approval_call(request, principal, "POST", f"/admin-api/v1/requests/{request_id}/retry-sync", {})
        return {"request_id": request_id, "callback_status": result.get("callback_status"), "grant_status": result.get("grant_status")}

    @app.get("/api/admin/audit")
    def audit(request: Request, principal: Principal = Depends(current_principal)):
        access(principal, {"MSP_ADMIN"}, "audit:read")
        result = approval_call(request, principal, "GET", "/admin-api/v1/audit-events")
        return {"items": [{k: r.get(k) for k in ("audit_id", "event_type", "aggregate_id", "actor_id", "created_at")} for r in result],
                "source": "APPROVAL_DATABASE"}

    @app.get("/api/admin/grants")
    def grants(request: Request, principal: Principal = Depends(current_principal)):
        access(principal, {"MSP_ADMIN"}, "admin:write")
        settings = app.state.settings
        if not settings.grant_api_url:
            raise HTTPException(503, "Grant API is not connected")
        headers = ({"X-Dev-User": principal.subject, "X-Dev-Roles": "grant-admin,auditor",
                    "X-Dev-Scopes": "grant:manage audit:read"} if settings.auth_mode == "dev"
                   else {"Authorization": request.headers.get("Authorization", "")})
        try:
            with httpx.Client(transport=getattr(app.state, "portal_grant_transport", None), timeout=settings.callback_timeout_seconds) as client:
                response = client.get(settings.grant_api_url + "/admin-api/v1/grants?status=ALL", headers=headers)
            response.raise_for_status()
            return {"items": [{k: r.get(k) for k in ("grant_id", "request_id", "subject_id", "status", "expires_at", "created_at")}
                              for r in response.json()], "source": "GRANT_DATABASE"}
        except (httpx.HTTPError, ValueError, OSError) as exc:
            raise HTTPException(503, "Grant API is unavailable or denied the read") from exc

    @app.get("/api/llm/models")
    def models(principal: Principal = Depends(current_principal)):
        access(principal, CUSTOMERS | {"LLM_USER", "MSP_ADMIN"}, "llm:invoke")
        enabled = app.state.settings.auth_mode == "dev" and app.state.settings.enable_local_llm_simulator
        return {"items": [{"id": "local-simulator", "name": "Local simulator", "status": "SIMULATED" if enabled else "NOT_CONNECTED"}],
                "provider_connected": False}

    @app.post("/api/llm/chat")
    def chat(payload: Chat, principal: Principal = Depends(current_principal), db: Session = Depends(get_db),
             idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128)):
        access(principal, CUSTOMERS | {"LLM_USER", "MSP_ADMIN"}, "llm:invoke")
        if app.state.settings.auth_mode != "dev" or not app.state.settings.enable_local_llm_simulator:
            raise HTTPException(503, "model provider is not connected; local simulator is disabled")
        # Store numeric character-based simulation units only, never prompt, prompt hash, or output text.
        key = hashlib.sha256(json.dumps([principal.tenant_id, principal.subject, idempotency_key]).encode()).hexdigest()
        existing = db.scalar(select(PortalUsage).where(PortalUsage.idempotency_key == key))
        if existing is None:
            usage = PortalUsage(usage_id=str(uuid4()), idempotency_key=key, tenant_id=principal.tenant_id,
                owner_id=principal.subject, model=payload.model, input_units=len(payload.prompt),
                output_units=len(MODEL_MESSAGE), created_at=datetime.now(timezone.utc))
            db.add(usage)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
        return {"model": payload.model, "message": MODEL_MESSAGE, "source": "LOCAL_SIMULATOR", "provider_connected": False}

    @app.get("/api/llm/usage")
    @app.get("/api/llm/cost")
    def usage(principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
        access(principal, CUSTOMERS | {"LLM_USER", "MSP_ADMIN"}, "llm:usage:read")
        rows = list(db.scalars(select(PortalUsage).where(PortalUsage.tenant_id == principal.tenant_id,
            PortalUsage.owner_id == principal.subject).order_by(PortalUsage.created_at.desc())))
        return {"items": [{"id": r.usage_id, "model": r.model, "input_units": r.input_units,
                           "output_units": r.output_units, "created_at": r.created_at} for r in rows],
                "requests": len(rows), "simulation_units": sum(r.input_units + r.output_units for r in rows),
                "tokens": None, "amount_krw": None, "source": "LOCAL_SIMULATOR",
                "provider_connected": False, "billing_connected": False}

    @app.post("/api/llm/workspace-requests")
    def llm_workspace(payload: WorkspaceRequest, principal: Principal = Depends(current_principal)):
        access(principal, CUSTOMERS | {"LLM_USER", "MSP_ADMIN"}, "llm:invoke")
        # User entitlement is not provisioning authority; this product remains gated.
        raise HTTPException(409, "DEVELOPER_WORKSPACE adapter is not implemented; no workspace was provisioned")

    def monitoring_assistant_access(principal: Principal) -> Principal:
        roles = {"LLM_USER", "MSP_OPERATOR", "MSP_ADMIN"}
        access(principal, roles, "llm:invoke")
        return access(principal, roles, "monitoring:assist")

    @app.get("/api/llm/monitoring-assistant")
    def monitoring_assistant_status(principal: Principal = Depends(current_principal)):
        monitoring_assistant_access(principal)
        settings = app.state.settings
        local_enabled = settings.auth_mode == "dev" and settings.monitoring_assistant_provider == "local"
        external_configured = (
            settings.monitoring_assistant_provider == "openai"
            and bool(settings.monitoring_assistant_model)
            and bool(settings.monitoring_assistant_token_file)
        )
        return {
            "status": "LOCAL_SIMULATED" if local_enabled else "CONFIGURED" if external_configured else "NOT_CONNECTED",
            "provider_connected": False,
            "authoritative": False,
            "accepted_inputs": "SANITIZED_NUMERIC_SIGNALS_ONLY",
            "runtime_evidence": "NOT_VALIDATED",
        }

    @app.post("/api/llm/monitoring-assistant/analyze")
    def analyze_monitoring(
        payload: MonitoringAssistRequest,
        principal: Principal = Depends(current_principal),
        db: Session = Depends(get_db),
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    ):
        monitoring_assistant_access(principal)
        settings = app.state.settings
        key = hashlib.sha256(
            json.dumps(["monitoring-assistant", principal.tenant_id, principal.subject, idempotency_key]).encode()
        ).hexdigest()
        if db.scalar(select(PortalUsage).where(PortalUsage.idempotency_key == key)) is not None:
            raise HTTPException(409, "monitoring advisory request was already completed")
        try:
            if settings.auth_mode == "dev" and settings.monitoring_assistant_provider == "local":
                result = local_advisory(payload)
            elif settings.monitoring_assistant_provider == "openai":
                result = openai_advisory(
                    payload,
                    model=settings.monitoring_assistant_model,
                    token_file=settings.monitoring_assistant_token_file,
                    timeout_seconds=settings.monitoring_assistant_timeout_seconds,
                    transport=getattr(app.state, "monitoring_assistant_transport", None),
                )
            else:
                raise MonitoringAssistantError("monitoring assistant provider is not connected")
        except MonitoringAssistantError as exc:
            raise HTTPException(503, str(exc)) from exc
        usage = PortalUsage(
            usage_id=str(uuid4()), idempotency_key=key, tenant_id=principal.tenant_id,
            owner_id=principal.subject, model=result.model, input_units=result.input_units,
            output_units=result.output_units, created_at=datetime.now(timezone.utc),
        )
        db.add(usage)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(409, "monitoring advisory request was already completed") from exc
        return {
            "advisory": result.text,
            "source": result.source,
            "model": result.model,
            "provider_connected": result.provider_connected,
            "authoritative": False,
            "action_authorized": False,
            "human_review_required": True,
            "runtime_evidence": "NOT_VALIDATED",
        }
