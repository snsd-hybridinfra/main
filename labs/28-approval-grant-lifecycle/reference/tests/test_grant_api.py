from __future__ import annotations

from fastapi.testclient import TestClient

import grant_api.main as grant_main
from grant_api.config import Settings
from grant_api.main import create_app


SERVICE = {"X-Dev-User": "approval-api", "X-Dev-Roles": "service"}
GRANT_ADMIN = {"X-Dev-User": "grant-admin-1", "X-Dev-Roles": "grant-admin"}


def test_revoke_blocks_grant_before_destroy_is_queued(tmp_path, monkeypatch) -> None:
    observed: list[str] = []

    def capture_destroy(_, grant, **__):
        observed.append(grant.status)
        return "QUEUED", None

    monkeypatch.setattr(grant_main, "request_destroy", capture_destroy)
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'grant-destroy.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            approval_api_url="http://approval-api.test",
            grant_signing_key="test-only-signing-key-at-least-32-bytes",
            grant_signing_algorithm="HS256",
        )
    )
    with TestClient(app) as client:
        issued = client.post(
            "/internal/v1/grants",
            headers=SERVICE,
            json={
                "request_id": "destroy-request",
                "idempotency_key": "grant-destroy-request-v3",
                "subject_id": "user-1",
                "scopes": ["resource:access"],
                "duration_hours": 24,
                "event_version": 3,
            },
        ).json()
        revoked = client.post(
            f"/admin-api/v1/grants/{issued['grant']['grant_id']}/revoke",
            headers=GRANT_ADMIN,
        )
        assert revoked.status_code == 200
        assert revoked.json()["grant"]["status"] == "REVOKED"
        assert revoked.json()["deprovision_status"] == "QUEUED"
        assert observed == ["REVOKED"]


def test_revoke_blocks_previously_issued_jwt(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'grant.db').as_posix()}"
    app = create_app(
        Settings(
            database_url=database_url,
            auto_create_schema=True,
            auth_mode="dev",
            grant_signing_key="test-only-signing-key-at-least-32-bytes",
            grant_signing_algorithm="HS256",
            grant_issuer="https://grant.test",
            grant_audience="protected-resource",
        )
    )

    with TestClient(app) as client:
        issued = client.post(
            "/internal/v1/grants",
            headers=SERVICE,
            json={
                "request_id": "request-1",
                "idempotency_key": "grant-request-1-v3",
                "subject_id": "user-1",
                "scopes": ["resource:access"],
                "duration_hours": 24,
                "event_version": 3,
                "retry_count": 0,
            },
        )
        assert issued.status_code == 201
        grant_assertion = issued.json()["token"]
        grant_id = issued.json()["grant"]["grant_id"]
        assert issued.json()["grant"]["status"] == "ACTIVE"

        allowed = client.get(
            "/api/v1/protected-resource", headers={"Authorization": f"Bearer {grant_assertion}"}
        )
        assert allowed.status_code == 200

        revoked = client.post(
            f"/admin-api/v1/grants/{grant_id}/revoke", headers=GRANT_ADMIN
        )
        assert revoked.status_code == 200
        assert revoked.json()["grant"]["status"] == "REVOKED"

        reused = client.get(
            "/api/v1/protected-resource", headers={"Authorization": f"Bearer {grant_assertion}"}
        )
        assert reused.status_code == 403
        assert "REVOKED" in reused.json()["detail"]


def test_demo_reset_deletes_grants_and_grant_audits(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'grant-demo-reset.db').as_posix()}"
    app = create_app(
        Settings(
            database_url=database_url,
            auto_create_schema=True,
            auth_mode="dev",
            enable_demo_reset=True,
            grant_signing_key="test-only-signing-key-at-least-32-bytes",
            grant_signing_algorithm="HS256",
        )
    )

    with TestClient(app) as client:
        issued = client.post(
            "/internal/v1/grants",
            headers=SERVICE,
            json={
                "request_id": "reset-request-1",
                "idempotency_key": "reset-grant-request-1",
                "subject_id": "user-1",
                "scopes": ["resource:access"],
                "duration_hours": 24,
                "event_version": 3,
                "retry_count": 0,
            },
        )
        assert issued.status_code == 201

        reset = client.post("/internal/v1/demo/reset", headers=SERVICE)
        assert reset.status_code == 200
        assert reset.json()["deleted"] == {"grants": 1, "grant_audit_events": 1}
        assert client.get("/admin-api/v1/grants?status=ALL", headers=GRANT_ADMIN).json() == []
        assert client.get("/admin-api/v1/grant-audit-events", headers=GRANT_ADMIN).json() == []


def test_demo_expire_now_blocks_token_and_records_expiry(tmp_path) -> None:
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'grant-expire-now.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            enable_demo_reset=True,
            grant_signing_key="test-only-signing-key-at-least-32-bytes",
            grant_signing_algorithm="HS256",
        )
    )

    with TestClient(app) as client:
        issued = client.post(
            "/internal/v1/grants",
            headers=SERVICE,
            json={
                "request_id": "expire-now-request-1",
                "idempotency_key": "expire-now-grant-request-1",
                "subject_id": "demo-user",
                "scopes": ["resource:access"],
                "duration_hours": 24,
                "event_version": 3,
            },
        ).json()
        grant_id = issued["grant"]["grant_id"]
        grant_assertion = issued["token"]

        expired = client.post(
            f"/admin-api/v1/grants/{grant_id}/expire-now",
            headers=GRANT_ADMIN,
        )
        assert expired.status_code == 200
        assert expired.json()["grant"]["status"] == "EXPIRED"
        assert expired.json()["grant"]["event_version"] == 4

        denied = client.get(
            "/api/v1/protected-resource", headers={"Authorization": f"Bearer {grant_assertion}"}
        )
        assert denied.status_code == 403
        events = client.get("/admin-api/v1/grant-audit-events", headers=GRANT_ADMIN).json()
        assert events[0]["event_type"] == "GRANT_EXPIRED"
        assert events[0]["details"]["demo_trigger"] == "expire-now"
