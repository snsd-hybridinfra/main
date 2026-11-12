from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import approval_api.main as approval_main
from approval_api.config import Settings
from approval_api.main import create_app


SERVICE = {"X-Dev-User": "request-api", "X-Dev-Roles": "service"}
APPROVER = {"X-Dev-User": "approver-1", "X-Dev-Roles": "approver"}
AUDITOR = {"X-Dev-User": "auditor-1", "X-Dev-Roles": "auditor"}
RUNNER = {"X-Dev-User": "terraform-runner", "X-Dev-Roles": "service"}


def ingest_payload(request_id: str = "request-1") -> dict:
    return {
        "request_id": request_id,
        "idempotency_key": f"create-{request_id}",
        "requester_id": "user-1",
        "product_code": "DEV-OS-VM-S",
        "cpu": 2,
        "memory_gib": 2,
        "storage_gib": 30,
        "duration_hours": 24,
        "purpose": "승인 API 검증",
        "parameters": {
            "project_name": "payment-api-test",
            "workload_purpose": "saas-application-development",
        },
        "status": "PENDING",
        "event_version": 1,
        "retry_count": 0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def test_approval_decision_and_audit(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'approval.db').as_posix()}"
    app = create_app(Settings(database_url=database_url, auto_create_schema=True, auth_mode="dev"))

    with TestClient(app) as client:
        ingested = client.post("/internal/v1/requests", headers=SERVICE, json=ingest_payload())
        assert ingested.status_code == 200
        assert ingested.json()["status"] == "PENDING"

        pending = client.get("/admin-api/v1/requests?status=PENDING", headers=APPROVER)
        assert pending.status_code == 200
        assert len(pending.json()) == 1

        approved = client.post(
            "/admin-api/v1/requests/request-1/approve",
            headers=APPROVER,
            json={"reason": "개발 검증 승인"},
        )
        assert approved.status_code == 200
        assert approved.json()["request"]["status"] == "APPROVED"
        assert approved.json()["request"]["event_version"] == 2
        assert approved.json()["callback_status"] == "SKIPPED"
        assert approved.json()["grant_status"] == "SKIPPED"

        duplicate = client.post(
            "/admin-api/v1/requests/request-1/approve", headers=APPROVER, json={}
        )
        assert duplicate.status_code == 409

        audits = client.get("/admin-api/v1/audit-events", headers=AUDITOR)
        assert audits.status_code == 200
        assert {event["event_type"] for event in audits.json()} >= {
            "REQUEST_RECEIVED",
            "REQUEST_APPROVED",
        }



def test_rejection_is_terminal(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'rejection.db').as_posix()}"
    app = create_app(Settings(database_url=database_url, auto_create_schema=True, auth_mode="dev"))
    with TestClient(app) as client:
        client.post("/internal/v1/requests", headers=SERVICE, json=ingest_payload("request-2"))
        rejected = client.post(
            "/admin-api/v1/requests/request-2/reject",
            headers=APPROVER,
            json={"reason": "목적 불충분"},
        )
        assert rejected.status_code == 200
        assert rejected.json()["request"]["status"] == "REJECTED"
        assert rejected.json()["grant_status"] == "NOT_REQUESTED"


def test_user_cancellation_is_projected_to_control_db(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'cancellation.db').as_posix()}"
    app = create_app(Settings(database_url=database_url, auto_create_schema=True, auth_mode="dev"))
    with TestClient(app) as client:
        initial = ingest_payload("request-3")
        assert client.post("/internal/v1/requests", headers=SERVICE, json=initial).status_code == 200
        cancelled = {**initial, "status": "CANCELLED", "event_version": 2}
        projected = client.post("/internal/v1/requests", headers=SERVICE, json=cancelled)
        assert projected.status_code == 200
        assert projected.json()["status"] == "CANCELLED"
        assert projected.json()["event_version"] == 2

        cannot_approve = client.post(
            "/admin-api/v1/requests/request-3/approve", headers=APPROVER, json={}
        )
        assert cannot_approve.status_code == 409


def test_admin_demo_reset_orchestrates_and_deletes_control_data(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'approval-demo-reset.db').as_posix()}"
    monkeypatch.setattr(
        approval_main,
        "reset_demo_services",
        lambda _: {"grants": 1, "grant_audit_events": 1, "resources": 1, "requests": 1},
    )
    app = create_app(
        Settings(
            database_url=database_url,
            auto_create_schema=True,
            auth_mode="dev",
            enable_demo_reset=True,
        )
    )

    with TestClient(app) as client:
        client.post("/internal/v1/requests", headers=SERVICE, json=ingest_payload("reset-request-1"))
        client.post(
            "/admin-api/v1/requests/reset-request-1/approve",
            headers=APPROVER,
            json={"reason": "초기화 테스트"},
        )

        reset = client.post("/admin-api/v1/demo/reset", headers=APPROVER)
        assert reset.status_code == 200
        assert reset.json()["deleted"]["approval_requests"] == 1
        assert reset.json()["deleted"]["approval_decisions"] == 1
        assert reset.json()["deleted"]["request_audit_events"] == 2
        assert client.get("/admin-api/v1/requests?status=ALL", headers=APPROVER).json() == []
        assert client.get("/admin-api/v1/audit-events", headers=AUDITOR).json() == []


