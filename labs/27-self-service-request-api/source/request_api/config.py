from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = "sqlite+pysqlite:///./request-api.db"
    auto_create_schema: bool = False
    auth_mode: str = "oidc"
    oidc_issuer: str = ""
    oidc_audience: str = "request-api"
    oidc_jwks_url: str = ""
    approval_api_url: str = ""
    grant_api_url: str = ""
    service_token: str = ""
    service_token_url: str = ""
    service_client_id: str = ""
    service_client_secret_file: str = ""
    service_scope: str = "service:callback"
    callback_timeout_seconds: float = 3.0
    enable_provisioning_states: bool = False
    enable_legacy_execution_profile_requests: bool = False
    enable_local_llm_simulator: bool = False
    monitoring_assistant_provider: str = "disabled"
    monitoring_assistant_model: str = ""
    monitoring_assistant_token_file: str = ""
    monitoring_assistant_timeout_seconds: float = 10.0
    enable_mock_provisioner: bool = False
    enable_demo_reset: bool = False
    mock_provision_delay_seconds: float = 2.0
    required_db_revision: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite+pysqlite:///./request-api.db"),
            auto_create_schema=_as_bool(os.getenv("AUTO_CREATE_SCHEMA")),
            auth_mode=os.getenv("AUTH_MODE", "oidc").lower(),
            oidc_issuer=os.getenv("OIDC_ISSUER", ""),
            oidc_audience=os.getenv("OIDC_AUDIENCE", "request-api"),
            oidc_jwks_url=os.getenv("OIDC_JWKS_URL", ""),
            approval_api_url=os.getenv("APPROVAL_API_URL", "").rstrip("/"),
            grant_api_url=os.getenv("GRANT_API_URL", "").rstrip("/"),
            service_token=os.getenv("SERVICE_TOKEN", ""),
            service_token_url=os.getenv("SERVICE_TOKEN_URL", ""),
            service_client_id=os.getenv("SERVICE_CLIENT_ID", ""),
            service_client_secret_file=os.getenv("SERVICE_CLIENT_SECRET_FILE", ""),
            service_scope=os.getenv("SERVICE_SCOPE", "service:callback"),
            callback_timeout_seconds=float(os.getenv("CALLBACK_TIMEOUT_SECONDS", "3")),
            enable_provisioning_states=_as_bool(os.getenv("ENABLE_PROVISIONING_STATES")),
            enable_legacy_execution_profile_requests=_as_bool(
                os.getenv("ENABLE_LEGACY_EXECUTION_PROFILE_REQUESTS")
            ),
            enable_local_llm_simulator=_as_bool(os.getenv("ENABLE_LOCAL_LLM_SIMULATOR")),
            monitoring_assistant_provider=os.getenv("MONITORING_ASSISTANT_PROVIDER", "disabled").lower(),
            monitoring_assistant_model=os.getenv("MONITORING_ASSISTANT_MODEL", ""),
            monitoring_assistant_token_file=os.getenv("MONITORING_ASSISTANT_TOKEN_FILE", ""),
            monitoring_assistant_timeout_seconds=float(os.getenv("MONITORING_ASSISTANT_TIMEOUT_SECONDS", "10")),
            enable_mock_provisioner=_as_bool(os.getenv("ENABLE_MOCK_PROVISIONER")),
            enable_demo_reset=_as_bool(os.getenv("ENABLE_DEMO_RESET")),
            mock_provision_delay_seconds=float(os.getenv("MOCK_PROVISION_DELAY_SECONDS", "2")),
            required_db_revision=os.getenv("REQUIRED_DB_REVISION", ""),
        )
