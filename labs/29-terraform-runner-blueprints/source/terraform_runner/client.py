from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import httpx

from .config import Settings


class ApprovalClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._token: tuple[str, float] | None = None
        self._lock = threading.Lock()

    def _headers(self) -> dict[str, str]:
        if self.settings.auth_mode == "dev":
            return {"X-Dev-User": self.settings.runner_id, "X-Dev-Roles": "service"}
        if not (
            self.settings.service_token_url
            and self.settings.service_client_id
            and self.settings.service_client_secret_file
        ):
            raise RuntimeError("runner service OAuth is not configured")
        now = time.time()
        with self._lock:
            if self._token and self._token[1] > now + 30:
                return {"Authorization": f"Bearer {self._token[0]}"}
            secret = Path(self.settings.service_client_secret_file).read_text(encoding="utf-8").strip()
            response = httpx.post(
                self.settings.service_token_url,
                data={
                    "grant_type": "client_credentials",
                    "scope": self.settings.service_scope,
                    "audience": "approval-api",
                },
                auth=(self.settings.service_client_id, secret),
                timeout=self.settings.callback_timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            token = str(body.get("access_token", ""))
            if not token:
                raise RuntimeError("service OAuth response has no access_token")
            self._token = (token, now + max(60, int(body.get("expires_in", 300))))
            return {"Authorization": f"Bearer {token}"}

    def claim(self) -> dict[str, Any] | None:
        response = httpx.post(
            f"{self.settings.approval_api_url}/internal/v1/provisioning/jobs/claim",
            json={"runner_id": self.settings.runner_id},
            headers=self._headers(),
            timeout=self.settings.callback_timeout_seconds,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return dict(response.json())

    def report(self, job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self.settings.approval_api_url}/internal/v1/provisioning/jobs/{job_id}/result",
            json=payload,
            headers=self._headers(),
            timeout=self.settings.callback_timeout_seconds,
        )
        response.raise_for_status()
        return dict(response.json())
