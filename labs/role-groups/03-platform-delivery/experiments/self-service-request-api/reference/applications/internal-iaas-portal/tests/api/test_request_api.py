from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from request_api.config import Settings as RequestSettings
from request_api.main import create_app


USER = {"X-Dev-User": "user-1", "X-Dev-Roles": "user"}
OTHER_USER = {"X-Dev-User": "user-2", "X-Dev-Roles": "user"}
SERVICE = {"X-Dev-User": "approval-api", "X-Dev-Roles": "service"}


def Settings(**values):
    values.setdefault("enable_legacy_execution_profile_requests", True)
    return RequestSettings(**values)


def request_payload() -> dict:
    return {
        "product_code": "DEV-OS-VM-S",
        "cpu": 0,
        "memory_gib": 0,
        "storage_gib": 0,
        "duration_hours": 24,
        "purpose": "API MVP 기능 검증",
        "parameters": {
            "project_name": "payment-api-test",
            "workload_purpose": "saas-application-development",
        },
    }


def test_catalog_and_idempotent_request_creation(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'request.db').as_posix()}"
    app = create_app(Settings(database_url=database_url, auto_create_schema=True, auth_mode="dev"))

    with TestClient(app) as client:
        catalog = client.get("/api/v1/catalog", headers=USER)
        assert catalog.status_code == 200
        assert [item["blueprint_id"] for item in catalog.json()] == [
            "DEVELOPER_WORKSPACE",
            "SECURE_ADMIN_WORKSPACE",
            "WEB_APPLICATION_STACK",
            "API_DEVELOPMENT_STACK",
            "VM_APPLICATION_STACK",
            "AI_AGENT_SANDBOX",
            "DATA_PROCESSING_LAB",
            "SYNTHETIC_MARKET_DATA_LAB",
        ]
        assert catalog.json()[0]["network_profile"] == "PRIVATE_DEVELOPER_ACCESS"
        assert catalog.json()[1]["allowed_duration_hours"] == [4, 8]

        denied_profiles = client.get("/internal/v1/execution-profiles", headers=USER)
        assert denied_profiles.status_code == 403
        profiles = client.get("/internal/v1/execution-profiles", headers=SERVICE)
        assert profiles.status_code == 200
        assert {item["product_code"] for item in profiles.json()} == {
            "DEV-OS-VM-S",
            "DEV-OS-VM-M",
            "DEV-OS-VM-L",
            "DEV-OS-K3S-S",
            "DEV-OS-K3S-M",
        }

        headers = {**USER, "Idempotency-Key": "request-create-1"}
        first = client.post("/api/v1/requests", json=request_payload(), headers=headers)
        second = client.post("/api/v1/requests", json=request_payload(), headers=headers)

        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["request_id"] == second.json()["request_id"]
        assert first.json()["status"] == "PENDING"
        assert first.json()["event_version"] == 1
        assert (first.json()["cpu"], first.json()["memory_gib"], first.json()["storage_gib"]) == (
            2,
            2,
            30,
        )

        hidden = client.get(f"/api/v1/requests/{first.json()['request_id']}", headers=OTHER_USER)
        assert hidden.status_code == 404


def test_request_projection_state_machine_ignores_stale_events(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'request-state.db').as_posix()}"
    app = create_app(Settings(database_url=database_url, auto_create_schema=True, auth_mode="dev"))

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/requests",
            json=request_payload(),
            headers={**USER, "Idempotency-Key": "request-state-1"},
        ).json()
        request_id = created["request_id"]

        approved = client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": "approval-event-2",
                "event_version": 2,
                "status": "APPROVED",
            },
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "APPROVED"

        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        granted = client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": "grant-event-3",
                "event_version": 3,
                "status": "GRANTED",
                "grant_id": "grant-1",
                "grant_expires_at": expires_at.isoformat(),
            },
        )
        assert granted.status_code == 200
        assert granted.json()["status"] == "GRANTED"

        stale = client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": "late-approval-event",
                "event_version": 2,
                "status": "APPROVED",
            },
        )
        assert stale.status_code == 200
        assert stale.json()["status"] == "GRANTED"
        assert stale.json()["event_version"] == 3

        gap = client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": "gap-event",
                "event_version": 5,
                "status": "REVOKED",
            },
        )
        assert gap.status_code == 409


