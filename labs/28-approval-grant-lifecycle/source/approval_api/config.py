from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = "sqlite+pysqlite:///./approval-api.db"
    auto_create_schema: bool = False
    auth_mode: str = "oidc"
    oidc_issuer: str = ""
    oidc_audience: str = "approval-api"
    oidc_jwks_url: str = ""
    request_api_url: str = ""
    grant_api_url: str = ""
    service_token: str = ""
    service_token_url: str = ""
    service_client_id: str = ""
    service_client_secret_file: str = ""
    service_scope: str = "service:callback"
    callback_timeout_seconds: float = 3.0
    enable_provisioning_jobs: bool = False
    enable_demo_reset: bool = False
    grafana_dashboard_url: str = ""
    required_db_revision: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite+pysqlite:///./approval-api.db"),
            auto_create_schema=_as_bool(os.getenv("AUTO_CREATE_SCHEMA")),
            auth_mode=os.getenv("AUTH_MODE", "oidc").lower(),
            oidc_issuer=os.getenv("OIDC_ISSUER", ""),
            oidc_audience=os.getenv("OIDC_AUDIENCE", "approval-api"),
            oidc_jwks_url=os.getenv("OIDC_JWKS_URL", ""),
            request_api_url=os.getenv("REQUEST_API_URL", "").rstrip("/"),
            grant_api_url=os.getenv("GRANT_API_URL", "").rstrip("/"),
            service_token=os.getenv("SERVICE_TOKEN", ""),
            service_token_url=os.getenv("SERVICE_TOKEN_URL", ""),
            service_client_id=os.getenv("SERVICE_CLIENT_ID", ""),
            service_client_secret_file=os.getenv("SERVICE_CLIENT_SECRET_FILE", ""),
            service_scope=os.getenv("SERVICE_SCOPE", "service:callback"),
            callback_timeout_seconds=float(os.getenv("CALLBACK_TIMEOUT_SECONDS", "3")),
            enable_provisioning_jobs=_as_bool(os.getenv("ENABLE_PROVISIONING_JOBS")),
            enable_demo_reset=_as_bool(os.getenv("ENABLE_DEMO_RESET")),
            grafana_dashboard_url=os.getenv("GRAFANA_DASHBOARD_URL", "").strip(),
            required_db_revision=os.getenv("REQUIRED_DB_REVISION", ""),
        )
