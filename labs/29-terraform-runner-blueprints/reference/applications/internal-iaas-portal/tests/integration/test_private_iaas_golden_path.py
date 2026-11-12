from __future__ import annotations

from fastapi.testclient import TestClient

import approval_api.main as approval_main
import grant_api.main as grant_main
from approval_api.config import Settings as ApprovalSettings
from approval_api.main import create_app as create_approval_app
from grant_api.config import Settings as GrantSettings
from grant_api.main import create_app as create_grant_app
from request_api.config import Settings as RequestSettings
from request_api.main import create_app as create_request_app
from terraform_runner.config import Settings as RunnerSettings
from terraform_runner.executor import Executor


USER = {"X-Dev-User": "golden-user", "X-Dev-Roles": "user"}
SERVICE = {"X-Dev-User": "service-callback", "X-Dev-Roles": "service"}
APPROVER = {"X-Dev-User": "golden-approver", "X-Dev-Roles": "approver"}
GRANT_ADMIN = {"X-Dev-User": "golden-grant-admin", "X-Dev-Roles": "grant-admin"}
RUNNER = {"X-Dev-User": "terraform-runner", "X-Dev-Roles": "service"}


def test_private_vm_golden_path_reaches_terminated_without_runtime_provider(
    tmp_path, monkeypatch
) -> None:
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
            enable_provisioning_jobs=True,
        )
    )
    grant_app = create_grant_app(
        GrantSettings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'grant.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            grant_signing_key="local-golden-path-signing-key-32-bytes",
            grant_signing_algorithm="HS256",
            grant_issuer="https://grant.golden-path.test",
            grant_audience="protected-resource",
        )
    )

    captured: dict[str, str] = {}
    with TestClient(request_app) as request_client, TestClient(
        approval_app
    ) as approval_client, TestClient(grant_app) as grant_client:

        def project_approval_status(_, item, *, reason=None):
            key = f"approval:{item.request_id}:{item.event_version}"
            response = request_client.post(
                f"/internal/v1/requests/{item.request_id}/status",
                headers=SERVICE,
                json={
                    "idempotency_key": key,
                    "event_version": item.event_version,
                    "retry_count": item.retry_count,
                    "status": item.status,
                    "reason": reason,
                },
            )
            return ("DELIVERED", None) if response.is_success else ("FAILED", response.text)

        def project_resource_status(
            _, item, *, resource_id, resource_status, event_version,
            endpoint=None, display_name=None, details=None
        ):
            response = request_client.post(
                f"/internal/v1/requests/{item.request_id}/resource",
                headers=SERVICE,
                json={
                    "resource_id": resource_id,
                    "status": resource_status,
                    "resource_type": item.product_code,
                    "event_version": event_version,
                    "endpoint": endpoint,
                    "display_name": display_name,
                    "details": details,
                },
            )
            return ("DELIVERED", None) if response.is_success else ("FAILED", response.text)

        def project_grant_status(_, grant):
            request_status = {
                "ACTIVE": "GRANTED",
                "REVOKED": "REVOKED",
                "EXPIRED": "EXPIRED",
            }[grant.status]
            response = request_client.post(
                f"/internal/v1/requests/{grant.request_id}/status",
                headers=SERVICE,
                json={
                    "idempotency_key": f"grant-status:{grant.grant_id}:{grant.event_version}",
                    "event_version": grant.event_version,
                    "retry_count": grant.retry_count,
                    "status": request_status,
                    "grant_id": grant.grant_id,
                    "grant_expires_at": grant.expires_at.isoformat(),
                },
            )
            return ("DELIVERED", None) if response.is_success else ("FAILED", response.text)

        def issue_grant(_, item, scopes, duration_hours):
            event_version = item.event_version + 1
            response = grant_client.post(
                "/internal/v1/grants",
                headers=SERVICE,
                json={
                    "request_id": item.request_id,
                    "idempotency_key": f"grant:{item.request_id}:{event_version}",
                    "subject_id": item.requester_id,
                    "scopes": scopes,
                    "duration_hours": duration_hours,
                    "event_version": event_version,
                    "retry_count": item.retry_count,
                },
            )
            if not response.is_success:
                return "FAILED", response.text
            payload = response.json()
            captured["grant_id"] = payload["grant"]["grant_id"]
            captured["token"] = payload["token"]
            return "DELIVERED", None

        def queue_destroy(_, grant, *, reason=None):
            response = approval_client.post(
                f"/internal/v1/provisioning/requests/{grant.request_id}/destroy",
                headers=SERVICE,
                json={"trigger_status": grant.status, "reason": reason},
            )
            return ("QUEUED", None) if response.is_success else ("FAILED", response.text)

        monkeypatch.setattr(approval_main, "send_request_status", project_approval_status)
        monkeypatch.setattr(approval_main, "send_resource_status", project_resource_status)
        monkeypatch.setattr(approval_main, "create_grant", issue_grant)
        monkeypatch.setattr(grant_main, "send_request_status", project_grant_status)
        monkeypatch.setattr(grant_main, "request_destroy", queue_destroy)

        created = request_client.post(
            "/api/v1/requests",
            headers={**USER, "Idempotency-Key": "golden-private-vm-1"},
            json={
                "product_code": "DEV-OS-VM-S",
                "cpu": 0,
                "memory_gib": 0,
                "storage_gib": 0,
                "duration_hours": 4,
                "purpose": "private IaaS golden path validation",
                "parameters": {
                    "project_name": "golden-private-vm",
                    "workload_purpose": "backend-integration-test",
                },
            },
        )
        assert created.status_code == 201
        request_data = created.json()
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
                "status": request_data["status"],
                "event_version": request_data["event_version"],
                "retry_count": request_data["retry_count"],
                "updated_at": request_data["updated_at"],
            },
        )
        assert ingested.status_code == 200

        approved = approval_client.post(
            f"/admin-api/v1/requests/{request_id}/approve",
            headers=APPROVER,
            json={"reason": "bounded local golden-path approval"},
        )
        assert approved.status_code == 200
        assert approved.json()["grant_status"] == "DEFERRED"
        assert request_client.get(f"/api/v1/requests/{request_id}", headers=USER).json()["status"] == "APPROVED"

        apply_job = approval_client.post(
            "/internal/v1/provisioning/jobs/claim",
            headers=RUNNER,
            json={"runner_id": "terraform-runner"},
        ).json()
        assert apply_job["operation"] == "APPLY"

        apply_responses = []

        def report_apply(payload):
            response = approval_client.post(
                f"/internal/v1/provisioning/jobs/{apply_job['job_id']}/result",
                headers=RUNNER,
                json=payload,
            )
            assert response.status_code == 200, response.text
            apply_responses.append(response.json())

        Executor(RunnerSettings(runner_mode="mock", mock_delay_seconds=0)).run(
            apply_job, report_apply
        )
        assert apply_responses[-1]["job"]["status"] == "SUCCEEDED"
        assert apply_responses[-1]["grant_status"] == "DELIVERED"

        active_request = request_client.get(
            f"/api/v1/requests/{request_id}", headers=USER
        ).json()
        resources = request_client.get("/api/v1/resources", headers=USER).json()
        assert active_request["status"] == "GRANTED"
        assert active_request["resource_status"] == "RUNNING"
        assert resources[0]["status"] == "RUNNING"
        assert resources[0]["details"]["network_exposure"] == "PRIVATE_ONLY"
        assert resources[0]["details"]["floating_ip"] is False
        assert grant_client.get(
            "/api/v1/protected-resource",
            headers={"Authorization": f"Bearer {captured['token']}"},
        ).status_code == 200

        revoked = grant_client.post(
            f"/admin-api/v1/grants/{captured['grant_id']}/revoke",
            headers=GRANT_ADMIN,
        )
        assert revoked.status_code == 200
        assert revoked.json()["deprovision_status"] == "QUEUED"
        assert grant_client.get(
            "/api/v1/protected-resource",
            headers={"Authorization": f"Bearer {captured['token']}"},
        ).status_code == 403

        destroy_job = approval_client.post(
            "/internal/v1/provisioning/jobs/claim",
            headers=RUNNER,
            json={"runner_id": "terraform-runner"},
        ).json()
        assert destroy_job["operation"] == "DESTROY"

        def report_destroy(payload):
            response = approval_client.post(
                f"/internal/v1/provisioning/jobs/{destroy_job['job_id']}/result",
                headers=RUNNER,
                json=payload,
            )
            assert response.status_code == 200, response.text

        Executor(RunnerSettings(runner_mode="mock", mock_delay_seconds=0)).run(
            destroy_job, report_destroy
        )
        final_request = request_client.get(
            f"/api/v1/requests/{request_id}", headers=USER
        ).json()
        final_resource = request_client.get("/api/v1/resources", headers=USER).json()[0]
        assert final_request["status"] == "REVOKED"
        assert final_request["resource_status"] == "TERMINATED"
        assert final_resource["status"] == "TERMINATED"