def test_resource_callback_tracks_state_without_overwriting_grant_status(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'request-resource.db').as_posix()}"
    app = create_app(Settings(database_url=database_url, auto_create_schema=True, auth_mode="dev"))

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/requests",
            json=request_payload(),
            headers={**USER, "Idempotency-Key": "request-resource-1"},
        ).json()
        request_id = created["request_id"]
        client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={"idempotency_key": "approval-2", "event_version": 2, "status": "APPROVED"},
        )
        client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": "grant-3",
                "event_version": 3,
                "status": "GRANTED",
                "grant_id": "grant-resource-1",
                "grant_expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            },
        )

        provisioning = client.post(
            f"/internal/v1/requests/{request_id}/resource",
            headers=SERVICE,
            json={
                "resource_id": "terraform-vm-1",
                "status": "PROVISIONING",
                "event_version": 1,
            },
        )
        assert provisioning.status_code == 200
        assert provisioning.json()["status"] == "PROVISIONING"

        running = client.post(
            f"/internal/v1/requests/{request_id}/resource",
            headers=SERVICE,
            json={
                "resource_id": "terraform-vm-1",
                "status": "RUNNING",
                "endpoint": "10.10.20.30",
                "event_version": 2,
            },
        )
        assert running.status_code == 200
        assert running.json()["status"] == "RUNNING"

        request_view = client.get(f"/api/v1/requests/{request_id}", headers=USER).json()
        assert request_view["status"] == "GRANTED"
        assert request_view["resource_status"] == "RUNNING"
        resources = client.get("/api/v1/resources", headers=USER).json()
        assert resources[0]["resource_id"] == "terraform-vm-1"
        assert resources[0]["endpoint"] == "10.10.20.30"


def test_dev_mock_provisioner_creates_and_terminates_demo_resource(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'request-mock-resource.db').as_posix()}"
    app = create_app(
        Settings(
            database_url=database_url,
            auto_create_schema=True,
            auth_mode="dev",
            enable_mock_provisioner=True,
            mock_provision_delay_seconds=0,
        )
    )

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/requests",
            json=request_payload(),
            headers={**USER, "Idempotency-Key": "request-mock-resource-1"},
        ).json()
        request_id = created["request_id"]
        client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={"idempotency_key": "mock-approval-2", "event_version": 2, "status": "APPROVED"},
        )
        granted = client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": "mock-grant-3",
                "event_version": 3,
                "status": "GRANTED",
                "grant_id": "mock-grant-1",
                "grant_expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            },
        )
        assert granted.status_code == 200

        resources = client.get("/api/v1/resources", headers=USER).json()
        assert len(resources) == 1
        assert resources[0]["resource_id"].startswith("DEMO-OS-VM-")
        assert resources[0]["status"] == "RUNNING"
        assert resources[0]["endpoint"].startswith("10.250.")

        revoked = client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": "mock-revoke-4",
                "event_version": 4,
                "status": "REVOKED",
                "grant_id": "mock-grant-1",
            },
        )
        assert revoked.status_code == 200

        resources = client.get("/api/v1/resources", headers=USER).json()
        assert resources[0]["status"] == "TERMINATED"
        assert resources[0]["endpoint"] is None
        request_view = client.get(f"/api/v1/requests/{request_id}", headers=USER).json()
        assert request_view["status"] == "REVOKED"
        assert request_view["resource_status"] == "TERMINATED"


def test_demo_reset_deletes_requests_and_resources_only_when_enabled(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'request-demo-reset.db').as_posix()}"
    app = create_app(
        Settings(
            database_url=database_url,
            auto_create_schema=True,
            auth_mode="dev",
            enable_mock_provisioner=True,
            enable_demo_reset=True,
            mock_provision_delay_seconds=0,
        )
    )

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/requests",
            json=request_payload(),
            headers={**USER, "Idempotency-Key": "request-demo-reset-1"},
        ).json()
        request_id = created["request_id"]
        client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={"idempotency_key": "reset-approval-2", "event_version": 2, "status": "APPROVED"},
        )
        client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": "reset-grant-3",
                "event_version": 3,
                "status": "GRANTED",
                "grant_id": "reset-grant-1",
                "grant_expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            },
        )

        reset = client.post("/internal/v1/demo/reset", headers=SERVICE)
        assert reset.status_code == 200
        assert reset.json()["deleted"] == {"resources": 1, "requests": 1}
        assert client.get("/api/v1/requests", headers=USER).json() == []
        assert client.get("/api/v1/resources", headers=USER).json() == []

    disabled_app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'request-demo-reset-disabled.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
        )
    )
    with TestClient(disabled_app) as client:
        assert client.post("/internal/v1/demo/reset", headers=SERVICE).status_code == 404


def test_demo_seed_creates_one_idempotent_pending_request(tmp_path) -> None:
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'request-demo-seed.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            enable_demo_reset=True,
        )
    )

    with TestClient(app) as client:
        seeded = client.post("/internal/v1/demo/seed", headers=SERVICE)
        assert seeded.status_code == 200
        assert seeded.json() == {
            "status": "seeded",
            "created": True,
            "delivery_status": "SKIPPED",
        }

        duplicate = client.post("/internal/v1/demo/seed", headers=SERVICE)
        assert duplicate.status_code == 200
        assert duplicate.json()["status"] == "existing"
        assert duplicate.json()["created"] is False

        requests = client.get(
            "/api/v1/requests",
            headers={"X-Dev-User": "demo-user", "X-Dev-Roles": "user"},
        ).json()
        assert len(requests) == 1
        assert requests[0]["product_code"] == "DEV-OS-VM-S"
        assert requests[0]["status"] == "PENDING"
        assert requests[0]["purpose"] == "MVP 핵심 시연용 사내 SaaS 개발 VM"


