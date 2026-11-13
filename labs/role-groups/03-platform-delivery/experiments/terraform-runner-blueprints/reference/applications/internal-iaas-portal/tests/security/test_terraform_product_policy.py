from __future__ import annotations

import json
from pathlib import Path

from approval_api.provisioning import TERRAFORM_PRODUCTS
from request_api.catalog import CATALOG_BY_CODE
from terraform_runner.executor import ALLOWED_MODULES, module_content_digest


ROOT = Path(__file__).resolve().parents[2]
MODULE_ROOT = ROOT / "terraform/modules"
ANSIBLE_ROOT = ROOT / "ansible"
K3S_CONFIGURATION_DIGEST = (
    "sha256:27ae92895d90f49a118c2fa5db7e897173e15fa002796090765872769c4a6e18"
)


def test_catalog_runner_and_module_artifacts_are_identical() -> None:
    canonical = json.loads((ROOT / "terraform/catalog.json").read_text(encoding="utf-8"))[
        "products"
    ]
    assert set(canonical) == {
        "DEV-OS-VM-S",
        "DEV-OS-VM-M",
        "DEV-OS-VM-L",
        "DEV-OS-K3S-S",
        "DEV-OS-K3S-M",
    }
    assert {path.name for path in MODULE_ROOT.iterdir() if path.is_dir()} == {
        "openstack-dev-vm-small",
        "openstack-dev-vm-medium",
        "openstack-dev-vm-large",
        "openstack-dev-k3s-small",
        "openstack-dev-k3s-medium",
    }

    for product_id, product in canonical.items():
        module_name = product["module_name"]
        digest = module_content_digest(MODULE_ROOT / module_name)
        assert digest == product["artifact_digest"]
        assert CATALOG_BY_CODE[product_id]["artifact_digest"] == digest
        assert TERRAFORM_PRODUCTS[product_id].artifact_digest == digest
        assert ALLOWED_MODULES[module_name]["artifact_digest"] == digest
        if "k3s" in module_name:
            assert product["configuration_digest"] == K3S_CONFIGURATION_DIGEST
            assert CATALOG_BY_CODE[product_id]["configuration_digest"] == K3S_CONFIGURATION_DIGEST
            assert TERRAFORM_PRODUCTS[product_id].configuration_digest == K3S_CONFIGURATION_DIGEST
            assert ALLOWED_MODULES[module_name]["configuration_digest"] == K3S_CONFIGURATION_DIGEST


def test_fixed_modules_are_private_nova_only() -> None:
    forbidden = (
        'resource "openstack_networking_floatingip_v2"',
        'resource "openstack_networking_network_v2"',
        'resource "openstack_networking_subnet_v2"',
        'resource "openstack_networking_router_v2"',
        'resource "openstack_networking_secgroup_v2"',
        'resource "openstack_identity_',
        "admin_pass",
        "remote-exec",
        "local-exec",
    )
    expected_products = {
        "openstack-dev-vm-small": "DEV-OS-VM-S",
        "openstack-dev-vm-medium": "DEV-OS-VM-M",
        "openstack-dev-vm-large": "DEV-OS-VM-L",
        "openstack-dev-k3s-small": "DEV-OS-K3S-S",
        "openstack-dev-k3s-medium": "DEV-OS-K3S-M",
    }
    for module_name, product_id in expected_products.items():
        module = MODULE_ROOT / module_name
        main = (module / "main.tf").read_text(encoding="utf-8")
        outputs = (module / "outputs.tf").read_text(encoding="utf-8")
        versions = (module / "versions.tf").read_text(encoding="utf-8")
        assert main.count('resource "openstack_compute_instance_v2"') == 1
        assert main.count('resource "openstack_networking_port_v2"') == 1
        assert "port_security_enabled" in main
        assert "security_group_ids" in main
        assert "config_drive" in main
        assert "private-only" in main
        assert product_id in main
        assert all(value not in main for value in forbidden)
        assert 'value = false' in outputs
        assert "floating_ip" in outputs
        assert "password" not in outputs.lower()
        assert "secret" not in outputs.lower()
        assert 'source  = "terraform-provider-openstack/openstack"' in versions
        assert 'version = "~> 3.4.0"' in versions

        if "k3s" in module_name:
            assert "user_data" not in main
            assert 'ConfigurationOwner  = "ANSIBLE"' in main
            assert 'value = "CONFIGURATION_REQUIRED"' in outputs
            assert "kubeconfig" not in outputs.lower()
            assert "token" not in outputs.lower()
        else:
            assert "user_data" not in main


def test_ansible_k3s_configuration_is_digest_pinned_and_fail_closed() -> None:
    assert module_content_digest(ANSIBLE_ROOT) == K3S_CONFIGURATION_DIGEST
    tasks = (ANSIBLE_ROOT / "roles/k3s_single_node/tasks/main.yaml").read_text(
        encoding="utf-8"
    )
    config = (ANSIBLE_ROOT / "roles/k3s_single_node/templates/config.yaml.j2").read_text(
        encoding="utf-8"
    )
    baseline = (
        ANSIBLE_ROOT / "roles/k3s_single_node/templates/dev-baseline.yaml.j2"
    ).read_text(encoding="utf-8")
    assert "checksum_algorithm: sha256" in tasks
    assert "k3s_airgap_images_sha256" in tasks
    assert "get --raw=/readyz" in tasks
    assert all(
        component in tasks
        for component in ("coredns", "metrics-server", "local-path-provisioner")
    )
    assert 'write-kubeconfig-mode: "0600"' in config
    assert "secrets-encryption: true" in config
    assert all(
        kind in baseline
        for kind in ("kind: ResourceQuota", "kind: LimitRange", "kind: NetworkPolicy")
    )


def test_catalog_denies_public_and_unregistered_change() -> None:
    catalog = json.loads((ROOT / "terraform/catalog.json").read_text(encoding="utf-8"))
    assert catalog["provider"] == "openstack"
    assert catalog["authority_state"] == "LOCAL_CANDIDATE"
    assert catalog["deployment_authorized"] is False
    denied = set(catalog["denied_capabilities"])
    assert {
        "floating_ip",
        "create_network",
        "create_security_group",
        "create_identity",
        "arbitrary_hcl",
        "unapproved_image",
        "unapproved_flavor",
        "unvalidated_k3s_bootstrap",
    }.issubset(denied)
