from __future__ import annotations

from fastapi.testclient import TestClient

from request_api.config import Settings
from request_api.main import create_app


USER = {"X-Dev-User": "blueprint-user", "X-Dev-Roles": "user"}
SERVICE = {"X-Dev-User": "blueprint-service", "X-Dev-Roles": "service"}


def app_for(tmp_path):
    return create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'blueprints.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
        )
    )


def vm_payload() -> dict:
    return {
        "blueprint_id": "VM_APPLICATION_STACK",
        "environment": "DEV",
        "size": "SMALL",
        "duration_hours": 24,
        "purpose": "private application integration lab",
    }


def test_public_catalog_contains_only_eight_blueprints(tmp_path) -> None:
    with TestClient(app_for(tmp_path)) as client:
        response = client.get("/api/v1/blueprints", headers=USER)
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 8
        assert {item["blueprint_id"] for item in items} == {
            "DEVELOPER_WORKSPACE",
            "SECURE_ADMIN_WORKSPACE",
            "WEB_APPLICATION_STACK",
            "API_DEVELOPMENT_STACK",
            "VM_APPLICATION_STACK",
            "AI_AGENT_SANDBOX",
            "DATA_PROCESSING_LAB",
            "SYNTHETIC_MARKET_DATA_LAB",
        }
        assert all("product_code" not in item for item in items)
        assert all("provider_binding" not in item for item in items)
        assert all("components" not in item for item in items)
        assert all(item["summary"] for item in items)
        profiles = {item["blueprint_id"]: item["business_domain_profiles"] for item in items}
        assert profiles["API_DEVELOPMENT_STACK"] == [
            "SECURITIES_ORDER_API_SIMULATION",
            "SECURITIES_POST_TRADE_SIMULATION",
        ]
        assert profiles["DATA_PROCESSING_LAB"] == [
            "SECURITIES_PORTFOLIO_RISK_SIMULATION"
        ]
        assert profiles["SYNTHETIC_MARKET_DATA_LAB"] == [
            "SECURITIES_MARKET_DATA_SIMULATION"
        ]


def test_direct_execution_profile_request_is_disabled_by_default(tmp_path) -> None:
    with TestClient(app_for(tmp_path)) as client:
        response = client.post(
            "/api/v1/requests",
            headers={**USER, "Idempotency-Key": "raw-profile-denied"},
            json={
                "product_code": "DEV-OS-VM-S",
                "duration_hours": 24,
                "purpose": "attempted direct profile request",
                "parameters": {
                    "project_name": "raw-profile",
                    "workload_purpose": "saas-application-development",
                },
            },
        )
        assert response.status_code == 403
        assert "blueprint request" in response.json()["detail"]


def test_public_resolution_is_deterministic_and_hides_internal_profile(tmp_path) -> None:
    with TestClient(app_for(tmp_path)) as client:
        first = client.post("/api/v1/blueprints/resolve", headers=USER, json=vm_payload())
        second = client.post("/api/v1/blueprints/resolve", headers=USER, json=vm_payload())
        assert first.status_code == 200
        assert first.json() == second.json()
        assert first.json()["resolution_status"] == "RESOLVED_LOCAL"
        assert "components" not in first.json()
        assert "blocking_components" not in first.json()
        assert "blocking_gates" not in first.json()
        assert first.json()["runtime_authorized"] is False
        assert first.json()["manifest_digest"].startswith("sha256:")
        assert "selected_execution_profile" not in first.json()


def test_securities_profile_is_digest_bound_and_not_user_selectable(tmp_path) -> None:
    payload = {
        "blueprint_id": "API_DEVELOPMENT_STACK",
        "environment": "DEV",
        "size": "SMALL",
        "duration_hours": 24,
        "purpose": "synthetic securities order API development",
    }
    with TestClient(app_for(tmp_path)) as client:
        response = client.post("/api/v1/blueprints/resolve", headers=USER, json=payload)
        assert response.status_code == 200
        assert response.json()["business_domain_profiles"] == [
            "SECURITIES_ORDER_API_SIMULATION",
            "SECURITIES_POST_TRADE_SIMULATION",
        ]
        attempted_override = client.post(
            "/api/v1/blueprints/resolve",
            headers=USER,
            json={**payload, "business_domain_profiles": ["REAL_SECURITIES_ORDERS"]},
        )
        assert attempted_override.status_code == 422


def test_internal_resolution_pins_profile_and_reverse_rollback(tmp_path) -> None:
    with TestClient(app_for(tmp_path)) as client:
        denied = client.post(
            "/internal/v1/blueprints/resolve", headers=USER, json=vm_payload()
        )
        assert denied.status_code == 403

        resolved = client.post(
            "/internal/v1/blueprints/resolve", headers=SERVICE, json=vm_payload()
        )
        assert resolved.status_code == 200
        body = resolved.json()
        assert body["selected_execution_profile"] == "DEV-OS-VM-S"
        assert body["deployment_transaction"] == "ALL_OR_NOTHING"
        assert body["rollback_component_order"] == [
            "OPERATIONS_PROFILE",
            "NETWORK_POLICY",
            "COMPUTE_VM",
        ]


