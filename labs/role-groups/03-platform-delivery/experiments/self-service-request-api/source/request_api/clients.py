from __future__ import annotations

from typing import Any

import httpx

from .config import Settings
from .blueprints import BlueprintResolutionError, resolve_blueprint
from .models import AccessRequest
from .service_auth import authorization_headers


def service_headers(settings: Settings, idempotency_key: str) -> dict[str, str]:
    headers = {"Idempotency-Key": idempotency_key}
    headers.update(authorization_headers(settings, "approval-api"))
    return headers


def send_to_approval(settings: Settings, item: AccessRequest) -> tuple[str, str | None]:
    if not settings.approval_api_url:
        return "SKIPPED", None
    try:
        payload: dict[str, Any] = {
            "request_id": item.request_id,
            "idempotency_key": item.idempotency_key,
            "requester_id": item.owner_id,
            "product_code": item.product_code,
            "cpu": item.cpu,
            "memory_gib": item.memory_gib,
            "storage_gib": item.storage_gib,
            "duration_hours": item.duration_hours,
            "purpose": item.purpose,
            "parameters": {k: v for k, v in item.parameters.items() if not k.startswith("_portal_")},
            "status": item.status,
            "event_version": item.event_version,
            "retry_count": item.retry_count,
            "updated_at": item.updated_at.isoformat(),
        }
        blueprint_id = item.parameters.get("_blueprint_id")
        if isinstance(blueprint_id, str):
            resolution = resolve_blueprint(
                blueprint_id=blueprint_id,
                environment=str(item.parameters.get("_blueprint_environment", "")),
                size=str(item.parameters.get("_blueprint_size", "")),
                duration_hours=item.duration_hours,
                purpose=item.purpose,
            )
            if resolution["resolution_status"] != "RESOLVED_LOCAL":
                raise BlueprintResolutionError("blueprint is no longer executable")
            if resolution["selected_execution_profile"] != item.product_code:
                raise BlueprintResolutionError("blueprint execution profile differs")
            if resolution["manifest_digest"] != item.parameters.get("_manifest_digest"):
                raise BlueprintResolutionError("blueprint manifest digest differs")
            payload.update(
                {
                    "blueprint_id": blueprint_id,
                    "manifest_digest": resolution["manifest_digest"],
                    "resolved_manifest": resolution,
                }
            )
        response = httpx.post(
            f"{settings.approval_api_url}/internal/v1/requests",
            json=payload,
            headers=service_headers(settings, item.idempotency_key),
            timeout=settings.callback_timeout_seconds,
        )
        response.raise_for_status()
        return "DELIVERED", None
    except (httpx.HTTPError, OSError, RuntimeError, ValueError) as exc:
        return "FAILED", str(exc)[:1000]
