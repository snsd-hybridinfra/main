from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from approval_api.config import Settings as ApprovalSettings
from approval_api.main import create_app as create_approval_app
from grant_api.config import Settings as GrantSettings
from grant_api.main import create_app as create_grant_app
from request_api.config import Settings as RequestSettings
from request_api.main import create_app as create_request_app


USER = {"X-Dev-User": "demo-user", "X-Dev-Roles": "user"}
SERVICE = {"X-Dev-User": "service-callback", "X-Dev-Roles": "service"}
APPROVER = {"X-Dev-User": "demo-approver", "X-Dev-Roles": "approver"}
GRANT_ADMIN = {"X-Dev-User": "demo-grant-admin", "X-Dev-Roles": "grant-admin"}


def test_poc_flow_request_approve_grant_revoke_and_reuse_block(tmp_path) -> None:
    request_app = create_request_app(
        RequestSettings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'request.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            enable_legacy_execution_profile_requests=True,
        )
    )
    approval_app = create_approval_app(
        ApprovalSettings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'approval.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
        )
    )
    grant_app = create_grant_app(
        GrantSettings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'grant.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            grant_signing_key="integration-test-signing-key-32-bytes-minimum",
            grant_signing_algorithm="HS256",
            grant_issuer="https://grant.integration.test",
            grant_audience="protected-resource",
        )
    )

    with TestClient(request_app) as request_client, TestClient(
        approval_app
    ) as approval_client, TestClient(grant_app) as grant_client:
        request_created = request_client.post(
            "/api/v1/requests",
            headers={**USER, "Idempotency-Key": "integration-request-1"},
            json={
                "product_code": "DEV-OS-VM-S",
                "cpu": 0,
                "memory_gib": 0,
                "storage_gib": 0,
                "duration_hours": 24,
                "purpose": "Phase 6 서비스 흐름 재현",
                "parameters": {
                    "project_name": "phase6-service-flow",
                    "workload_purpose": "backend-integration-test",
                },
            },
        )
        assert request_created.status_code == 201
        request_data = request_created.json()
        request_id = request_data["request_id"]
        assert request_data["status"] == "PENDING"

        ingested = approval_client.post(
            "/internal/v1/requests",
            headers=SERVICE,
            json={
                "request_id": request_id,
                "idempotency_key": request_data["idempotency_key"],
                "requester_id": request_data["owner_id"],
                "product_code": request_data["product_code"],
                "cpu": request_data["cpu"],
                "memory_gib": request_data["memory_gib"],
                "storage_gib": request_data["storage_gib"],
                "duration_hours": request_data["duration_hours"],
                    "purpose": request_data["purpose"],
                    "parameters": request_data["parameters"],
                "status": "PENDING",
                "event_version": request_data["event_version"],
                "retry_count": request_data["retry_count"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert ingested.status_code == 200

        decision = approval_client.post(
            f"/admin-api/v1/requests/{request_id}/approve",
            headers=APPROVER,
                json={"reason": "통합 테스트 승인"},
        )
        assert decision.status_code == 200
        assert decision.json()["request"]["status"] == "APPROVED"

        approved_projection = request_client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": f"approval:{request_id}:2",
                "event_version": 2,
                "status": "APPROVED",
            },
        )
        assert approved_projection.json()["status"] == "APPROVED"

        issued = grant_client.post(
            "/internal/v1/grants",
            headers=SERVICE,
            json={
                "request_id": request_id,
                "idempotency_key": f"grant:{request_id}:3",
                "subject_id": request_data["owner_id"],
                "scopes": ["openstack:vm:access"],
                "duration_hours": request_data["duration_hours"],
                "event_version": 3,
                "retry_count": 0,
            },
        )
        assert issued.status_code == 201
        grant_assertion = issued.json()["token"]
        grant = issued.json()["grant"]
        assert grant["status"] == "ACTIVE"

        granted_projection = request_client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": f"grant-status:{grant['grant_id']}:3",
                "event_version": 3,
                "status": "GRANTED",
                "grant_id": grant["grant_id"],
                "grant_expires_at": grant["expires_at"],
            },
        )
        assert granted_projection.json()["status"] == "GRANTED"

        access_before = grant_client.get(
            "/api/v1/protected-resource", headers={"Authorization": f"Bearer {grant_assertion}"}
        )
        assert access_before.status_code == 200

        revoked = grant_client.post(
            f"/admin-api/v1/grants/{grant['grant_id']}/revoke", headers=GRANT_ADMIN
        )
        assert revoked.status_code == 200
        revoked_grant = revoked.json()["grant"]
        assert revoked_grant["status"] == "REVOKED"

        revoked_projection = request_client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": f"grant-status:{grant['grant_id']}:4",
                "event_version": 4,
                "status": "REVOKED",
                "grant_id": grant["grant_id"],
                "grant_expires_at": grant["expires_at"],
            },
        )
        assert revoked_projection.json()["status"] == "REVOKED"

        access_after = grant_client.get(
            "/api/v1/protected-resource", headers={"Authorization": f"Bearer {grant_assertion}"}
        )
        assert access_after.status_code == 403

        final_request = request_client.get(f"/api/v1/requests/{request_id}", headers=USER)
        assert final_request.json()["status"] == "REVOKED"
        assert final_request.json()["grant_id"] == grant["grant_id"]
