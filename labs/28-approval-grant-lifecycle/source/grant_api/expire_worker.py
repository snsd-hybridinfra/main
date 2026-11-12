from __future__ import annotations

import os

import httpx

from .config import Settings
from .service_auth import authorization_headers


def expire_due_grants(settings: Settings | None = None) -> int:
    app_settings = settings or Settings.from_env()
    target = os.getenv("GRANT_API_INTERNAL_URL", "http://grant-api:8002").rstrip("/")
    response = httpx.post(
        f"{target}/internal/v1/grants/expire",
        headers=authorization_headers(app_settings, "grant-api"),
        timeout=app_settings.callback_timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError("grant expiry response is invalid")
    return len(payload)


def main() -> None:
    expired = expire_due_grants()
    print(f"grant expiry completed: expired={expired}")


if __name__ == "__main__":
    main()