def test_blueprint_request_persists_manifest_identity_without_profile_exposure(tmp_path) -> None:
    with TestClient(app_for(tmp_path)) as client:
        headers = {**USER, "Idempotency-Key": "blueprint-request-1"}
        first = client.post("/api/v1/blueprint-requests", headers=headers, json=vm_payload())
        second = client.post("/api/v1/blueprint-requests", headers=headers, json=vm_payload())
        assert first.status_code == 201
        assert first.json() == second.json()
        assert first.json()["blueprint_id"] == "VM_APPLICATION_STACK"
        assert first.json()["manifest_digest"].startswith("sha256:")
        assert "product_code" not in first.json()

        projected = client.get(
            f"/api/v1/requests/{first.json()['request_id']}", headers=USER
        )
        assert projected.status_code == 200
        assert projected.json()["product_code"] is None
        assert projected.json()["blueprint_id"] == "VM_APPLICATION_STACK"
        assert projected.json()["blueprint_environment"] == "DEV"
        assert projected.json()["blueprint_size"] == "SMALL"
        assert all(not key.startswith("_") for key in projected.json()["parameters"])

        changed = client.post(
            "/api/v1/blueprint-requests",
            headers=headers,
            json={**vm_payload(), "purpose": "different application integration lab"},
        )
        assert changed.status_code == 409


def test_blocked_blueprint_cannot_create_request(tmp_path) -> None:
    payload = {
        "blueprint_id": "DEVELOPER_WORKSPACE",
        "environment": "TEST",
        "size": "STANDARD",
        "duration_hours": 8,
        "purpose": "isolated developer desktop lab",
    }
    with TestClient(app_for(tmp_path)) as client:
        response = client.post(
            "/api/v1/blueprint-requests",
            headers={**USER, "Idempotency-Key": "blocked-vdi-request"},
            json=payload,
        )
        assert response.status_code == 409
        assert "VDI_WORKSPACE" in response.json()["detail"]
        assert client.get("/api/v1/requests", headers=USER).json() == []


def test_resolver_rejects_out_of_policy_and_free_form_inputs(tmp_path) -> None:
    invalid_payloads = [
        {**vm_payload(), "environment": "PROD"},
        {**vm_payload(), "size": "XLARGE"},
        {**vm_payload(), "duration_hours": 12},
        {**vm_payload(), "components": ["COMPUTE_VM"]},
        {**vm_payload(), "product_code": "DEV-OS-VM-S"},
        {**vm_payload(), "provider_id": "private-provider-id"},
        {**vm_payload(), "hcl": "resource {}"},
    ]
    with TestClient(app_for(tmp_path)) as client:
        for payload in invalid_payloads:
            response = client.post("/api/v1/blueprints/resolve", headers=USER, json=payload)
            assert response.status_code == 422


def test_vdi_blueprint_remains_blocked_without_provider_adapter(tmp_path) -> None:
    payload = {
        "blueprint_id": "DEVELOPER_WORKSPACE",
        "environment": "TEST",
        "size": "STANDARD",
        "duration_hours": 8,
        "purpose": "isolated developer desktop lab",
    }
    with TestClient(app_for(tmp_path)) as client:
        response = client.post("/internal/v1/blueprints/resolve", headers=SERVICE, json=payload)
        assert response.status_code == 200
        assert response.json()["resolution_status"] == "BLOCKED_UNIMPLEMENTED_COMPONENTS"
        assert response.json()["blocking_components"] == [
            "VDI_WORKSPACE",
            "OBJECT_STORAGE",
        ]


def test_ai_agent_sandbox_remains_fail_closed_without_storage_adapter(tmp_path) -> None:
    payload = {
        "blueprint_id": "AI_AGENT_SANDBOX",
        "environment": "TEST",
        "size": "STANDARD",
        "duration_hours": 4,
        "purpose": "bounded asynchronous repository maintenance task",
    }
    with TestClient(app_for(tmp_path)) as client:
        public = client.post("/api/v1/blueprints/resolve", headers=USER, json=payload)
        assert public.status_code == 200
        assert "components" not in public.json()
        assert "blocking_components" not in public.json()
        assert "blocking_gates" not in public.json()

        response = client.post("/internal/v1/blueprints/resolve", headers=SERVICE, json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["network_profile"] == "AI_AGENT_EGRESS_BROKERED"
        assert body["resolution_status"] == "BLOCKED_UNIMPLEMENTED_COMPONENTS"
        assert body["blocking_components"] == ["OBJECT_STORAGE"]
        assert body["blocking_gates"] == [
            "SANDBOX_RUNTIME_CLASS",
            "TASK_CREDENTIAL_BROKER",
            "FQDN_EGRESS_BROKER",
            "AGENT_BUDGET_ENFORCER",
            "APPROVAL_RESUME_CONTROLLER",
            "SANITIZED_TRACE_PIPELINE",
        ]
        assert body["runtime_authorized"] is False
