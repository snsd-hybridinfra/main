from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from grant_api.auth import Principal as GrantPrincipal
from grant_api.auth import current_principal as grant_current_principal
from grant_api.config import Settings as GrantSettings
from grant_api.main import create_app as create_grant_app
from request_api.config import Settings as RequestSettings
from request_api.main import create_app as create_request_app


def _rsa_pair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


@pytest.mark.authz
def test_request_api_validates_audience_role_and_scope(tmp_path, monkeypatch) -> None:
    private_pem, public_pem = _rsa_pair()

    class FakeJwksClient:
        def __init__(self, _: str) -> None:
            pass

        def get_signing_key_from_jwt(self, _: str) -> SimpleNamespace:
            return SimpleNamespace(key=public_pem)

    monkeypatch.setattr("request_api.auth.PyJWKClient", FakeJwksClient)
    settings = RequestSettings(
        database_url=f"sqlite+pysqlite:///{(tmp_path / 'request-auth.db').as_posix()}",
        auto_create_schema=True,
        auth_mode="oidc",
        oidc_issuer="https://issuer.test",
        oidc_audience="request-api",
        oidc_jwks_url="https://issuer.test/jwks",
    )
    now = datetime.now(timezone.utc)

    def token(*, audience: str = "request-api", role: str = "user", scope: str = "request:access") -> str:
        return jwt.encode(
            {
                "iss": "https://issuer.test",
                "aud": audience,
                "sub": "user-1",
                "iat": now,
                "exp": now + timedelta(minutes=5),
                "roles": [role],
                "scope": scope,
            },
            private_pem,
            algorithm="RS256",
        )

    with TestClient(create_request_app(settings)) as client:
        valid = client.get("/api/v1/catalog", headers={"Authorization": f"Bearer {token()}"})
        assert valid.status_code == 200

        wrong_audience = client.get(
            "/api/v1/catalog",
            headers={"Authorization": f"Bearer {token(audience='other-api')}"},
        )
        assert wrong_audience.status_code == 401

        wrong_role = client.get(
            "/api/v1/catalog",
            headers={"Authorization": f"Bearer {token(role='auditor')}"},
        )
        assert wrong_role.status_code == 403

        missing_scope = client.get(
            "/api/v1/catalog",
            headers={"Authorization": f"Bearer {token(scope='openid')}"},
        )
        assert missing_scope.status_code == 403


@pytest.mark.authz
def test_hs256_grant_signing_is_rejected_outside_dev(tmp_path) -> None:
    app = create_grant_app(
        GrantSettings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'grant-prod.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="oidc",
            grant_signing_algorithm="HS256",
            grant_signing_key="a-production-key-that-must-still-be-rejected",
        )
    )
    app.dependency_overrides[grant_current_principal] = lambda: GrantPrincipal(
        subject="approval-api",
        roles=frozenset({"service"}),
        scopes=frozenset({"service:callback"}),
    )

    with TestClient(app) as client:
        response = client.post(
            "/internal/v1/grants",
            json={
                "request_id": "request-prod-1",
                "idempotency_key": "grant-prod-1",
                "subject_id": "user-1",
                "scopes": ["resource:access"],
                "duration_hours": 1,
                "event_version": 3,
                "retry_count": 0,
            },
        )
    assert response.status_code == 503
    assert "HS256" in response.json()["detail"]


@pytest.mark.authz
def test_rs256_grant_can_be_issued_and_validated(tmp_path) -> None:
    private_pem, public_pem = _rsa_pair()
    private_path = tmp_path / "private.pem"
    public_path = tmp_path / "public.pem"
    private_path.write_text(private_pem, encoding="utf-8")
    public_path.write_text(public_pem, encoding="utf-8")
    app = create_grant_app(
        GrantSettings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'grant-rs.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            grant_signing_algorithm="RS256",
            grant_signing_private_key_file=str(private_path),
            grant_signing_public_key_file=str(public_path),
            grant_issuer="https://grant.test",
            grant_audience="protected-resource",
        )
    )

    with TestClient(app) as client:
        issued = client.post(
            "/internal/v1/grants",
            headers={"X-Dev-User": "approval-api", "X-Dev-Roles": "service"},
            json={
                "request_id": "request-rs-1",
                "idempotency_key": "grant-rs-1",
                "subject_id": "user-1",
                "scopes": ["resource:access"],
                "duration_hours": 1,
                "event_version": 3,
                "retry_count": 0,
            },
        )
        assert issued.status_code == 201
        grant_assertion = issued.json()["token"]
        allowed = client.get(
            "/api/v1/protected-resource",
            headers={"Authorization": f"Bearer {grant_assertion}"},
        )
        assert allowed.status_code == 200
