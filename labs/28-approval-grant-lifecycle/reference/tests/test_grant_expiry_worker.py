from __future__ import annotations

from types import SimpleNamespace

import pytest

from grant_api.expire_worker import expire_due_grants


def test_expiry_worker_calls_internal_endpoint_with_service_token(monkeypatch) -> None:
    calls: list[dict] = []

    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> list[dict]:
            return [{"grant": {"grant_id": "g-1"}}, {"grant": {"grant_id": "g-2"}}]

    def fake_post(url, *, headers, timeout):
        calls.append({"url": url, "headers": headers, "timeout": timeout})
        return Response()

    monkeypatch.setenv("GRANT_API_INTERNAL_URL", "http://grant-api.control-service:8002/")
    monkeypatch.setattr(
        "grant_api.expire_worker.authorization_headers",
        lambda settings, audience: {"Authorization": f"Bearer token-for-{audience}"},
    )
    monkeypatch.setattr("grant_api.expire_worker.httpx.post", fake_post)

    settings = SimpleNamespace(callback_timeout_seconds=5.0)
    assert expire_due_grants(settings) == 2
    assert calls == [
        {
            "url": "http://grant-api.control-service:8002/internal/v1/grants/expire",
            "headers": {"Authorization": "Bearer token-for-grant-api"},
            "timeout": 5.0,
        }
    ]


def test_expiry_worker_rejects_invalid_response(monkeypatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"unexpected": True}

    monkeypatch.setattr(
        "grant_api.expire_worker.authorization_headers", lambda settings, audience: {}
    )
    monkeypatch.setattr("grant_api.expire_worker.httpx.post", lambda *args, **kwargs: Response())
    with pytest.raises(RuntimeError, match="response is invalid"):
        expire_due_grants(SimpleNamespace(callback_timeout_seconds=5.0))
