from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = "sqlite+pysqlite:///./grant-api.db"
    auto_create_schema: bool = False
    auth_mode: str = "oidc"
    oidc_issuer: str = ""
    oidc_audience: str = "grant-api"
    oidc_jwks_url: str = ""
    request_api_url: str = ""
    approval_api_url: str = ""
    service_token: str = ""
    service_token_url: str = ""
    service_client_id: str = ""
    service_client_secret_file: str = ""
    service_scope: str = "service:callback"
    callback_timeout_seconds: float = 3.0
    grant_signing_key: str = ""
    grant_signing_algorithm: str = "RS256"
    grant_signing_private_key_file: str = ""
    grant_signing_public_key_file: str = ""
    grant_issuer: str = "https://grant.internal.example.com"
    grant_audience: str = "protected-resource"
    enable_demo_reset: bool = False
    required_db_revision: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite+pysqlite:///./grant-api.db"),
            auto_create_schema=_as_bool(os.getenv("AUTO_CREATE_SCHEMA")),
            auth_mode=os.getenv("AUTH_MODE", "oidc").lower(),
            oidc_issuer=os.getenv("OIDC_ISSUER", ""),
            oidc_audience=os.getenv("OIDC_AUDIENCE", "grant-api"),
            oidc_jwks_url=os.getenv("OIDC_JWKS_URL", ""),
            request_api_url=os.getenv("REQUEST_API_URL", "").rstrip("/"),
            approval_api_url=os.getenv("APPROVAL_API_URL", "").rstrip("/"),
            service_token=os.getenv("SERVICE_TOKEN", ""),
            service_token_url=os.getenv("SERVICE_TOKEN_URL", ""),
            service_client_id=os.getenv("SERVICE_CLIENT_ID", ""),
            service_client_secret_file=os.getenv("SERVICE_CLIENT_SECRET_FILE", ""),
            service_scope=os.getenv("SERVICE_SCOPE", "service:callback"),
            callback_timeout_seconds=float(os.getenv("CALLBACK_TIMEOUT_SECONDS", "3")),
            grant_signing_key=os.getenv("GRANT_SIGNING_KEY", ""),
            grant_signing_algorithm=os.getenv("GRANT_SIGNING_ALGORITHM", "RS256").upper(),
            grant_signing_private_key_file=os.getenv("GRANT_SIGNING_PRIVATE_KEY_FILE", ""),
            grant_signing_public_key_file=os.getenv("GRANT_SIGNING_PUBLIC_KEY_FILE", ""),
            grant_issuer=os.getenv("GRANT_ISSUER", "https://grant.internal.example.com"),
            grant_audience=os.getenv("GRANT_AUDIENCE", "protected-resource"),
            enable_demo_reset=_as_bool(os.getenv("ENABLE_DEMO_RESET")),
            required_db_revision=os.getenv("REQUIRED_DB_REVISION", ""),
        )
