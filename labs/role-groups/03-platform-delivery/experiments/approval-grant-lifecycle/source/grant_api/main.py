from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from .auth import Principal, require_roles
from .clients import request_destroy, send_request_status
from .config import Settings
from .db import Base, get_db, make_engine, make_session_factory
from .models import AuditEvent, Grant
from .schemas import (
    BoundGrantRevoke,
    DemoResetResult,
    GrantActionResult,
    GrantCreate,
    GrantIssued,
    GrantValidation,
    GrantView,
    HealthView,
    ProtectedResource,
)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings.from_env()
    engine = make_engine(app_settings.database_url)
    session_factory = make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if app_settings.auto_create_schema:
            Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(title="grant-api", version="0.1.0", lifespan=lifespan)
    app.state.settings = app_settings
    app.state.session_factory = session_factory

    service_principal = require_roles("service", scopes=("service:callback",))
    grant_admin_principal = require_roles("grant-admin", scopes=("grant:manage",))
    audit_principal = require_roles("grant-admin", "auditor", scopes=("audit:read",))

    key_cache: dict[str, str] = {}

    def _read_key(path: str, cache_name: str) -> str:
        if cache_name not in key_cache:
            try:
                key_cache[cache_name] = Path(path).read_text(encoding="utf-8")
            except (OSError, ValueError) as exc:
                raise HTTPException(
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                    "grant signing key is not available",
                ) from exc
        return key_cache[cache_name]

    def signing_keys() -> tuple[str, str, str]:
        algorithm = app_settings.grant_signing_algorithm.upper()
        if algorithm == "HS256":
            if app_settings.auth_mode != "dev" or len(app_settings.grant_signing_key) < 32:
                raise HTTPException(
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                    "HS256 is allowed only in dev mode with a 32-byte minimum key",
                )
            return app_settings.grant_signing_key, app_settings.grant_signing_key, algorithm
        if algorithm not in {"RS256", "ES256"}:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "unsupported grant algorithm")
        if not app_settings.grant_signing_private_key_file or not app_settings.grant_signing_public_key_file:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "asymmetric grant signing keys are not configured",
            )
        return (
            _read_key(app_settings.grant_signing_private_key_file, "private"),
            _read_key(app_settings.grant_signing_public_key_file, "public"),
            algorithm,
        )

    def issue_token(grant: Grant) -> str:
        private_key, _, algorithm = signing_keys()
        claims: dict[str, Any] = {
            "iss": app_settings.grant_issuer,
            "aud": app_settings.grant_audience,
            "sub": grant.subject_id,
            "jti": grant.grant_id,
            "request_id": grant.request_id,
            "scope": " ".join(grant.scopes),
            "grant_version": grant.event_version,
            "iat": _aware(grant.issued_at),
            "nbf": _aware(grant.issued_at),
            "exp": _aware(grant.expires_at),
        }
        return jwt.encode(claims, private_key, algorithm=algorithm, headers={"typ": "JWT"})

    def validate_token(token: str, db: Session) -> tuple[Grant, dict[str, Any]]:
        _, public_key, algorithm = signing_keys()
        try:
            claims = jwt.decode(
                token,
                public_key,
                algorithms=[algorithm],
                audience=app_settings.grant_audience,
                issuer=app_settings.grant_issuer,
                options={"require": ["exp", "iat", "sub", "jti", "request_id"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "invalid grant token") from exc
        grant = db.get(Grant, str(claims["jti"]))
        if not grant or grant.request_id != str(claims["request_id"]):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "grant does not exist")
        if grant.status != "ACTIVE":
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"grant is {grant.status}")
        if _aware(grant.expires_at) <= datetime.now(timezone.utc):
            grant.status = "EXPIRED"
            grant.event_version += 1
            db.add(
                AuditEvent(
                    audit_id=str(uuid4()),
                    event_type="GRANT_EXPIRED",
                    aggregate_type="grant",
                    aggregate_id=grant.grant_id,
                    actor_id="grant-api-expiry-check",
                    details={"request_id": grant.request_id, "event_version": grant.event_version},
                )
            )
            db.commit()
            db.refresh(grant)
            callback_status, callback_error = send_request_status(app_settings, grant)
            _, deprovision_error = request_destroy(
                app_settings, grant, reason="grant expired during token validation"
            )
            grant.callback_status = callback_status
            errors = [value for value in (callback_error, deprovision_error) if value]
            grant.last_error = " | ".join(errors) or None
            if errors:
                grant.retry_count += 1
            db.commit()
            raise HTTPException(status.HTTP_403_FORBIDDEN, "grant is EXPIRED")
        return grant, claims

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
            'iaas_service_up{service="grant-api"} 1\n',
            media_type="text/plain; version=0.0.4",
        )

    @app.post("/internal/v1/grants", response_model=GrantIssued, status_code=status.HTTP_201_CREATED)
    def create_grant(
        payload: GrantCreate,
        principal: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> GrantIssued:
        existing = db.scalar(select(Grant).where(Grant.idempotency_key == payload.idempotency_key))
        if existing:
            if existing.callback_status == "FAILED":
                callback_status, error = send_request_status(app_settings, existing)
                existing.callback_status = callback_status
                existing.last_error = error
                if error:
                    existing.retry_count += 1
                db.commit()
                db.refresh(existing)
            return GrantIssued(
                **{
                    "grant": GrantView.model_validate(existing),
                    "token": issue_token(existing),
                    "callback_status": existing.callback_status,
                }
            )
        by_request = db.scalar(select(Grant).where(Grant.request_id == payload.request_id))
        if by_request:
            raise HTTPException(status.HTTP_409_CONFLICT, "request already has a grant")
        now = datetime.now(timezone.utc)
        grant = Grant(
            grant_id=str(uuid4()),
            request_id=payload.request_id,
            idempotency_key=payload.idempotency_key,
            subject_id=payload.subject_id,
            scopes=sorted(set(payload.scopes)),
            status="ACTIVE",
            issued_at=now,
            expires_at=now + timedelta(hours=payload.duration_hours),
            event_version=payload.event_version,
            retry_count=payload.retry_count,
        )
        db.add(grant)
        db.add(
            AuditEvent(
                audit_id=str(uuid4()),
                event_type="GRANT_ISSUED",
                aggregate_type="grant",
                aggregate_id=grant.grant_id,
                actor_id=principal.subject,
                details={
                    "request_id": grant.request_id,
                    "event_version": grant.event_version,
                    "scopes": grant.scopes,
                },
            )
        )
        db.commit()
        db.refresh(grant)
        callback_status, error = send_request_status(app_settings, grant)
        grant.callback_status = callback_status
        grant.last_error = error
        if error:
            grant.retry_count += 1
        db.commit()
        db.refresh(grant)
        return GrantIssued(
            **{
                "grant": GrantView.model_validate(grant),
                "token": issue_token(grant),
                "callback_status": callback_status,
            }
        )

    @app.get("/admin-api/v1/grants", response_model=list[GrantView])
    def list_grants(
        _: Annotated[Principal, Depends(grant_admin_principal)],
        db: Annotated[Session, Depends(get_db)],
        grant_status: Annotated[str, Query(alias="status")] = "ACTIVE",
    ) -> list[Grant]:
        stmt = select(Grant)
        if grant_status.upper() != "ALL":
            stmt = stmt.where(Grant.status == grant_status.upper())
        return list(db.scalars(stmt.order_by(Grant.issued_at.desc())))

    @app.get("/admin-api/v1/grants/{grant_id}", response_model=GrantView)
    def get_grant(
        grant_id: str,
        _: Annotated[Principal, Depends(grant_admin_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> Grant:
        grant = db.get(Grant, grant_id)
        if not grant:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "grant not found")
        return grant

    @app.post("/admin-api/v1/grants/{grant_id}/revoke", response_model=GrantActionResult)
    def revoke_grant(
        grant_id: str,
        principal: Annotated[Principal, Depends(grant_admin_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> GrantActionResult:
        grant = db.get(Grant, grant_id)
        if not grant:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "grant not found")
        if grant.status == "REVOKED":
            return GrantActionResult(grant=GrantView.model_validate(grant), callback_status=grant.callback_status)
        if grant.status != "ACTIVE":
            raise HTTPException(status.HTTP_409_CONFLICT, f"grant is {grant.status}")
        grant.status = "REVOKED"
        grant.revoked_at = datetime.now(timezone.utc)
        grant.event_version += 1
        db.add(
            AuditEvent(
                audit_id=str(uuid4()),
                event_type="GRANT_REVOKED",
                aggregate_type="grant",
                aggregate_id=grant.grant_id,
                actor_id=principal.subject,
                details={"request_id": grant.request_id, "event_version": grant.event_version},
            )
        )
        db.commit()
        db.refresh(grant)
        callback_status, error = send_request_status(app_settings, grant)
        deprovision_status, deprovision_error = request_destroy(
            app_settings, grant, reason="grant revoked"
        )
        grant.callback_status = callback_status
        errors = [value for value in (error, deprovision_error) if value]
        grant.last_error = " | ".join(errors) or None
        if errors:
            grant.retry_count += 1
        db.commit()
        db.refresh(grant)
        return GrantActionResult(
            grant=GrantView.model_validate(grant),
            callback_status=callback_status,
            deprovision_status=deprovision_status,
        )

    @app.post("/internal/v1/grants/{grant_id}/revoke")
    def revoke_bound_grant(
        grant_id: str, payload: BoundGrantRevoke,
        principal: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> dict:
        grant = db.get(Grant, grant_id)
        if not grant or grant.request_id != payload.request_id or grant.subject_id != payload.owner_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "bound grant not found")
        if grant.status == "REVOKED":
            callback_status, error = send_request_status(app_settings, grant)
            deprovision_status, destroy_error = request_destroy(app_settings, grant, reason=payload.reason)
            grant.callback_status = callback_status
            grant.last_error = " | ".join(v for v in (error, destroy_error) if v) or None
            grant.retry_count += int(bool(grant.last_error))
            db.commit()
            return {"grant_id": grant_id, "callback_status": callback_status, "deprovision_status": deprovision_status}
        result = revoke_grant(grant_id, principal, db)
        return {"grant_id": grant_id, "callback_status": result.callback_status, "deprovision_status": result.deprovision_status}

    @app.post("/admin-api/v1/grants/{grant_id}/expire-now", response_model=GrantActionResult)
    def expire_grant_now(
        grant_id: str,
        principal: Annotated[Principal, Depends(grant_admin_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> GrantActionResult:
        if app_settings.auth_mode != "dev" or not app_settings.enable_demo_reset:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "demo expiry is not available")
        grant = db.get(Grant, grant_id)
        if not grant:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "grant not found")
        if grant.status == "EXPIRED":
            return GrantActionResult(
                grant=GrantView.model_validate(grant), callback_status=grant.callback_status
            )
        if grant.status != "ACTIVE":
            raise HTTPException(status.HTTP_409_CONFLICT, f"grant is {grant.status}")

        grant.status = "EXPIRED"
        grant.expires_at = datetime.now(timezone.utc)
        grant.event_version += 1
        db.add(
            AuditEvent(
                audit_id=str(uuid4()),
                event_type="GRANT_EXPIRED",
                aggregate_type="grant",
                aggregate_id=grant.grant_id,
                actor_id=principal.subject,
                details={
                    "request_id": grant.request_id,
                    "event_version": grant.event_version,
                    "demo_trigger": "expire-now",
                },
            )
        )
        db.commit()
        db.refresh(grant)
        callback_status, error = send_request_status(app_settings, grant)
        deprovision_status, deprovision_error = request_destroy(
            app_settings, grant, reason="grant expired"
        )
        grant.callback_status = callback_status
        errors = [value for value in (error, deprovision_error) if value]
        grant.last_error = " | ".join(errors) or None
        if errors:
            grant.retry_count += 1
        db.commit()
        db.refresh(grant)
        return GrantActionResult(
            grant=GrantView.model_validate(grant),
            callback_status=callback_status,
            deprovision_status=deprovision_status,
        )

    @app.post("/internal/v1/grants/expire", response_model=list[GrantActionResult])
    def expire_grants(
        principal: Annotated[
            Principal,
            Depends(require_roles("service", "grant-admin", scopes=("grant:write",))),
        ],
        db: Annotated[Session, Depends(get_db)],
    ) -> list[GrantActionResult]:
        now = datetime.now(timezone.utc)
        due = list(db.scalars(select(Grant).where(Grant.status == "ACTIVE", Grant.expires_at <= now)))
        results: list[GrantActionResult] = []
        for grant in due:
            grant.status = "EXPIRED"
            grant.event_version += 1
            db.add(
                AuditEvent(
                    audit_id=str(uuid4()),
                    event_type="GRANT_EXPIRED",
                    aggregate_type="grant",
                    aggregate_id=grant.grant_id,
                    actor_id=principal.subject,
                    details={"request_id": grant.request_id, "event_version": grant.event_version},
                )
            )
            db.commit()
            db.refresh(grant)
            callback_status, error = send_request_status(app_settings, grant)
            deprovision_status, deprovision_error = request_destroy(
                app_settings, grant, reason="grant expired"
            )
            grant.callback_status = callback_status
            errors = [value for value in (error, deprovision_error) if value]
            grant.last_error = " | ".join(errors) or None
            if errors:
                grant.retry_count += 1
            db.commit()
            db.refresh(grant)
            results.append(
                GrantActionResult(
                    grant=GrantView.model_validate(grant),
                    callback_status=callback_status,
                    deprovision_status=deprovision_status,
                )
            )
        return results

    @app.post("/api/v1/grants/validate", response_model=GrantValidation)
    def validate_grant(
        db: Annotated[Session, Depends(get_db)],
        authorization: Annotated[str | None, Header()] = None,
    ) -> GrantValidation:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Grant bearer token is required")
        grant, _ = validate_token(authorization.split(" ", 1)[1], db)
        return GrantValidation(
            active=True,
            grant_id=grant.grant_id,
            request_id=grant.request_id,
            subject_id=grant.subject_id,
            scopes=grant.scopes,
            expires_at=grant.expires_at,
        )

    @app.get("/api/v1/protected-resource", response_model=ProtectedResource)
    def protected_resource(
        db: Annotated[Session, Depends(get_db)],
        authorization: Annotated[str | None, Header()] = None,
    ) -> ProtectedResource:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Grant bearer token is required")
        grant, _ = validate_token(authorization.split(" ", 1)[1], db)
        return ProtectedResource(
            message="protected resource access granted",
            grant_id=grant.grant_id,
            subject_id=grant.subject_id,
        )

    @app.get("/admin-api/v1/grant-audit-events", response_model=list[dict[str, Any]])
    def list_audit_events(
        _: Annotated[Principal, Depends(audit_principal)],
        db: Annotated[Session, Depends(get_db)],
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
    ) -> list[dict[str, Any]]:
        events = list(
            db.scalars(
                select(AuditEvent)
                .where(AuditEvent.aggregate_type == "grant")
                .order_by(AuditEvent.created_at.desc())
                .limit(limit)
            )
        )
        return [
            {
                "audit_id": event.audit_id,
                "event_type": event.event_type,
                "grant_id": event.aggregate_id,
                "request_id": event.details.get("request_id"),
                "actor_id": event.actor_id,
                "details": event.details,
                "created_at": event.created_at,
            }
            for event in events
        ]

    @app.post("/internal/v1/demo/reset", response_model=DemoResetResult, include_in_schema=False)
    def reset_demo_data(
        _: Annotated[Principal, Depends(service_principal)],
        db: Annotated[Session, Depends(get_db)],
    ) -> DemoResetResult:
        if app_settings.auth_mode != "dev" or not app_settings.enable_demo_reset:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "demo reset is not available")
        grant_count = int(db.scalar(select(func.count()).select_from(Grant)) or 0)
        audit_count = int(
            db.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(AuditEvent.aggregate_type == "grant")
            )
            or 0
        )
        db.execute(delete(AuditEvent).where(AuditEvent.aggregate_type == "grant"))
        db.execute(delete(Grant))
        db.commit()
        return DemoResetResult(
            deleted={"grants": grant_count, "grant_audit_events": audit_count}
        )

    return app


app = create_app()
