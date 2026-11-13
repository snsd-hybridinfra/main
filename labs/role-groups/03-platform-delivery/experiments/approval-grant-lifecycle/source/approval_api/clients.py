from __future__ import annotations

from typing import Any

import httpx

from .config import Settings
from .models import ApprovalRequest
from .service_auth import authorization_headers


def service_headers(settings: Settings, idempotency_key: str, audience: str) -> dict[str, str]:
    headers = {"Idempotency-Key": idempotency_key}
    headers.update(authorization_headers(settings, audience))
    return headers


def send_request_status(
    settings: Settings,
    item: ApprovalRequest,
    *,
    reason: str | None = None,
) -> tuple[str, str | None]:
    if not settings.request_api_url:
        return "SKIPPED", None
    key = f"approval:{item.request_id}:{item.event_version}"
    payload = {
        "idempotency_key": key,
        "event_version": item.event_version,
        "retry_count": item.retry_count,
        "status": item.status,
        "reason": reason,
    }
    try:
        response = httpx.post(
            f"{settings.request_api_url}/internal/v1/requests/{item.request_id}/status",
            json=payload,
            headers=service_headers(settings, key, "request-api"),
            timeout=settings.callback_timeout_seconds,
        )
        response.raise_for_status()
        return "DELIVERED", None
    except (httpx.HTTPError, OSError, RuntimeError, ValueError) as exc:
        return "FAILED", str(exc)[:1000]


def create_grant(
    settings: Settings,
    item: ApprovalRequest,
    scopes: list[str],
    duration_hours: int,
) -> tuple[str, str | None]:
    if not settings.grant_api_url:
        return "SKIPPED", None
    grant_event_version = item.event_version + 1
    key = f"grant:{item.request_id}:{grant_event_version}"
    payload: dict[str, Any] = {
        "request_id": item.request_id,
        "idempotency_key": key,
        "subject_id": item.requester_id,
        "scopes": scopes,
        "duration_hours": duration_hours,
        "event_version": grant_event_version,
        "retry_count": item.retry_count,
    }
    try:
        response = httpx.post(
            f"{settings.grant_api_url}/internal/v1/grants",
            json=payload,
            headers=service_headers(settings, key, "grant-api"),
            timeout=settings.callback_timeout_seconds,
        )
        response.raise_for_status()
        return "DELIVERED", None
    except (httpx.HTTPError, OSError, RuntimeError, ValueError) as exc:
        return "FAILED", str(exc)[:1000]


def send_resource_status(
    settings: Settings,
    item: ApprovalRequest,
    *,
    resource_id: str,
    resource_status: str,
    event_version: int,
    endpoint: str | None = None,
    display_name: str | None = None,
    details: dict[str, str | int | bool] | None = None,
) -> tuple[str, str | None]:
    if not settings.request_api_url:
        return "SKIPPED", None
    key = f"resource:{item.request_id}:{event_version}:{resource_status.lower()}"
    payload: dict[str, Any] = {
        "resource_id": resource_id,
        "status": resource_status,
        "resource_type": item.product_code,
        "event_version": event_version,
    }
    if endpoint is not None:
        payload["endpoint"] = endpoint
    if display_name:
        payload["display_name"] = display_name
    if details is not None:
        payload["details"] = details
    try:
        response = httpx.post(
            f"{settings.request_api_url}/internal/v1/requests/{item.request_id}/resource",
            json=payload,
            headers=service_headers(settings, key, "request-api"),
            timeout=settings.callback_timeout_seconds,
        )
        response.raise_for_status()
        return "DELIVERED", None
    except (httpx.HTTPError, OSError, RuntimeError, ValueError) as exc:
        return "FAILED", str(exc)[:1000]


def reset_demo_services(settings: Settings) -> dict[str, int]:
    targets = (
        (settings.grant_api_url, "grant-api"),
        (settings.request_api_url, "request-api"),
    )
    if any(not url for url, _ in targets):
        raise RuntimeError("demo reset downstream is not configured")

    deleted: dict[str, int] = {}
    for api_url, audience in targets:
        try:
            response = httpx.post(
                f"{api_url}/internal/v1/demo/reset",
                headers=service_headers(settings, "demo-reset", audience),
                timeout=settings.callback_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            for name, count in payload.get("deleted", {}).items():
                deleted[str(name)] = int(count)
        except (httpx.HTTPError, OSError, RuntimeError, TypeError, ValueError) as exc:
            raise RuntimeError(f"{audience} demo reset failed") from exc
    return deleted


def seed_demo_request(settings: Settings) -> dict[str, Any]:
    if not settings.request_api_url:
        raise RuntimeError("demo seed downstream is not configured")
    try:
        response = httpx.post(
            f"{settings.request_api_url}/internal/v1/demo/seed",
            headers=service_headers(settings, "demo-seed-dev-os-vm-s-v1", "request-api"),
            timeout=settings.callback_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "status": str(payload["status"]),
            "created": bool(payload["created"]),
            "delivery_status": str(payload["delivery_status"]),
        }
    except (httpx.HTTPError, OSError, RuntimeError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("request-api demo seed failed") from exc
