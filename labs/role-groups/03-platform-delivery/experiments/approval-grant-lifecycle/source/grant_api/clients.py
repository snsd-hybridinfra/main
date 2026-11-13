from __future__ import annotations

import httpx

from .config import Settings
from .models import Grant
from .service_auth import authorization_headers


def service_headers(
    settings: Settings,
    idempotency_key: str,
    audience: str = "request-api",
) -> dict[str, str]:
    headers = {"Idempotency-Key": idempotency_key}
    headers.update(authorization_headers(settings, audience))
    return headers


def send_request_status(settings: Settings, grant: Grant) -> tuple[str, str | None]:
    if not settings.request_api_url:
        return "SKIPPED", None
    request_status = {"ACTIVE": "GRANTED", "REVOKED": "REVOKED", "EXPIRED": "EXPIRED"}[grant.status]
    key = f"grant-status:{grant.grant_id}:{grant.event_version}"
    payload = {
        "idempotency_key": key,
        "event_version": grant.event_version,
        "retry_count": grant.retry_count,
        "status": request_status,
        "grant_id": grant.grant_id,
        "grant_expires_at": grant.expires_at.isoformat(),
    }
    try:
        response = httpx.post(
            f"{settings.request_api_url}/internal/v1/requests/{grant.request_id}/status",
            json=payload,
            headers=service_headers(settings, key),
            timeout=settings.callback_timeout_seconds,
        )
        response.raise_for_status()
        return "DELIVERED", None
    except (httpx.HTTPError, OSError, RuntimeError, ValueError) as exc:
        return "FAILED", str(exc)[:1000]


def request_destroy(
    settings: Settings,
    grant: Grant,
    *,
    reason: str | None = None,
) -> tuple[str, str | None]:
    if not settings.approval_api_url:
        return "SKIPPED", None
    key = f"destroy:{grant.request_id}:{grant.event_version}"
    payload = {"trigger_status": grant.status, "reason": reason}
    try:
        response = httpx.post(
            f"{settings.approval_api_url}/internal/v1/provisioning/requests/{grant.request_id}/destroy",
            json=payload,
            headers=service_headers(settings, key, "approval-api"),
            timeout=settings.callback_timeout_seconds,
        )
        if response.status_code == 409:
            return "SKIPPED", None
        response.raise_for_status()
        return "QUEUED", None
    except (httpx.HTTPError, OSError, RuntimeError, ValueError) as exc:
        return "FAILED", str(exc)[:1000]
