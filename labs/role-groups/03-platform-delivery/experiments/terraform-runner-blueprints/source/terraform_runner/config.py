from __future__ import annotations

import os
from dataclasses import dataclass


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    approval_api_url: str = "http://approval-api:8001"
    runner_id: str = "terraform-runner"
    auth_mode: str = "oidc"
    service_token_url: str = ""
    service_client_id: str = ""
    service_client_secret_file: str = ""
    service_scope: str = "service:callback"
    poll_interval_seconds: float = 2.0
    callback_timeout_seconds: float = 10.0
    runner_mode: str = "mock"
    terraform_bin: str = "terraform"
    terraform_binary_sha256: str = ""
    terraform_supply_chain_lock: str = "/workspace/terraform/supply-chain-lock.json"
    terraform_catalog: str = "/workspace/terraform/catalog.json"
    terraform_provider_mirror_root: str = ""
    openstack_provider_package: str = ""
    openstack_provider_package_sha256: str = ""
    module_root: str = "/workspace/terraform/modules"
    work_root: str = "/work"
    state_root: str = "/state"
    deployment_authorized: bool = False
    clouds_config_file: str = ""
    cloud_name: str = ""
    target_region: str = "RegionOne"
    network_id: str = ""
    security_group_ids: tuple[str, ...] = ()
    approved_image_name: str = ""
    approved_k3s_image_name: str = ""
    keypair_name: str = ""
    flavor_small: str = ""
    flavor_medium: str = ""
    flavor_large: str = ""
    k3s_configuration_authorized: bool = False
    ansible_playbook_bin: str = "ansible-playbook"
    ansible_root: str = "/workspace/ansible"
    ansible_remote_user: str = ""
    ansible_private_key_file: str = ""
    ansible_known_hosts_file: str = ""
    k3s_binary_path: str = ""
    k3s_binary_sha256: str = ""
    k3s_airgap_images_path: str = ""
    k3s_airgap_images_sha256: str = ""
    mock_delay_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            approval_api_url=os.getenv("APPROVAL_API_URL", "http://approval-api:8001").rstrip("/"),
            runner_id=os.getenv("RUNNER_ID", "terraform-runner"),
            auth_mode=os.getenv("AUTH_MODE", "oidc").lower(),
            service_token_url=os.getenv("SERVICE_TOKEN_URL", ""),
            service_client_id=os.getenv("SERVICE_CLIENT_ID", ""),
            service_client_secret_file=os.getenv("SERVICE_CLIENT_SECRET_FILE", ""),
            service_scope=os.getenv("SERVICE_SCOPE", "service:callback"),
            poll_interval_seconds=float(os.getenv("POLL_INTERVAL_SECONDS", "2")),
            callback_timeout_seconds=float(os.getenv("CALLBACK_TIMEOUT_SECONDS", "10")),
            runner_mode=os.getenv("RUNNER_MODE", "mock").lower(),
            terraform_bin=os.getenv("TERRAFORM_BIN", "terraform"),
            terraform_binary_sha256=os.getenv("TF_TERRAFORM_BINARY_SHA256", "").lower(),
            terraform_supply_chain_lock=os.getenv(
                "TF_SUPPLY_CHAIN_LOCK", "/workspace/terraform/supply-chain-lock.json"
            ),
            terraform_catalog=os.getenv(
                "TF_TERRAFORM_CATALOG", "/workspace/terraform/catalog.json"
            ),
            terraform_provider_mirror_root=os.getenv("TF_PROVIDER_MIRROR_ROOT", ""),
            openstack_provider_package=os.getenv("TF_OPENSTACK_PROVIDER_PACKAGE", ""),
            openstack_provider_package_sha256=os.getenv(
                "TF_OPENSTACK_PROVIDER_PACKAGE_SHA256", ""
            ).lower(),
            module_root=os.getenv("TERRAFORM_MODULE_ROOT", "/workspace/terraform/modules"),
            work_root=os.getenv("TERRAFORM_WORK_ROOT", "/work"),
            state_root=os.getenv("TERRAFORM_STATE_ROOT", "/state"),
            deployment_authorized=_bool(
                os.getenv("TF_OPENSTACK_DEPLOYMENT_AUTHORIZED", "false")
            ),
            clouds_config_file=os.getenv("OS_CLIENT_CONFIG_FILE", ""),
            cloud_name=os.getenv("OS_CLOUD", ""),
            target_region=os.getenv("OS_REGION_NAME", "RegionOne"),
            network_id=os.getenv("TF_OPENSTACK_NETWORK_ID", ""),
            security_group_ids=_csv(os.getenv("TF_OPENSTACK_SECURITY_GROUP_IDS", "")),
            approved_image_name=os.getenv("TF_OPENSTACK_APPROVED_IMAGE_NAME", ""),
            approved_k3s_image_name=os.getenv("TF_OPENSTACK_APPROVED_K3S_IMAGE_NAME", ""),
            keypair_name=os.getenv("TF_OPENSTACK_KEYPAIR_NAME", ""),
            flavor_small=os.getenv("TF_OPENSTACK_FLAVOR_SMALL", ""),
            flavor_medium=os.getenv("TF_OPENSTACK_FLAVOR_MEDIUM", ""),
            flavor_large=os.getenv("TF_OPENSTACK_FLAVOR_LARGE", ""),
            k3s_configuration_authorized=_bool(
                os.getenv("TF_K3S_CONFIGURATION_AUTHORIZED", "false")
            ),
            ansible_playbook_bin=os.getenv("ANSIBLE_PLAYBOOK_BIN", "ansible-playbook"),
            ansible_root=os.getenv("ANSIBLE_ROOT", "/workspace/ansible"),
            ansible_remote_user=os.getenv("TF_K3S_ANSIBLE_REMOTE_USER", ""),
            ansible_private_key_file=os.getenv("TF_K3S_ANSIBLE_PRIVATE_KEY_FILE", ""),
            ansible_known_hosts_file=os.getenv("TF_K3S_ANSIBLE_KNOWN_HOSTS_FILE", ""),
            k3s_binary_path=os.getenv("TF_K3S_BINARY_PATH", ""),
            k3s_binary_sha256=os.getenv("TF_K3S_BINARY_SHA256", "").lower(),
            k3s_airgap_images_path=os.getenv("TF_K3S_AIRGAP_IMAGES_PATH", ""),
            k3s_airgap_images_sha256=os.getenv(
                "TF_K3S_AIRGAP_IMAGES_SHA256", ""
            ).lower(),
            mock_delay_seconds=float(os.getenv("MOCK_DELAY_SECONDS", "1")),
        )
