from __future__ import annotations

from types import SimpleNamespace

import pytest

from request_api.service_auth import authorization_headers


@pytest.mark.authz
def test_service_client_credentials_uses_target_audience_and_cache(tmp_path, monkeypatch) -> None:
    secret_path = tmp_path / "client-secret"
    secret_path.write_text("oauth-secret", encoding="utf-8")
    calls: list[dict] = []

    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"access_token": "short-lived-token", "token_type": "Bearer", "expires_in": 300}

    def fake_post(url, *, data, auth, timeout):
        calls.append({"url": url, "data": data, "auth": auth, "timeout": timeout})
        return Response()

    monkeypatch.setattr("request_api.service_auth.httpx.post", fake_post)
    settings = SimpleNamespace(
        service_token="",
        auth_mode="oidc",
        service_token_url="https://issuer.test/token",
        service_client_id="request-api-callback",
        service_client_secret_file=str(secret_path),
        service_scope="service:callback",
        callback_timeout_seconds=3.0,
    )

    first = authorization_headers(settings, "approval-api")
    second = authorization_headers(settings, "approval-api")

    assert first == second == {"Authorization": "Bearer short-lived-token"}
    assert len(calls) == 1
    assert calls[0]["auth"] == ("request-api-callback", "oauth-secret")
    assert calls[0]["data"] == {
        "grant_type": "client_credentials",
        "scope": "service:callback",
        "audience": "approval-api",
    }


@pytest.mark.authz
def test_static_service_token_is_rejected_in_oidc_mode() -> None:
    settings = SimpleNamespace(service_token="fixed-token", auth_mode="oidc")
    with pytest.raises(RuntimeError, match="only in dev"):
        authorization_headers(settings, "approval-api")
