from __future__ import annotations

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]


def _documents(path: Path) -> list[dict]:
    return [document for document in yaml.safe_load_all(path.read_text(encoding="utf-8")) if document]


@pytest.mark.kubernetes
def test_workloads_use_restricted_container_settings_and_digest() -> None:
    paths = [
        ROOT / "kubernetes/edge-gateway/deployment.yaml",
        ROOT / "kubernetes/user-portal/deployment.yaml",
        ROOT / "kubernetes/admin-portal/deployment.yaml",
        ROOT / "kubernetes/request-api/deployment.yaml",
        ROOT / "kubernetes/approval-api/deployment.yaml",
        ROOT / "kubernetes/grant-api/deployment.yaml",
        ROOT / "kubernetes/terraform-runner/deployment.yaml",
    ]
    for path in paths:
        deployment = _documents(path)[0]
        pod = deployment["spec"]["template"]["spec"]
        assert pod["automountServiceAccountToken"] is False
        assert pod["enableServiceLinks"] is False
        assert pod["securityContext"]["runAsNonRoot"] is True
        assert pod["securityContext"]["seccompProfile"]["type"] == "RuntimeDefault"
        for container in pod["containers"]:
            security = container["securityContext"]
            assert security["allowPrivilegeEscalation"] is False
            assert security["readOnlyRootFilesystem"] is True
            assert security["capabilities"]["drop"] == ["ALL"]
            assert "@sha256:" in container["image"]
            assert ":latest" not in container["image"]


@pytest.mark.kubernetes
def test_production_config_disables_dev_auth_and_auto_schema() -> None:
    expected_revisions = {
        ROOT / "kubernetes/request-api/configmap.yaml": "0006_portal_usage",
        ROOT / "kubernetes/approval-api/configmap.yaml": "0003_provisioning_jobs",
        ROOT / "kubernetes/grant-api/configmap.yaml": "0003_provisioning_jobs",
    }
    for path, expected_revision in expected_revisions.items():
        config = _documents(path)[0]["data"]
        assert config["AUTH_MODE"] == "oidc"
        assert config["AUTO_CREATE_SCHEMA"] == "false"
        assert config["REQUIRED_DB_REVISION"] == expected_revision


@pytest.mark.kubernetes
def test_default_deny_and_no_plaintext_secret_manifests() -> None:
    policies = []
    for path in (ROOT / "kubernetes").rglob("*.yaml"):
        for document in _documents(path):
            assert document.get("kind") != "Secret", f"plaintext Secret manifest: {path}"
            if document.get("kind") == "NetworkPolicy":
                policies.append(document)
    namespaces = {
        policy["metadata"]["namespace"]
        for policy in policies
        if policy["metadata"]["name"] == "default-deny-all"
        and policy["spec"]["podSelector"] == {}
        and set(policy["spec"]["policyTypes"]) == {"Ingress", "Egress"}
    }
    assert {"edge-system", "user-service", "admin-service", "control-service"}.issubset(
        namespaces
    )


@pytest.mark.kubernetes
def test_identity_products_are_not_implemented_in_owned_security_path() -> None:
    keycloak_dir = ROOT / "security/keycloak"
    assert not any(path.is_file() for path in keycloak_dir.rglob("*"))
    edge_service = _documents(ROOT / "kubernetes/edge-gateway/service.yaml")[0]
    assert edge_service["spec"]["type"] == "NodePort"


@pytest.mark.kubernetes
def test_grant_expiry_cronjob_is_restricted_and_uses_oauth() -> None:
    cronjob = _documents(ROOT / "kubernetes/grant-api/expiry-cronjob.yaml")[0]
    assert cronjob["spec"]["concurrencyPolicy"] == "Forbid"
    pod = cronjob["spec"]["jobTemplate"]["spec"]["template"]["spec"]
    assert pod["serviceAccountName"] == "grant-expiry"
    assert pod["automountServiceAccountToken"] is False
    assert pod["securityContext"]["runAsNonRoot"] is True
    assert pod["securityContext"]["seccompProfile"]["type"] == "RuntimeDefault"
    container = pod["containers"][0]
    assert "@sha256:" in container["image"]
    assert container["securityContext"]["readOnlyRootFilesystem"] is True
    assert container["securityContext"]["capabilities"]["drop"] == ["ALL"]
    env = {item["name"]: item.get("value") for item in container["env"]}
    assert env["AUTH_MODE"] == "oidc"
    assert env["SERVICE_SCOPE"] == "grant:write"
    assert env["SERVICE_CLIENT_SECRET_FILE"] == "/etc/service-oauth/client-secret"
    assert "DATABASE_URL" not in env