def test_admin_demo_seed_orchestrates_without_exposing_internal_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        approval_main,
        "seed_demo_request",
        lambda _: {"status": "seeded", "created": True, "delivery_status": "DELIVERED"},
    )
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'approval-demo-seed.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            enable_demo_reset=True,
        )
    )

    with TestClient(app) as client:
        response = client.post("/admin-api/v1/demo/seed", headers=APPROVER)
        assert response.status_code == 200
        assert response.json() == {
            "status": "seeded",
            "created": True,
            "delivery_status": "DELIVERED",
        }
        assert "request_id" not in response.json()


def test_monitoring_dashboard_waits_for_valid_grafana_url(tmp_path) -> None:
    pending_app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'monitoring-pending.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
        )
    )
    with TestClient(pending_app) as client:
        response = client.get("/admin-api/v1/monitoring-dashboard", headers=AUDITOR)
        assert response.status_code == 200
        assert response.json() == {
            "provider": "grafana",
            "status": "PENDING",
            "dashboard_url": None,
        }

    ready_app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'monitoring-ready.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            grafana_dashboard_url="https://grafana.example.com/d/iaas/operations?kiosk",
        )
    )
    with TestClient(ready_app) as client:
        response = client.get("/admin-api/v1/monitoring-dashboard", headers=AUDITOR)
        assert response.status_code == 200
        assert response.json()["status"] == "READY"
        assert response.json()["dashboard_url"].startswith("https://grafana.example.com/")

    invalid_app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'monitoring-invalid.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            grafana_dashboard_url="javascript:alert(1)",
        )
    )
    with TestClient(invalid_app) as client:
        response = client.get("/admin-api/v1/monitoring-dashboard", headers=AUDITOR)
        assert response.status_code == 200
        assert response.json()["status"] == "INVALID"
        assert response.json()["dashboard_url"] is None


def test_terraform_job_defers_grant_until_validated_apply_and_queues_destroy(
    tmp_path, monkeypatch
) -> None:
    grants: list[tuple[str, list[str], int]] = []

    def capture_grant(_, item, scopes, duration):
        grants.append((item.request_id, scopes, duration))
        return "DELIVERED", None

    monkeypatch.setattr(approval_main, "create_grant", capture_grant)
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'terraform-jobs.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            enable_provisioning_jobs=True,
        )
    )

    with TestClient(app) as client:
        assert client.post(
            "/internal/v1/requests", headers=SERVICE, json=ingest_payload("terraform-request")
        ).status_code == 200
        approved = client.post(
            "/admin-api/v1/requests/terraform-request/approve",
            headers=APPROVER,
            json={"reason": "Terraform 실행 승인"},
        )
        assert approved.status_code == 200
        assert approved.json()["grant_status"] == "DEFERRED"
        assert grants == []

        claimed = client.post(
            "/internal/v1/provisioning/jobs/claim",
            headers=RUNNER,
            json={"runner_id": "terraform-runner"},
        )
        assert claimed.status_code == 200
        job = claimed.json()
        assert job["operation"] == "APPLY"
        assert job["product_code"] == "DEV-OS-VM-S"
        assert job["product_version"] == 1
        assert job["module_name"] == "openstack-dev-vm-small"
        assert job["module_version"] == "1.0.0"
        assert job["artifact_digest"].startswith("sha256:")
        assert job["approved_by"] == "approver-1"
        assert job["input_values"]["project_name"] == "payment-api-test"
        assert set(job["input_values"]["required_tags"]) == {
            "RequestId",
            "OwnerId",
            "ProductId",
            "ExpiresAt",
            "ManagedBy",
            "Exposure",
        }
        assert job["status"] == "PLANNING"

        progress = client.post(
            f"/internal/v1/provisioning/jobs/{job['job_id']}/result",
            headers=RUNNER,
            json={"status": "PROVISIONING", "resource_id": job["resource_id"]},
        )
        assert progress.status_code == 200
        assert progress.json()["job"]["status"] == "APPLYING"
        assert grants == []

        invalid = client.post(
            f"/internal/v1/provisioning/jobs/{job['job_id']}/result",
            headers=RUNNER,
            json={"status": "RUNNING", "resource_id": job["resource_id"]},
        )
        assert invalid.status_code == 422
        assert grants == []

        running = client.post(
            f"/internal/v1/provisioning/jobs/{job['job_id']}/result",
            headers=RUNNER,
            json={
                "status": "RUNNING",
                "resource_id": job["resource_id"],
                "endpoint": "10.42.1.20",
                "details": {"actual_resource_id": "i-0123456789"},
                "outputs": {"primary_resource_id": "i-0123456789"},
                "validation_passed": True,
            },
        )
        assert running.status_code == 200
        assert running.json()["job"]["status"] == "SUCCEEDED"
        assert running.json()["grant_status"] == "DELIVERED"
        assert grants == [("terraform-request", ["openstack:vm:access"], 24)]

        destroy = client.post(
            "/internal/v1/provisioning/requests/terraform-request/destroy",
            headers=SERVICE,
            json={"trigger_status": "REVOKED", "reason": "Grant 회수"},
        )
        assert destroy.status_code == 200
        assert destroy.json()["operation"] == "DESTROY"
        assert destroy.json()["status"] == "QUEUED"


