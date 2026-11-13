from __future__ import annotations

from copy import deepcopy

from fastapi.testclient import TestClient

import request_api.main as request_main
from approval_api.config import Settings as ApprovalSettings
from approval_api.main import create_app as create_approval_app
from request_api.blueprints import resolve_blueprint
from request_api.config import Settings as RequestSettings
from request_api.main import create_app as create_request_app
from terraform_runner.config import Settings as RunnerSettings
from terraform_runner.executor import Executor


USER = {"X-Dev-User": "composite-user", "X-Dev-Roles": "user"}
SERVICE = {"X-Dev-User": "request-api", "X-Dev-Roles": "service"}
APPROVER = {"X-Dev-User": "composite-approver", "X-Dev-Roles": "approver"}
RUNNER = {"X-Dev-User": "terraform-runner", "X-Dev-Roles": "service"}


def test_resolved_manifest_reaches_runner_and_tampering_is_denied(
    tmp_path, monkeypatch
) -> None:
    request_app = create_request_app(
        RequestSettings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'request.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
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

    with TestClient(request_app) as request_client, TestClient(
        approval_app
    ) as approval_client:

        def deliver_to_approval(_, item):
            resolution = resolve_blueprint(
                blueprint_id=item.parameters["_blueprint_id"],
                environment=item.parameters["_blueprint_environment"],
                size=item.parameters["_blueprint_size"],
                duration_hours=item.duration_hours,
                purpose=item.purpose,
            )
            response = approval_client.post(
                "/internal/v1/requests",
                headers=SERVICE,
                json={
                    "request_id": item.request_id,
                    "idempotency_key": item.idempotency_key,
                    "requester_id": item.owner_id,
                    "product_code": item.product_code,
                    "cpu": item.cpu,
                    "memory_gib": item.memory_gib,
                    "storage_gib": item.storage_gib,
                    "duration_hours": item.duration_hours,
                    "purpose": item.purpose,
                    "parameters": item.parameters,
                    "blueprint_id": resolution["blueprint_id"],
                    "manifest_digest": resolution["manifest_digest"],
                    "resolved_manifest": resolution,
                    "status": item.status,
                    "event_version": item.event_version,
                    "retry_count": item.retry_count,
                    "updated_at": item.updated_at.isoformat(),
                },
            )
            return ("DELIVERED", None) if response.is_success else ("FAILED", response.text)

        monkeypatch.setattr(request_main, "send_to_approval", deliver_to_approval)
        created = request_client.post(
            "/api/v1/blueprint-requests",
            headers={**USER, "Idempotency-Key": "composite-e2e-1"},
            json={
                "blueprint_id": "VM_APPLICATION_STACK",
                "environment": "TEST",
                "size": "STANDARD",
                "duration_hours": 24,
                "purpose": "composite manifest approval and runner validation",
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["delivery_status"] == "DELIVERED"

        request_id = created.json()["request_id"]
        approved = approval_client.post(
            f"/admin-api/v1/requests/{request_id}/approve",
            headers=APPROVER,
            json={"reason": "bounded local composite-flow validation"},
        )
        assert approved.status_code == 200, approved.text
        assert approved.json()["grant_status"] == "DEFERRED"

        job = approval_client.post(
            "/internal/v1/provisioning/jobs/claim",
            headers=RUNNER,
            json={"runner_id": "terraform-runner"},
        ).json()
        values = job["input_values"]
        assert values["blueprint_id"] == "VM_APPLICATION_STACK"
        assert values["manifest_digest"] == created.json()["manifest_digest"]
        assert values["resolved_manifest"]["selected_execution_profile"] == "DEV-OS-VM-M"
        assert values["required_tags"]["ManifestDigest"] == values["manifest_digest"]

        reports: list[dict] = []
        Executor(RunnerSettings(runner_mode="mock", mock_delay_seconds=0)).run(
            job, reports.append
        )
        assert reports[-1]["status"] == "RUNNING"
        assert reports[-1]["validation_passed"] is True

        tampered = deepcopy(job)
        tampered["input_values"]["resolved_manifest"]["purpose"] = "tampered purpose"
        denied_reports: list[dict] = []
        Executor(RunnerSettings(runner_mode="mock", mock_delay_seconds=0)).run(
            tampered, denied_reports.append
        )
        assert denied_reports[-1]["status"] == "PROVISION_FAILED"
        assert denied_reports[-1]["failure_code"] == "POLICY_DENIED"
