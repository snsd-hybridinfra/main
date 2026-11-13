from __future__ import annotations

import copy

import pytest
from fastapi.testclient import TestClient

from request_api.blueprints import canonical_manifest_digest, resolve_blueprint
from request_api.config import Settings
from request_api.main import create_app
from request_api.saas_paas import (
    EXPECTED_COMPONENT_ORDER,
    FinancialSaaSBundleError,
    build_financial_saas_tenant_bundle,
)


def resolution(*, environment: str = "TEST", size: str = "SMALL") -> dict:
    return resolve_blueprint(
        blueprint_id="API_DEVELOPMENT_STACK",
        environment=environment,
        size=size,
        duration_hours=24,
        purpose="financial SaaS non-production integration lab",
    )


def test_tenant_bundle_is_deterministic_inert_and_digest_bound() -> None:
    first, first_digest = build_financial_saas_tenant_bundle(resolution())
    second, second_digest = build_financial_saas_tenant_bundle(resolution())

    assert first == second
    assert first_digest == second_digest
    assert first_digest.startswith("sha256:")
    assert first["namespace"].startswith("saas-test-")
    assert first["runtime_authorized"] is False
    assert first["deployable"] is False
    assert first["deployment_transaction"] == "ALL_OR_NOTHING"
    assert first["rollback_order"] == list(reversed(first["apply_order"]))


def test_tenant_baseline_is_restricted_private_and_secretless() -> None:
    bundle, _ = build_financial_saas_tenant_bundle(resolution())
    objects = bundle["objects"]
    kinds = [item["kind"] for item in objects]
    assert kinds == [
        "Namespace",
        "ResourceQuota",
        "LimitRange",
        "ServiceAccount",
        "Role",
        "RoleBinding",
        "NetworkPolicy",
        "NetworkPolicy",
        "NetworkPolicy",
        "NetworkPolicy",
    ]
    namespace = objects[0]
    assert namespace["metadata"]["labels"]["pod-security.kubernetes.io/enforce"] == "restricted"
    assert objects[3]["automountServiceAccountToken"] is False
    assert "Secret" not in kinds
    assert all(item.get("spec", {}).get("type") != "LoadBalancer" for item in objects)
    names = {item["metadata"]["name"] for item in objects if item["kind"] == "NetworkPolicy"}
    assert names == {
        "default-deny",
        "allow-cluster-dns",
        "allow-private-ingress",
        "allow-approved-data-services",
    }


def test_size_profile_changes_quota_without_changing_product_topology() -> None:
    small, _ = build_financial_saas_tenant_bundle(resolution(size="SMALL"))
    standard, _ = build_financial_saas_tenant_bundle(resolution(size="STANDARD"))
    small_quota = next(item for item in small["objects"] if item["kind"] == "ResourceQuota")
    standard_quota = next(item for item in standard["objects"] if item["kind"] == "ResourceQuota")
    assert small_quota["spec"]["hard"]["limits.cpu"] == "2"
    assert standard_quota["spec"]["hard"]["limits.cpu"] == "4"
    assert [item["kind"] for item in small["objects"]] == [item["kind"] for item in standard["objects"]]


def test_tamper_wrong_product_and_extra_secret_field_fail_closed() -> None:
    valid = resolution()
    attempts = []

    tampered_environment = copy.deepcopy(valid)
    tampered_environment["environment"] = "PROD"
    attempts.append(tampered_environment)

    wrong_product = resolve_blueprint(
        blueprint_id="WEB_APPLICATION_STACK",
        environment="TEST",
        size="SMALL",
        duration_hours=24,
        purpose="private web application integration lab",
    )
    attempts.append(wrong_product)

    injected_secret = copy.deepcopy(valid)
    injected_secret["secret"] = "must-not-be-accepted"
    attempts.append(injected_secret)

    reordered = copy.deepcopy(valid)
    reordered["component_plan"] = list(reversed(reordered["component_plan"]))
    attempts.append(reordered)

    for attempt in attempts:
        with pytest.raises(FinancialSaaSBundleError):
            build_financial_saas_tenant_bundle(attempt)

    assert [item["component_id"] for item in valid["component_plan"]] == EXPECTED_COMPONENT_ORDER


def test_service_only_endpoint_returns_inert_bundle_and_denies_user(tmp_path) -> None:
    app = create_app(
        Settings(
            database_url=f"sqlite+pysqlite:///{(tmp_path / 'saas-paas.db').as_posix()}",
            auto_create_schema=True,
            auth_mode="dev",
        )
    )
    payload = {
        "blueprint_id": "API_DEVELOPMENT_STACK",
        "environment": "TEST",
        "size": "SMALL",
        "duration_hours": 24,
        "purpose": "financial SaaS non-production integration lab",
    }
    with TestClient(app) as client:
        denied = client.post(
            "/internal/v1/financial-saas/tenant-bundle",
            headers={"X-Dev-User": "saas-user", "X-Dev-Roles": "user"},
            json=payload,
        )
        assert denied.status_code == 403

        allowed = client.post(
            "/internal/v1/financial-saas/tenant-bundle",
            headers={"X-Dev-User": "saas-service", "X-Dev-Roles": "service"},
            json=payload,
        )
        assert allowed.status_code == 200
        assert allowed.json()["bundle"]["deployable"] is False
        assert allowed.json()["bundle_digest"].startswith("sha256:")


@pytest.mark.parametrize(
    "profiles", [[], ["REAL_SECURITIES_ORDERS"], ["SECURITIES_PORTFOLIO_RISK_SIMULATION"]]
)
def test_rehashed_unapproved_business_domain_profiles_fail_closed(profiles) -> None:
    source = resolution()
    source.pop("manifest_digest")
    source["business_domain_profiles"] = profiles
    source["manifest_digest"] = canonical_manifest_digest(source)
    with pytest.raises(FinancialSaaSBundleError, match="business domain profiles mismatch"):
        build_financial_saas_tenant_bundle(source)