@pytest.mark.parametrize(
    ("product_code", "parameters", "runtime_spec", "id_prefix", "detail_key"),
    [
        (
            "DEV-OS-VM-S",
            {"project_name": "team-alpha-dev", "workload_purpose": "backend-integration-test"},
            (2, 2, 30),
            "DEMO-OS-VM-",
            "cloud",
        ),
        (
            "DEV-OS-VM-M",
            {"project_name": "team-alpha-medium", "workload_purpose": "saas-application-development"},
            (2, 4, 50),
            "DEMO-OS-VM-",
            "cloud",
        ),
        (
            "DEV-OS-VM-L",
            {"project_name": "team-alpha-large", "workload_purpose": "backend-integration-test"},
            (2, 8, 80),
            "DEMO-OS-VM-",
            "cloud",
        ),
        (
            "DEV-OS-K3S-S",
            {"project_name": "team-alpha-k3s", "workload_purpose": "microservice-container-lab"},
            (2, 4, 40),
            "DEMO-OS-K3S-",
            "bootstrap_status",
        ),
        (
            "DEV-OS-K3S-M",
            {"project_name": "team-alpha-k3s-medium", "workload_purpose": "saas-deployment-test"},
            (2, 8, 80),
            "DEMO-OS-K3S-",
            "bootstrap_status",
        ),
    ],
)
def test_fixed_product_mock_provisioning_and_termination(
    tmp_path, product_code, parameters, runtime_spec, id_prefix, detail_key
) -> None:
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / f'{product_code}.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
            enable_mock_provisioner=True,
            mock_provision_delay_seconds=0,
        )
    )
    payload = {
        "product_code": product_code,
        "cpu": 0,
        "memory_gib": 0,
        "storage_gib": 0,
        "duration_hours": 24,
        "purpose": "고정 상품 모의 프로비저닝 검증",
        "parameters": parameters,
    }

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/requests",
            json=payload,
            headers={**USER, "Idempotency-Key": f"secondary-{product_code}"},
        )
        assert created.status_code == 201
        request_id = created.json()["request_id"]
        assert created.json()["parameters"] == parameters
        assert (
            created.json()["cpu"],
            created.json()["memory_gib"],
            created.json()["storage_gib"],
        ) == runtime_spec

        client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={"idempotency_key": "approval-2", "event_version": 2, "status": "APPROVED"},
        )
        granted = client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": "grant-3",
                "event_version": 3,
                "status": "GRANTED",
                "grant_id": "grant-secondary",
                "grant_expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            },
        )
        assert granted.status_code == 200
        resources = client.get("/api/v1/resources", headers=USER).json()
        assert len(resources) == 1
        assert resources[0]["resource_id"].startswith(id_prefix)
        assert resources[0]["resource_type"] == product_code
        assert resources[0]["status"] == "RUNNING"
        assert detail_key in resources[0]["details"]

        revoked = client.post(
            f"/internal/v1/requests/{request_id}/status",
            headers=SERVICE,
            json={
                "idempotency_key": "revoke-4",
                "event_version": 4,
                "status": "REVOKED",
                "grant_id": "grant-secondary",
            },
        )
        assert revoked.status_code == 200
        assert client.get("/api/v1/resources", headers=USER).json()[0]["status"] == "TERMINATED"


def test_product_parameters_reject_unapproved_values(tmp_path) -> None:
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'invalid-product-parameters.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
        )
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/requests",
            headers={**USER, "Idempotency-Key": "invalid-project"},
            json={
                "product_code": "DEV-OS-VM-S",
                "cpu": 0,
                "memory_gib": 0,
                "storage_gib": 0,
                "duration_hours": 24,
                "purpose": "승인되지 않은 프로젝트명 검증",
                "parameters": {
                    "project_name": "SYSTEM:ADMIN",
                    "workload_purpose": "saas-application-development",
                },
            },
        )
        assert response.status_code == 422


def test_product_rejects_user_managed_provider_spec_and_unapproved_duration(tmp_path) -> None:
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'fixed-product-policy.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
        )
    )
    with TestClient(app) as client:
        custom_spec = {**request_payload(), "cpu": 4}
        response = client.post(
            "/api/v1/requests",
            headers={**USER, "Idempotency-Key": "custom-spec"},
            json=custom_spec,
        )
        assert response.status_code == 422

        allowed_short_duration = {**request_payload(), "duration_hours": 4}
        response = client.post(
            "/api/v1/requests",
            headers={**USER, "Idempotency-Key": "allowed-short-duration"},
            json=allowed_short_duration,
        )
        assert response.status_code == 201

        invalid_duration = {**request_payload(), "duration_hours": 12}
        response = client.post(
            "/api/v1/requests",
            headers={**USER, "Idempotency-Key": "invalid-duration"},
            json=invalid_duration,
        )
        assert response.status_code == 422


def test_product_limits_each_user_to_one_active_resource(tmp_path) -> None:
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'resource-limit.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
        )
    )
    with TestClient(app) as client:
        first = client.post(
            "/api/v1/requests",
            headers={**USER, "Idempotency-Key": "first-resource"},
            json=request_payload(),
        )
        assert first.status_code == 201
        second = client.post(
            "/api/v1/requests",
            headers={**USER, "Idempotency-Key": "second-resource"},
            json=request_payload(),
        )
        assert second.status_code == 409