@pytest.mark.parametrize(
    "failure_code",
    ["BOOTSTRAP_VALIDATION_REQUIRED", "CONFIGURATION_FAILED", "ROLLBACK_FAILED"],
)
def test_runner_recovery_failures_are_recorded_and_retryable(
    tmp_path, failure_code: str
) -> None:
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / f'recovery-{failure_code}.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            enable_provisioning_jobs=True,
        )
    )
    request_id = f"recovery-{failure_code.lower().replace('_', '-')}"

    with TestClient(app) as client:
        assert client.post(
            "/internal/v1/requests", headers=SERVICE, json=ingest_payload(request_id)
        ).status_code == 200
        assert client.post(
            f"/admin-api/v1/requests/{request_id}/approve",
            headers=APPROVER,
            json={"reason": "복구 경계 검증"},
        ).status_code == 200
        claimed = client.post(
            "/internal/v1/provisioning/jobs/claim",
            headers=RUNNER,
            json={"runner_id": "terraform-runner"},
        ).json()
        failed = client.post(
            f"/internal/v1/provisioning/jobs/{claimed['job_id']}/result",
            headers=RUNNER,
            json={
                "status": "PROVISION_FAILED",
                "resource_id": claimed["resource_id"],
                "failure_code": failure_code,
                "details": {
                    "recovery_status": "ROLLBACK_FAILED",
                    "recovery_verification": "NOT_PROVEN",
                    "original_failure_code": "CONFIGURATION_FAILED",
                },
                "error": "sanitized recovery failure",
            },
        )
        assert failed.status_code == 200
        assert failed.json()["job"]["status"] == failure_code

        retry = client.post(
            f"/admin-api/v1/provisioning/jobs/{claimed['job_id']}/retry",
            headers=APPROVER,
        )
        assert retry.status_code == 200
        assert retry.json()["status"] == "QUEUED"

        audits = client.get(
            "/admin-api/v1/audit-events?aggregate_type=provisioning-job",
            headers=AUDITOR,
        ).json()
        result_event = next(
            value for value in audits if value["event_type"] == "TERRAFORM_APPLY_PROVISION_FAILED"
        )
        assert result_event["details"]["recovery_status"] == "ROLLBACK_FAILED"
        assert result_event["details"]["recovery_verification"] == "NOT_PROVEN"


@pytest.mark.parametrize(
    ("product_code", "parameters", "expected_scopes"),
    [
        (
            "DEV-OS-VM-S",
            {"project_name": "team-alpha-dev", "workload_purpose": "backend-integration-test"},
            ["openstack:vm:access"],
        ),
        (
            "DEV-OS-VM-M",
            {"project_name": "team-alpha-medium", "workload_purpose": "saas-application-development"},
            ["openstack:vm:access"],
        ),
        (
            "DEV-OS-VM-L",
            {"project_name": "team-alpha-large", "workload_purpose": "backend-integration-test"},
            ["openstack:vm:access"],
        ),
        (
            "DEV-OS-K3S-S",
            {"project_name": "team-alpha-k3s", "workload_purpose": "microservice-container-lab"},
            ["openstack:k3s:admin"],
        ),
        (
            "DEV-OS-K3S-M",
            {"project_name": "team-alpha-k3s-medium", "workload_purpose": "saas-deployment-test"},
            ["openstack:k3s:admin"],
        ),
    ],
)
def test_approval_uses_server_side_product_scopes(
    tmp_path, monkeypatch, product_code, parameters, expected_scopes
) -> None:
    captured: dict[str, list[str]] = {}

    def capture_grant(_, __, scopes, ___):
        captured["scopes"] = scopes
        return "DELIVERED", None

    monkeypatch.setattr(approval_main, "create_grant", capture_grant)
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / f'approval-{product_code}.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
        )
    )
    payload = {
        **ingest_payload(f"policy-{product_code}"),
        "product_code": product_code,
        "parameters": parameters,
    }
    runtime_specs = {
        "DEV-OS-VM-S": (2, 2, 30),
        "DEV-OS-VM-M": (2, 4, 50),
        "DEV-OS-VM-L": (2, 8, 80),
        "DEV-OS-K3S-S": (2, 4, 40),
        "DEV-OS-K3S-M": (2, 8, 80),
    }
    payload.update(zip(("cpu", "memory_gib", "storage_gib"), runtime_specs[product_code]))

    with TestClient(app) as client:
        assert client.post("/internal/v1/requests", headers=SERVICE, json=payload).status_code == 200
        approved = client.post(
            f"/admin-api/v1/requests/policy-{product_code}/approve",
            headers=APPROVER,
            json={"reason": "상품 정책 승인", "grant_scopes": ["admin:*"]},
        )
        assert approved.status_code == 200
        assert captured["scopes"] == expected_scopes
