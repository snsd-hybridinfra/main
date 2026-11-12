from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import httpx

_cache: dict[tuple[str, str, str, str], tuple[str, float]] = {}
_lock = threading.Lock()


def authorization_headers(settings: Any, audience: str) -> dict[str, str]:
    if settings.service_token:
        if settings.auth_mode != "dev":
            raise RuntimeError("static service token is allowed only in dev mode")
        return {"Authorization": f"Bearer {settings.service_token}"}
    if settings.auth_mode == "dev":
        return {"X-Dev-User": "approval-api", "X-Dev-Roles": "service"}
    if not settings.service_token_url or not settings.service_client_id:
        raise RuntimeError("service OAuth client is not configured")
    if not settings.service_client_secret_file:
        raise RuntimeError("service OAuth client secret file is not configured")

    cache_key = (
        settings.service_token_url,
        settings.service_client_id,
        audience,
        settings.service_scope,
    )
    now = time.time()
    with _lock:
        cached = _cache.get(cache_key)
        if cached and cached[1] > now + 30:
            return {"Authorization": f"Bearer {cached[0]}"}

        secret = Path(settings.service_client_secret_file).read_text(encoding="utf-8").strip()
        if not secret:
            raise RuntimeError("service OAuth client secret is empty")
        data = {"grant_type": "client_credentials", "scope": settings.service_scope}
        if audience:
            data["audience"] = audience
        response = httpx.post(
            settings.service_token_url,
            data=data,
            auth=(settings.service_client_id, secret),
            timeout=settings.callback_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        token = str(payload.get("access_token", ""))
        if not token or str(payload.get("token_type", "Bearer")).lower() != "bearer":
            raise RuntimeError("service OAuth response is invalid")
        expires_in = max(60, int(payload.get("expires_in", 300)))
        _cache[cache_key] = (token, now + expires_in)
        return {"Authorization": f"Bearer {token}"}
